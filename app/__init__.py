# app/__init__.py
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Unauthorized"}), 401


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # Create uploads directory
    uploads_dir = os.path.join(app.instance_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Load config
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///tastebite.db'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            UPLOAD_FOLDER=uploads_dir,
            MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
        )

        # Configure CORS
        CORS(app, 
             resources={r"/api/*": {
                 "origins": [
                     "http://localhost:5173",
                     "http://localhost:3000",
                     "https://tastebite-front.vercel.app"
                 ],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": [
                     "Content-Type",
                     "Authorization",
                     "Accept",
                     "Origin",
                     "X-Requested-With",
                     "Access-Control-Request-Method",
                     "Access-Control-Request-Headers",
                     "X-CSRF-TOKEN"
                 ],
                 "supports_credentials": True,
                 "expose_headers": [
                     "Content-Type",
                     "Authorization",
                     "Access-Control-Allow-Origin",
                     "Access-Control-Allow-Credentials",
                     "Set-Cookie"
                 ],
                 "max_age": 3600
             }},
             supports_credentials=True
        )

        # Production-specific cookie settings for cross-domain authentication
        if os.environ.get('RENDER') == 'true':
            app.config.update(
                SESSION_COOKIE_SECURE=True,
                SESSION_COOKIE_SAMESITE='None',
                SESSION_COOKIE_HTTPONLY=False,  # Allow JavaScript access for mobile
                SESSION_COOKIE_DOMAIN=None,  # Let browser handle domain
                REMEMBER_COOKIE_SECURE=True,
                REMEMBER_COOKIE_SAMESITE='None',
                REMEMBER_COOKIE_HTTPONLY=False,  # Allow JavaScript access for mobile
                REMEMBER_COOKIE_DOMAIN=None,  # Let browser handle domain
            )
        else:
            # Development settings
            app.config.update(
                SESSION_COOKIE_SECURE=False,
                SESSION_COOKIE_SAMESITE='Lax',
                SESSION_COOKIE_HTTPONLY=True,
                SESSION_COOKIE_DOMAIN=None,
                REMEMBER_COOKIE_SECURE=False,
                REMEMBER_COOKIE_SAMESITE='Lax',
                REMEMBER_COOKIE_HTTPONLY=True,
                REMEMBER_COOKIE_DOMAIN=None,
            )
        
        app.config.update(
            # Common session settings
            PERMANENT_SESSION_LIFETIME=86400,  # 24 hours
            SESSION_REFRESH_EACH_REQUEST=True,
        )
    else:
        app.config.from_mapping(test_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    login_manager.login_view = None  # Disable redirect to login view
    jwt.init_app(app)
    
    # Register blueprints
    from .routes import bp, bp_ai
    app.register_blueprint(bp, url_prefix="/api")
    app.register_blueprint(bp_ai)

    # # Create database tables
    # with app.app_context():
    #     try:
    #         db.create_all()
    #         logger.info("Database tables created successfully")
    #     except Exception as e:
    #         logger.error(f"Error creating database tables: {str(e)}")
    #         raise

    return app
