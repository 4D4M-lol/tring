from datetime import datetime

from flask_login import UserMixin

from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    profile_picture = db.Column(db.String(255), nullable=False, default="default.jpg")
    banner_pic = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_admin = db.Column(db.Boolean, default=False)
    
    reputation = db.Column(db.Integer, default=0, nullable=False)
    brainpoints = db.Column(db.Integer, default=0, nullable=False)
    
    daily_points_earned = db.Column(db.Integer, default=0, nullable=False)
    daily_reputation_earned = db.Column(db.Integer, default=0, nullable=False)
    
    last_activity_date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    
    last_username_change = db.Column(db.DateTime, nullable=True)
    last_password_change = db.Column(db.DateTime, nullable=True)
    
    def check_and_reset_daily_limits(self):
        today = datetime.utcnow().date()
        
        if self.last_activity_date != today:
            self.daily_points_earned = 0
            self.daily_reputation_earned = 0
            self.last_activity_date = today