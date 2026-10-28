from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models.user import db, User
from models.post import Post
from models.comment import Comment
from models.withdraw import WithdrawalRequest

from utils.admin import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_posts = Post.query.count()
    pending_withdrawals = WithdrawalRequest.query.filter_by(status="Pending").count()
    
    return render_template("admin/dashboard.html", total_users=total_users, total_posts=total_posts, pending_withdrawals=pending_withdrawals)

@admin_bp.route("/withdrawals")
@login_required
@admin_required
def manage_withdrawals():
    requests = WithdrawalRequest.query.order_by(WithdrawalRequest.created_at.desc()).all()
    
    return render_template("admin/withdrawals.html", requests=requests)

@admin_bp.route("/withdrawals/action/<int:req_id>/<action>", methods=["POST"])
@login_required
@admin_required
def withdrawal_action(req_id, action):
    req_item = WithdrawalRequest.query.get_or_404(req_id)
    
    if action == "approve":
        req_item.status = "Approved"
        
        flash(f"Penarikan #{req_id} disetujui.", "success")
    elif action == "reject":
        req_item.status = "Rejected"
        req_item.user.brainpoints += req_item.points_deducted
        
        flash(f"Penarikan #{req_id} ditolak dan poin dikembalikan.", "info")
        
    db.session.commit()
    
    return redirect(url_for("admin.manage_withdrawals"))

@admin_bp.route("/users")
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    
    return render_template("admin/users.html", users=users)

@admin_bp.route("/users/toggle-admin/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash("Anda tidak dapat mengubah status admin diri sendiri.", "error")
        
        return redirect(url_for("admin.manage_users"))
        
    user.is_admin = not user.is_admin
    
    db.session.commit()
    
    flash(f"Status admin untuk @{user.username} berhasil diubah.", "success")
    
    return redirect(url_for("admin.manage_users"))

@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash("Tidak dapat menghapus akun sendiri.", "error")
        
        return redirect(url_for("admin.manage_users"))
        
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User @{user.username} berhasil dihapus.", "success")
    
    return redirect(url_for("admin.manage_users"))

@admin_bp.route("/posts/delete/<int:post_id>", methods=["POST"])
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    db.session.delete(post)
    db.session.commit()
    
    flash("Postingan yang melanggar berhasil dihapus.", "success")
    
    return redirect(request.referrer or url_for("main.home"))

@admin_bp.route("/comments/delete/<int:comment_id>", methods=["POST"])
@login_required
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash("Komentar berhasil dihapus.", "success")
    
    return redirect(request.referrer or url_for("main.home"))