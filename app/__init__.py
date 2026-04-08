from pathlib import Path

from flask import Flask
from flask_cors import CORS

from app.core.config import Config
from app.db.database import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    # Ensure instance directory exists for sqlite defaults.
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from app.api.word_routes import word_bp
    from app.api.user_routes import user_bp

    # app.register_blueprint(word_bp)
    # app.register_blueprint(user_bp)

    app.register_blueprint(word_bp, url_prefix="/api/words")
    app.register_blueprint(user_bp, url_prefix="/api/users")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    with app.app_context():
        db.create_all()

    return app
