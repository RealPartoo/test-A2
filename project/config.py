import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True

    # MySQL
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_DB   = os.environ.get("MYSQL_DB", "IFN582_Database")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "P@$$w0rd")

    # -------- uploads (สำคัญ) --------
    BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    # โฟลเดอร์จริงที่ใช้ save รูป
    UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
    # ชนิดไฟล์อนุญาต
    ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp"}
    # จำกัดขนาดไฟล์
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False