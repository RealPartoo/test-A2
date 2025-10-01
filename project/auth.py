from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import get_user_by_email, verify_password, create_user  # <- ใช้ฟังก์ชันใน models ของคุณ

auth = Blueprint("auth", __name__)

# -----------------------------
# Login
# -----------------------------
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            flash("Invalid email or password.", "danger")
            return render_template("login.html"), 401

        # set session
        session.clear()
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]        # สำคัญ!

        # ไปหน้าที่ตั้งไว้ (เช่น /customer/center) หรือกลับหน้าแรก
        next_url = request.args.get("next") or url_for("main.home")
        return redirect(next_url)

    return render_template("login.html")

# -----------------------------
# Logout
# -----------------------------
@auth.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("main.home"))

# -----------------------------
# Register
# -----------------------------
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = request.form.get("role") or "customer"  # ตั้ง default เป็น customer

        if not name or not email or not password:
            flash("Please fill in all required fields.", "warning")
            return render_template("register.html"), 400

        try:
            # บันทึกลง DB (ฟังก์ชันใน models ของคุณต้องรองรับ 4 พารามิเตอร์นี้)
            create_user(name, email, password, role)
            flash("Account created. Please sign in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            # แสดงข้อความ error สั้น ๆ (log รายละเอียดจริงใน server)
            flash("Could not create account. Please try again.", "danger")
            return render_template("register.html"), 500

    return render_template("register.html")
