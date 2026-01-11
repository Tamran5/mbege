from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_cors import CORS 
from flask_mail import Mail # Tambahkan Flask-Mail
from authlib.integrations.flask_client import OAuth 
import os

# Inisialisasi Database dan Ekstensi
db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
mail = Mail() # Inisialisasi objek Mail untuk OTP

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)
    mail.init_app(app) 
    
    # CORS tetap diaktifkan untuk mendukung Flutter Web
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

def register_blueprints(app):
    # 1. Dashboard Web (HTML)
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

    # 2. Mobile API (Flutter/JSON)
    from apps.api import api_bp
    app.register_blueprint(api_bp)

def create_app(config):
    # BASE_DIR menunjuk ke folder 'apps' (mbege_version2/apps)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        # PERBAIKAN: Path static disesuaikan agar tidak bertumpuk 'apps/apps/static'
        static_folder=os.path.join(BASE_DIR, 'static'),
        static_url_path='/static'
    )

    app.config.from_object(config)

    # Registrasi Ekstensi dan Blueprints
    register_extensions(app)
    register_blueprints(app)

    Migrate(app, db)

    return app