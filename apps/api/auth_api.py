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
from apps.authentication.util import hash_pass,  verify_pass
from sqlalchemy import or_

from apps import db
from apps.authentication.models import Users, LogDistribusi, Artikel,MasterIngredient, Menus, MenuIngredients,UlasanPenerima,AktivitasDapur,ChatHistory,LaporanKendala
from . import api_bp
from apps.api.utils import token_required
from apps.home.utils import get_sentiment_prediction, proses_verifikasi_ktp, get_chatbot_response

mail = Mail()


# Konfigurasi folder upload (Sesuaikan path ini)
UPLOAD_FOLDER = 'static/uploads/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/update-profile', methods=['POST'])
@token_required
def update_profile(current_user):
    try:
        # --- 1. Ambil Data Teks (Multipart Form) ---
        name = request.form.get('name')
        email = request.form.get('email') # Jika email boleh diubah
        phone = request.form.get('phone')
        
        # Data Role Spesifik
        npsn = request.form.get('npsn')
        school_name = request.form.get('school_name')
        nisn = request.form.get('nisn')
        student_class = request.form.get('user_class') # Key dari Flutter
        nik = request.form.get('nik')

        # --- 2. Update Data Dasar ---
        if name: current_user.fullname = name
        if email: current_user.email = email
        if phone: current_user.phone = phone
        
        # --- 3. Update Data Spesifik Role ---
        if current_user.role == 'pengelola_sekolah':
            if npsn: current_user.npsn = npsn
            if school_name: current_user.school_name = school_name
        
        elif current_user.role == 'siswa':
            if nisn: current_user.nisn = nisn
            if student_class: current_user.user_class = student_class 
            
        elif current_user.role in ['lansia', 'penerima_lansia']:
            if nik: current_user.nik = nik 

        # --- 4. Handle Upload Foto ---
        if 'photo' in request.files:
            file = request.files['photo']
            
            if file and allowed_file(file.filename):
                # Overwrite foto lama berdasarkan ID User
                new_filename = f"profile_{current_user.id}.jpg"
                
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                
                file.save(os.path.join(UPLOAD_FOLDER, new_filename))
                
                # Simpan nama file ke database
                current_user.profile_picture = new_filename

        # --- 5. Simpan ke Database ---
        db.session.commit()

        # --- 6. KIRIM RESPON LENGKAP (PENTING UNTUK FLUTTER) ---
        return jsonify({
            "status": "success", 
            "message": "Profil berhasil diperbarui",
            "data": {
                # Data Dasar
                "name": current_user.fullname,
                "phone": current_user.phone,
                "email": current_user.email,
                "role": current_user.role,
                "photo": current_user.profile_picture,
                
                # Data Role (Kirim semua agar _saveSession di Flutter tidak menimpa dengan null)
                "nik": getattr(current_user, 'nik', None),
                "nisn": getattr(current_user, 'nisn', None),
                "npsn": getattr(current_user, 'npsn', None),
                "school_name": getattr(current_user, 'school_name', None),
                "user_class": getattr(current_user, 'user_class', None),
                "is_approved": bool(current_user.is_approved)
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    
def get_db_context(user_message):
    context = ""
    
    # A. Cek jika tanya Menu
    if "menu" in user_message.lower():
        today_menu = Menus.query.filter_by(distribution_date=date.today()).first()
        if today_menu:
            context += f"Data Menu Hari Ini: {today_menu.menu_name}, Kalori: {today_menu.total_kcal} kcal. "
        else:
            context += "Data Menu: Belum ada menu yang diinput untuk hari ini. "

    # B. Cek jika tanya Distribusi/Pengiriman
    if "sampai" in user_message.lower() or "distribusi" in user_message.lower():
        # Contoh mengambil log terakhir
        last_delivery = LogDistribusi.query.order_by(LogDistribusi.waktu_sampai.desc()).first()
        if last_delivery:
            sekolah = Users.query.get(last_delivery.sekolah_id)
            context += f"Status Distribusi: Makanan terakhir sampai di {sekolah.school_name} pada jam {last_delivery.waktu_sampai.strftime('%H:%M')}. "

    # C. Cek jika tanya Progres Dapur
    if "dapur" in user_message.lower() or "masak" in user_message.lower():
        last_activity = AktivitasDapur.query.order_by(AktivitasDapur.waktu_mulai.desc()).first()
        if last_activity:
            dapur = Users.query.get(last_activity.user_id)
            context += f"Aktivitas Dapur: {dapur.kitchen_name} sedang melakukan {last_activity.jenis_aktivitas} (Status: {last_activity.status}). "

    return context

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





@api_bp.route('/register', methods=['POST'])
def register():
    # Menggunakan request.form karena mendukung pengiriman file (Multipart)
    data = request.form 
    # --- TAMBAHKAN BARIS INI UNTUK DEBUGGING ---
    print("----------------------------------------")
    print("DEBUG DATA MASUK:", data)
    print("DEBUG Role:", data.get('role'))
    print("DEBUG Sekolah ID:", data.get('sekolah_id'))
    print("DEBUG Token:", data.get('registration_token'))
    print("----------------------------------------")
    # ---------------------------------------------
    role = data.get('role')
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')
    
    # 1. Validasi Input Dasar
    if not phone or not password or not role:
        return jsonify({"status": "error", "message": "Data utama tidak lengkap"}), 400

    # 2. Cek duplikasi User (Nomor HP atau Email)
    user_exists = Users.query.filter((Users.phone == phone) | (Users.email == email)).first()
    if user_exists:
        msg = "Nomor HP sudah terdaftar" if user_exists.phone == phone else "Email sudah terdaftar"
        return jsonify({"status": "error", "message": msg}), 400

    # 3. Inisialisasi User Baru
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
        is_approved=False # Default menunggu verifikasi admin dapur
    )

    # --- POIN KRUSIAL: Menghindari Double Hashing ---
    # Kirim password string mentah ke setter model agar tidak terjadi AttributeError
    new_user.password = password

    # 4. Logika Khusus Berdasarkan Role
    if role == 'pengelola_sekolah':
        new_user.npsn = data.get('npsn')
        new_user.school_name = data.get('school_name')
        new_user.student_count = int(data.get('student_count', 0))
        new_user.school_token = generate_random_token() 
        
        # Simpan file SK Operator
        if 'file_sk_operator' in request.files:
            new_user.file_sk_operator = save_document(
                request.files['file_sk_operator'], 
                'documents/sk'
            )

    elif role == 'siswa':
        sekolah_id = data.get('sekolah_id')
        token_input = data.get('registration_token')

        if not sekolah_id or not token_input:
            return jsonify({"status": "error", "message": "Pilih Sekolah dan masukkan Token"}), 400

        school = Users.query.filter_by(id=sekolah_id, role='pengelola_sekolah').first()
        if not school or school.school_token != token_input:
            return jsonify({"status": "error", "message": "Token registrasi salah!"}), 401

        new_user.nisn = data.get('nisn')
        new_user.sekolah_id = sekolah_id
        new_user.dapur_id = school.dapur_id

    elif role == 'lansia':
        # --- PENAMBAHAN LOGIKA KHUSUS LANSIA ---
        # NIK hasil ekstraksi AI YOLOv11 dari Flutter
        new_user.nik = data.get('nik')
        
        # Titik GPS rumah untuk keperluan pengantaran makanan
        new_user.coordinates = data.get('coordinates')
        
        # Simpan file JPG KTP asli agar bisa direview Admin Dapur
        if 'file_ktp' in request.files:
            new_user.file_ktp = save_document(
                request.files['file_ktp'], 
                'documents/ktp'
            )

    # 5. Eksekusi Simpan ke Database
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
        return jsonify({"status": "error", "message": f"Database Error: {str(e)}"}), 500
    

# --- 2. RUTE LOGIN ---

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 1. Validasi Format JSON
    if not data:
        return jsonify({"status": "error", "message": "Format data tidak valid"}), 400

    # Ambil data
    identifier = data.get('phone', '').strip() 
    password = data.get('password')

    # 2. VALIDASI INPUT KOSONG (Ini yang mencegah Error 500/AttributeError)
    if not identifier or not password:
        return jsonify({
            "status": "error", 
            "message": "Nomor HP/Email dan Password wajib diisi"
        }), 400

    # 3. Cari User (Logic Email ATAU HP)
    user = Users.query.filter(
        or_(Users.phone == identifier, Users.email == identifier)
    ).first()

    # 4. Verifikasi Password
    if not user or not user.verify_password(password):
        return jsonify({"status": "error", "message": "Email/Nomor HP atau Password salah"}), 401

    # ... (Logika Nama Sekolah Dinamis tetap sama)
    display_school_name = user.school_name 
    if user.role == 'siswa' and user.sekolah_id:
        sekolah_terkait = Users.query.get(user.sekolah_id)
        display_school_name = sekolah_terkait.school_name if sekolah_terkait else "Sekolah Belum Terdaftar"

    # 3. Pembuatan JWT Token
    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    # 4. Kirim Respon Sukses
    return jsonify({
        "status": "success",
        "token": token,
        "data": {
            "name": user.fullname,
            "email": user.email,
            "phone": user.phone,
            "nik": user.nik,
            "role": user.role,
            "is_approved": bool(user.is_approved),
            "school_name": display_school_name, 
            "registration_token": user.school_token,
            "nisn": user.nisn
        }
    }), 200


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
        "role": current_user.role,             # Info untuk logika routing (opsional di sini)
        "is_approved": current_user.is_approved, 
        "data": {
            # --- DATA UTAMA (Wajib ada agar _saveSession Flutter aman) ---
            "name": current_user.fullname,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,                 # PENTING: Masukkan lagi disini
            "is_approved": current_user.is_approved,   # PENTING: Masukkan lagi disini
            
            # --- PERBAIKAN 1: FOTO PROFIL ---
            # Pastikan nama kolom di DB sesuai (misal: profile_picture atau photo)
            "photo": current_user.profile_picture, 

            # --- DATA SEKOLAH ---
            "school_name": current_user.school_name,
            # Registration token jika perlu disimpan
            "registration_token": getattr(current_user, 'registration_token', None), 
            
            # --- DATA SPESIFIK ROLE ---
            "npsn": getattr(current_user, 'npsn', None),
            "nisn": getattr(current_user, 'nisn', None),
            "nik": getattr(current_user, 'nik', None),

            # --- PERBAIKAN 2: KEY KELAS ---
            # Gunakan key 'user_class' agar cocok dengan Flutter
            "user_class": getattr(current_user, 'user_class', None) 
        }
    }), 200

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
    
@api_bp.route('/verify-ktp', methods=['POST'])
def api_verify_ktp():
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada gambar yang diunggah"}), 400
    
    file = request.files['image']
    img_bytes = file.read()
    
    # Menjalankan fungsi AI dari util.py
    result = proses_verifikasi_ktp(img_bytes)
    
    return jsonify(result)




# @api_bp.route('/forgot-password', methods=['POST', 'OPTIONS'], strict_slashes=False)
# def forgot_password():
#     # 1. Tangani Preflight OPTIONS (Wajib agar tidak Error 500)
#     if request.method == 'OPTIONS':
#         return jsonify({"status": "ok"}), 200

#     # 2. Ambil data JSON (Hanya untuk POST)
#     data = request.get_json()
    
#     # Validasi jika data kosong
#     if not data:
#         return jsonify({"status": "error", "message": "Format data tidak valid"}), 400

#     identifier = data.get('identifier', '').strip()
#     print(f"DEBUG: Mencari user dengan identifier: '{identifier}'")
    
#     # 3. Logika pencarian user (Gunakan or_ untuk Email/Phone)
#     from sqlalchemy import or_
#     user = Users.query.filter(or_(Users.email == identifier, Users.phone == identifier)).first()
    
#     if not user:
#         return jsonify({"status": "error", "message": "Akun tidak ditemukan"}), 404

