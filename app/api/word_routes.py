import json
import threading
from flask import Blueprint, request, jsonify
from app.db.models import UserHistory 

from app.core.logger import logger
from app.services.nlp_api import generate_trivia_fact
from app.services.word_service import get_word_for_user
from app.services.evaluation_service import evaluate_user_answer, generate_word_data
from app.db.database import db
from app.db.models import UserStats, NLPWord, TriviaFact

word_bp = Blueprint("word", __name__)


@word_bp.route("/get_word", methods=["GET"])
def get_word():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id", "student_01")

    if not isinstance(user_id, str) or not user_id.strip():
        return jsonify({"error": "user_id must be a non-empty string"}), 400

    try:
        result = get_word_for_user(user_id.strip())
    except Exception:
        logger.exception(
            "Unexpected error while generating word for user_id=%s", user_id
        )
        return jsonify({"error": "Internal server error"}), 500

    status_code = 200 if "error" not in result else 404
    return jsonify(result), status_code


@word_bp.route("/submit_answer", methods=["POST"])
def submit_answer():
    data = request.get_json() or {}
    user_id = data.get("user_id", "student_01")
    submitted_word = data.get("word")
    answer = data.get("answer")

    if not submitted_word or not answer:
        return jsonify({"error": "Missing word or answer"}), 400

    result = evaluate_user_answer(submitted_word, "", answer)

    user = UserStats.query.filter_by(user_id=user_id).first()
    if not user:
        user = UserStats(user_id=user_id, accuracy=0.0, attempts=0, streak=0)
        db.session.add(user)

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

    return jsonify(
        {
            "feedback": result.get("feedback", "Answer recorded."),
            "is_correct": result.get("is_correct", False),
            "nextWordRecommended": result.get("is_correct", False),
        }
    )


@word_bp.route("/submit_mcq", methods=["POST"])
def submit_mcq():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    word = data.get("word")  # Get the word from the frontend
    is_correct = data.get("is_correct", False)

    if not user_id:
        return jsonify({"error": "No user logged in"}), 401

    # 1. Update overall UserStats (existing code)
    user = UserStats.query.filter_by(user_id=user_id).first()
    if not user:
        user = UserStats(user_id=user_id, accuracy=0.0, attempts=0, streak=0)
        db.session.add(user)

    previous_correct = (user.accuracy or 0.0) * (user.attempts or 0)
    user.attempts = (user.attempts or 0) + 1

    if is_correct:
        user.streak = (user.streak or 0) + 1
        new_correct = previous_correct + 1
    else:
        user.streak = 0
        new_correct = previous_correct

    user.accuracy = new_correct / user.attempts

    # 2. SAVE TO USER HISTORY (New code)
    if word:
        history_entry = UserHistory(user_id=user_id, word=word, is_correct=is_correct)
        db.session.add(history_entry)

    db.session.commit()

    return jsonify({"message": "MCQ stats updated", "is_correct": is_correct})


def background_fact_generator(app_context):
    with app_context:
        new_fact = generate_trivia_fact()
        try:
            if not TriviaFact.query.filter_by(fact_text=new_fact).first():
                db.session.add(TriviaFact(fact_text=new_fact))
                db.session.commit()
        except Exception:
            db.session.rollback()


@word_bp.route("/fact", methods=["GET"])
def get_fact():
    from flask import current_app

    fact_record = TriviaFact.query.order_by(db.func.random()).first()
    fact_text = (
        fact_record.fact_text
        if fact_record
        else "Did you know? The longest word in English without a true vowel is 'rhythm'."
    )

    app_context = current_app.app_context()
    thread = threading.Thread(target=background_fact_generator, args=(app_context,))
    thread.start()

    return jsonify({"fact": fact_text})


@word_bp.route("/lookup", methods=["POST"])
def lookup_word():
    data = request.get_json() or {}
    word_to_find = data.get("word", "").strip().lower()

    if not word_to_find:
        return jsonify({"error": "No word provided"}), 400

    existing = NLPWord.query.filter_by(word=word_to_find).first()
    if existing:
        return jsonify(
            {
                "word": existing.word,
                "difficulty": existing.difficulty,
                "meaning": existing.meaning,
                "example": existing.example,
                "mcq": {
                    "question": existing.mcq_question,
                    "options": (
                        json.loads(existing.mcq_options) if existing.mcq_options else []
                    ),
                    "correct_option": existing.mcq_correct,
                },
            }
        )

    try:
        word_data = generate_word_data("medium", "intermediate", word_to_find)

        if word_data and "meaning" in word_data:
            mcq_data = word_data.get("mcq", {})
            new_entry = NLPWord(
                word=word_to_find,
                difficulty="medium",
                meaning=word_data.get("meaning"),
                example=word_data.get("example"),
                mcq_question=mcq_data.get("question"),
                mcq_options=json.dumps(mcq_data.get("options", [])),
                mcq_correct=mcq_data.get("correct_option"),
            )

            try:
                db.session.add(new_entry)
                db.session.commit()
            except Exception as db_err:
                db.session.rollback()
                logger.warning(
                    f"Skipped saving '{word_to_find}' (likely already exists)."
                )

            return jsonify(word_data)
        else:
            return jsonify({"error": "Could not find a definition for that word."}), 404

    except Exception as e:
        logger.error(f"Lookup failed: {e}")
        return jsonify({"error": "AI lookup failed."}), 500
