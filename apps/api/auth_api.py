import os
import jwt
import random
import string
import secrets
from datetime import datetime, timedelta, timezone, date 
from flask import request, jsonify, current_app
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from flask_login import current_user

from apps import db
from apps.authentication.models import Users, LogDistribusi, Artikel,MasterIngredient, Menus, MenuIngredients,UlasanPenerima
from . import api_bp
from apps.api.utils import token_required

mail = Mail()

# --- HELPER: OTP & EMAIL ---
def send_otp_email(target_email):
    """Menghasilkan OTP 6 digit dan mengirimkannya ke email tujuan."""
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    msg = Message("Verifikasi Perubahan Email - MBG",
                  recipients=[target_email])
    msg.body = f"Kode OTP Anda adalah: {otp_code}. Kode ini digunakan untuk memverifikasi email baru Anda."
    
    try:
        mail.send(msg)
        return otp_code
    except Exception as e:
        print(f"Error sending email: {e}")
        return None

# --- HELPER: SIMPAN DOKUMEN ---
def save_document(file, folder):
    if file:
        filename = secure_filename(file.filename)
        unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file.save(os.path.join(upload_path, unique_name))
        
        db_path = os.path.join(folder, unique_name).replace('\\', '/')
        return db_path
    return None

# --- HELPER: GENERATE TOKEN (Sesuai Batasan String(10)) ---
def generate_random_token():
    """REG- (4 char) + 6 digit = 10 karakter."""
    digits = ''.join(random.choices(string.digits, k=6))
    return f"REG-{digits}"


# --- 1. RUTE REGISTRASI ---
@api_bp.route('/register', methods=['POST'])
def register():
    data = request.form 
    role = data.get('role')
    phone = data.get('phone')
    email = data.get('email') 
    
    user_exists = Users.query.filter((Users.phone == phone) | (Users.email == email)).first()
    if user_exists:
        msg = "Nomor HP sudah terdaftar" if user_exists.phone == phone else "Email sudah terdaftar"
        return jsonify({"status": "error", "message": msg}), 400

    new_user = Users(
        fullname=data.get('fullname'),
        phone=phone, 
        email=email,
        role=role,
        province=data.get('province'),
        city=data.get('city'),
        district=data.get('district'),
        village=data.get('village'),
        address=data.get('address'),
        dapur_id=data.get('dapur_id'), 
        is_approved=False 
    )
    new_user.password = data.get('password')

    # Logika Khusus Sekolah
    if role == 'pengelola_sekolah':
        new_user.npsn = data.get('npsn')
        new_user.school_name = data.get('school_name')
        new_user.student_count = int(data.get('student_count', 0))
        new_user.school_token = generate_random_token() # Simpan ke DB
        
        if 'file_sk_operator' in request.files:
            new_user.file_sk_operator = save_document(request.files['file_sk_operator'], 'documents/sk')

    # Logika Khusus Siswa
    elif role == 'siswa':
        sekolah_id = data.get('sekolah_id')
        token_input = data.get('registration_token')

        if not sekolah_id or not token_input:
            return jsonify({"status": "error", "message": "Pilih Sekolah dan masukkan Token"}), 400

        school = Users.query.filter_by(id=sekolah_id, role='pengelola_sekolah').first()
        if not school:
            return jsonify({"status": "error", "message": "Sekolah tidak ditemukan"}), 404

        # Validasi Token
        if school.school_token != token_input:
            return jsonify({"status": "error", "message": "Token registrasi salah!"}), 401

        new_user.nisn = data.get('nisn')
        new_user.sekolah_id = sekolah_id
        new_user.dapur_id = school.dapur_id 

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "status": "success", 
            "message": f"Registrasi {role} berhasil. Tunggu verifikasi admin.",
            "token_anda": new_user.school_token if role == 'pengelola_sekolah' else None
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# --- 2. RUTE LOGIN ---
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')

    user = Users.query.filter_by(phone=phone).first()

    if not user or not user.verify_password(password):
        return jsonify({"status": "error", "message": "Nomor HP atau Password salah"}), 401

    # Ambil Nama Sekolah Dinamis
    display_school_name = user.school_name 
    if user.role == 'siswa' and user.sekolah_id:
        sekolah_terkait = Users.query.get(user.sekolah_id)
        display_school_name = sekolah_terkait.school_name if sekolah_terkait else "Sekolah Tidak Ditemukan"

    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        "status": "success",
        "token": token,
        "data": {
            "name": user.fullname,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_approved": bool(user.is_approved),
            "school_name": display_school_name, 
            "registration_token": user.school_token,
            "nisn": user.nisn
        }
    })

