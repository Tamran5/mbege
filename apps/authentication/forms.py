# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FileField
from wtforms.validators import Email, DataRequired, EqualTo

# login and registration

class LoginForm(FlaskForm):
    username = StringField('Username',
                         id='username_login',
                         validators=[DataRequired()])
    password = PasswordField('Password',
                             id='pwd_login',
                             validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    # --- 1. Akun Login ---
    email = StringField('Email',
                      id='email_create',
                      validators=[DataRequired(), Email()])
    
    password = PasswordField('Password',
                             id='pwd_create',
                             validators=[DataRequired()])
    
    confirm_password = PasswordField('Konfirmasi Password',
                                     id='pwd_confirm',
                                     validators=[DataRequired(), EqualTo('password', message='Password harus sama')])

    # --- 2. Biodata Penanggung Jawab ---
    fullname = StringField('Nama Lengkap', id='fullname', validators=[DataRequired()])
    nik = StringField('NIK', id='nik', validators=[DataRequired()])
    whatsapp = StringField('WhatsApp', id='whatsapp', validators=[DataRequired()])

    # --- 3. Profil Dapur ---
    kitchen_name = StringField('Nama Dapur', id='kitchen_name', validators=[DataRequired()])
    
    mitra_type = SelectField('Jenis Mitra', choices=[
        ('umkm', 'UMKM'),
        ('industrial', 'Industri'),
        ('school', 'Sekolah'),
        ('tnipolri', 'TNI/Polri')
    ])
    
    # --- UPDATE: Struktur Wilayah Baru (Hierarki) ---
    # Catatan: Choices biasanya dikosongkan [] di sini dan diisi via JavaScript (AJAX) 
    # atau di-set dinamis lewat route Python saat render_template.
    
    province = SelectField('Provinsi', id='province', validators=[DataRequired()], choices=[])
    
    regency = SelectField('Kabupaten/Kota', id='regency', validators=[DataRequired()], choices=[])
    
    district = SelectField('Kecamatan', id='district', validators=[DataRequired()], choices=[])
    
    # --- Lanjutan Alamat ---
    address = TextAreaField('Alamat Detail (Jalan/RT/RW)', id='address', validators=[DataRequired()])
    
    coordinates = StringField('Koordinat', id='coordinates', validators=[DataRequired()])

    # --- 5. File Uploads ---
    file_ktp = FileField('Foto KTP')
    file_slhs = FileField('Sertifikat SLHS')
    file_kitchen_photo = FileField('Foto Dapur')