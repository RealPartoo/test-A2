# project/models.py
import os
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash

# ====== DB CONFIG ======
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "P@$$w0rd")
DB_NAME = os.getenv("DB_NAME", "IFN582_Database")   # ปรับให้เป็นชื่อ DB ของคุณ

def get_db():
    """
    คืน connection ใหม่ทุกครั้งที่เรียก (autocommit เปิดไว้)
    """
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=True,
        cursorclass=DictCursor,
        charset="utf8mb4",
    )

# ====== SCHEMA BOOTSTRAP ======
def ensure_schema():
    """
    สร้างตาราง users ถ้ายังไม่มี
    """
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin','vendor','customer') NOT NULL DEFAULT 'customer',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(sql)

# เรียกตอน import ไฟล์ เพื่อให้แน่ใจว่ามีตาราง
ensure_schema()

# ====== PASSWORD HELPERS ======
def hash_password(plain: str) -> str:
    return generate_password_hash(plain, method="pbkdf2:sha256", salt_length=16)

def verify_password(plain: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, plain)

# ====== USER QUERIES ======
def get_user_by_email(email: str):
    """
    คืน dict {'id','name','email','password_hash','role',...} หรือ None
    """
    sql = "SELECT id, name, email, password_hash, role, created_at, updated_at FROM users WHERE email=%s LIMIT 1"
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(sql, (email,))
        return cur.fetchone()

def create_user(name: str, email: str, password_plain: str, role: str = "customer"):
    """
    สร้างผู้ใช้ใหม่ (จะ raise error ถ้า email ซ้ำ เพราะ unique)
    """
    # normalize inputs
    name = (name or "").strip()
    email = (email or "").strip().lower()
    role = (role or "customer").strip().lower()
    if role not in ("admin", "vendor", "customer"):
        role = "customer"

    password_hash = hash_password(password_plain)

    sql = """
        INSERT INTO users (name, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """
    with get_db() as conn, conn.cursor() as cur:
        cur.execute(sql, (name, email, password_hash, role))
        return cur.lastrowid