@api_bp.route('/update-profile', methods=['POST'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    
    try:
        # 1. Update data dasar (Berlaku untuk semua role)
        if 'name' in data: current_user.fullname = data.get('name')
        if 'email' in data: current_user.email = data.get('email')
        if 'phone' in data: current_user.phone = data.get('phone')

        # 2. Update data spesifik berdasarkan ROLE
        if current_user.role == 'pengelola_sekolah':
            if 'npsn' in data: current_user.npsn = data.get('npsn')
            if 'school_name' in data: current_user.school_name = data.get('school_name')
        
        elif current_user.role == 'siswa':
            if 'nisn' in data: current_user.nisn = data.get('nisn')
            if 'class' in data: current_user.student_class = data.get('class') # Pastikan kolom ini ada di Model
            
        elif current_user.role == 'lansia':
            if 'nik' in data: current_user.nik = data.get('nik') # Pastikan kolom ini ada di Model
            # Lansia mungkin tidak punya NPSN/Sekolah

        db.session.commit()
        return jsonify({"status": "success", "message": f"Profil {current_user.role} berhasil diperbarui"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/request-change-email', methods=['POST'])
@token_required
def request_change_email(current_user):
    data = request.get_json()
    new_email = data.get('new_email')
    password = data.get('password')

    if not current_user.verify_password(password):
        return jsonify({"status": "error", "message": "Password salah"}), 401

    if Users.query.filter_by(email=new_email).first():
        return jsonify({"status": "error", "message": "Email sudah digunakan"}), 400

    otp = send_otp_email(new_email)
    if otp:
        current_user.temp_otp = otp
        current_user.otp_created_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({"status": "success", "message": "OTP terkirim (Berlaku 5 menit)"}), 200
    
    return jsonify({"status": "error", "message": "Gagal mengirim OTP"}), 500

@api_bp.route('/verify-change-email', methods=['POST'])
@token_required
def verify_change_email(current_user):
    data = request.get_json()
    otp_input = data.get('otp')
    new_email = data.get('new_email')

    if current_user.temp_otp == otp_input:
        current_user.email = new_email
        current_user.temp_otp = None
        db.session.commit()
        return jsonify({"status": "success", "message": "Email berhasil diperbarui"}), 200
    
    return jsonify({"status": "error", "message": "OTP tidak valid"}), 400
    
@api_bp.route('/check-status', methods=['GET'])
@token_required
def check_status(current_user):
    return jsonify({
        "status": "success",
        "role": current_user.role,
        "is_approved": current_user.is_approved,
        "data": {
            "name": current_user.fullname,
            "email": current_user.email,
            "school_name": current_user.school_name, #
            "school_token": current_user.school_token
        }
    })

@api_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    if not current_user.verify_password(data.get('old_password')):
        return jsonify({"status": "error", "message": "Password lama salah"}), 401

    try:
        current_user.password = data.get('new_password')
        db.session.commit()
        return jsonify({"status": "success", "message": "Password diperbarui"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 5. GET PARTNERS (LOGIKA DIPERBAIKI) ---
@api_bp.route('/get-partners', methods=['GET'])
def get_partners():
    target_role = request.args.get('role') 
    district_name = request.args.get('district')

    if not target_role or not district_name:
        return jsonify([]), 200

    partners = Users.query.filter(
        Users.role == target_role,
        Users.is_approved == True,
        Users.district.ilike(f"%{district_name}%")
    ).all()

    return jsonify([{
        "id": p.id,
        "name": p.kitchen_name if p.role == 'admin_dapur' else p.school_name,
        "address": p.address
    } for p in partners]), 200

@api_bp.route('/v1/menu-hari-ini', methods=['GET'])
def api_get_today_menu():
    """Endpoint JSON dinamis berdasarkan tanggal yang dipilih di mobile."""
    try:
        # Ambil parameter tanggal dari URL (?date=2026-01-12)
        # Jika tidak ada parameter, maka gunakan hari ini sebagai default
        date_str = request.args.get('date')
        
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today() 
        
        # Filter berdasarkan target_date yang diminta
        menu = Menus.query.filter_by(distribution_date=target_date).first()

        if not menu:
            return jsonify({
                "status": "empty", 
                "message": f"Belum ada menu untuk tanggal {target_date}"
            }), 404

        komponen_piring = []
        for item in menu.components:
            komponen_piring.append({
                "n": item.ingredient_info.name,
                "b": f"{int(item.weight)} g" if "Susu" not in item.ingredient_info.category else f"{int(item.weight)} ml",
                "c": "#1A237E" # Warna biru primary untuk UI Flutter
            })

        return jsonify({
            "status": "success",
            "data": {
                "id": menu.id,
                "menu": menu.menu_name,
                "image": f"{request.host_url.rstrip('/')}/static/uploads/menus/{menu.photo}" if menu.photo else None,
                "kcal": str(int(menu.total_kcal)),
                "nutrisi": {
                    "karbo": {"b": f"{int(menu.total_carb)}g", "p": "60%"},
                    "prot": {"b": f"{int(menu.total_protein)}g", "p": "15%"},
                    "lem": {"b": f"{int(menu.total_fat)}g", "p": "25%"},
                    "serat": f"{menu.total_fiber}g",
                    "zat_besi": f"{menu.total_iron}mg",
                    "kalsium": f"{menu.total_calcium}mg"
                },
                "komponen": komponen_piring
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- 4. RUTE REGENERATE TOKEN (Dashboard Sekolah) ---
@api_bp.route('/school/regenerate-token', methods=['POST'])
@token_required
def regenerate_token(current_user):
    if current_user.role != 'pengelola_sekolah':
        return jsonify({"status": "error", "message": "Akses ditolak"}), 403

    new_token = generate_random_token()
    try:
        current_user.school_token = new_token
        db.session.commit()
        return jsonify({"status": "success", "new_token": new_token}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 6. ADMINISTRASI SEKOLAH (VERIFIKASI SISWA) ---
@api_bp.route('/school/pending-students', methods=['GET'])
@token_required
def get_pending_students(current_user):
    if current_user.role != 'pengelola_sekolah':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    pending = Users.query.filter_by(sekolah_id=current_user.id, role='siswa', is_approved=False).all()
    data = [{
        "id": s.id,
        "fullname": s.fullname,
        "phone": s.phone,
        "email": s.email,
        "nisn": s.nisn
    } for s in pending]

    return jsonify({"status": "success", "data": data})


@api_bp.route('/school/stats', methods=['GET'])
@token_required
def get_school_stats(current_user):
    # 1. Hitung antrian verifikasi (Siswa yang baru daftar tapi belum disetujui)
    perlu_verifikasi = Users.query.filter_by(
        sekolah_id=current_user.id, 
        role='siswa', 
        is_approved=False
    ).count()

    # 2. Hitung total siswa yang sudah aktif
    total_siswa = Users.query.filter_by(
        sekolah_id=current_user.id, 
        role='siswa', 
        is_approved=True
    ).count()

    # 3. CEK KONFIRMASI HARI INI (Penting untuk pembatasan 1x sehari)
    # Mencari apakah sudah ada log distribusi dari sekolah ini pada tanggal hari ini
    sudah_konfirmasi = LogDistribusi.query.filter(
        LogDistribusi.sekolah_id == current_user.id,
        db.func.date(LogDistribusi.waktu_sampai) == date.today()
    ).first()

    return jsonify({
        "status": "success",
        "data": {
            "total_siswa": total_siswa,
            "perlu_verifikasi": perlu_verifikasi,
            "school_token": current_user.school_token,
            # Mengirimkan status True/False ke Flutter
            "has_confirmed_today": True if sudah_konfirmasi else False 
        }
    })

@api_bp.route('/school/verify-student', methods=['POST'])
@token_required
def verify_student(current_user):
    data = request.get_json()
    student_id = data.get('student_id')
    action = data.get('action') 

    student = Users.query.get(student_id)
    if not student or student.sekolah_id != current_user.id:
        return jsonify({"status": "error", "message": "Siswa tidak ditemukan"}), 404

    if action == 'approve':
        student.is_approved = True
    elif action == 'reject':
        db.session.delete(student) 

    db.session.commit()
    return jsonify({"status": "success", "message": f"Siswa berhasil di-{action}"})

@api_bp.route('/school/students', methods=['GET'])
@token_required
def get_approved_students(current_user):
    """Mengambil semua siswa yang sudah disetujui di sekolah ini."""
    students = Users.query.filter_by(
        sekolah_id=current_user.id, 
        role='siswa', 
        is_approved=True
    ).all()

    data = [{
        "id": s.id,
        "fullname": s.fullname,
        "phone": s.phone,
        "email": s.email,
        "nisn": s.nisn,
        "class": s.user_class
    } for s in students]

    return jsonify({"status": "success", "data": data})

import re

# --- HELPER: LOGIKA KENAIKAN KELAS ---
def increment_class(current_class):
    if not current_class:
        return current_class
    
    # Mencari pola angka di awal string (contoh: '4' dari '4A')
    match = re.match(r"(\d+)(.*)", str(current_class))
    if match:
        number = int(match.group(1)) # Mengambil angka 4
        suffix = match.group(2)      # Mengambil huruf 'A'
        
        # Contoh: Jika sudah kelas 6 (SD) atau 12 (SMA), set status 'Lulus'
        if number >= 6 and number < 7: # Logika untuk SD
            return "LULUS"
        elif number >= 12: # Logika untuk SMA
            return "LULUS"
            
        return f"{number + 1}{suffix}" # Menggabungkan kembali menjadi '5A'
    return current_class

# --- UPDATE RUTE AKSI MASSAL ---
@api_bp.route('/school/bulk-action', methods=['POST'])
@token_required
def bulk_action_students(current_user):
    data = request.get_json()
    ids = data.get('student_ids', [])
    action = data.get('action') # 'promote', 'graduate', atau 'delete'

    if not ids:
        return jsonify({"status": "error", "message": "Pilih siswa terlebih dahulu"}), 400

    # Pastikan hanya memproses siswa yang terdaftar di sekolah pengelola tersebut
    students = Users.query.filter(Users.id.in_(ids), Users.sekolah_id == current_user.id).all()

    try:
        for s in students:
            if action == 'promote':
                # Menggunakan helper untuk menaikkan kelas secara otomatis
                s.user_class = increment_class(s.user_class)
            
            elif action == 'graduate':
                s.user_class = "LULUS"
                
            elif action == 'delete':
                db.session.delete(s)

        db.session.commit()
        return jsonify({
            "status": "success", 
            "message": f"Berhasil memproses {len(students)} siswa"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    
@api_bp.route('/school/confirm-arrival', methods=['POST'])
@token_required
def confirm_arrival(current_user):
    """
    Endpoint untuk sekolah mengonfirmasi kedatangan makanan.
    Request: Multipart Form Data (arrival_photo)
    """
    try:
        # 1. Validasi Keberadaan File
        if 'arrival_photo' not in request.files:
            return jsonify({"status": "error", "message": "File foto tidak ditemukan"}), 400
        
        file = request.files['arrival_photo']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Nama file kosong"}), 400

        # 2. Proses Penyimpanan File
        # Format nama file: arrival_SEKOLAH_ID_TIMESTAMP.jpg
        timestamp = int(datetime.now().timestamp())
        filename = secure_filename(f"arrival_{current_user.id}_{timestamp}.jpg")
        
        # Pastikan folder 'static/uploads/distribusi' sudah ada
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'distribusi')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            
        file.save(os.path.join(upload_path, filename))

        # 3. Simpan Log ke Tabel LogDistribusi
        new_log = LogDistribusi(
            dapur_id=current_user.dapur_id,    # Diambil dari relasi sekolah ke dapur
            sekolah_id=current_user.id,        # ID sekolah yang sedang login
            foto_bukti=filename,
            waktu_sampai=datetime.now(),
            porsi_sampai=current_user.student_count, # Otomatis mengambil estimasi porsi sekolah
            status='Diterima'
        )

        db.session.add(new_log)
        db.session.commit()

        return jsonify({
            "status": "success", 
            "message": "Konfirmasi kedatangan berhasil disimpan!",
            "data": {
                "waktu": new_log.waktu_sampai.strftime('%H:%M'),
                "porsi": new_log.porsi_sampai
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error Konfirmasi: {str(e)}")
        return jsonify({"status": "error", "message": "Terjadi kesalahan internal"}), 500
    

@api_bp.route('/submit-ulasan', methods=['POST', 'OPTIONS'])
@token_required
def api_submit_ulasan(current_user): 
    # --- HANDLE OPTIONS ---
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    try:
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({"status": "error", "message": "Data tidak diterima"}), 400
        
        # Ekstraksi Data dari JSON
        ulasan_teks = data.get('komentar', '')
        rating_val = int(data.get('rating', 0))
        tags_list = data.get('tags', [])
        tags_str = ",".join(tags_list) if isinstance(tags_list, list) else ""

        # --- LOGIKA BARU: MENGGUNAKAN AI MODEL ---
        # AI akan menganalisis teks komentar siswa secara mendalam
        sentiment_label = get_sentiment_prediction(ulasan_teks)

        # Gunakan 'current_user' dari dekorator
        new_review = UlasanPenerima(
            user_id=current_user.id,
            nama_pengulas=getattr(current_user, 'fullname', 'Pengguna'),
            rating=rating_val,
            tags=tags_str,
            ulasan_teks=ulasan_teks,
            status_ai=sentiment_label, # Hasil prediksi dari model BERT
            tanggal=datetime.now()
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "Ulasan berhasil dianalisis oleh AI dan terkirim!"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400