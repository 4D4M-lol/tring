import os

from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from flask_login import login_required, current_user

from werkzeug.utils import secure_filename

from extensions import db

from models.post import PostMedia, Post, PostVote, Category
from models.user import User
from models.comment import Comment, CommentVote

posts_bp = Blueprint("posts", __name__)

ALLOWED_IMAGES = { "png", "jpg", "jpeg", "webp", "gif" }
ALLOWED_VIDEOS = { "mp4", "webm", "mov" }
ALLOWED_AUDIO = { "mp3", "wav", "ogg" }
MAX_FILES_PER_POST = 4

MAX_DAILY_POINTS = 50
MAX_DAILY_REP = 20

def get_media_type(filename):
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    
    if ext in ALLOWED_IMAGES:
        return "image"
    elif ext in ALLOWED_VIDEOS:
        return "video"
    elif ext in ALLOWED_AUDIO:
        return "audio"
    
    return None

def reset_daily_limits_if_needed(user):
    today = datetime.utcnow().date()
    
    if user.last_activity_date != today:
        user.daily_points_earned = 0
        user.daily_reputation_earned = 0
        user.last_activity_date = today

def update_user_points(giver, receiver, base_points_delta, rep_delta=1):
    if giver.id == receiver.id:
        return
    
    receiver.check_and_reset_daily_limits()

    multiplier = 1.0 + (receiver.reputation / 1000.0)
    
    if base_points_delta > 0:
        if receiver.daily_points_earned >= MAX_DAILY_POINTS:
            final_points = 0
            rep_delta = 0
        else:
            final_points = int(base_points_delta * multiplier)
            
            if receiver.daily_points_earned + final_points > MAX_DAILY_POINTS:
                final_points = MAX_DAILY_POINTS - receiver.daily_points_earned
            
            receiver.daily_points_earned += final_points

        if rep_delta > 0 and receiver.daily_reputation_earned < MAX_DAILY_REP:
            receiver.reputation += rep_delta
            receiver.daily_reputation_earned += rep_delta
    else:
        final_points = base_points_delta
        
        receiver.reputation = max(0, receiver.reputation - 1)

    receiver.brainpoints = max(0, receiver.brainpoints + final_points)
    
    db.session.commit()

