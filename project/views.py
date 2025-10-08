# project/views.py
import os, uuid
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import (
    ensure_provider_for_user, create_artwork, list_artworks, get_artwork, list_distinct_artists, list_distinct_galleries, 
)
from flask import send_from_directory


main = Blueprint("main", __name__)

# ---------------- helpers ----------------
def role_required(*roles):
    def wrapper(fn):
        def inner(*a, **kw):
            if not current_user.is_authenticated:
                return abort(403)
            if current_user.role not in roles:
                return abort(403)
            return fn(*a, **kw)
        inner.__name__ = fn.__name__
        return login_required(inner)
    return wrapper

def _cart():
    return session.setdefault("cart", [])

def _save_image(file_storage):
    """
    เซฟไฟล์ลง <project>/project/static/uploads/<new_name>
    และคืนค่า string สำหรับเก็บใน DB เป็น 'uploads/<new_name>'
    (เพื่อให้เรียกใช้ด้วย url_for('static', filename=imageUrl) ได้ตรง)
    """
    cfg = current_app.config
    fname = secure_filename(file_storage.filename or "")
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if ext not in cfg["ALLOWED_IMAGE_EXTS"]:
        raise ValueError("Unsupported image type")
    new_name = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(cfg["UPLOAD_FOLDER"], new_name)
    file_storage.save(dest)
    # ✅ เก็บใน DB แบบ static-relative
    return f"uploads/{new_name}"

# ---------------- pages ----------------
@main.get("/")
def home():
    return render_template("home.html")

@main.get("/gallery")
def gallery():
    filters = {
        "artist":  request.args.get("artist") or "",
        "gallery": request.args.get("gallery") or "",
        "type":    request.args.get("type") or "",
        "genre":   request.args.get("genre") or "",
        "price":   request.args.get("price") or "",
        "size":    request.args.get("size") or "",
        "period":  request.args.get("period") or "",
        "q":       request.args.get("q") or "",
    }
    items = list_artworks(filters)

    # dropdown options จาก DB
    artist_opts   = list_distinct_artists()
    gallery_opts  = list_distinct_galleries()

    return render_template(
        "gallery.html",
        items=items,
        filters=filters,
        artist_opts=artist_opts,
        gallery_opts=gallery_opts,
    )

@main.get("/item/<int:item_id>")
def item_detail(item_id: int):
    it = get_artwork(item_id)
    if not it:
        abort(404)
    return render_template("item_detail.html", item=it)

# ---- cart ----
@main.post("/cart/add/<int:item_id>")
def cart_add(item_id: int):
    it = get_artwork(item_id)
    if not it:
        flash("Artwork not found", "warning")
        return redirect(url_for("main.gallery"))
    months = int(request.form.get("months", "1") or 1)
    _cart().append({
        "id": it["artworkId"],
        "title": it["title"],
        "imageUrl": it["imageUrl"],
        "pricePerMonth": float(it["pricePerMonth"]),
        "months": months,
        "subtotal": float(it["pricePerMonth"]) * months
    })
    session.modified = True
    flash("Added to cart", "success")
    return redirect(request.referrer or url_for("main.gallery"))

@main.get("/cart/clear")
def cart_clear():
    session.pop("cart", None)
    flash("Cart cleared", "info")
    return redirect(request.referrer or url_for("main.gallery"))

@main.get("/checkout")
def checkout():
    cart = _cart()
    total = sum(x["subtotal"] for x in cart)
    return render_template("checkout.html", cart=cart, total=total)

# ---- upload (vendor) ----
@main.route("/upload", methods=["GET", "POST"])
@role_required("artist", "gallery", "admin")
def upload():
    prov = ensure_provider_for_user(current_user.id, current_user.role, current_user.userName)

    if request.method == "POST":
        try:
            img = request.files.get("image")
            if not img or img.filename == "":
                flash("Please choose an image", "warning")
                return redirect(url_for("main.upload"))
            image_path = _save_image(img)  # <-- คืน 'uploads/<file>'

            data = {
                "title": request.form.get("title", "").strip(),
                "artistName": request.form.get("artistName", "").strip() or (prov["artistName"] or ""),
                "galleryName": request.form.get("galleryName", "").strip() or (prov["galleryName"] or ""),
                "type": request.form.get("type"),
                "genre": request.form.get("genre"),
                "pricePerMonth": float(request.form.get("pricePerMonth", "0") or 0),
                "size": request.form.get("size"),
                "year": request.form.get("year"),
                "leaseStatus": request.form.get("leaseStatus", "Available"),
                "imageUrl": image_path,  # <-- เก็บแบบ static-relative
                "description": request.form.get("description", "")[:1000]
            }
            if not data["title"] or data["pricePerMonth"] <= 0:
                flash("Please complete required fields", "warning")
                return redirect(url_for("main.upload"))

            new_id = create_artwork(prov["providerId"], data)
            flash("Artwork uploaded", "success")
            return redirect(url_for("main.item_detail", item_id=new_id))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Upload failed", "danger")

    return render_template("vendor_manage.html")

@main.get("/uploads/<path:filename>")
def uploads_compat(filename):
    # ชี้ไปยังโฟลเดอร์จริงที่ตั้งไว้ใน __init__.py -> app.config["UPLOAD_FOLDER"]
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)

# ---- centers (minimal) ----
@main.get("/admin/center")
@role_required("admin")
def admin_center():
    return render_template("user_center_admin.html")

@main.get("/customer/center")
@role_required("customer")
def customer_center():
    return render_template("user_center_customer.html")

@main.get("/vendor/center")
@role_required("artist", "gallery", "admin")
def vendor_center():
    return render_template("user_center_vendor.html")
