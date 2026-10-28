from datetime import datetime

from extensions import db

class WithdrawalRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    points_deducted = db.Column(db.Integer, nullable=False)
    amount_rupiah = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("withdrawals", lazy=True))