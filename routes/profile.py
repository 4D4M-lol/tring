import os

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for,
    flash,
    current_app
)
from flask_login import login_required, current_user

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db

from models.user import User
from models.post import PostVote

from utils.cooldown import check_cooldown, COOLDOWN_DAYS

profile_bp = Blueprint("profile", __name__)

ALLOWED_IMAGE_EXTENSIONS = { "png", "jpg", "jpeg", "webp" }

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@profile_bp.route("/profile/<username>")
def view_profile(username):
    target_user = User.query.filter_by(username=username).first_or_404()
    is_own_profile = False
    
    if current_user.is_authenticated:
        is_own_profile = (int(current_user.id) == int(target_user.id))

    user_votes = { }
    
    if "user_id" in session:
        votes = PostVote.query.filter_by(user_id=session["user_id"]).all()
        user_votes = { vote.post_id: vote.vote_type for vote in votes }
    
    return render_template(
        "profile.html", 
        user=target_user, 
        is_own_profile=is_own_profile,
        user_votes=user_votes,
        current_user=current_user
    )

@profile_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        now = datetime.utcnow()

        if action == "update_bio":
            new_bio = request.form.get("bio", "").strip()
            
            current_user.bio = new_bio
            
            db.session.commit()
            
            flash("Bio berhasil diubah!", "success")
        elif action == "update_username":
            can_change, days_left = \
                check_cooldown(current_user.last_username_change, "username")
            
            if not can_change:
                flash(f"Kamu bisa mengganti username lagi dalam {days_left} hari.", "danger")
            else:
                new_username = request.form.get("username").strip()
                existing_user = User.query.filter_by(username=new_username).first()
                
                if existing_user and existing_user.id != current_user.id:
                    flash("Username sudah diambil.", "danger")
                else:
                    current_user.username = new_username
                    current_user.last_username_change = now
                    
                    db.session.commit()
                    
                    flash("Username berhasil dirubah!", "success")
        elif action == "update_password":
            can_change, days_left = \
                check_cooldown(current_user.last_password_change, "password")
                
            if not can_change:
                flash(f"Kamu bisa mengganti username lagi dalam {days_left} hari.", "danger")
            else:
                old_pass = request.form.get("old_password")
                new_pass = request.form.get("new_password")
                
                if not check_password_hash(current_user.password_hash, old_pass):
                    flash("Password salah.", "danger")
                else:
                    current_user.password_hash = generate_password_hash(new_pass)
                    current_user.last_password_change = now
                    
                    db.session.commit()
                    
                    flash("Password berhasil dirubah!", "success")
        elif action == "update_pfp":
            file = request.files.get("pfp_file")
            
            if file and file.filename != "":
                filename = secure_filename(f"avatar_{current_user.id}_{int(now.timestamp())}.jpg")
                upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "avatars", filename)
                
                file.save(upload_path)
                
                current_user.profile_picture = filename
                current_user.last_pfp_change = now
                
                db.session.commit()
                
                flash("Foto profil berhasil dirubah!", "success")
        elif action == "update_banner":
            file = request.files.get("banner_file")
            
            if file and file.filename != "":
                filename = secure_filename(f"banner_{current_user.id}_{int(now.timestamp())}.jpg")
                upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "banners", filename)
                
                file.save(upload_path)
                
                current_user.banner_picture = filename
                current_user.last_banner_change = now
                
                db.session.commit()
                
                flash("Banner berhasil dirubah!", "success")

        return redirect(url_for("profile.settings"))

    cooldowns = {
        "username": check_cooldown(current_user.last_username_change, "username"),
        "password": check_cooldown(current_user.last_password_change, "password")
    }

    return render_template("settings.html", cooldowns=cooldowns, rules=COOLDOWN_DAYS)