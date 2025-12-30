# -*- encoding: utf-8 -*-
import os
import json
import base64
from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from werkzeug.utils import secure_filename

from apps import db
from apps.home import blueprint
from apps.home.utils import get_sentiment_prediction
from flask import jsonify

# --- IMPORT MODELS ---
from apps.authentication.models import (
    Users, MasterIngredient, Menus, MenuIngredients, 
    Staff, AttendanceLog, Penerima, AktivitasDapur,UlasanPenerima
)

# =========================================================
#  CONFIG & HELPER
# =========================================================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'apps/static/assets/img/menus'
ACTIVITY_UPLOAD_FOLDER = 'apps/static/uploads/activities'

def allowed_file(filename):
    """Memeriksa ekstensi file yang diizinkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =========================================================
#  ROUTE UTAMA & DASHBOARD (Mencegah BuildError Gambar 11)
# =========================================================

@blueprint.route('/')
def home():
    return render_template('home/home.html', segment='home')

@blueprint.route('/dashboard')
@login_required
def index():
    """Endpoint: home_blueprint.index"""
    role = getattr(current_user, 'role', None)

    if role == 'super_admin':
        return redirect(url_for('home_blueprint.dashboard_superadmin'))
    
    # Cek Approval untuk Admin Dapur
    if role == 'admin_dapur' and not getattr(current_user, 'is_approved', False):
        return render_template('home/pending_approval.html'), 200

    return render_template('home/index.html', segment='index')

# =========================================================
#  PROFILE 
# =========================================================

@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Endpoint: home_blueprint.profile"""
    if request.method == 'POST':
        try:
            current_user.fullname = request.form.get('fullname')
            current_user.kitchen_name = request.form.get('kitchen_name')
            current_user.whatsapp = request.form.get('whatsapp')
            current_user.address = request.form.get('address')
            db.session.commit()
            flash("Profil dapur berhasil diperbarui!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Gagal memperbarui profil: {str(e)}", "danger")
            
    return render_template('home/profile.html', segment='profile')

# =========================================================
#  MANAJEMEN GIZI (MASTER BAHAN BAKU STANDAR 2025)
# =========================================================

@blueprint.route('/penyusunan-resep')
@login_required
def penyusunan_resep():
    if getattr(current_user, 'role', None) == 'admin_dapur' and not current_user.is_approved:
        return render_template('home/pending_approval.html'), 200
        
    ingredients = MasterIngredient.query.filter_by(user_id=current_user.id).order_by(MasterIngredient.id.desc()).all()
    return render_template('home/penyusunan_resep.html', segment='penyusunan_resep', ingredients=ingredients)

