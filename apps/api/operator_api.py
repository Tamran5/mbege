from flask import request, jsonify
from apps import db
from apps.api import api_bp # Mengambil blueprint dari __init__.py
from apps.api.utils import token_required

@api_bp.route('/operator/verify-siswa', methods=['POST'])
@token_required
def verify_siswa(current_user):
    # Logika verifikasi siswa oleh operator sekolah
    if current_user.role != 'pengelola_sekolah':
        return jsonify({"status": "error", "message": "Akses ditolak"}), 403
        
    return jsonify({"status": "success", "message": "Siswa berhasil diverifikasi"})