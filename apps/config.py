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

    SESSION_COOKIE_NAME = 'mbg_admin_session'
    
    # Memastikan sesi dibersihkan saat browser ditutup (opsional)
    SESSION_PERMANENT = False
    
    # --- Konfigurasi Database (MySQL) ---
    # Menggunakan +pymysql untuk koneksi stabil dari Flask ke MySQL
    SQLALCHEMY_DATABASE_URI = '{}+pymysql://{}:{}@{}:{}/{}'.format(
        config('DB_ENGINE',   default='mysql'),
        config('DB_USERNAME', default='root'),
        config('DB_PASS',     default=''),
        config('DB_HOST',     default='localhost'),
        config('DB_PORT',     default=3306, cast=int),
        config('DB_NAME',     default='mbg_db')
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Konfigurasi Flask-Mail (OTP Email) ---
    MAIL_SERVER         = config('MAIL_SERVER',   default='smtp.gmail.com')
    MAIL_PORT           = config('MAIL_PORT',     default=587, cast=int)
    MAIL_USE_TLS        = config('MAIL_USE_TLS',  default=True, cast=bool)
    MAIL_USERNAME       = config('MAIL_USERNAME')
    MAIL_PASSWORD       = config('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = config('MAIL_DEFAULT_SENDER')

    # --- Konfigurasi Upload File ---
    UPLOAD_FOLDER = os.path.join(basedir, 'apps', 'static', 'uploads')
    
    # Batasi Ukuran File Upload (Maksimal 2 MB)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024


class ProductionConfig(Config):
    DEBUG = False

    # Security Settings
    SESSION_COOKIE_HTTPONLY  = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class DebugConfig(Config):
    DEBUG = True


# Memuat konfigurasi berdasarkan environment (Production atau Debug)
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}