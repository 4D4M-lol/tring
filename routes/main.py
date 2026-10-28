from flask import Blueprint, render_template, redirect, url_for, session, request

from sqlalchemy.orm import joinedload

from extensions import db

from models.user import User
from models.post import Post, PostVote, Category

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    category_slug = request.args.get("category")
    categories = Category.query.all()
    current_category = None

    query = Post.query

    if category_slug:
        current_category = Category.query.filter_by(slug=category_slug).first()
        
        if current_category:
            query = query.filter_by(category_id=current_category.id)

    all_posts = query.options(
        joinedload(Post.user) if hasattr(Post, "user") else joinedload("author")
    ).all()
    
    posts = sorted(
        all_posts,
        key=lambda p: (
            not p.is_solved,
            p.likes_count,
            p.created_at
        ),
        reverse=True
    )

    user_votes = { }
    
    if "user_id" in session:
        votes = PostVote.query.filter_by(user_id=session["user_id"]).all()
        user_votes = { vote.post_id: vote.vote_type for vote in votes }

    return render_template(
        "home.html",
        posts=posts,
        categories=categories,
        current_category=current_category,
        user_votes=user_votes
    )

@main_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    posts = []
    users = []
    
    if query:
        raw_posts = Post.query.options(
            joinedload(Post.user) if hasattr(Post, "user") else joinedload("author")
        ).filter(
            (Post.title.ilike(f"%{query}%")) | 
            (Post.content.ilike(f"%{query}%"))
        ).all()
        
        posts = sorted(
            raw_posts,
            key=lambda p: (
                p.is_solved,
                p.likes_count,
                p.created_at
            ),
            reverse=True
        )

        users = User.query.filter(
            User.username.ilike(f"%{query}%")
        ).all()

    user_votes = { }
    
    if "user_id" in session:
        votes = PostVote.query.filter_by(user_id=session["user_id"]).all()
        user_votes = { vote.post_id: vote.vote_type for vote in votes }

    return render_template(
        "search.html", 
        query=query, 
        posts=posts, 
        users=users,
        user_votes=user_votes
    )