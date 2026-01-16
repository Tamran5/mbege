from flask import request, jsonify, current_app
from functools import wraps
import jwt
from apps.authentication.models import Users 

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # --- 1. BYPASS UNTUK OPTIONS (PENTING!) ---
        # Browser (Flutter Web) mengirim OPTIONS tanpa header Authorization.
        # Kita izinkan lewat agar rute bisa menangani CORS dengan benar.
        if request.method == 'OPTIONS':
            return f(None, *args, **kwargs)

        token = None
        
        # 2. Ekstraksi Header dengan Validasi Karakter
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split(" ")
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]
        
        # 3. Cek apakah token benar-benar ada dan bukan string "null"
        if not token or token == "" or token == "null":
            return jsonify({
                'status': 'error', 
                'message': 'Token tidak ditemukan atau tidak valid!'
            }), 401

        try:
            # 4. Validasi Format Dasar (Segmen JWT)
            if token.count('.') != 2:
                raise jwt.InvalidTokenError("Format JWT tidak lengkap (kurang segmen)")

            # 5. Decode menggunakan SECRET_KEY
            data = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=["HS256"]
            )
            
            # 6. Cari User menggunakan Primary Key
            current_user = Users.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({
                    'status': 'error', 
                    'message': 'User sudah tidak terdaftar!'
                }), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({
                'status': 'error', 
                'message': 'Sesi Anda telah berakhir, silakan login kembali!'
            }), 401
        except jwt.InvalidTokenError as e:
            print(f"JWT Error: {str(e)}")
            return jsonify({
                'status': 'error', 
                'message': 'Token tidak valid!'
            }), 401
        except Exception as e:
            print(f"Unknown Error: {str(e)}")
            return jsonify({
                'status': 'error', 
                'message': 'Terjadi kesalahan sistem!'
            }), 401

        # Lanjutkan ke fungsi rute dengan membawa objek user
        return f(current_user, *args, **kwargs)

    return decorated