#     # Generate OTP 6 Digit
#     otp = ''.join(random.choices(string.digits, k=6))
#     user.temp_otp = otp
#     user.otp_created_at = datetime.now(timezone.utc)
#     db.session.commit()

#     # Kirim OTP ke email yang terdaftar di akun tersebut
#     msg = Message("Reset Kata Sandi ", recipients=[user.email])
#     msg.body = f"Halo {user.fullname},\n\nKode OTP Anda untuk reset kata sandi adalah: {otp}"
    
#     try:
#         mail.send(msg)
#         return jsonify({
#             "status": "success", 
#             "message": f"OTP berhasil dikirim ke email: {user.email[:3]}***@***.com",
#             "phone": user.phone # Kembalikan phone untuk identifikasi di rute reset
#         }), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": "Gagal mengirim email"}), 500

@api_bp.route('/forgot-password', methods=['POST', 'OPTIONS'], strict_slashes=False)
def forgot_password():
    # 1. Handle Preflight OPTIONS untuk CORS
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    # 2. Ambil data dari Flutter
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Format data tidak valid"}), 400

    identifier = data.get('identifier', '').strip()
    
    # Debug untuk memastikan data masuk ke server
    print(f"DEBUG: Mencari user dengan identifier: '{identifier}'")

    # 3. Cari user berdasarkan Email ATAU Nomor HP
    user = Users.query.filter(or_(
        Users.email == identifier, 
        Users.phone == identifier
    )).first()

    if not user:
        return jsonify({
            "status": "error", 
            "message": "Akun tidak ditemukan. Pastikan Email atau No HP benar."
        }), 200

    # 4. Generate OTP 6 Digit Angka
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Simpan ke Database
    try:
        user.temp_otp = otp
        user.otp_created_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Gagal menyimpan data ke server"}), 500

    # 5. Kirim Email melalui Flask-Mail
    msg = Message(
        subject="Kode OTP Reset Kata Sandi MBG",
        sender="noreply@mbg-app.com", # Sesuaikan dengan pengirim Anda
        recipients=[user.email]
    )
    msg.body = f"Halo {user.fullname},\n\nKode OTP Anda untuk reset kata sandi adalah: {otp}\n\nKode ini bersifat rahasia. Mohon jangan berikan kepada siapapun."

    try:
        mail.send(msg)
        # Masking email untuk privasi (contoh: yan***@gmail.com)
        email_parts = user.email.split('@')
        masked_email = f"{email_parts[0][:3]}***@{email_parts[1]}"
        
        return jsonify({
            "status": "success",
            "message": f"Kode OTP telah dikirim ke email: {masked_email}",
            "phone": user.phone # Dikirim balik untuk identifikasi di halaman reset password
        }), 200
    except Exception as e:
        print(f"ERROR MAIL: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "Gagal mengirim email OTP. Periksa koneksi internet server."
        }), 500