@blueprint.route('/api/simpan-bahan-master', methods=['POST'])
@login_required
def api_simpan_bahan():
    try:
        data = request.get_json()
        # Menyimpan 11 Parameter Gizi sesuai Tabel 5.2 MBG 2025
        new_item = MasterIngredient(
            user_id=current_user.id,
            name=data.get('name'),
            category=data.get('category'),
            kcal=float(data.get('kcal', 0)),
            carb=float(data.get('carb', 0)),
            protein=float(data.get('prot', 0)),
            fat=float(data.get('fat', 0)),
            fiber=float(data.get('fiber', 0)),
            calcium=float(data.get('calcium', 0)),
            iron=float(data.get('iron', 0)),
            vit_a=float(data.get('vita', 0)),
            vit_c=float(data.get('vitc', 0)),
            folate=float(data.get('folate', 0)),
            vit_b12=float(data.get('b12', 0))
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"status": "success", "message": "Bahan baku standar 2025 disimpan!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@blueprint.route('/api/update-bahan-master/<int:id>', methods=['POST'])
@login_required
def api_update_bahan(id):
    try:
        item = MasterIngredient.query.get_or_404(id)
        if item.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
            
        data = request.json
        item.name = data.get('name')
        item.category = data.get('category')
        item.kcal = float(data.get('kcal', 0))
        item.carb = float(data.get('carb', 0))
        item.protein = float(data.get('prot', 0))
        item.fat = float(data.get('fat', 0))
        item.fiber = float(data.get('fiber', 0))
        item.calcium = float(data.get('calcium', 0))
        item.iron = float(data.get('iron', 0))
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Data gizi diperbarui"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    
    

# =========================================================
#  KATALOG MENU (SUSUN PAKET HARIAN SOP MBG)
# =========================================================

# =========================================================
#  KATALOG MENU (1 HARI 1 MENU VALIDATION)
# =========================================================

@blueprint.route('/katalog-menu')
@login_required
def daftar_katalog():
    if getattr(current_user, 'role', None) == 'admin_dapur' and not current_user.is_approved:
        return render_template('home/pending_approval.html'), 200
        
    recipes = MasterIngredient.query.filter_by(user_id=current_user.id).all()
    menus = Menus.query.filter_by(user_id=current_user.id).order_by(Menus.created_at.desc()).all()
    
    return render_template('home/katalog_menu.html', segment='katalog_menu', recipes=recipes, menus=menus)

@blueprint.route('/api/simpan-menu-katalog', methods=['POST'])
@login_required
def api_simpan_menu_katalog():
    try:
        # 1. Validasi Batasan 1 Hari 1 Menu
        tgl_input = request.form.get('tgl_distribusi') # format: YYYY-MM-DD
        target_date = datetime.strptime(tgl_input, '%Y-%m-%d').date()

        # Cek apakah sudah ada menu di tanggal tersebut untuk user ini
        existing_menu = Menus.query.filter(
            Menus.user_id == current_user.id,
            db.func.date(Menus.created_at) == target_date
        ).first()

        if existing_menu:
            flash(f"Gagal! Menu untuk tanggal {tgl_input} sudah ada. Silakan hapus menu lama terlebih dahulu jika ingin mengganti.", "danger")
            return redirect(url_for('home_blueprint.daftar_katalog'))

        # 2. Proses Upload Foto
        file_foto = request.files.get('photo')
        filename = None
        if file_foto and allowed_file(file_foto.filename):
            filename = secure_filename(file_foto.filename)
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file_foto.save(os.path.join(UPLOAD_FOLDER, filename))

        # 3. Ambil ID dari 5 Pilar & Kalkulasi Gizi
        pilar_ids = [
            request.form.get('karbo_id'),
            request.form.get('protein_h_id'),
            request.form.get('protein_n_id'),
            request.form.get('sayur_id'),
            request.form.get('susu_id')
        ]
        pilar_ids = [int(pid) for pid in pilar_ids if pid]

        total_prot = 0.0; total_carb = 0.0; total_fat = 0.0; total_kcal = 0.0
        total_fiber = 0.0; total_calcium = 0.0
        
        selected_ingredients = MasterIngredient.query.filter(MasterIngredient.id.in_(pilar_ids)).all()
        menu_name_parts = [i.name for i in selected_ingredients]

        for i in selected_ingredients:
            total_prot += i.protein; total_carb += i.carb; total_fat += i.fat
            total_kcal += i.kcal; total_fiber += i.fiber; total_calcium += i.calcium

        # 4. Simpan ke Database
        new_menu = Menus(
            user_id=current_user.id,
            menu_name=" & ".join(menu_name_parts[:3]) + "...", 
            photo=filename,
            total_protein=total_prot,
            total_carb=total_carb,
            total_fat=total_fat,
            total_kcal=total_kcal,
            total_fiber=total_fiber,
            total_calcium=total_calcium,
            created_at=datetime.combine(target_date, datetime.now().time()) # Set waktu sesuai tgl distribusi
        )
        db.session.add(new_menu)
        db.session.flush()

        for pid in pilar_ids:
            db.session.add(MenuIngredients(menu_id=new_menu.id, ingredient_id=pid, weight=100.0))

        db.session.commit()
        flash(f"Paket Menu untuk tanggal {tgl_input} Berhasil Dipublikasikan!", "success")
        return redirect(url_for('home_blueprint.daftar_katalog'))

    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menyusun menu: {str(e)}", "danger")
        return redirect(url_for('home_blueprint.daftar_katalog'))

# =========================================================
#  WEB SERVICES (API UNTUK MOBILE)
# =========================================================

@blueprint.route('/api/v1/menu-hari-ini', methods=['GET'])
def api_get_today_menu():
    """Endpoint JSON untuk aplikasi mobile Android/iOS."""
    try:
        hari_ini = date.today()
        # Cari menu yang terdaftar untuk hari ini
        menu = Menus.query.filter(db.func.date(Menus.created_at) == hari_ini).first()

        if not menu:
            return jsonify({
                "status": "empty", 
                "message": "Belum ada menu yang disusun untuk hari ini."
            }), 404

        return jsonify({
            "status": "success",
            "data": {
                "id": menu.id,
                "nama_paket": menu.menu_name,
                "foto_url": f"{request.host_url}static/assets/img/menus/{menu.photo}" if menu.photo else None,
                "nutrisi": {
                    "kalori": round(menu.total_kcal, 2),
                    "protein": round(menu.total_protein, 2),
                    "karbohidrat": round(menu.total_carb, 2),
                    "lemak": round(menu.total_fat, 2),
                    "serat": round(menu.total_fiber, 2)
                },
                "tanggal": menu.created_at.strftime('%Y-%m-%d')
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================================
#  OPERASIONAL & ULASAN
# =========================================================

@blueprint.route('/ulasan')
@login_required
def ulasan_penerima():
    return render_template('home/ulasan.html', segment='ulasan')

@blueprint.route('/api/ulasan-stats')
@login_required
def api_ulasan_stats():
    # Pastikan model yang digunakan adalah UlasanPenerima
    reviews = UlasanPenerima.query.filter_by(user_id=current_user.id).all()
    processed_data = []
    pos, neg, net = 0, 0, 0

    for r in reviews:
        sentiment = get_sentiment_prediction(r.ulasan_teks)
        if sentiment == 'Positif': pos += 1
        elif sentiment == 'Negatif': neg += 1
        else: net += 1
        
        processed_data.append({
            'penerima': r.nama_pengulas,  # PERBAIKAN: Gunakan nama_pengulas sesuai DB
            'text': r.ulasan_teks,
            'status': sentiment.lower(),
            'tanggal': r.tanggal.strftime('%Y-%m-%d')
        })

    total = len(processed_data)
    satisfaction = (pos / total * 100) if total > 0 else 0

    return jsonify({
        'total': total,
        'satisfaction': f"{int(satisfaction)}%",
        'negative_count': neg,
        'chart_data': [pos, net, neg],
        'reviews': processed_data
    })

@blueprint.route('/api/submit-ulasan', methods=['POST'])
def api_receive_review():
    try:
        data = request.get_json(force=True)
        # Menggunakan UlasanPenerima, bukan Penerima
        new_review = UlasanPenerima(
            user_id=data.get('user_id'),
            nama_pengulas=data.get('nama'), # Mengambil field 'nama' dari Postman
            ulasan_teks=data.get('review'), # Mengambil field 'review' dari Postman
            tanggal=datetime.now()
        )
        db.session.add(new_review)
        db.session.commit()
        return jsonify({"status": "success", "message": "Ulasan berhasil disimpan"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@blueprint.route('/monitoring')
@login_required
def route_monitoring():
    """Endpoint: home_blueprint.route_monitoring"""
    if getattr(current_user, 'role', None) != 'admin_dapur':
        return redirect(url_for('home_blueprint.index'))
    
    total_target = sum(item.kuota for item in current_user.my_beneficiaries)
    return render_template('home/monitoring.html', segment='monitoring', target_porsi=total_target)

@blueprint.route('/api/submit-activity', methods=['POST'])
@login_required
def api_submit_activity():
    try:
        data = request.json
        process_name = data.get('process')
        photo_base64 = data.get('photo')

        if not process_name or not photo_base64:
            return jsonify({'status': 'error', 'message': 'Data tidak lengkap'}), 400

        # Decode Base64 Photo
        if ',' in photo_base64:
            _, encoded = photo_base64.split(',', 1)
        else:
            encoded = photo_base64
        
        image_data = base64.b64decode(encoded)
        filename = f"activity_{current_user.id}_{int(datetime.now().timestamp())}.jpg"
        
        if not os.path.exists(ACTIVITY_UPLOAD_FOLDER):
            os.makedirs(ACTIVITY_UPLOAD_FOLDER)
            
        full_path = os.path.join(ACTIVITY_UPLOAD_FOLDER, filename)
        with open(full_path, 'wb') as f:
            f.write(image_data)

        new_activity = AktivitasDapur(
            user_id=current_user.id,
            jenis_aktivitas=process_name,
            bukti_foto=filename,
            waktu_mulai=datetime.now(),
            status='Proses'
        )
        db.session.add(new_activity)
        db.session.commit()

        return jsonify({'status': 'success', 'data': new_activity.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =========================================================
#  SUPER ADMIN (ADMIN GIZI)
# =========================================================

@blueprint.route('/admin-gizi')
@login_required
def dashboard_superadmin():
    """Dashboard khusus Super Admin."""
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))

    wilayah = getattr(current_user, 'district', None)
    stats = {
        'total': Users.query.filter_by(role='admin_dapur', district=wilayah).count() if wilayah else 0,
        'aktif': Users.query.filter_by(role='admin_dapur', is_approved=True, district=wilayah).count() if wilayah else 0
    }
    return render_template('home/superadmin_dashboard.html', segment='admin_gizi', stats=stats)

@blueprint.route('/verifikasi-mitra')
@login_required
def verifikasi_mitra():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    
    wilayah = getattr(current_user, 'district', None)
    pending_users = Users.query.filter_by(role='admin_dapur', is_approved=False, district=wilayah).all() if wilayah else []
    return render_template('home/superadmin_verifikasi.html', pendaftar=pending_users, segment='verifikasi')

@blueprint.route('/data-mitra')
@login_required
def data_mitra():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    
    wilayah = getattr(current_user, 'district', None)
    mitra_aktif = Users.query.filter_by(role='admin_dapur', is_approved=True, district=wilayah).all() if wilayah else []
    return render_template('home/data_mitra.html', mitra_list=mitra_aktif, segment='data_mitra')

@blueprint.route('/peta-sebaran')
@login_required
def peta_sebaran():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    return render_template('home/map_sebaran.html', segment='peta_sebaran')

@blueprint.route('/admin-gizi/monitoring-proses')
@login_required
def gizi_monitoring_proses():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    return render_template('home/monitoring_proses.html', segment='monitoring_proses')

@blueprint.route('/admin-gizi/profile', methods=['GET', 'POST'])
@login_required
def superadmin_profile():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    return render_template('home/profile.html', segment='profile_admin')

# =========================================================
#  GENERIC ROUTE (FIXED)
# =========================================================

@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'
        return render_template("home/" + template, segment=template.replace('.html', ''))
    except TemplateNotFound:
        return render_template('home/page-404.html'), 404
    except:
        return render_template('home/page-500.html'), 500

# =========================================================
#  API SEARCH & PENDUKUNG
# =========================================================

@blueprint.route('/api/cari-bahan-master')
@login_required
def api_cari_bahan():
    query = request.args.get('q', '')
    ingredients = MasterIngredient.query.filter(
        MasterIngredient.user_id == current_user.id,
        MasterIngredient.name.ilike(f'%{query}%')
    ).all()
    return jsonify([{
        'id': i.id, 'name': i.name, 'category': i.category,
        'kcal': i.kcal, 'prot': i.protein, 'carb': i.carb, 'fat': i.fat,
        'fiber': i.fiber, 'calcium': i.calcium 
    } for i in ingredients])

@blueprint.route('/api/hapus-bahan-master/<int:id>', methods=['DELETE'])
@login_required
def api_delete_ingredient(id):
    item = MasterIngredient.query.filter_by(id=id, user_id=current_user.id).first()
    if not item:
        return jsonify({"status": "error", "message": "Not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "success"})

@blueprint.route('/approve/<int:id>')
@login_required
def approve_mitra(id):
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))

    user = Users.query.get_or_404(id)
    try:
        user.is_approved = True
        db.session.commit()
        flash(f"Mitra {user.kitchen_name} berhasil disetujui!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menyetujui mitra: {str(e)}", "danger")
    
    return redirect(url_for('home_blueprint.verifikasi_mitra'))

@blueprint.route('/reject/<int:id>')
@login_required
def reject_mitra(id):
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))

    user = Users.query.get_or_404(id)
    try:
        # Pilihan: Hapus user atau sekadar tandai ditolak
        db.session.delete(user) 
        db.session.commit()
        flash(f"Pendaftaran {user.kitchen_name} telah ditolak.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal menolak mitra: {str(e)}", "danger")
    
    return redirect(url_for('home_blueprint.verifikasi_mitra'))

@blueprint.route('/hapus-menu/<int:id>')
@login_required
def hapus_menu(id):
    menu = Menus.query.get_or_404(id)
    if menu.user_id != current_user.id:
        flash("Akses ditolak!", "danger")
        return redirect(url_for('home_blueprint.daftar_katalog'))
    
    db.session.delete(menu)
    db.session.commit()
    flash('Menu berhasil dihapus.', 'success')
    return redirect(url_for('home_blueprint.daftar_katalog'))

@blueprint.route('/edit-menu/<int:id>')
@login_required
def edit_menu(id):
    menu = Menus.query.get_or_404(id)
    if menu.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    return render_template('home/edit_menu.html', menu=menu, segment='katalog_menu')