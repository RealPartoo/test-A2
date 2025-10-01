import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from .extensions import db
from .forms import ArtworkForm
from .models import Artwork

bp = Blueprint("vendor", __name__, template_folder="templates")

def role_required(*roles):
    def decorator(fn):
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash("You do not have permission.", "warning")
                return redirect(url_for("auth.login"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@bp.route("/manage", methods=["GET","POST"])
@login_required
@role_required("artist", "admin")
def manage():
    form = ArtworkForm()
    if form.validate_on_submit():
        # save file (optional)
        img_rel = None
        file = request.files.get("image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            new_name = f"{uuid4().hex}{ext}"
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], new_name)
            file.save(save_path)
            img_rel = f"uploads/{new_name}"  # ไว้ใช้กับ url_for('static', filename=img_rel)

        art = Artwork(
            title=form.title.data,
            artist_id=current_user.id,
            gallery_name=form.gallery_name.data or None,
            art_type=form.art_type.data or None,
            genre=form.genre.data or None,
            size=form.size.data or None,
            year=form.year.data or None,
            price_per_month=form.price_per_month.data,
            description=form.description.data or None,
            availability="Available",
            image_path=img_rel,  # อาจเป็น None ถ้าไม่ได้อัปไฟล์
        )
        db.session.add(art); db.session.commit()
        flash("Artwork uploaded.", "success")
        return redirect(url_for("vendor.manage"))

    # รายการของศิลปินเอง (หรือทั้งหมดถ้าเป็นแอดมิน)
    if current_user.role == "admin":
        my_items = Artwork.query.order_by(Artwork.id.desc()).all()
    else:
        my_items = Artwork.query.filter_by(artist_id=current_user.id).order_by(Artwork.id.desc()).all()

    return render_template("vendor_manage.html", form=form, my_items=my_items)
