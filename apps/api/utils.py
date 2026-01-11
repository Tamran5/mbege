from flask import request, jsonify, current_app
from functools import wraps
import jwt
from apps.authentication.models import Users 

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Cek Header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'status': 'error', 'message': 'Token tidak ditemukan!'}), 401

        try:
            # 2. Decode menggunakan SECRET_KEY dari config aplikasi
            # Pastikan ini sama dengan saat login!
            data = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=["HS256"]
            )
            
            # 3. Cari User
            current_user = Users.query.filter_by(id=data['user_id']).first()
            
            if not current_user:
                return jsonify({'status': 'error', 'message': 'User tidak valid!'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token sudah kedaluwarsa!'}), 401
        except jwt.InvalidTokenError as e:
            # Tambahkan print untuk melihat alasan detail di console Flask
            print(f"JWT Error: {str(e)}") 
            return jsonify({'status': 'error', 'message': 'Token tidak valid!'}), 401
        except Exception as e:
            print(f"Unknown Error: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Terjadi kesalahan sistem!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated