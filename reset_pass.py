from apps import db, create_app
from apps.config import config_dict
from apps.authentication.models import Users

app = create_app(config_dict['Debug'])

with app.app_context():
    # Ambil user Yanto dari ID 10 atau Email
    user = Users.query.filter_by(email='yanto@gmail.com').first()
    
    if user:
        # Cukup masukkan string biasa. Setter di models.py baris 74 
        # akan otomatis mengubahnya menjadi hash biner (BLOB)
        user.password = 'yanto' 
        
        db.session.commit()
        print("---------------------------------------------------")
        print("SUKSES: Password Yanto direset ke teks 'yanto'.")
        print("Model Anda telah otomatis melakukan hashing ke BLOB.")
        print("---------------------------------------------------")
    else:
        print("User tidak ditemukan.")