@api_bp.route('/reset-password', methods=['POST', 'OPTIONS'], strict_slashes=False)
def reset_password():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    phone = data.get('phone')
    otp_input = data.get('otp')
    new_password = data.get('new_password')

    # 1. Cari user berdasarkan nomor HP (yang dikirim balik dari forgot-password)
    user = Users.query.filter_by(phone=phone).first()

    if not user:
        return jsonify({"status": "error", "message": "User tidak ditemukan"}), 404

    # 2. Validasi OTP (Pastikan tidak None dan cocok)
    if user.temp_otp and user.temp_otp == otp_input:
        # 3. Update Password (Ini akan otomatis di-hash oleh setter model)
        user.password = new_password 
        user.temp_otp = None  # Hapus OTP agar tidak bisa dipakai lagi
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "Kata sandi berhasil diperbarui, silakan login kembali"
        }), 200
    
    return jsonify({"status": "error", "message": "Kode OTP salah atau sudah kadaluarsa"}), 400

# apps/api/auth_api.py

@api_bp.route('/google-login', methods=['POST', 'OPTIONS'])
def google_login():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    email = data.get('email', '').strip().lower()

    # 1. Cari User di Database
    user = Users.query.filter_by(email=email).first()

    # 2. Proteksi: Hanya user terdaftar yang bisa login
    if not user:
        return jsonify({
            "status": "error",
            "message": "Akun tidak ditemukan. Silakan lakukan pendaftaran manual terlebih dahulu."
        }), 200

    # 3. Logika Nama Sekolah untuk Role Siswa
    display_school_name = user.school_name 
    if user.role == 'siswa' and user.sekolah_id:
        sekolah = Users.query.get(user.sekolah_id)
        display_school_name = sekolah.school_name if sekolah else "Sekolah Belum Terdaftar"

    # 4. Generate JWT Token
    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    # 5. Respon Data (Tanpa Avatar)
    return jsonify({
        "status": "success",
        "token": token,
        "data": {
            "name": user.fullname,
            "email": user.email,
            "phone": user.phone or "",
            "role": user.role, # 'siswa', 'pengelola_sekolah', atau 'lansia'
            "is_approved": bool(user.is_approved),
            "school_name": display_school_name
        }
    }), 200



