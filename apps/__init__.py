from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_migrate import Migrate
from flask_cors import CORS 
from flask_mail import Mail # Tambahkan Flask-Mail
from authlib.integrations.flask_client import OAuth 
import os
from werkzeug.middleware.proxy_fix import ProxyFix

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
    
    # --- PERBAIKAN CORS ---
    # Ubah r"/api/*" menjadi r"/*" agar folder /static (gambar) juga bisa diakses oleh Flutter Web
    CORS(app, resources={r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "ngrok-skip-browser-warning", "Access-Control-Allow-Origin"]
    }})

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

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    Migrate(app, db)

    return app