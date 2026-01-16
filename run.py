# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_migrate import Migrate
from flask_cors import CORS 
from sys import exit
from decouple import config
from pyngrok import ngrok  

from apps.config import config_dict
from apps import create_app, db

# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)

# --- INTEGRASI UNTUK FLUTTER WEB & MOBILE ---
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False) 

Migrate(app, db)

if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('Environment = ' + get_config_mode)
    app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)

# --- KONFIGURASI NGROK OTOMATIS ---
def start_ngrok():
    try:
        token = config('NGROK_AUTHTOKEN', default=None)
        domain = config('NGROK_DOMAIN', default=None)
        
        if token and domain:
            ngrok.set_auth_token(token)
            # Membuka tunnel ke port 5000
            public_url = ngrok.connect(5000, domain=domain).public_url
            print(f"\n[NGROK] Tunnel aktif di: {public_url}")
            print("[NGROK] Gunakan URL ini untuk akses dari Flutter/Postman\n")
        else:
            print("\n[NGROK] Token atau Domain tidak ditemukan di .env. Ngrok tidak dijalankan.\n")
    except Exception as e:
        print(f"\n[NGROK] Gagal menjalankan ngrok: {e}\n")

if __name__ == "__main__":
    # Jalankan ngrok hanya saat mode DEBUG/Development
    if DEBUG:
        start_ngrok()
        
    app.run(host='0.0.0.0', port=5000, debug=True)