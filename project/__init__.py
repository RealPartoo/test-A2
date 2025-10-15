# project/__init__.py
import os
from flask import Flask

# binds Flask-MySQLdb in models.py and exposes get_db() etc.
from .models import init_models, close_db

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Base config (override via env) ----
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    # ---- MySQL (Flask-MySQLdb) ----
    app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "127.0.0.1")
    app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", "3306"))
    app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
    app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "password")
    app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "artlease")
    # return rows as dicts so templates can use art.title, etc.
    app.config["MYSQL_CURSORCLASS"] = "DictCursor"

    # ---- Uploads ----
    upload_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir
    app.config["ALLOWED_IMAGE_EXTS"] = {"jpg", "jpeg", "png", "gif", "webp"}

    # ---- DB bind & teardown ----
    init_models(app)
    app.teardown_appcontext(close_db)

    # ---- Blueprints ----
    from .views import main
    app.register_blueprint(main)

    # optional auth blueprint (if present)
    try:
        from .auth import auth
        app.register_blueprint(auth)
    except Exception:
        pass

    return app
