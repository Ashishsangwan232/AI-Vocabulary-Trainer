from app.db.database import db
import json
from datetime import datetime # <-- Add this import

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False) # Plain text for local dev

class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False) # Matches User.username
    word = db.Column(db.String, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True)
    accuracy = db.Column(db.Float, default=0)
    avg_time = db.Column(db.Float, default=0)
    attempts = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)

class NLPWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String, unique=True)
    difficulty = db.Column(db.String)
    meaning = db.Column(db.Text)
    example = db.Column(db.Text)
    mcq_question = db.Column(db.Text)
    mcq_options = db.Column(db.Text)
    mcq_correct = db.Column(db.String)

class TriviaFact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fact_text = db.Column(db.Text, unique=True)