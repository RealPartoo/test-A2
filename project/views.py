# project/views.py
import os
import uuid
from functools import wraps

from flask import (
    Blueprint, render_template, abort, request, redirect,
    url_for, flash, current_app, session, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import date
from .models import (
    ensure_provider_for_user,
    create_artwork,
    list_artworks,
    get_artwork,
    list_distinct_artists,
    list_distinct_galleries,
    create_order,        # NEW
    add_order_items,
    create_payment, 
    create_address, 
    create_order_row, 
    add_order_item_row     # NEW
)

# Optional admin/customer/vendor helpers (safe if not implemented)
try:
    from .models import admin_list_orders, admin_list_artworks, admin_list_providers
except Exception:
    admin_list_orders = admin_list_artworks = admin_list_providers = None

try:
    from .models import list_orders_for_user
except Exception:
    list_orders_for_user = None

try:
    from .models import list_artworks_by_provider, update_artwork, delete_artwork
except Exception:
    list_artworks_by_provider = update_artwork = delete_artwork = None

try:
    from .models import list_orders_for_user
except Exception:
    list_orders_for_user = None


main = Blueprint("main", __name__)

# ------------- helpers -------------
def role_required(*roles):
    """
    - Redirects unauthenticated users to login (via login_required).
    - Returns 403 for authenticated users whose role is not in roles.
    """
    def decorator(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            if current_user.is_authenticated and roles and current_user.role not in roles:
                return abort(403)
            return fn(*args, **kwargs)
        return login_required(inner)
    return decorator


def _cart():
    return session.setdefault("cart", [])


def _parse_float(val, default=0.0):
    try:
        return float(val)
    except Exception:
        return default


def _save_image(file_storage):
    """
    Save to <project>/project/static/uploads/<uuid>.<ext>
    Return 'uploads/<uuid>.<ext>' so templates can use:
      url_for('static', filename=imageUrl)
    """
    cfg = current_app.config
    fname = secure_filename(file_storage.filename or "")
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if not ext or ext not in cfg["ALLOWED_IMAGE_EXTS"]:
        raise ValueError("Unsupported image type")
    new_name = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(cfg["UPLOAD_FOLDER"], new_name)
    file_storage.save(dest)
    return f"uploads/{new_name}"


# ------------- pages -------------
@main.get("/")
def home():
    return render_template("home.html")


@main.get("/gallery")
def gallery():
    # Read filters (from navbar or on-page form)
    filters = {
        "artist":  (request.args.get("artist") or "").strip(),
        "gallery": (request.args.get("gallery") or "").strip(),
        "type":    (request.args.get("type") or "").strip(),
        "genre":   (request.args.get("genre") or "").strip(),
        "price":   (request.args.get("price") or "").strip(),   # '0-50','50-500','500-5000','5000-20000','20000+'
        "size":    (request.args.get("size") or "").strip(),    # 's','m','l','xl'
        "period":  (request.args.get("period") or "").strip(),  # '2020s','2010s',...,'pre-1980'
        "q":       (request.args.get("q") or "").strip(),
        # optional providerId if you reuse for vendor listing
        "providerId": request.args.get("providerId")
    }

    items = list_artworks(filters)

    # Dropdown options
    try:
        artist_opts = list_distinct_artists() or []
    except Exception:
        artist_opts = []
    try:
        gallery_opts = list_distinct_galleries() or []
    except Exception:
        gallery_opts = []

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


# ========== cart ==========
@main.post("/cart/add/<int:item_id>")
def cart_add(item_id: int):
    it = get_artwork(item_id)
    if not it:
        flash("Artwork not found", "warning")
        return redirect(url_for("main.gallery"))

    months = request.form.get("months", "1")
    try:
        months = max(1, min(int(months), 12))
    except Exception:
        months = 1

    # NEW: read startDate (YYYY-MM-DD)
    start_date_str = (request.form.get("startDate") or "").strip()

    price = _parse_float(it.get("pricePerMonth"), 0.0)

    _cart().append({
        "id": it["artworkId"],
        "title": it["title"],
        "imageUrl": it["imageUrl"],
        "pricePerMonth": price,
        "months": months,
        "subtotal": price * months,
        "startDate": start_date_str,    # <-- keep ISO date in cart
    })
    session.modified = True
    flash("Added to cart", "success")
    return redirect(request.referrer or url_for("main.gallery"))


@main.get("/cart/clear")
def cart_clear():
    session.pop("cart", None)
    flash("Cart cleared", "info")
    return redirect(request.referrer or url_for("main.gallery"))


def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    # clamp day
    days = [31,29 if (y%4==0 and (y%100!=0 or y%400==0)) else 28,31,30,31,30,31,31,30,31,30,31][m-1]
    return date(y, m, min(d.day, days))

@main.route("/checkout", methods=["GET","POST"])
def checkout():
    cart = _cart()
    total = sum(_parse_float(x.get("subtotal"), 0.0) for x in cart)

    if request.method == "GET":
        return render_template("checkout.html", cart=cart, total=total)

    # POST
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("main.checkout"))

    # read form (ชื่อฟิลด์ตามเพื่อน แต่แมพเข้าตารางตามของคุณ)
    email = (request.form.get("email") or "").strip()
    phone = (request.form.get("phoneNumber") or "").strip()
    recipient = (request.form.get("recipientName") or "").strip()
    addr = (request.form.get("address") or "").strip()
    city = (request.form.get("city") or "").strip()
    state = (request.form.get("state") or "").strip()
    postcode = (request.form.get("postcode") or "").strip()
    card = (request.form.get("cardNumber") or "").strip()
    exp = (request.form.get("expDate") or "").strip()
    cvv = (request.form.get("cvv") or "").strip()

    if not all([email, phone, recipient, addr, city, state, postcode, card, exp, cvv]):
        flash("Please complete all fields.", "warning")
        return render_template("checkout.html", cart=cart, total=total)

    try:
        # 1) payments
        payment_id = create_payment(card, exp, cvv)
        # 2) addresses
        address_id = create_address(recipient, addr, city, state, postcode)
        # 3) orders
        user_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
        order_id = create_order_row(user_id, email, phone, total, address_id, payment_id)
        # 4) order_items (คำนวณช่วงเช่าจาก months)
        start = date.today()
        for line in cart:
            months = int(line.get("months", 1))
            end = _add_months(start, months)
            add_order_item_row(
                order_id=order_id,
                artwork_id=int(line["id"]),
                image_url=line["imageUrl"],
                price_per_month=_parse_float(line["pricePerMonth"], 0.0),
                months=months,
                start_date=start,
                end_date=end,
                total_price=_parse_float(line["subtotal"], 0.0),
            )

        # success
        session.pop("cart", None)
        flash(f"Order #{order_id} placed successfully!", "success")
        return redirect(url_for("main.customer_center") if getattr(current_user, "is_authenticated", False) else url_for("main.home"))

    except Exception:
        flash("Checkout failed. Please try again.", "danger")
        return render_template("checkout.html", cart=cart, total=total)


# ========== upload & vendor ==========
@main.route("/upload", methods=["GET", "POST"])
@role_required("artist", "gallery", "admin")
def upload():
    # Ensure provider row for this user/role
    prov = ensure_provider_for_user(current_user.id, current_user.role, current_user.userName)

    if request.method == "POST":
        try:
            img = request.files.get("image")
            if not img or img.filename == "":
                flash("Please choose an image", "warning")
                return redirect(url_for("main.upload"))
            image_path = _save_image(img)  # returns 'uploads/<file>'

            # Simple parsing
            def _float(s, d=0.0):
                try:
                    return float(s)
                except Exception:
                    return d

            data = {
                "title": (request.form.get("title", "") or "").strip(),
                "artistName": (request.form.get("artistName", "") or (prov.get("artistName") or "")).strip(),
                "galleryName": (request.form.get("galleryName", "") or (prov.get("galleryName") or "")).strip(),
                "type": request.form.get("type"),
                "genre": request.form.get("genre"),
                "pricePerMonth": _float(request.form.get("pricePerMonth", "0"), 0.0),
                "size": request.form.get("size"),
                "year": request.form.get("year"),
                "leaseStatus": request.form.get("leaseStatus", "Available"),
                "imageUrl": image_path,  # static-relative (served via /static)
                "description": (request.form.get("description", "") or "")[:1000],
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


@main.get("/vendor/center")
@role_required("artist", "gallery", "admin")
def vendor_center():
    try:
        if current_user.role == "admin":
            # admin เห็นของทุกคน (และเลือกกรองตาม providerId ได้ผ่าน ?providerId=xxx)
            provider_id = request.args.get("providerId")
            filters = {}
            if provider_id:
                filters["providerId"] = provider_id
            artworks = list_artworks(filters) or []   # {} = ทั้งหมดที่ isDeleted=0
        else:
            # ศิลปิน/แกลเลอรี เห็นเฉพาะของตัวเอง
            from .models import list_my_artworks  # ฟังก์ชันที่ join providers -> artworks
            artworks = list_my_artworks(current_user.id) or []
    except Exception:
        current_app.logger.exception("Load artworks failed")
        flash("Failed to load artworks.", "danger")
        artworks = []

    return render_template("user_center_vendor.html", artworks=artworks)



@main.route("/item/<int:artwork_id>/edit", methods=["GET", "POST"])
@role_required("artist", "gallery", "admin")
def item_edit(artwork_id: int):
    art = get_artwork(artwork_id)
    if not art:
        abort(404)

    # Optional: ownership check
    try:
        prov = ensure_provider_for_user(current_user.id, current_user.role, current_user.userName)
        if art.get("providerId") and art["providerId"] != prov["providerId"] and current_user.role != "admin":
            return abort(403)
    except Exception:
        pass

    if request.method == "POST":
        if not callable(update_artwork):
            flash("Update not implemented yet.", "warning")
            return redirect(url_for("main.item_edit", artwork_id=artwork_id))

        title        = (request.form.get("title") or "").strip()
        artistName   = (request.form.get("artistName") or "").strip()
        galleryName  = (request.form.get("galleryName") or "").strip()
        type_        = request.form.get("type")
        genre        = request.form.get("genre")
        year         = request.form.get("year")
        size         = request.form.get("size")
        leaseStatus  = request.form.get("leaseStatus", "Available")
        try:
            price = float(request.form.get("pricePerMonth") or "0")
        except Exception:
            price = 0.0
        desc         = (request.form.get("description") or "")[:1000]

        if not title or price <= 0:
            flash("Please complete required fields", "warning")
            return redirect(url_for("main.item_edit", artwork_id=artwork_id))

        # Optional new image
        img = request.files.get("image")
        new_image_url = None
        if img and img.filename:
            try:
                new_image_url = _save_image(img)
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("main.item_edit", artwork_id=artwork_id))

        payload = {
            "title": title,
            "artistName": artistName,
            "galleryName": galleryName,
            "type": type_,
            "genre": genre,
            "year": year,
            "size": size,
            "leaseStatus": leaseStatus,
            "pricePerMonth": price,
            "description": desc,
        }
        if new_image_url:
            payload["imageUrl"] = new_image_url

        try:
            update_artwork(artwork_id, payload)
            flash("Artwork updated", "success")
            return redirect(url_for("main.vendor_center"))
        except Exception:
            flash("Update failed", "danger")

    return render_template("item_edit.html", artwork=art)


@main.post("/item/<int:artwork_id>/delete")
@role_required("artist", "gallery", "admin")
def item_delete(artwork_id: int):
    if not callable(delete_artwork):
        flash("Delete not implemented yet.", "warning")
        return redirect(url_for("main.vendor_center"))

    art = get_artwork(artwork_id)
    if not art:
        flash("Artwork not found", "warning")
        return redirect(url_for("main.vendor_center"))

    # Optional: ownership check
    try:
        prov = ensure_provider_for_user(current_user.id, current_user.role, current_user.userName)
        if art.get("providerId") and art["providerId"] != prov["providerId"] and current_user.role != "admin":
            return abort(403)
    except Exception:
        pass

    try:
        delete_artwork(artwork_id)
        flash("Artwork deleted", "info")
    except Exception:
        flash("Delete failed", "danger")
    return redirect(url_for("main.vendor_center"))


# Compatibility route for legacy '/uploads/<file>'
@main.get("/uploads/<path:filename>")
def uploads_compat(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


# ========== centers (admin / customer) ==========
@main.get("/admin/center")
@role_required("admin")
def admin_center():
    orders = admin_list_orders() if callable(admin_list_orders) else []
    artworks = admin_list_artworks() if callable(admin_list_artworks) else []
    providers = admin_list_providers() if callable(admin_list_providers) else []
    return render_template("user_center_admin.html",
                           orders=orders, artworks=artworks, providers=providers)


@main.get("/customer/center")
@role_required("customer")
def customer_center():
    if callable(list_orders_for_user):
        orders = list_orders_for_user(current_user.id)
    else:
        orders = []
    return render_template("user_center_customer.html", orders=orders)
