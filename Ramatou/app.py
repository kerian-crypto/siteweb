from __future__ import annotations

from pathlib import Path

from flask import Flask

from blueprints.admin import admin_bp
from blueprints.user import user_bp
from extensions import db, socketio
import realtime  # noqa: F401
from security import csrf_protect, current_user_data, get_or_create_csrf_token, is_logged_in
from services import migrate_schema, seed_data

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "unknow_store.db"
DOWNLOADS_DIR = BASE_DIR / "static" / "downloads"
QRCODE_DIR = BASE_DIR / "static" / "qrcodes"
INVOICE_DIR = BASE_DIR / "static" / "invoices"
CHAT_UPLOAD_DIR = BASE_DIR / "static" / "chat_uploads"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://ramatou_db_user:tFt9ZomPJqjljrGz1TO9GvIGqlHguIWJ@dpg-d6e0k3tm5p6s73fhg5cg-a/ramatou_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-change-me"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

    app.config["BASE_DIR"] = str(BASE_DIR)
    app.config["DOWNLOADS_DIR"] = str(DOWNLOADS_DIR)
    app.config["QRCODE_DIR"] = str(QRCODE_DIR)
    app.config["INVOICE_DIR"] = str(INVOICE_DIR)
    app.config["CHAT_UPLOAD_DIR"] = str(CHAT_UPLOAD_DIR)

    db.init_app(app)
    socketio.init_app(app)

    @app.context_processor
    def inject_globals():
        return {
            "current_user": current_user_data(),
            "is_logged_in": is_logged_in(),
            "csrf_token": get_or_create_csrf_token,
        }

    @app.before_request
    def _csrf():
        return csrf_protect()

    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        migrate_schema()
        seed_data(DOWNLOADS_DIR)

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
