from flask import Blueprint, request, jsonify

from app.core.logger import logger
from app.services.word_service import get_word_for_user
from app.services.evaluation_service import evaluate_user_answer  # Add this
from app.db.database import db  # Add this
from app.db.models import UserStats  # Add this

word_bp = Blueprint("word", __name__)

# @word_bp.route("/get_word",methods=["GET", "POST"])
@word_bp.route("/get_word",methods=["GET"])
def get_word():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id", "student_01")

    if not isinstance(user_id, str) or not user_id.strip():
        return jsonify({"error": "user_id must be a non-empty string"}), 400

    try:
        result = get_word_for_user(user_id.strip())
    except Exception:
        logger.exception("Unexpected error while generating word for user_id=%s", user_id)
        return jsonify({"error": "Internal server error"}), 500

    status_code = 200 if "error" not in result else 404
    return jsonify(result), status_code



@word_bp.route("/submit_answer", methods=["POST"])
def submit_answer():
    data = request.get_json() or {}
    user_id = data.get("user_id", "student_01")
    submitted_word = data.get("word")
    answer = data.get("answer")

    # 1. Ensure all required fields are present
    if not submitted_word or not answer:
        return jsonify({"error": "Missing word or answer"}), 400

    # 2. Call the evaluation service 
    # (Passing an empty string for meaning since the NLP/fallback can check exact word matches)
    result = evaluate_user_answer(submitted_word, "", answer)

    # 3. Update UserStats based on the result
    user = UserStats.query.filter_by(user_id=user_id).first()
    if not user:
        # Create user if they don't exist yet
        user = UserStats(user_id=user_id, accuracy=0.0, attempts=0, streak=0)
        db.session.add(user)
    
    # Calculate previous total correct answers to properly adjust the new accuracy
    previous_correct = (user.accuracy or 0.0) * (user.attempts or 0)
    
    user.attempts = (user.attempts or 0) + 1
    
    if result.get("is_correct"):
        user.streak = (user.streak or 0) + 1
        new_correct = previous_correct + 1
    else:
        user.streak = 0
        new_correct = previous_correct

    user.accuracy = new_correct / user.attempts
    
    db.session.commit()
    
    return jsonify({
        "feedback": result.get("feedback", "Answer recorded."),
        "is_correct": result.get("is_correct", False),
        "nextWordRecommended": result.get("is_correct", False)
    })