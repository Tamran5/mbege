from flask_login import UserMixin
from apps import db, login_manager 
from apps.authentication.util import hash_pass, verify_pass 
from datetime import datetime

# --- MODEL USER UTAMA (Terintegrasi Data Wilayah & Kemitraan) ---


class Artikel(db.Model):
    __tablename__ = 'artikel'

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(255), nullable=False)
    konten = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(255))
    
    # Menentukan audiens: 'siswa', 'lansia', atau 'semua'
    target_role = db.Column(db.String(20), default='semua') 
    
    # Relasi ke Admin Dapur pengirim
    dapur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    penulis = db.relationship('Users', backref=db.backref('my_articles', lazy='dynamic'))

class LogDistribusi(db.Model):
    __tablename__ = 'log_distribusi'
    id = db.Column(db.Integer, primary_key=True)
    
    # Relasi ke Dapur dan Sekolah
    dapur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sekolah_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Data Kedatangan
    foto_bukti = db.Column(db.String(255)) # Nama file dari Flutter
    waktu_sampai = db.Column(db.DateTime, default=datetime.now)
    porsi_sampai = db.Column(db.Integer)
    status = db.Column(db.String(20), default='Diterima')

    # Relasi balik untuk memudahkan query
    sekolah = db.relationship('Users', foreign_keys=[sekolah_id])
class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column('password', db.LargeBinary)
    
    # PERAN: 'admin_dapur', 'pengelola_sekolah', 'siswa', 'lansia'
    role = db.Column(db.String(20), default='admin_dapur')
    is_approved = db.Column(db.Boolean, default=False) 

    school_token = db.Column(db.String(10), unique=True, nullable=True)
    user_class = db.Column(db.String(20), nullable=True)
    # --- DATA IDENTITAS & PROFIL ---
    fullname = db.Column(db.String(100))
    phone = db.Column(db.String(20)) # Mapping dari _phoneController di Flutter
    nik = db.Column(db.String(20), nullable=True) 
    nisn = db.Column(db.String(20), nullable=True) 
    npsn = db.Column(db.String(20), nullable=True) 
    school_name = db.Column(db.String(100), nullable=True) 
    student_count = db.Column(db.Integer, default=0)
    
    # --- DATA WILAYAH LENGKAP (Input dari Flutter) ---
    province = db.Column(db.String(100))
    city = db.Column(db.String(100))
    district = db.Column(db.String(100))
    village = db.Column(db.String(100))
    address = db.Column(db.Text) # Detail Jalan/RT/RW
    coordinates = db.Column(db.String(100)) 

    # --- RELASI KEMITRAAN BERJENJANG ---
    # 1. Menghubungkan Siswa ke Sekolah
    sekolah_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # 2. Menghubungkan Sekolah/Lansia ke Mitra Dapur (Pilihan saat Register)
    dapur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relasi backref untuk membedakan daftar penerima di sisi Dapur
    pendaftar_dapur = db.relationship('Users', 
                                      foreign_keys=[dapur_id],
                                      backref=db.backref('mitra_dapur', remote_side=[id]))
    # Tambahkan ini di bawah relasi pendaftar_dapur
    pendaftar_sekolah = db.relationship('Users', 
                                    foreign_keys=[sekolah_id],
                                    backref=db.backref('daftar_siswa', remote_side=[id]))
    
    profile_picture = db.Column(db.String(255), nullable=True, default='default_avatar.png')
    # --- FILE UPLOADS (Path ke static/uploads) ---
    file_ktp = db.Column(db.String(255))         
    file_sk_operator = db.Column(db.String(255)) 
    file_kitchen_photo = db.Column(db.String(255))

    # --- DATA LOKASI & DAPUR ---
    kitchen_name = db.Column(db.String(100)) # Khusus Admin Dapur
    mitra_type = db.Column(db.String(50))   # Khusus Admin Dapur


    # --- RELASI FUNGSIONAL ---
    master_ingredients = db.relationship('MasterIngredient', backref='owner', lazy='dynamic')
    my_menus = db.relationship('Menus', backref='chef', lazy='dynamic')
    my_staff = db.relationship('Staff', backref='boss', lazy='dynamic')
    my_beneficiaries = db.relationship('Penerima', backref='owner', lazy='dynamic')
    my_activities = db.relationship('AktivitasDapur', backref='admin_dapur', lazy='dynamic')
    reviews = db.relationship('UlasanPenerima', backref='student', lazy='dynamic')
    distribusi_logs = db.relationship('LogDistribusi', 
                                      foreign_keys=[LogDistribusi.dapur_id], 
                                      backref='dapur_pengirim', 
                                      lazy='dynamic')
    my_chats = db.relationship('ChatHistory', backref='sender', lazy='dynamic')

    temp_otp = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = hash_pass(password)

    def verify_password(self, password):        
        return verify_pass(password, self.password_hash)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


