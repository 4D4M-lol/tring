import re

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
from flask_login import login_required, login_user, logout_user, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db

from models.user import User

auth_bp = Blueprint("auth", __name__)

def is_valid_username(username):
    pattern = r"^[a-zA-Z0-9_-]{3,30}$"
    
    return bool(re.match(pattern, username))

def is_valid_password(password):
    if len(password) < 8:
        return False, "Password harus memiliki setidaknya 8 huru."
    if not re.search(r"[A-Z]", password):
        return False, "Password harus memiliki setidaknya 1 huruf kapital."
    if not re.search(r"[a-z]", password):
        return False, "Password harus memiliki setidaknya 1 huruf kecil."
    if not re.search(r"[0-9]", password):
        return False, "Password harus memiliki setidaknya 1 angka."
    
    return True, ""

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not is_valid_username(username):
        flash("Username hanya bisa memiliki huruf kapital dan kecil, angka, underscore (_) atau strip (-). Panjang username harus diantara 3 sampai 30", "error")
        
        return redirect(url_for("auth.signup"))

    pass_valid, pass_msg = is_valid_password(password)
    
    if not pass_valid:
        flash(pass_msg, "error")
        
        return redirect(url_for("auth.signup"))

    existing_user = User.query.filter_by(username=username).first()
    
    if existing_user:
        flash("Username sudah dipakai, coba lagi.", "error")
        
        return redirect(url_for("auth.signup"))

    password_hash = generate_password_hash(password)

    user = User(
        username=username,
        password_hash=password_hash
    )

    db.session.add(user)
    db.session.commit()

    flash("Akun berhasil dibuat, silahkan login.", "success")
    
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        flash("Username dan password harus diisi.", "error")
        
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        login_user(user, remember=True, force=True)

        session["user_id"] = user.id
        session["username"] = user.username
        session["profile_picture"] = user.profile_picture

        return redirect(url_for("main.home"))

    flash("Username atau password salah.", "error")
    
    return redirect(url_for("auth.login"))

@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    
    if current_user.is_authenticated:
        logout_user()

    response = make_response(redirect(url_for("auth.login")))
    
    response.set_cookie("session", "", expires=0)
    
    flash("Berhasil logout.", "success")
    
    return response