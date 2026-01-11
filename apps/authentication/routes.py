# -*- encoding: utf-8 -*-
from flask import render_template, redirect, request, url_for, current_app, flash, session
from flask_login import current_user, login_user, logout_user
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename
import os
import uuid

# Import objek global dari apps
from apps import db, login_manager, oauth
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users

# =========================================================
#  HELPER FUNCTIONS
# =========================================================

def get_google_client():
    """Mengambil konfigurasi Google OAuth. Pastikan sudah di-init di apps/__init__.py"""
    if hasattr(oauth, 'google'):
        return oauth.google
    
    return oauth.register(
        name='google',
        client_id=current_app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

def save_file(file_obj):
    """Menyimpan file pendaftaran dengan validasi ukuran maksimal 2MB."""
    if not file_obj:
        return None
    try:
        # Cek ukuran file (Max 2MB)
        file_obj.seek(0, os.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0) # Reset pointer
        
        if file_size > 2 * 1024 * 1024:
            return "SIZE_ERROR"

        filename = secure_filename(file_obj.filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        upload_path = current_app.config.get('UPLOAD_FOLDER', 'apps/static/uploads')
        
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            
        full_path = os.path.join(upload_path, unique_name)
        file_obj.save(full_path)
        return f"/static/uploads/{unique_name}"
    except Exception as e:
        current_app.logger.error(f"Error saving file: {e}")
        return None

# =========================================================
#  AUTENTIKASI GOOGLE
# =========================================================

# apps/authentication/routes.py

@blueprint.route('/login/google')
def google_login():
    """Menerima parameter intent: 'login' atau 'register'."""
    # Ambil intent dari URL, default ke 'login' jika tidak ada
    intent = request.args.get('intent', 'login')
    session['auth_intent'] = intent 
    
    google = get_google_client()
    redirect_uri = url_for('authentication_blueprint.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@blueprint.route('/google-callback')
def google_callback():
    google = get_google_client()
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        flash("Gagal mengambil data dari Google.", "danger")
        return redirect(url_for('authentication_blueprint.login'))

    email = user_info.get('email')
    user = Users.query.filter_by(email=email).first()
    intent = session.pop('auth_intent', 'login')

    if user:
        # Filter Role untuk Google Login
        allowed_web_roles = ['admin_dapur', 'super_admin']
        if user.role not in allowed_web_roles:
            flash("Akses Ditolak: Gunakan Aplikasi Mobile.", "danger")
            return redirect(url_for('authentication_blueprint.login'))

        if intent == 'register':
            flash("Email sudah terdaftar. Silakan Masuk.", "info")
            return redirect(url_for('authentication_blueprint.login'))
        
        if user.role == 'admin_dapur' and not user.is_approved:
            return render_template('home/pending_approval.html', form=LoginForm())
        
        login_user(user)
        return redirect(url_for('home_blueprint.index'))

    else:
        # Alur jika user belum terdaftar
        if intent == 'login':
            flash("Email belum terdaftar. Silakan Daftar.", "danger")
            return redirect(url_for('authentication_blueprint.login'))
        
        session['google_data'] = {'email': email, 'fullname': user_info.get('name')}
        return redirect(url_for('authentication_blueprint.register'))
    
    return redirect(url_for('authentication_blueprint.login'))

# =========================================================
#  LOGIN & REGISTER MANUAL
# =========================================================
@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    
    # A. PRIORITAS: PROSES DATA YANG DIKETIK (POST)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()

        # Debug: Cek di terminal apakah user ditemukan
        print(f">>> MENCARI USER: {email}")

        if user and user.verify_password(password):
            # 1. Bersihkan sesi Santoso secara total sebelum Yanto masuk
            logout_user()
            session.clear()
            
            # 2. Login sebagai Yanto
            login_user(user)
            print(f">>> LOGIN BERHASIL: {user.email}")
            return redirect(url_for('home_blueprint.index'))
        
        # Jika gagal di sini, berarti data di DB memang tidak cocok
        print(">>> LOGIN GAGAL: Password atau Email salah di DB.")
        return render_template('accounts/login.html', 
                             msg='Username atau Password salah', 
                             form=login_form)

    # B. CEK SESI LAMA (Hanya saat baru buka halaman/GET)
    if current_user.is_authenticated:
        allowed_web_roles = ['admin_dapur', 'super_admin']
        if current_user.role not in allowed_web_roles:
            logout_user()
            session.clear()
            return render_template('accounts/login.html', form=login_form)
        return redirect(url_for('home_blueprint.index'))

    return render_template('accounts/login.html', form=login_form)
@blueprint.route('/register-choice')
def register_choice():
    """Halaman pilihan metode pendaftaran."""
    return render_template('accounts/pilihan_pendaftaran.html')

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    google_data = session.get('google_data')

    if request.method == 'POST':
        # Sinkronisasi pilihan wilayah dinamis dari request form
        create_account_form.province.choices = [(request.form.get('province'), request.form.get('province'))]
        create_account_form.regency.choices = [(request.form.get('regency'), request.form.get('regency'))]
        create_account_form.district.choices = [(request.form.get('district'), request.form.get('district'))]

        email = request.form.get('email')
        password = request.form.get('password')
        confirm_pass = request.form.get('confirm_password')

        if password != confirm_pass:
            return render_template('accounts/register.html', msg='Password tidak cocok', form=create_account_form, google_data=google_data)

        if Users.query.filter_by(email=email).first():
            return render_template('accounts/register.html', msg='Email sudah terdaftar', form=create_account_form, google_data=google_data)

        try:
            # Simpan Berkas Dokumen dengan pengecekan ukuran
            path_ktp = save_file(request.files.get('file_ktp'))
            path_slhs = save_file(request.files.get('file_slhs'))
            path_kitchen = save_file(request.files.get('file_kitchen_photo'))

            if "SIZE_ERROR" in [path_ktp, path_slhs, path_kitchen]:
                flash("Salah satu file terlalu besar (Maksimal 2MB)", "danger")
                return render_template('accounts/register.html', form=create_account_form, google_data=google_data)

            new_user = Users(
                email=email,
                password=password,
                role='admin_dapur',
                is_approved=False,
                fullname=request.form.get('fullname'),
                nik=request.form.get('nik'),
                whatsapp=request.form.get('whatsapp'),
                kitchen_name=request.form.get('kitchen_name'),
                mitra_type=request.form.get('mitra_type'),
                province=request.form.get('province'),
                regency=request.form.get('regency'),
                district=request.form.get('district'),
                address=request.form.get('address'),
                coordinates=request.form.get('coordinates'),
                file_ktp=path_ktp,
                file_slhs=path_slhs,
                file_kitchen_photo=path_kitchen
            )

            db.session.add(new_user)
            db.session.commit()
            session.pop('google_data', None) # Hapus data session setelah sukses

            return render_template('accounts/login.html', msg='Pendaftaran Berhasil! Menunggu verifikasi admin.', form=LoginForm())

        except Exception as e:
            db.session.rollback()
            return render_template('accounts/register.html', msg=f'Terjadi kesalahan: {str(e)}', form=create_account_form, google_data=google_data)

    return render_template('accounts/register.html', form=create_account_form, google_data=google_data)

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))