# --- MODEL AKTIVITAS DAPUR ---
class AktivitasDapur(db.Model):
    __tablename__ = 'aktivitas_dapur'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    jenis_aktivitas = db.Column(db.String(50), nullable=False)
    bukti_foto = db.Column(db.String(255), nullable=False)
    
    tanggal = db.Column(db.Date, default=datetime.now().date)   
    waktu_mulai = db.Column(db.DateTime, default=datetime.now)  
    waktu_selesai = db.Column(db.DateTime, nullable=True)       
    status = db.Column(db.String(20), default='Proses')
    catatan = db.Column(db.Text, nullable=True)                 

    def to_dict(self):
        return {
            'id': self.id,
            'aktivitas': self.jenis_aktivitas,
            'foto': self.bukti_foto,
            'jam': self.waktu_mulai.strftime('%H:%M'),
            'status': self.status,
            'selesai': self.waktu_selesai.strftime('%H:%M') if self.waktu_selesai else '-'
        }

# --- DATABASE KOMPOSISI PANGAN ---
class MasterIngredient(db.Model):
    __tablename__ = 'master_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    name = db.Column(db.String(100), nullable=False)
    
    # Kategori: Sumber Karbohidrat, Protein Hewani, Protein Nabati, Sayuran, Buah, Susu, Lemak
    category = db.Column(db.String(50)) 
    
    # Berat Porsi Standar (gr) - Berat bersih yang biasa disajikan
    weight = db.Column(db.Float, default=0.0) 
    
    # Kandungan Gizi Makro (Per 100gr BDD)
    kcal = db.Column(db.Float, default=0.0)    # Energi (kkal)
    protein = db.Column(db.Float, default=0.0) # Protein (g)
    fat = db.Column(db.Float, default=0.0)     # Lemak (g)
    carb = db.Column(db.Float, default=0.0)    # Karbohidrat (g)
    
    # Kandungan Gizi Mikro (Wajib Standar MBG 2024)
    fiber = db.Column(db.Float, default=0.0)   # Serat (g)
    calcium = db.Column(db.Float, default=0.0) # Kalsium (mg)
    iron = db.Column(db.Float, default=0.0)    # Zat Besi (mg)
    vit_a = db.Column(db.Float, default=0.0)   # Vitamin A (RE)
    vit_c = db.Column(db.Float, default=0.0)   # Vitamin C (mg)
    folate = db.Column(db.Float, default=0.0)  # Folat (mcg)
    vit_b12 = db.Column(db.Float, default=0.0) # Vitamin B12 (mcg)

# --- KATALOG MENU HARIAN (DITAMPILKAN KE USER) ---
class Menus(db.Model):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    menu_name = db.Column(db.String(255), nullable=False)
    photo = db.Column(db.String(255)) # Foto QC Sajian
    
    # Jadwal Distribusi
    distribution_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    
    # Akumulasi Gizi Total Per Porsi (Hasil kalkulasi komponen)
    total_kcal = db.Column(db.Float, default=0.0)
    total_protein = db.Column(db.Float, default=0.0)
    total_fat = db.Column(db.Float, default=0.0)
    total_carb = db.Column(db.Float, default=0.0)
    
    # Akumulasi Mikro Nutrisi untuk Tampilan Aplikasi Mobile
    total_fiber = db.Column(db.Float, default=0.0)
    total_iron = db.Column(db.Float, default=0.0)
    total_calcium = db.Column(db.Float, default=0.0)
    total_vit_a = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi ke komponen piring
    components = db.relationship('MenuIngredients', backref='menu', cascade="all, delete-orphan")


# --- DETAIL KOMPONEN ISI PIRINGKU ---
class MenuIngredients(db.Model):
    __tablename__ = 'menu_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('master_ingredients.id'), nullable=False)
    
    # Berat bersih komponen yang digunakan dlm porsi ini (gr)
    weight = db.Column(db.Float, nullable=False) 
    
    # Link ke info nutrisi dasar
    ingredient_info = db.relationship('MasterIngredient')


