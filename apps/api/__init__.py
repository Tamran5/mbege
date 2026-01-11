# apps/api/__init__.py
from flask import Blueprint

# 1. Definisikan blueprint terlebih dahulu
api_bp = Blueprint(
    'api', 
    __name__, 
    url_prefix='/api'
)

# 2. Impor rute DI BAWAH definisi blueprint agar tidak terjadi circular import
try:
    from apps.api import auth_api, operator_api
except ImportError as e:
    # Ini akan membantu Anda melihat jika ada file yang benar-benar belum dibuat
    print(f"Peringatan: Gagal mengimpor modul API: {e}")