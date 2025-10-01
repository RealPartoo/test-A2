import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    # MySQL (ปรับชื่อ DB/ผู้ใช้ ตามที่คุณแจ้ง)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:P@$$w0rd@localhost:3306/IFN582_Database"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # ที่เก็บไฟล์อัปโหลด (ภายใต้ static เพื่อเสิร์ฟง่าย)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

class DevConfig(Config):
    TEMPLATES_AUTO_RELOAD = True
