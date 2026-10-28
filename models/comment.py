from datetime import datetime

from extensions import db

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

    user = db.relationship("User", backref=db.backref("comments", lazy=True))
    post = db.relationship("Post", backref=db.backref("comments", lazy=True, cascade="all, delete-orphan"), foreign_keys=[post_id])
    
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)
    
    replies = db.relationship("Comment", backref=db.backref("parent", remote_side=[id]), lazy=True, cascade="all, delete-orphan")

    votes = db.relationship("CommentVote", backref="post", lazy=True, cascade="all, delete-orphan")

    @property
    def likes_count(self):
        return CommentVote.query.filter_by(comment_id=self.id, vote_type=1).count()

    @property
    def dislikes_count(self):
        return CommentVote.query.filter_by(comment_id=self.id, vote_type=-1).count()
    
    @property
    def score(self):
        return self.likes_count - self.dislikes_count

class CommentVote(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "comment_id", name="unique_user_comment_vote"),
    )

    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=False)
    
    vote_type = db.Column(db.Integer, nullable=False)