@api_bp.route('/chatbot', methods=['POST'])
@token_required
def api_chatbot(current_user):
    # 1. Validasi Input
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"status": "error", "message": "Pesan tidak boleh kosong"}), 400

    try:
        # 2. Ambil Memory (3 Pesan Terakhir)
        # Memory membantu asisten memahami konteks pembicaraan sebelumnya
        past_chats = ChatHistory.query.filter_by(user_id=current_user.id)\
                     .order_by(ChatHistory.timestamp.desc()).limit(3).all()
        
        chat_memory = ""
        for chat in reversed(past_chats):
            chat_memory += f"User: {chat.message}\nAsisten: {chat.reply}\n"

        bot_reply = get_chatbot_response(user_message, chat_memory)

        # 4. Simpan Riwayat Baru ke Database
        new_chat = ChatHistory(
            user_id=current_user.id,
            message=user_message,
            reply=bot_reply,
            timestamp=datetime.now()
        )
        db.session.add(new_chat)
        db.session.commit()

        # 5. Kirim Respon ke Flutter
        return jsonify({
            "status": "success",
            "data": {
                "reply": bot_reply,
                "timestamp": datetime.now().strftime('%H:%M'),
                "user": current_user.username
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error pada Route Chatbot: {e}")
        return jsonify({
            "status": "error", 
            "message": "Terjadi kesalahan pada sistem asisten."
        }), 500

@api_bp.route('/laporkan-kendala', methods=['POST'])
@token_required # Asumsi Anda menggunakan decorator token untuk Flutter
def api_laporkan_kendala(current_user):
    # Pastikan hanya pengelola sekolah yang bisa melapor
    if current_user.role != 'pengelola_sekolah':
        return jsonify({"message": "Akses ditolak, hanya untuk pengelola"}), 403

    try:
        kategori = request.form.get('kategori')
        deskripsi = request.form.get('deskripsi')
        file = request.files.get('foto')

        # Ambil ID dapur yang bermitra dengan sekolah ini
        target_dapur_id = current_user.dapur_id
        
        if not target_dapur_id:
            return jsonify({"message": "Sekolah Anda belum terhubung ke mitra dapur"}), 400

        filename = None
        if file:
            # Penamaan file unik berdasarkan ID user dan timestamp
            filename = f"kendala_{current_user.id}_{int(datetime.now().timestamp())}.jpg"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'kendala', filename))

        new_report = LaporanKendala(
            user_id=current_user.id,
            dapur_id=target_dapur_id, # Otomatis terhubung ke dapur mitra
            kategori=kategori,
            deskripsi=deskripsi,
            foto_bukti=filename
        )
        
        db.session.add(new_report)
        db.session.commit()

        return jsonify({"status": "success", "message": "Laporan terkirim ke dapur mitra"}), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@api_bp.route('/articles', methods=['GET'])
@token_required
def get_article(current_user):
    try:
        # 1. Ambil data asli dari Database (Urutkan terbaru)
        articles = Artikel.query.order_by(Artikel.created_at.desc()).all()
        
        data = []
        for art in articles:
            # 2. Konstruksi URL Gambar yang Valid (Support Ngrok)
            # Pastikan folder 'static/uploads/articles/' sesuai dengan lokasi penyimpanan Anda
            image_url = None
            if art.foto:
                base_url = request.host_url.rstrip('/')
                image_url = f"{base_url}/static/uploads/articles/{art.foto}"

            # 3. Mapping data dari Model Python ke JSON Flutter
            data.append({
                "id": art.id,
                "judul": art.judul,           # Sesuai model: judul
                "konten": art.konten,         # Sesuai model: konten
                "target": art.target_role,    # Sesuai model: target_role
                "foto": art.foto,             # Nama file saja (backup)
                "image_url": image_url,       # URL Lengkap siap pakai
                "created_at": art.created_at.strftime('%Y-%m-%d')
            })

        return jsonify({
            "status": "success",
            "data": data
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500