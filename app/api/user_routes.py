from flask import Blueprint, jsonify, request
from app.db.models import UserStats, UserHistory
from app.ml.inference import predict_user_level
from app.services.user_service import get_user_features

user_bp = Blueprint("user", __name__)


@user_bp.route("/progress", methods=["GET"])
def progress():
    user_id = request.args.get("user_id", "student_01").strip()

    if not user_id:
        return jsonify({"error": "user_id must be a non-empty string"}), 400

    # Fetch base user stats
    user = UserStats.query.filter_by(user_id=user_id).first()

    # 1. Base ML Prediction
    features = get_user_features(user_id)
    level = predict_user_level(features)

    # 2. Dynamic Calculation: Max Streak & Chart Data
    history = (
        UserHistory.query.filter_by(user_id=user_id)
        .order_by(UserHistory.timestamp.asc())
        .all()
    )

    max_streak = 0
    temp_streak = 0
    daily_stats = {}

    for item in history:
        # Calculate All-Time Best Streak
        if item.is_correct:
            temp_streak += 1
            max_streak = max(max_streak, temp_streak)
        else:
            temp_streak = 0

        # Aggregate data by date (YYYY-MM-DD) for graphs
        date_str = item.timestamp.strftime("%Y-%m-%d")
        if date_str not in daily_stats:
            daily_stats[date_str] = {"total": 0, "correct": 0}

        daily_stats[date_str]["total"] += 1
        if item.is_correct:
            daily_stats[date_str]["correct"] += 1

    # Format chart data for React Recharts
    chart_data = []
    for date_str, stats in daily_stats.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        chart_data.append(
            {
                "date": date_str[-5:],  # Show only MM-DD for clean graph labels
                "accuracy": round(acc, 1),
                "words": stats["total"],
            }
        )

    # Keep only the last 7 active days for the trend graph
    chart_data = chart_data[-7:]

    # --- ADD THIS RIGHT BEFORE THE RETURN IN progress() ---
    # Dynamic XP Calculation
    correct_total = int((user.attempts or 0) * (user.accuracy or 0)) if user else 0
    xp = (correct_total * 10) + (max_streak * 15)

    if xp < 100:
        title = "Novice"
    elif xp < 300:
        title = "Apprentice"
    elif xp < 600:
        title = "Adept"
    elif xp < 1000:
        title = "Scholar"
    else:
        title = "Lexicon Master"

    return jsonify(
        {
            "accuracy": float(user.accuracy or 0.0) if user else 0.0,
            "level": level,
            "completed": int(user.attempts or 0) if user else 0,
            "streak": int(user.streak or 0) if user else 0,
            "max_streak": max_streak,
            "chart_data": chart_data,
            "trend": "up" if user and (user.accuracy or 0) > 0.7 else "stable",
            "xp": xp, 
            "title": title, 
        }
    )


@user_bp.route("/history", methods=["GET"])
def get_history():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    # Fetch the 50 most recent words for the Dashboard table
    history = (
        UserHistory.query.filter_by(user_id=user_id)
        .order_by(UserHistory.timestamp.desc())
        .limit(50)
        .all()
    )

    results = []
    for item in history:
        results.append(
            {
                "word": item.word,
                "is_correct": item.is_correct,
                # Format timestamp cleanly for the React frontend
                "timestamp": item.timestamp.strftime("%b %d, %Y - %I:%M %p"),
            }
        )

    return jsonify(results), 200


@user_bp.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    users = UserStats.query.all()
    board = []
    
    for u in users:
        # Calculate max streak for this specific user
        history = UserHistory.query.filter_by(user_id=u.user_id).order_by(UserHistory.timestamp.asc()).all()
        max_str = 0
        tmp_str = 0
        for h in history:
            if h.is_correct:
                tmp_str += 1
                max_str = max(max_str, tmp_str)
            else:
                tmp_str = 0
                
        correct = int((u.attempts or 0) * (u.accuracy or 0))
        xp = (correct * 10) + (max_str * 15)
        
        board.append({
            "username": u.user_id,
            "xp": xp,
            "streak": u.streak or 0
        })
        
    # Sort by XP descending and return top 10
    board.sort(key=lambda x: x["xp"], reverse=True)
    return jsonify(board[:10]), 200