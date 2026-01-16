from flask import request, jsonify
from apps import db
from apps.api import api_bp # Mengambil blueprint dari __init__.py
from apps.api.utils import token_required
from flask import jsonify
from apps.api import api_bp
from apps.authentication.models import Artikel
from apps.api.utils import token_required

@api_bp.route('/operator/verify-siswa', methods=['POST'])
@token_required
def verify_siswa(current_user):
    # Logika verifikasi siswa oleh operator sekolah
    if current_user.role != 'pengelola_sekolah':
        return jsonify({"status": "error", "message": "Akses ditolak"}), 403
        
    return jsonify({"status": "success", "message": "Siswa berhasil diverifikasi"})


@api_bp.route('/articles', methods=['GET'])
@token_required
def get_articles(current_user):
    # Filter: Hanya ambil artikel dari Dapur pengguna dan role yang sesuai
    # Sesuai logika: Siswa & Lansia hanya melihat artikel dari dapur tempat mereka terdaftar
    articles = Artikel.query.filter(
        Artikel.dapur_id == current_user.dapur_id,
        Artikel.target_role.in_([current_user.role, 'semua'])
    ).order_by(Artikel.created_at.desc()).all()

    return jsonify({
        "status": "success",
        "data": [{
            "id": a.id,
            "judul": a.judul,
            "konten": a.konten,
            "foto": a.foto, # Kirim nama filenya saja
            "tanggal": a.created_at.strftime('%d %b %Y')
        } for a in articles]
    })