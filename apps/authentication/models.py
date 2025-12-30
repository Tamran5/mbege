from flask_login import UserMixin
from apps import db, login_manager 
from apps.authentication.util import hash_pass, verify_pass 
from datetime import datetime

# --- MODEL USER (LOGIN & PROFIL) ---
class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column('password', db.LargeBinary)
    
    role = db.Column(db.String(20), default='admin_dapur')
    is_approved = db.Column(db.Boolean, default=False) 

    # Data Diri & Dapur
    fullname = db.Column(db.String(100))
    nik = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    kitchen_name = db.Column(db.String(100))
    mitra_type = db.Column(db.String(50))
    
    # Lokasi
    province = db.Column(db.String(50))
    regency = db.Column(db.String(50))
    district = db.Column(db.String(50))
    address = db.Column(db.Text)
    coordinates = db.Column(db.String(100))

    # File Uploads
    file_ktp = db.Column(db.String(255))
    file_slhs = db.Column(db.String(255))
    file_kitchen_photo = db.Column(db.String(255))

    # --- RELASI DATABASE ---
    master_ingredients = db.relationship('MasterIngredient', backref='owner', lazy='dynamic')
    my_menus = db.relationship('Menus', backref='chef', lazy='dynamic')
    my_staff = db.relationship('Staff', backref='boss', lazy='dynamic')
    my_beneficiaries = db.relationship('Penerima', backref='owner', lazy='dynamic')
    my_activities = db.relationship('AktivitasDapur', backref='admin_dapur', lazy='dynamic', cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = hash_pass(password)

    def verify_password(self, password):        
        return verify_pass(password, self.password_hash)

    def get_lat_long(self):
        try:
            if self.coordinates and ',' in self.coordinates:
                lat, lng = self.coordinates.split(',')
                return float(lat.strip()), float(lng.strip())
        except ValueError:
            return None
        return None

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


# --- MASTER BAHAN BAKU (UPDATE STANDAR GIZI 2025) ---
class MasterIngredient(db.Model):
    __tablename__ = 'master_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50)) 
    
    # Gizi Makro
    kcal = db.Column(db.Float, default=0.0)    # Energi (kkal)
    carb = db.Column(db.Float, default=0.0)    # Karbohidrat (g)
    protein = db.Column(db.Float, default=0.0) # Protein (g)
    fat = db.Column(db.Float, default=0.0)     # Lemak (g)
    
    # Gizi Mikro (Integrasi Gambar 6)
    fiber = db.Column(db.Float, default=0.0)   # Serat (g)
    calcium = db.Column(db.Float, default=0.0) # Kalsium (mg)
    iron = db.Column(db.Float, default=0.0)    # Zat Besi (mg)
    vit_a = db.Column(db.Float, default=0.0)   # Vitamin A (RE)
    vit_c = db.Column(db.Float, default=0.0)   # Vitamin C (mg)
    folate = db.Column(db.Float, default=0.0)  # Folat (mcg)
    vit_b12 = db.Column(db.Float, default=0.0) # Vitamin B12 (mcg)

# --- KATALOG MENU ---
class Menus(db.Model):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    menu_name = db.Column(db.String(255), nullable=False)
    photo = db.Column(db.String(255)) 
    
    total_kcal = db.Column(db.Float, default=0.0)
    total_carb = db.Column(db.Float, default=0.0)
    total_protein = db.Column(db.Float, default=0.0)
    total_fat = db.Column(db.Float, default=0.0)
    # Tambahkan rekap gizi mikro utama
    total_fiber = db.Column(db.Float, default=0.0)
    total_calcium = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    components = db.relationship('MenuIngredients', backref='menu', cascade="all, delete-orphan")


# --- KOMPOSISI RESEP (RELEVANSI KE BAHAN BAKU) ---
class MenuIngredients(db.Model):
    __tablename__ = 'menu_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('master_ingredients.id'), nullable=False)
    
    weight = db.Column(db.Float, nullable=False)
    
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

# --- MODEL ULASAN/FEEDBACK (BARU) ---
class UlasanPenerima(db.Model):
    __tablename__ = 'ulasan_penerima'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    nama_pengulas = db.Column(db.String(100)) # Menyimpan data 'nama' dari JSON
    ulasan_teks = db.Column(db.Text, nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'nama': self.nama_pengulas,
            'ulasan': self.ulasan_teks,
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

# --- LOGIN LOADER ---
@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None