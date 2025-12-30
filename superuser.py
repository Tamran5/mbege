from run import app
from apps import db
from apps.authentication.models import Users

# Kita butuh context aplikasi untuk akses database
with app.app_context():
    
    # 1. Tentukan Username & Password Super Admin
    username = "admingizi"
    email = "admin@gizi.com"
    password = "admingizi123" # Ganti dengan password kuat

    # 2. Cek apakah user sudah ada biar tidak error duplikat
    check_user = Users.query.filter_by(username=username).first()

    if check_user:
        print(f"User '{username}' sudah ada. Tidak perlu dibuat ulang.")
    else:
        # 3. Buat User Baru
        # Perhatikan: Kita kosongkan data dapur (kitchen_name, dll) karena ini admin pusat
        super_admin = Users(
            username=username,
            email=email,
            password=password,
            
            # --- BAGIAN PENTING ---
            role='super_admin',  # Role khusus
            is_approved=True,    # HARUS TRUE agar bisa langsung login
            # ----------------------
            
            fullname="Admin Pusat Gizi",
            whatsapp="08000000000"
        )

        db.session.add(super_admin)
        db.session.commit()
        
        print("===========================================")
        print("SUKSES! Akun Super Admin Berhasil Dibuat.")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print("Silakan login di halaman /login")
        print("===========================================")