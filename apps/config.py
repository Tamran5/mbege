# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from decouple import config

class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_007')

    # --- Konfigurasi Database (MySQL) ---
    # Update: Menambahkan '+pymysql' agar menggunakan driver yang tepat
    SQLALCHEMY_DATABASE_URI = '{}+pymysql://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE', default='mysql'),
        config('DB_USERNAME', default='root'),
        config('DB_PASS', default=''),
        config('DB_HOST', default='localhost'),
        config('DB_PORT', default=3306),
        config('DB_NAME', default='mbg_db')
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Konfigurasi Upload File (PENTING) ---
    # Ditambahkan karena Model Users Anda memiliki kolom file (file_ktp, dll)
    # File akan disimpan di: apps/static/uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'apps/static/uploads')
    
  
    # Batasi Ukuran File Upload (Sesuai permintaan: 2 MB)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class DebugConfig(Config):
    DEBUG = True


# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}