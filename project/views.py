from __future__ import annotations
from decimal import Decimal
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, session, flash, abort
)
from functools import wraps

main = Blueprint("main", __name__)

ITEMS = [
    {
        "id": 1,
        "title": "Sunset Abstraction",
        "artistName": "A. Morgan",
        "galleryName": "Studio Alpha",
        "type": "Oil Painting",
        "genre": "Illustrative",
        "size": "50.8 × 40.6 cm",
        "year": 2025,
        "availability": "Available",
        "pricePerMonth": 59.0,
        "imageUrl": "img/P1.png",
        "description": "Warm abstract planes framing a low sun.",
    },
    {
        "id": 2,
        "title": "Playful Lines",
        "artistName": "R. Dune",
        "galleryName": "Blue Dot",
        "type": "Digital Painting",
        "genre": "Surrealism",
        "size": "60 × 42 cm",
        "year": 2025,
        "availability": "Available",
        "pricePerMonth": 39.0,
        "imageUrl": "img/P2.png",
        "description": "Loose, looping lines on a pastel field.",
    },
    {
        "id": 3,
        "title": "Golden Orbit",
        "artistName": "N. Lark",
        "galleryName": "Orbit House",
        "type": "Acrylic Painting",
        "genre": "Graffiti",
        "size": "80 × 60 cm",
        "year": 2024,
        "availability": "Unavailable",
        "pricePerMonth": 79.0,
        "imageUrl": "img/magier-wXqd2vZTdJQ-unsplash.jpg",
        "description": "Bold arcs intersecting a dark disk.",
    },
    {
        "id": 4,
        "title": "Forms in Yellow",
        "artistName": "E. Field",
        "galleryName": "Studio Alpha",
        "type": "Oil Painting",
        "genre": "Folk Art",
        "size": "60 × 60 cm",
        "year": 2025,
        "availability": "Available",
        "pricePerMonth": 65.0,
        "imageUrl": "img/premium_vector-1689096860545-a5e876cad8fd.avif",
        "description": "Organic forms floating on gold ground.",
    },
    {
        "id": 5,
        "title": "Bench with Cat",
        "artistName": "K. Mori",
        "galleryName": "Blue Dot",
        "type": "Pastel Painting",
        "genre": "Illustrative",
        "size": "60 × 42 cm",
        "year": 2025,
        "availability": "Available",
        "pricePerMonth": 29.0,
        "imageUrl": "img/C1.jpg",
        "description": "Cozy scene: figure pats a curious cat.",
    },
    {
        "id": 6,
        "title": "Aurora Flow",
        "artistName": "P. Czerwinski",
        "galleryName": "Orbit House",
        "type": "Acrylic Painting",
        "genre": "Surrealism",
        "size": "60 × 42 cm",
        "year": 2025,
        "availability": "Available",
        "pricePerMonth": 35.0,
        "imageUrl": "img/pawel-czerwinski-ruJm3dBXCqw-unsplash.jpg",
        "description": "Cool and warm streams like aurora.",
    },
]

def _get_cart() -> list[dict]:
    cart = session.get("cart")
    if not isinstance(cart, list):
        cart = []
        session["cart"] = cart
    return cart

def _recalc_totals(cart: list[dict]) -> Decimal:
    total = Decimal("0")
    for line in cart:
        price = Decimal(str(line.get("pricePerMonth", 0)))
        months = int(line.get("months", 1) or 1)
        line["subtotal"] = float(price * months)
        total += price * months
    session["cart_total"] = float(total)
    return total

def role_required(*roles):
    """
    บังคับว่า user ต้องล็อกอินและมี role ใด role หนึ่งใน roles
    ถ้ายังไม่ล็อกอิน -> redirect ไป login พร้อม next
    ถ้า role ไม่ตรง -> 403
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            role = session.get("user_role")
            if role is None:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("auth.login", next=request.path))
            if role not in roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapper
    return decorator

@main.route("/")
def home():
    return render_template("home.html") if _has("home.html") else render_template("base.html")


def _has(name: str) -> bool:
    # util เล็ก ๆ ให้เรา render base.html ได้หากไม่มี home.html
    # ในโปรเจคจริงคุณน่าจะมี home.html อยู่แล้ว
    import os
    from flask import current_app
    tpl = os.path.join(current_app.root_path, "templates", name)
    return os.path.exists(tpl)

@main.route("/gallery")
def gallery():
    return render_template("gallery.html", items=ITEMS)

@main.route("/item/<int:item_id>")
def item_detail(item_id: int):
    item = next((i for i in ITEMS if i["id"] == item_id), None)
    if not item:
        abort(404)
    ctx = {"item": item, "it": item, **item}
    return render_template("item_detail.html", **ctx)

# IMPORTANT: no <item_id> in the path anymore
@main.route("/cart/add", methods=["POST"])
def cart_add():
    try:
        item_id = int(request.form.get("item_id", "0"))
    except ValueError:
        item_id = 0

    item = next((i for i in ITEMS if i["id"] == item_id), None)
    if not item:
        abort(404)

    months_raw = request.form.get("months", "1")
    try:
        months = max(1, int(months_raw))
    except ValueError:
        months = 1

    cart = _get_cart()
    existing = next((c for c in cart if c["id"] == item_id), None)
    if existing:
        existing["months"] = months
    else:
        cart.append({
            "id": item["id"],
            "title": item["title"],
            "pricePerMonth": item["pricePerMonth"],
            "imageUrl": item["imageUrl"],
            "months": months,
        })

    _recalc_totals(cart)
    flash("Item added to cart.", "success")
    return redirect(url_for("main.checkout"))

@main.route("/checkout")
def checkout():
    cart = _get_cart()
    _recalc_totals(cart)
    total = session.get("cart_total", 0.0)
    return render_template("checkout.html", cart=cart, total=total)

# -----------------------------
# User Centers (สามหน้า)
# -----------------------------
@main.route("/customer/center")
@role_required("customer", "admin")
def customer_center():
    return render_template("user_center_customer.html")

@main.route("/vendor/center")
@role_required("vendor", "admin")
def vendor_center():
    return render_template("user_center_vendor.html")

@main.route("/admin/center")
@role_required("admin")
def admin_center():
    return render_template("user_center_admin.html")


# -----------------------------
# Dev helper: สลับ role ง่าย ๆ (อย่าใช้ใน production)
# -----------------------------
@main.route("/__as/<role>")
def as_role(role):
    if role not in ("admin", "vendor", "customer"):
        abort(400)
    session.clear()
    session["user_id"] = 999
    session["user_email"] = f"{role}@dev.local"
    session["user_role"] = role
    return f"Now acting as {role}. Try /{role}/center"



