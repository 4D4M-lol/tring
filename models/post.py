from datetime import datetime

from extensions import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(50), nullable=True, default="hash")
    
    posts = db.relationship("Post", backref="category", lazy=True)

class PostMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    
    file_path = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    
    user = db.relationship("User", backref=db.backref("posts", lazy=True))
    
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_solved = db.Column(db.Boolean, default=False)
    
    solved_comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)

    solved_comment = db.relationship("Comment", foreign_keys=[solved_comment_id])

    media = db.relationship("PostMedia", backref="post", cascade="all, delete-orphan")
    
    votes = db.relationship("PostVote", backref="post", lazy=True, cascade="all, delete-orphan")

    @property
    def likes_count(self):
        return PostVote.query.filter_by(post_id=self.id, vote_type=1).count()

    @property
    def dislikes_count(self):
        return PostVote.query.filter_by(post_id=self.id, vote_type=-1).count()
    
    @property
    def score(self):
        return self.likes_count - self.dislikes_count

class PostVote(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "post_id", name="unique_user_post_vote"),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    
    vote_type = db.Column(db.Integer, nullable=False)