@posts_bp.route("/create-post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        files = request.files.getlist("media")
        title = request.form.get("title")
        content = request.form.get("content")
        category_id = request.form.get("category_id")

        new_post = Post(title=title, content=content, category_id=category_id, user_id=current_user.id)

        db.session.add(new_post)
        db.session.commit()

        upload_folder = os.path.join(current_app.root_path, "static", "uploads", "posts")
        
        os.makedirs(upload_folder, exist_ok=True)

        for file in files:
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                unique_filename = f"{new_post.id}_{filename}"
                file_path = os.path.join(upload_folder, unique_filename)
                
                file.save(file_path)
                
                media_type = get_media_type(filename.lower())

                new_media = PostMedia(
                    post_id=new_post.id,
                    file_path=unique_filename,
                    media_type=media_type
                )
                db.session.add(new_media)

        db.session.commit()
        
        return redirect(url_for("main.home"))

    categories = Category.query.all()
    
    return render_template("create_post.html", categories=categories)

@posts_bp.route("/post/<int:post_id>")
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    all_comments = Comment.query.filter_by(post_id=post.id).all()
    sorted_comments = sorted(
        all_comments,
        key=lambda c: (
            c.id == post.solved_comment_id,
            c.score,
            c.created_at
        ),
        reverse=True
    )
    
    user_post_votes = { }
    user_comment_votes = { }

    user_id = session.get("user_id")
    username = session.get("username")
    current_user = User.query.filter_by(username=username).first_or_404()

    if user_id:
        post_vote = PostVote.query.filter_by(user_id=user_id, post_id=post_id).first()
        
        if post_vote:
            user_post_votes[post_id] = post_vote.vote_type

        comment_votes = CommentVote.query.filter_by(user_id=user_id).all()
        user_comment_votes = {
            comment_vote.comment_id: comment_vote.vote_type for comment_vote in comment_votes
        }

    return render_template(
        "post_detail.html",
        current_user=current_user,
        post=post,
        comments=sorted_comments,
        user_post_votes=user_post_votes,
        user_comment_votes=user_comment_votes
    )

@posts_bp.route("/comment/<int:comment_id>/vote", methods=["POST"])
def vote_comment(comment_id):
    if "user_id" not in session:
        flash("You need to be logged in to vote.", "error")
        
        return redirect(url_for("auth.login"))

    comment = Comment.query.get_or_404(comment_id)
    user_id = session["user_id"]
    giver = User.query.get_or_404(user_id)
    receiver = comment.user

    vote_type = int(request.form.get("vote_type", 0))

    if vote_type not in [1, -1]:
        return redirect(url_for("posts.view_post", post_id=comment.post_id))

    existing_vote = CommentVote.query.filter_by(user_id=user_id, comment_id=comment_id).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            if existing_vote.vote_type == 1:
                update_user_points(giver, receiver, -5)
            elif existing_vote.vote_type == -1:
                update_user_points(giver, receiver, 5)
            db.session.delete(existing_vote)
        else:
            if existing_vote.vote_type == 1 and vote_type == -1:
                update_user_points(giver, receiver, -5)
            elif existing_vote.vote_type == -1 and vote_type == 1:
                update_user_points(giver, receiver, 5)
            existing_vote.vote_type = vote_type
    else:
        new_vote = CommentVote(user_id=user_id, comment_id=comment_id, vote_type=vote_type)
        db.session.add(new_vote)
        if vote_type == 1:
            update_user_points(giver, receiver, 5)
        elif vote_type == -1:
            update_user_points(giver, receiver, -5)

    db.session.commit()
    return redirect(url_for("posts.view_post", post_id=comment.post_id))

@posts_bp.route("/post/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    if "user_id" not in session:
        flash("You need to be logged in to comment.", "error")
        return redirect(url_for("auth.login"))

    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id")

    if not content:
        flash("Comment can not be empty.", "error")
        return redirect(url_for("posts.view_post", post_id=post_id))

    new_comment = Comment(
        content=content,
        post_id=post_id,
        user_id=session["user_id"],
        parent_id=int(parent_id) if parent_id else None
    )

    db.session.add(new_comment)
    db.session.commit()

    flash("Comment sent!", "success")
    return redirect(url_for("posts.view_post", post_id=post_id))

@posts_bp.route("/post/<int:post_id>/vote", methods=["POST"])
def vote(post_id):
    if "user_id" not in session:
        flash("You need to be logged in to vote", "error")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    giver = User.query.get_or_404(user_id)
    post = Post.query.get_or_404(post_id)
    receiver = post.user

    vote_type = int(request.form.get("vote_type", 0))
    
    if vote_type not in [1, -1]:
        return redirect(url_for("main.home"))

    existing_vote = PostVote.query.filter_by(user_id=user_id, post_id=post_id).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            if existing_vote.vote_type == 1:
                update_user_points(giver, receiver, -5)
            elif existing_vote.vote_type == -1:
                update_user_points(giver, receiver, 5)
                
            db.session.delete(existing_vote)
        else:
            if existing_vote.vote_type == 1 and vote_type == -1:
                update_user_points(giver, receiver, -5)
            elif existing_vote.vote_type == -1 and vote_type == 1:
                update_user_points(giver, receiver, 5)
                
            existing_vote.vote_type = vote_type
    else:
        new_vote = PostVote(user_id=user_id, post_id=post_id, vote_type=vote_type)
        db.session.add(new_vote)
        
        if vote_type == 1:
            update_user_points(giver, receiver, 5)
        elif vote_type == -1:
            update_user_points(giver, receiver, -5)

    db.session.commit()
    return redirect(request.referrer or url_for("main.home"))

@posts_bp.route("/post/<int:post_id>/mark-solution/<int:comment_id>", methods=["POST"])
@login_required
def mark_solution(post_id, comment_id):
    post = Post.query.get_or_404(post_id)
    comment = Comment.query.get_or_404(comment_id)
    post_owner = current_user

    if post.user_id != post_owner.id:
        flash("You need to have access in order to choose the solution for this problem.", "danger")
        
        return redirect(url_for("posts.view_post", post_id=post.id))

    if comment.post_id != post.id:
        flash("The chosen comment is not valid for this post.", "warning")
        
        return redirect(url_for("posts.view_post", post_id=post.id))

    solver = comment.user

    if post.solved_comment_id != comment.id:
        if post.solved_comment_id:
            old_comment = Comment.query.get(post.solved_comment_id)
            
            if old_comment and old_comment.user:
                update_user_points(post_owner, old_comment.user, -200, rep_delta=0)
                
                old_comment.user.reputation = max(0, old_comment.user.reputation - 25)

        post.is_solved = True
        post.solved_comment_id = comment.id
        
        update_user_points(post_owner, solver, 200, rep_delta=0)
        
        solver.reputation += 25

        flash("Successfully marked comment as the solution (+200 Brainpoints & +25 Reputation awarded)!", "success")
    else:
        flash("This comment is already marked as the solution.", "info")

    db.session.commit()
    
    return redirect(url_for("posts.view_post", post_id=post_id))