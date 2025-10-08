# project/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from .models import get_user_by_email, get_user_by_id, verify_password, create_user

auth = Blueprint("auth", __name__)

class AuthUser(UserMixin):
    def __init__(self, row):
        self.id = row["userId"]
        self.userName = row["userName"]
        self.email = row["email"]
        self.role = row["role"]

def user_from_row(row):
    return AuthUser(row) if row else None

def load_user_from_db(user_id):
    row = get_user_by_id(int(user_id))
    return user_from_row(row)

@auth.get("/login")
def login():
    return render_template("login.html")

@auth.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    row = get_user_by_email(email)
    if not row or not verify_password(row["passwordHash"], password):
        flash("Invalid email or password", "danger")
        return redirect(url_for("auth.login"))

    login_user(user_from_row(row))
    # ✅ Toast: login success
    flash("Login success", "success")

    next_url = request.args.get("next") or request.form.get("next")
    return redirect(next_url or url_for("main.home"))

@auth.get("/register")
def register():
    return render_template("register.html")

@auth.post("/register")
def register_post():
    userName = request.form.get("userName", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "customer")

    if not userName or not email or not password:
        flash("Please complete all fields", "warning")
        return redirect(url_for("auth.register"))

    if get_user_by_email(email):
        flash("This email is already registered", "warning")
        return redirect(url_for("auth.register"))

    create_user(userName, email, password, role)
    # ✅ Toast: register success (optional)
    flash("Account created. Please log in.", "success")
    return redirect(url_for("auth.login"))

@auth.get("/logout")
@login_required
def logout():
    logout_user()
    # ✅ Toast: logout success
    flash("Logout success", "info")
    return redirect(url_for("main.home"))
