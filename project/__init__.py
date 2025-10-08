# project/__init__.py
import os
from flask import Flask, session
from flask_login import LoginManager
from .config import DevelopmentConfig  # ใช้ dev เป็นค่าเริ่มต้น
from .extensions import close_db
from .auth import auth, load_user_from_db
from .views import main

# ----- Flask-Login -----
login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def _load_user(user_id):
    return load_user_from_db(user_id)

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(DevelopmentConfig)

    # ===== Uploads (static/uploads) =====
    # DB จะเก็บ imageUrl เป็น 'uploads/<file>'
    static_dir = os.path.join(app.root_path, "static")
    upload_root = os.path.join(static_dir, "uploads")
    os.makedirs(upload_root, exist_ok=True)

    # ตั้งค่าเริ่มต้น
    app.config.setdefault("UPLOAD_FOLDER", upload_root)  # ที่ “เซฟไฟล์จริง”
    app.config.setdefault("ALLOWED_IMAGE_EXTS", {"jpg", "jpeg", "png", "gif", "webp"})
    app.config.setdefault("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)  # 16MB

    # ----- Login / teardown -----
    login_manager.init_app(app)
    app.teardown_appcontext(close_db)

    # ----- Jinja context (badge ตะกร้าใน navbar) -----
    @app.context_processor
    def inject_nav_badges():
        cart = session.get("cart", [])
        return {"cart_count": len(cart)}

    # ----- Blueprints -----
    app.register_blueprint(auth)
    app.register_blueprint(main)
    return app
