# -*- encoding: utf-8 -*-
import os
import json
import base64
from sqlalchemy import func
from datetime import datetime, date,timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify,session
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from werkzeug.utils import secure_filename
from flask import current_app
from apps import db
from sqlalchemy.orm import aliased
from apps.home import blueprint
from flask import jsonify
from functools import wraps
from flask import abort
from flask_login import current_user
from flask import request, redirect, url_for, flash
from flask_login import logout_user, current_user



# --- IMPORT MODELS ---
from apps.authentication.models import (
    Users, MasterIngredient, Menus, MenuIngredients, 
    Staff, AttendanceLog, Penerima, AktivitasDapur,UlasanPenerima,LogDistribusi,Artikel
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

@blueprint.before_app_request
def restrict_web_access():
    # 1. Tentukan halaman yang dikecualikan (login, static, api) agar tidak looping
    exempt_paths = [
        url_for('authentication_blueprint.login'),
        url_for('authentication_blueprint.logout'),
        url_for('home_blueprint.index'),
        '/static/',
        '/api/'
    ]
    
    # Cek apakah request saat ini menuju halaman web (bukan API atau file static)
    if not any(request.path.startswith(path) for path in exempt_paths) and not request.path.startswith('/static'):
        if current_user.is_authenticated:
            allowed_web_roles = ['admin_dapur', 'super_admin']
            
            # Jika role dilarang (Siswa/Lansia/Pengelola) mencoba akses Dashboard Web
            if current_user.role not in allowed_web_roles:
                logout_user() 
                flash("Akses Ditolak: Role Anda hanya diizinkan via Mobile.", "danger")
                return redirect(url_for('authentication_blueprint.login'))
            

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_web_roles = ['admin_dapur', 'super_admin']
        print(f"DEBUG DEKORATOR: User={current_user.email}, Role='{current_user.role}'")
        # Jika tidak login atau role tidak sesuai, tolak akses (Error 403)
        if not current_user.is_authenticated or current_user.role not in allowed_web_roles:
            print("DEBUG DEKORATOR: AKSES DITOLAK (403)")
            abort(403) 
        return f(*args, **kwargs)
    return decorated_function

@blueprint.route('/')
def home():
    return render_template('home/home.html')

@blueprint.route('/dashboard')
@login_required
@admin_required
def index():
    # --- 1. Logika Statistik (Tetap sama) ---
    Siswa = aliased(Users)
    Sekolah = aliased(Users)
    
    total_siswa = db.session.query(func.count(Siswa.id))\
        .select_from(Siswa)\
        .join(Sekolah, Siswa.sekolah_id == Sekolah.id)\
        .filter(Sekolah.dapur_id == current_user.id)\
        .filter(Siswa.role == 'siswa', Siswa.is_approved == True).scalar() or 0

    antrian_verifikasi = Users.query.filter_by(dapur_id=current_user.id, is_approved=False).count()

    porsi_hari_ini = db.session.query(func.sum(LogDistribusi.porsi_sampai))\
        .filter(LogDistribusi.dapur_id == current_user.id)\
        .filter(func.date(LogDistribusi.waktu_sampai) == date.today()).scalar() or 0

    # --- 2. LOGIKA GRAFIK 7 HARI TERAKHIR ---
    labels = []
    data_porsi = []
    
    for i in range(6, -1, -1):
        target_date = date.today() - timedelta(days=i)
        
        # Ambil total porsi pada tanggal tersebut
        daily_sum = db.session.query(func.sum(LogDistribusi.porsi_sampai))\
            .filter(LogDistribusi.dapur_id == current_user.id)\
            .filter(func.date(LogDistribusi.waktu_sampai) == target_date).scalar() or 0
        
        # Simpan label (Nama Hari) dan datanya
        labels.append(target_date.strftime('%a')) # Hasil: 'Mon', 'Tue', dst.
        data_porsi.append(int(daily_sum))

    stats = {
        'total_siswa': total_siswa,
        'antrian': antrian_verifikasi,
        'porsi': porsi_hari_ini,
        'kepuasan': "94%",
        'chart_labels': labels, # Kirim ke frontend
        'chart_data': data_porsi   # Kirim ke frontend
    }

    recent_arrivals = LogDistribusi.query.filter_by(dapur_id=current_user.id)\
                      .order_by(LogDistribusi.waktu_sampai.desc()).limit(5).all()

    return render_template('home/index.html', stats=stats, arrivals=recent_arrivals, segment='index')
# =========================================================
#  PROFILE 
# =========================================================


@blueprint.route('/manajemen-artikel')
@login_required
@admin_required
def daftar_artikel():
    # Mengambil hanya artikel milik dapur ini
    list_artikel = Artikel.query.filter_by(dapur_id=current_user.id).order_by(Artikel.created_at.desc()).all()
    return render_template('home/manajemen_artikel.html', artikel=list_artikel, segment='manajemen_artikel')

@blueprint.route('/manajemen-artikel/simpan', methods=['POST'])
@login_required
@admin_required
def simpan_artikel():
    artikel_id = request.form.get('id')
    judul = request.form.get('judul')
    konten = request.form.get('konten')
    target = request.form.get('target_role') # 'siswa', 'lansia', atau 'semua'
    
    # Penanganan Upload Foto
    foto_file = request.files.get('foto')
    filename = None
    if foto_file:
        filename = secure_filename(f"art_{current_user.id}_{int(datetime.now().timestamp())}.jpg")
        path = os.path.join(current_app.root_path, 'static/uploads/articles')
        os.makedirs(path, exist_ok=True)
        foto_file.save(os.path.join(path, filename))

    if artikel_id: # Mode Edit
        art = Artikel.query.get(artikel_id)
        if art and art.dapur_id == current_user.id:
            art.judul = judul
            art.konten = konten
            art.target_role = target
            if filename:
                # Hapus foto lama jika ada penggantian
                if art.foto:
                    old_path = os.path.join(current_app.root_path, 'static/uploads/articles', art.foto)
                    if os.path.exists(old_path): os.remove(old_path)
                art.foto = filename
    else: # Mode Tambah Baru
        new_art = Artikel(judul=judul, konten=konten, foto=filename, target_role=target, dapur_id=current_user.id)
        db.session.add(new_art)
    
    db.session.commit()
    return redirect(url_for('home_blueprint.daftar_artikel'))

@blueprint.route('/manajemen-artikel/hapus/<int:id>')
@login_required
@admin_required
def hapus_artikel(id):
    art = Artikel.query.get_or_404(id)
    # Validasi kepemilikan sebelum hapus
    if art.dapur_id == current_user.id:
        if art.foto:
            path = os.path.join(current_app.root_path, 'static/uploads/articles', art.foto)
            if os.path.exists(path): os.remove(path)
        db.session.delete(art)
        db.session.commit()
    return redirect(url_for('home_blueprint.daftar_artikel'))

@blueprint.route('/data-penerima')
@login_required
@admin_required
def data_penerima():
    # 1. Daftar Sekolah: Tetap seperti sebelumnya
    sekolah_list = Users.query.filter_by(
        role='pengelola_sekolah', 
        is_approved=True, 
        district=current_user.district
    ).all()

    lansia_list = Users.query.filter_by(
        role='lansia',
        is_approved=True,
        district=current_user.district
    ).all()
    
    return render_template('home/data_penerima.html', 
                           title='Data Penerima Aktif',
                           sekolah_list=sekolah_list,
                           lansia_list=lansia_list)

@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
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
@admin_required
def penyusunan_resep():
    if getattr(current_user, 'role', None) == 'admin_dapur' and not current_user.is_approved:
        return render_template('home/pending_approval.html'), 200
        
    ingredients = MasterIngredient.query.filter_by(user_id=current_user.id).order_by(MasterIngredient.id.desc()).all()
    return render_template('home/penyusunan_resep.html', segment='penyusunan_resep', ingredients=ingredients)

@blueprint.route('/api/simpan-bahan-master', methods=['POST'])
@login_required
@admin_required
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
    

@blueprint.route('/verifikasi-penerima')
@login_required
@admin_required
def verifikasi_penerima():
    if current_user.role != 'admin_dapur':
        return render_template('home/page-403.html'), 403
    
    # PERBAIKAN: Hanya ambil pendaftar yang memilih dapur ini
    pendaftar = Users.query.filter(
        Users.role.in_(['pengelola_sekolah', 'lansia']),
        Users.is_approved == False,
        Users.dapur_id == current_user.id  # Filter relasi
    ).all()
    
    return render_template('home/verifikasi_penerima.html', pendaftar=pendaftar, segment='verifikasi_penerima')

@blueprint.route('/verifikasi/<action>/<int:user_id>')
@login_required
@admin_required
def process_verifikasi(action, user_id):
    # Proteksi: Hanya Admin Dapur yang boleh mengeksekusi
    if current_user.role != 'admin_dapur':
        flash("Akses ditolak!", "danger")
        return redirect(url_for('home_blueprint.index'))

    user = Users.query.get_or_404(user_id)

    if action == 'approve':
        user.is_approved = True # Mengubah status agar bisa login di Flutter
        flash(f"Pendaftaran {user.fullname} ({user.role}) berhasil DISETUJUI.", "success")
    
    elif action == 'reject':
        # Jika ditolak, data dihapus dari database untuk menjaga kebersihan antrian
        db.session.delete(user)
        flash(f"Pendaftaran {user.fullname} telah DITOLAK dan dihapus.", "warning")

    try:
        db.session.commit() # Simpan perubahan ke database fisik
    except Exception as e:
        db.session.rollback()
        flash(f"Gagal memproses data: {str(e)}", "danger")

    return redirect(url_for('home_blueprint.verifikasi_penerima'))


@blueprint.route('/api/update-activity-status/<int:activity_id>', methods=['POST'])
@login_required
@admin_required
def update_activity_status(activity_id):
    # 1. Cek Role Secara Manual
    # Hanya izinkan jika role adalah 'super_admin'
    if current_user.role != 'super_admin':
        return jsonify({
            'status': 'error', 
            'message': 'Akses ditolak. Anda bukan Super Admin.'
        }), 403

    try:
        data = request.json
        new_status = data.get('status') # 'selesai' atau 'ditolak'

        if not new_status:
            return jsonify({'status': 'error', 'message': 'Status tidak ditentukan'}), 400

        # 2. Cari data aktivitas dapur
        activity = AktivitasDapur.query.get(activity_id)

        if not activity:
            return jsonify({'status': 'error', 'message': 'Aktivitas tidak ditemukan'}), 404

        # 3. Update Status dan Metadata
        activity.status = new_status
        
        if new_status == 'selesai':
            activity.waktu_selesai = datetime.now() # Mencatat waktu verifikasi
            activity.catatan = "Disetujui oleh Super Admin"
        elif new_status == 'ditolak':
            activity.catatan = "Ditolak oleh Super Admin"

        db.session.commit()

        return jsonify({
            'status': 'success', 
            'message': f'Aktivitas berhasil di-update ke status {new_status}'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
@blueprint.route('/api/update-bahan-master/<int:id>', methods=['POST'])
@login_required
@admin_required
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

@blueprint.route('/katalog-menu')
@login_required
@admin_required
def daftar_katalog():
    if getattr(current_user, 'role', None) == 'admin_dapur' and not current_user.is_approved:
        return render_template('home/pending_approval.html'), 200
        
    recipes = MasterIngredient.query.filter_by(user_id=current_user.id).all()
    # Mengurutkan berdasarkan tanggal distribusi terbaru
    menus = Menus.query.filter_by(user_id=current_user.id).order_by(Menus.distribution_date.desc()).all()
    
    return render_template('home/katalog_menu.html', segment='katalog_menu', recipes=recipes, menus=menus)

@blueprint.route('/api/simpan-menu-katalog', methods=['POST'])
@login_required
@admin_required
def api_simpan_menu_katalog():
    try:
        tgl_input = request.form.get('tgl_distribusi')
        target_date = datetime.strptime(tgl_input, '%Y-%m-%d').date()

        existing_menu = Menus.query.filter_by(
            user_id=current_user.id,
            distribution_date=target_date
        ).first()

        if existing_menu:
            return jsonify({'status': 'error', 'message': f'Menu untuk tanggal {tgl_input} sudah ada.'}), 400

        pilar_ids = [
            request.form.get('karbo_id'),
            request.form.get('protein_h_id'),
            request.form.get('protein_n_id'),
            request.form.get('sayur_id'),
            request.form.get('buah_id'),
            request.form.get('susu_id')
        ]
        pilar_ids = [int(pid) for pid in pilar_ids if pid and pid.isdigit()]

        total_prot = 0.0; total_carb = 0.0; total_fat = 0.0; total_kcal = 0.0
        total_fiber = 0.0; total_calcium = 0.0; total_iron = 0.0; total_vit_a = 0.0
        
        selected_ingredients = MasterIngredient.query.filter(MasterIngredient.id.in_(pilar_ids)).all()
        menu_names = []

        for ing in selected_ingredients:
            # PENGAMAN: Gunakan 'or 0.0' jika kolom di DB bernilai NULL
            berat_bersih = ing.weight or 0.0
            ratio = berat_bersih / 100.0
            
            total_kcal += ((ing.kcal or 0.0) * ratio)
            total_prot += ((ing.protein or 0.0) * ratio)
            total_fat += ((ing.fat or 0.0) * ratio)
            total_carb += ((ing.carb or 0.0) * ratio)
            total_fiber += ((ing.fiber or 0.0) * ratio)
            total_calcium += ((ing.calcium or 0.0) * ratio)
            total_iron += ((ing.iron or 0.0) * ratio)
            total_vit_a += ((ing.vit_a or 0.0) * ratio)
            
            menu_names.append(ing.name)

        # PROSES FOTO QC
        file_foto = request.files.get('photo')
        filename = "default_menu.jpg"
        if file_foto and file_foto.filename != '':
            filename = secure_filename(f"{current_user.id}_{tgl_input}_{file_foto.filename}")
            # PERBAIKAN: Gunakan current_app.config bukan blueprint.config
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'menus')
            
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
                
            file_foto.save(os.path.join(upload_path, filename))

        new_menu = Menus(
            user_id=current_user.id,
            menu_name=", ".join(menu_names[:4]) + "...",
            photo=filename,
            distribution_date=target_date,
            total_kcal=round(total_kcal, 1),
            total_protein=round(total_prot, 1),
            total_fat=round(total_fat, 1),
            total_carb=round(total_carb, 1),
            total_fiber=round(total_fiber, 1),
            total_calcium=round(total_calcium, 1),
            total_iron=round(total_iron, 1),
            total_vit_a=round(total_vit_a, 1)
        )
        db.session.add(new_menu)
        db.session.flush()

        for ing in selected_ingredients:
            db.session.add(MenuIngredients(
                menu_id=new_menu.id, 
                ingredient_id=ing.id, 
                weight=ing.weight or 0.0
            ))

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Menu berhasil dipublikasikan!'})

    except Exception as e:
        db.session.rollback()
        # Cetak error ke terminal Flask untuk debug lebih lanjut
        print(f"ERROR PUBLIKASI: {str(e)}") 
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =========================================================
#  OPERASIONAL & ULASAN
# =========================================================


@blueprint.route('/monitoring-kedatangan')
@login_required
@admin_required
def monitoring_kedatangan_view():
    # 1. Ambil parameter tanggal dari URL
    date_str = request.args.get('date')
    
    # 2. Inisialisasi Query Dasar
    query = LogDistribusi.query.filter_by(dapur_id=current_user.id)
    
    if date_str:
        try:
            # Konversi string '2026-01-17' menjadi objek Date Python
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # PERBAIKAN VITAL: Gunakan db.func.date untuk membuang bagian Jam:Menit di database
            query = query.filter(db.func.date(LogDistribusi.waktu_sampai) == target_date)
        except ValueError:
            # Jika format tanggal salah, kembali ke hari ini
            query = query.filter(db.func.date(LogDistribusi.waktu_sampai) == date.today())
    else:
        # Default jika tidak ada tanggal yang dipilih: Tampilkan hari ini
        query = query.filter(db.func.date(LogDistribusi.waktu_sampai) == date.today())
        
    kedatangan_logs = query.order_by(LogDistribusi.waktu_sampai.desc()).all()
    
    return render_template('home/monitoring_kedatangan.html', 
                           kedatangan=kedatangan_logs, 
                           segment='monitoring_kedatangan')

@blueprint.route('/dapur/arrival-monitoring', methods=['GET'])
@login_required
@admin_required
def monitor_arrivals():
    # Menggunakan relasi distribusi_logs yang baru saja ditambahkan di class Users
    logs = current_user.distribusi_logs.order_by(LogDistribusi.waktu_sampai.desc()).all()
    
    return jsonify({
        "status": "success",
        "data": [{
            "sekolah": log.sekolah.school_name, # Mengambil dari relasi sekolah
            "waktu_sampai": log.waktu_sampai.strftime('%H:%M'),
            "foto_bukti": log.foto_bukti,
            "porsi": log.porsi_sampai,
            "operator": log.sekolah.fullname, # Nama operator yang mengonfirmasi
            "status": log.status
        } for log in logs]
    })

@blueprint.route('/ulasan')
@login_required
@admin_required
def ulasan_penerima():
    return render_template('home/ulasan.html', segment='ulasan')

@blueprint.route('/api/ulasan-stats')
@login_required
def api_ulasan_stats():
    # Proteksi Peran
    if current_user.role != 'admin_dapur':
        return jsonify({"status": "error", "message": "Akses Ditolak"}), 403

    # Ambil parameter tanggal dari URL (default hari ini)
    target_date = request.args.get('tanggal', datetime.now().strftime('%Y-%m-%d'))
    
    # Query ulasan (Bisa ditambahkan filter sekolah jika katering memegang banyak sekolah)
    reviews = UlasanPenerima.query.filter(
        db.func.date(UlasanPenerima.tanggal) == target_date
    ).all()

    processed_data = []
    pos, neg, net = 0, 0, 0

    for r in reviews:
        # Ambil status_ai yang sudah tersimpan (lebih efisien)
        sentiment = (r.status_ai or 'netral').lower()
        
        if sentiment == 'positif': pos += 1
        elif sentiment == 'negatif': neg += 1
        else: net += 1
        
        processed_data.append({
            'penerima': r.nama_pengulas,
            'rating': r.rating,
            'tags': r.tags.split(',') if r.tags else [], # Split string ke list untuk JS
            'text': r.ulasan_teks,
            'status': sentiment,
            'tanggal': r.tanggal.strftime('%Y-%m-%d %H:%M')
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

@blueprint.route('/monitoring')
@login_required
@admin_required
def route_monitoring():
    if current_user.role != 'admin_dapur':
        return redirect(url_for('home_blueprint.index'))
    
    # FIX 1: Ambil data aktivitas hari ini untuk user yang login
    from datetime import datetime
    today = datetime.now().date()
    activities = AktivitasDapur.query.filter_by(
        user_id=current_user.id, 
        tanggal=today
    ).order_by(AktivitasDapur.waktu_mulai.desc()).all()

    total_target = sum(item.kuota for item in current_user.my_beneficiaries)
    
    # FIX 2: Kirim variabel 'activities' ke template
    return render_template('home/monitoring.html', 
                           activities=activities, 
                           target_porsi=total_target)


    

@blueprint.route('/api/submit-activity', methods=['POST'])
@login_required
@admin_required
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
            status='proses'
        )
        db.session.add(new_activity)
        db.session.commit()

        return jsonify({'status': 'success', 'data': new_activity.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@blueprint.route('/api/kitchen-locations', methods=['GET'])
@login_required
def api_kitchen_locations():
    # Mengambil daftar dapur agar filter di halaman monitoring tidak error
    kitchens = Users.query.filter_by(role='admin_dapur').all()
    return jsonify([{'id': k.id, 'nama': k.kitchen_name or k.username} for k in kitchens])

# =========================================================
#  SUPER ADMIN (ADMIN GIZI)
# =========================================================

@blueprint.route('/admin-gizi')
@login_required
@admin_required
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
@admin_required
def verifikasi_mitra():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    
    wilayah = getattr(current_user, 'district', None)
    pending_users = Users.query.filter_by(role='admin_dapur', is_approved=False, district=wilayah).all() if wilayah else []
    return render_template('home/superadmin_verifikasi.html', pendaftar=pending_users, segment='verifikasi')

@blueprint.route('/monitoring-live')
@login_required
def monitoring_live():
    # 1. Proteksi Role: Hanya izinkan super_admin
    if current_user.role != 'super_admin':
        # Mengembalikan error 403 (Forbidden) jika bukan super_admin
        return abort(403) 

    # 2. Lanjutkan Query jika lolos validasi
    activities_query = db.session.query(AktivitasDapur, Users).join(
        Users, AktivitasDapur.user_id == Users.id
    ).order_by(AktivitasDapur.waktu_mulai.desc()).all()

    formatted_activities = []
    for activity, user in activities_query:
        formatted_activities.append({
            'waktu': activity.waktu_mulai.strftime('%H:%M'),
            'nama_dapur': user.kitchen_name or user.username,
            'inisial': (user.kitchen_name or user.username)[0].upper(),
            'alamat': user.district or user.address or '-',
            'tahap': activity.jenis_aktivitas,
            'img_url': f"/static/uploads/activities/{activity.bukti_foto}",
            'status': activity.status.lower()
        })

    return render_template('home/monitoring_proses.html', activities=formatted_activities)

@blueprint.route('/data-mitra')
@login_required
@admin_required
def data_mitra():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    
    wilayah = getattr(current_user, 'district', None)
    mitra_aktif = Users.query.filter_by(role='admin_dapur', is_approved=True, district=wilayah).all() if wilayah else []
    return render_template('home/data_mitra.html', mitra_list=mitra_aktif, segment='data_mitra')


@blueprint.route('/peta-sebaran')
@login_required
@admin_required
def peta_sebaran():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    return render_template('home/map_sebaran.html', segment='peta_sebaran')

@blueprint.route('/admin-gizi/monitoring-proses')
@login_required
@admin_required
def gizi_monitoring_proses():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    return render_template('home/monitoring_proses.html', segment='monitoring_proses')

@blueprint.route('/admin-gizi/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def superadmin_profile():
    if getattr(current_user, 'role', None) != 'super_admin':
        return redirect(url_for('home_blueprint.index'))
    return render_template('home/profile.html', segment='profile_admin')

# =========================================================
#  GENERIC ROUTE (FIXED)
# =========================================================

@blueprint.route('/<template>')
@login_required
@admin_required
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
@admin_required
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
@admin_required
def api_delete_ingredient(id):
    item = MasterIngredient.query.filter_by(id=id, user_id=current_user.id).first()
    if not item:
        return jsonify({"status": "error", "message": "Not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "success"})

@blueprint.route('/approve/<int:id>')
@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def edit_menu(id):
    menu = Menus.query.get_or_404(id)
    if menu.user_id != current_user.id:
        return render_template('home/page-403.html'), 403
    return render_template('home/edit_menu.html', menu=menu, segment='katalog_menu')