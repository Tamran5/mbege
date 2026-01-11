import os
import jwt
import datetime
import random
import string
from flask import request, jsonify, current_app
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from apps import db
from apps.authentication.models import Users 
from . import api_bp
from apps.api.utils import token_required
from datetime import datetime, timedelta, timezone

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
        unique_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file.save(os.path.join(upload_path, unique_name))
        
        # Simpan path dengan format '/' agar kompatibel dengan URL
        db_path = os.path.join(folder, unique_name).replace('\\', '/')
        return db_path
    return None

# --- 1. RUTE REGISTRASI (MULTIPART) ---
@api_bp.route('/register', methods=['POST'])
def register():
    data = request.form 
    role = data.get('role')
    phone = data.get('phone')
    email = data.get('email') 
    
    user_exists = Users.query.filter(
        (Users.phone == phone) | (Users.email == email)
    ).first()
    
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
        # AMBIL DAPUR_ID DI SINI agar semua role (Sekolah/Lansia) memilikinya
        dapur_id=data.get('dapur_id'), 
        is_approved=False 
    )
    new_user.password = data.get('password')

    # Logika Khusus Sekolah
    if role == 'pengelola_sekolah':
        new_user.npsn = data.get('npsn')
        new_user.school_name = data.get('school_name')
        new_user.student_count = int(data.get('student_count', 0))
        if 'file_sk_operator' in request.files:
            new_user.file_sk_operator = save_document(request.files['file_sk_operator'], 'documents/sk')

    # TAMBAHKAN Logika Khusus Lansia
    elif role == 'lansia':
        new_user.nik = data.get('nik')
        new_user.coordinates = data.get('coordinates') 
        if 'file_ktp' in request.files:
            new_user.file_ktp = save_document(request.files['file_ktp'], 'documents/ktp')

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "status": "success", 
            "message": f"Registrasi {role} berhasil. Tunggu verifikasi admin."
        }), 201
    except Exception as e:
        db.session.rollback()
        # Debug ini sangat penting untuk melihat field mana yang error
        print(f"DATABASE ERROR: {str(e)}") 
        return jsonify({"status": "error", "message": f"Gagal simpan data: {str(e)}"}), 500

# --- 2. RUTE LOGIN ---
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    role = data.get('role')

    user = Users.query.filter_by(phone=phone).first()
    print(f">>> LOGIN SUCCESS: {user.fullname} | Role di DB: {user.role} | Approved: {user.is_approved}")

    if not user or not user.verify_password(password):
        return jsonify({"status": "error", "message": "Nomor HP atau Password salah"}), 401

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
            "npsn": user.npsn,
            "school_name": user.school_name,
            "nik": user.nik, 
            "coordinates": user.coordinates 
        }
    })

# --- 3. RUTE UPDATE PROFIL (BARU) ---
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
    try:
        return jsonify({
            "status": "success",
            "is_approved": current_user.is_approved,
            "role": current_user.role,
            "data": {
                "name": current_user.fullname,
                "email": current_user.email,
                "npsn": current_user.npsn,
                "school_name": current_user.school_name
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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