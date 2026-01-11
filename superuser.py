from run import app
from apps import db
from apps.authentication.models import Users

# Kita butuh context aplikasi untuk akses database
with app.app_context():
    
    # 1. Tentukan Identitas Super Admin
    username = "admin gizi"
    email = "admin.tegal@gizi.com"
    password = "admingizi123" # Pastikan di-hash oleh @password.setter di models.py

    # 2. Cek apakah user sudah ada
    check_user = Users.query.filter_by(username=username).first()

    if check_user:
        print(f"User '{username}' sudah ada. Tidak perlu dibuat ulang.")
    else:
        # 3. Buat User Baru dengan Data Wilayah Margadana
        super_admin = Users(
            username=username,
            email=email,
            password=password, # Akan otomatis di-hash oleh model
            
            # --- ROLE & STATUS ---
            role='super_admin',
            is_approved=True,  # Langsung aktif tanpa verifikasi
            
            # --- DATA IDENTITAS ---
            fullname="Admin Gizi Kota Tegal",
            whatsapp="081234567890",
            
            # --- DATA WILAYAH (Sesuai Request: Margadana)
            province="JAWA TENGAH",
            city="KOTA TEGAL",
            district="MARGADANA",
            village="MARGADANA",
            address="Kantor Dinas Gizi Margadana, Kota Tegal"
        )

        try:
            db.session.add(super_admin)
            db.session.commit()
            
            print("===========================================")
            print("SUKSES! Akun Super Admin Margadana Berhasil Dibuat.")
            print(f"Username : {username}")
            print(f"Role     : {super_admin.role}")
            print(f"Wilayah  : {super_admin.district}, {super_admin.city}")
            print("===========================================")
        except Exception as e:
            db.session.rollback()
            print(f"Gagal membuat akun: {str(e)}")