# --- MODEL PENERIMA & STAFF (TIDAK BERUBAH) ---
class Penerima(db.Model):
    __tablename__ = 'penerima'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    kategori = db.Column(db.String(50), nullable=False)
    nama_lokasi = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(200))
    kuota = db.Column(db.Integer, default=0)
    pic_nama = db.Column(db.String(100))
    pic_telepon = db.Column(db.String(20)) 

    def to_dict(self):
        return {'id': self.id, 'category': self.kategori, 'name': self.nama_lokasi, 'location': self.alamat, 'count': self.kuota, 'pic': self.pic_nama, 'phone': self.pic_telepon}

class UlasanPenerima(db.Model):
    __tablename__ = 'ulasan_penerima'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # --- KOLOM BARU YANG HARUS DITAMBAHKAN ---
    rating = db.Column(db.Integer, nullable=False, default=0) 
    tags = db.Column(db.String(255)) # Disimpan sebagai string "Tag1,Tag2"
    status_ai = db.Column(db.String(20), default='netral') 
    # ----------------------------------------

    nama_pengulas = db.Column(db.String(100))
    ulasan_teks = db.Column(db.Text, nullable=True) # Dibuat nullable agar siswa bisa isi tag saja
    tanggal = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'penerima': self.nama_pengulas, 
            'rating': self.rating,
            'tags': self.tags.split(',') if self.tags else [], 
            'text': self.ulasan_teks,
            'status': self.status_ai,
            'tanggal': self.tanggal.strftime('%Y-%m-%d %H:%M')
        }
class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    img_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    logs = db.relationship('AttendanceLog', backref='employee', lazy='dynamic', cascade='all, delete-orphan')

    def generate_avatar(self):
        color = 'adb5bd'
        if 'Chef' in self.role: color = '2dce89'
        elif 'Cook' in self.role: color = '11cdef'
        elif 'Packer' in self.role: color = 'fb6340'
        elif 'Driver' in self.role: color = '5e72e4'
        self.img_url = f"https://ui-avatars.com/api/?name={self.name}&background={color}&color=fff"

    def to_dict(self, target_date=None):
        if target_date is None: target_date = datetime.now().date()
        log = self.logs.filter_by(date=target_date).first()
        current_status = 'Off'; check_in_time = None; check_out_time = None
        if log:
            check_in_time = log.check_in.strftime('%H:%M')
            if log.check_out: current_status = 'Pulang'; check_out_time = log.check_out.strftime('%H:%M')
            else: current_status = 'Hadir'
        monthly_attendance = self.logs.filter(db.extract('month', AttendanceLog.date) == target_date.month, db.extract('year', AttendanceLog.date) == target_date.year).count()
        return {'id': self.id, 'name': self.name, 'role': self.role, 'phone': self.phone, 'img': self.img_url, 'status': current_status, 'attendance': monthly_attendance, 'check_in_time': check_in_time, 'check_out_time': check_out_time}

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.now().date)
    check_in = db.Column(db.DateTime, default=datetime.now)
    check_out = db.Column(db.DateTime, nullable=True)
    status_note = db.Column(db.String(50), default='Hadir')

# --- MODEL MEMORI CHATBOT (RAG & HISTORY) ---
class ChatHistory(db.Model):
    __tablename__ = 'chat_history'

    id = db.Column(db.Integer, primary_key=True)
    
    # Menghubungkan ke user yang sedang bertanya
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Konten percakapan
    message = db.Column(db.Text, nullable=False) # Pertanyaan User
    reply = db.Column(db.Text, nullable=False)   # Jawaban Llama 3
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user_id,
            'message': self.message,
            'reply': self.reply,
            'time': self.timestamp.strftime('%H:%M')
        }
    
class LaporanKendala(db.Model):
    __tablename__ = 'laporan_kendala'

    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dapur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    kategori = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    foto_bukti = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), default='pending') 
    
    # Pelacakan Waktu
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    pengirim = db.relationship('Users', foreign_keys=[user_id], backref='laporan_dikirim')
    dapur_tujuan = db.relationship('Users', foreign_keys=[dapur_id], backref='laporan_masuk_dapur')

# --- LOGIN LOADER ---
@login_manager.user_loader
def user_loader(id):
    return Users.query.get(int(id))

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    user = Users.query.filter_by(email=email).first()
    return user if user else None

