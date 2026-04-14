from pathlib import Path
from flask import Flask
from flask_cors import CORS

from app.core.config import Config
from app.db.database import db

# Blueprints
from app.api.auth_routes import auth_bp
from app.api.admin_routes import admin_bp
from app.api.model_routes import model_bp
from app.api.word_routes import word_bp
from app.api.user_routes import user_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    # Ensure instance folder exists
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Initialize DB
    db.init_app(app)

    # -----------------------------
    # REGISTER BLUEPRINTS
    # -----------------------------
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(model_bp, url_prefix="/api/models")
    app.register_blueprint(word_bp, url_prefix="/api/words")
    app.register_blueprint(user_bp, url_prefix="/api/users")

    # -----------------------------
    # HEALTH CHECK
    # -----------------------------
    @app.get("/health")
    def health():
        return {"status": "ok"}

    # -----------------------------
    # GLOBAL ERROR HANDLER (🔥 IMPORTANT)
    # -----------------------------
    @app.errorhandler(Exception)
    def handle_exception(e):
        print("GLOBAL ERROR:", str(e))
        return {"error": str(e)}, 500

    # -----------------------------
    # CREATE DB TABLES
    # -----------------------------
    with app.app_context():
        db.create_all()

    return app