from run import app
from apps import db
from apps.authentication.models import Users

with app.app_context():
    # 1. Definisikan username untuk Super Admin wilayah tersebut
    username_admin = "admin_margadana" 

    # Cek apakah user sudah ada
    old_user = Users.query.filter_by(username=username_admin).first()
    if old_user:
        db.session.delete(old_user)
        db.session.commit()

    # 2. Buat user baru (Pengawas Gizi wilayah Margadana)
    new_super_admin = Users(
        username=username_admin,
        email="pengawas.margadana@gizi.com",
        password="admingizi123",    # Otomatis di-hash oleh @password.setter
        role='super_admin',         # Role untuk akses monitoring live
        is_approved=True,
        fullname="Anton",
        
        # Kunci wilayah agar terhubung otomatis
        district="Margadana",       # HARUS SAMA dengan district Admin Dapur
        city="Kota Tegal"
    )
    
    db.session.add(new_super_admin)
    db.session.commit()
    print(f"Super Admin {username_admin} berhasil dibuat dan terhubung ke wilayah Margadana.")