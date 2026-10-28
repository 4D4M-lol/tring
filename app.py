import click
import os

from dotenv import load_dotenv

from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from extensions import db, login_manager

from models.user import User 
from models.post import PostMedia, Post, PostVote, Category
from models.comment import Comment, CommentVote

from routes.main import main_bp
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.posts import posts_bp
from routes.withdrawal import withdrawal_bp

CATEGORIES_DATA = [
    {"name": "General Discussion", "slug": "general", "icon": "message-circle"},
    {"name": "Digital & Visual Art", "slug": "art-design", "icon": "palette"},
    {"name": "Music & Sound Design", "slug": "music-sound", "icon": "music"},
    {"name": "Programming & Tech", "slug": "programming-tech", "icon": "code-2"},
    {"name": "Game Dev & Design", "slug": "game-dev", "icon": "gamepad-2"},
    {"name": "Hardware & Electronics", "slug": "hardware", "icon": "cpu"},
    {"name": "Science & Education", "slug": "science-edu", "icon": "atom"},
    {"name": "Writing & Lore", "slug": "writing-lore", "icon": "book-open"},
    {"name": "Showcase & Feedback", "slug": "showcase", "icon": "sparkles"},
    {"name": "Q&A & Help", "slug": "help", "icon": "help-circle"},
]

load_dotenv()

app: Flask = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

login_manager.init_app(app)

login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.init_app(app)

app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(withdrawal_bp)

def init_categories():
    for item in CATEGORIES_DATA:
        category = Category.query.filter_by(slug=item["slug"]).first()
        
        if not category:
            db.session.add(Category(name=item["name"], slug=item["slug"], icon=item["icon"]))
        else:
            category.icon = item["icon"]
            
    db.session.commit()

with app.app_context():
    db.create_all()
    
    init_categories()
    
@app.cli.command("addbp")
@click.argument("username")
@click.argument("amount")
def add_brainpoint_command(username, amount):
    user = User.query.filter_by(username=username).first()
    
    if user:
        user.brainpoints += int(amount)
        
        db.session.commit()
        click.echo(f"Berhasil menambahkan {amount}Bp ke @{username}!")
    else:
        click.echo(f"Error: User dengan username '@{username}' tidak ditemukan.")
    
@app.cli.command("mkadmin")
@click.argument("username")
def make_admin_command(username):
    user = User.query.filter_by(username=username).first()
    
    if user:
        if user.is_admin:
            click.echo(f"User @{username} sudah menjadi admin sebelumnya.")
        else:
            user.is_admin = True
            db.session.commit()
            click.echo(f"Berhasil! User @{username} sekarang telah menjadi Admin.")
    else:
        click.echo(f"Error: User dengan username '@{username}' tidak ditemukan.")

@app.cli.command("resetdb")
def reset_db():
    db.drop_all()
    db.create_all()

    print("Database reset.")

if __name__ == "__main__":
    app.run(debug=True)