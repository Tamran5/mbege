# apps/api/__init__.py
from flask import Blueprint
import traceback # Tambahkan ini

api_bp = Blueprint('api', __name__, url_prefix='/api')

try:
    from . import auth_api, operator_api
    print("DEBUG: Modul API Berhasil Dimuat!")
except ImportError as e:
    print("\n" + "!"*50)
    print(f"FATAL ERROR: Gagal mengimpor modul API!")
    print(f"Detail Error: {e}")
    traceback.print_exc() # Ini akan menunjukkan baris mana yang error di auth_api.py
    print("!"*50 + "\n")