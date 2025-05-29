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

# Configure logging
logging.basicConfig(level=logging.INFO)
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


def create_app():
    app = Flask(__name__, static_folder='static')

    # ───────────────  Paths & config  ───────────────
    instance_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'instance'
    )
    os.makedirs(instance_path, exist_ok=True)

    # Force PostgreSQL URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set!")
        raise ValueError("DATABASE_URL environment variable is not set!")
    
    # Ensure we're using PostgreSQL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("Converted postgres:// to postgresql://")
    
    # Log database URL (without password)
    safe_url = database_url.replace(database_url.split("@")[0], "***")
    logger.info(f"Using database: {safe_url}")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 86400  # 24 hours

    # ───────────────  Session / CORS  ───────────────
    app.config["SESSION_COOKIE_SECURE"] = True  # Enable for HTTPS
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
        },
        supports_credentials=True
    )

    # ───────────────  Extensions  ───────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    jwt.init_app(app)

    # ───────────────  Blueprints  ───────────────
    from .routes import bp, bp_ai
    app.register_blueprint(bp, url_prefix="/api")
    app.register_blueprint(bp_ai)          # уже имеет url_prefix='/api/ai'

    # ───────────────  Debug helper  ───────────────
    @app.route("/debug")
    def debug():
        return jsonify({
            "status": "ok",
            "config": {
                "database_url": app.config["SQLALCHEMY_DATABASE_URI"],
                "instance_path": instance_path,
                "allowed_origins": allowed_origins
            }
        })

    # Test database connection
    with app.app_context():
        try:
            db.engine.connect()
            logger.info("Successfully connected to the database")
        except Exception as e:
            logger.error(f"Failed to connect to the database: {str(e)}")
            logger.exception("Full traceback:")
            raise

    return app
