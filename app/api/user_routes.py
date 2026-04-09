from app.db.models import UserHistory 
from flask import Blueprint, jsonify, request
from app.db.models import UserStats

user_bp = Blueprint("user", __name__)


def _level_from_accuracy(accuracy: float, attempts: int) -> str:
    if attempts < 10:
        return "Beginner"
    if accuracy >= 0.85:
        return "Advanced"
    if accuracy >= 0.6:
        return "Intermediate"
    return "Beginner"


@user_bp.route("/progress", methods=["GET"])
def progress():
    user_id = request.args.get("user_id", "student_01").strip()

    if not user_id:
        return jsonify({"error": "user_id must be a non-empty string"}), 400

    user = UserStats.query.filter_by(user_id=user_id).first()

    if not user:
        return jsonify(
            {"accuracy": 0.0, "level": "Beginner", "completed": 0, "streak": 0}
        )

    accuracy = float(user.accuracy or 0.0) if user else 0.0
    trend = "up" if accuracy > 0.7 else "stable"
    
    return jsonify({
        "accuracy": accuracy,
        "level": _level_from_accuracy(accuracy, int(user.attempts or 0)) if user else "Beginner",
        "completed": int(user.attempts or 0),
        "streak": int(user.streak or 0),
        "trend": trend # New field for frontend visualization
    })


@user_bp.route("/history", methods=["GET"])
def get_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    history = UserHistory.query.filter_by(user_id=user_id).order_by(UserHistory.timestamp.desc()).limit(50).all()
    
    results = []
    for item in history:
        results.append({
            "word": item.word,
            "is_correct": item.is_correct,
            "timestamp": item.timestamp.strftime("%b %d, %Y - %I:%M %p")
        })
        
    return jsonify(results), 200