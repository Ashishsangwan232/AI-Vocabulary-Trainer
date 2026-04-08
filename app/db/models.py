from app.db.database import db

class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True)

    accuracy = db.Column(db.Float, default=0)
    avg_time = db.Column(db.Float, default=0)
    attempts = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
