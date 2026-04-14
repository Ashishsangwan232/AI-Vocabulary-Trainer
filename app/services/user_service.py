import pandas as pd
from app.db.models import UserStats, UserHistory

# Updated to 6 features to match the new ML pipeline
FEATURE_COLUMNS = ["accuracy", "avg_time", "attempts", "streak", "recent_accuracy", "improvement_rate"]

def get_user_features(user_id):
    user = UserStats.query.filter_by(user_id=user_id).first()

    # If new user, give them neutral neutral/baseline stats
    if not user:
        return pd.DataFrame([[0.0, 0.0, 0.0, 0.0, 0.5, 0.0]], columns=FEATURE_COLUMNS)

    # 1. Fetch recent history for temporal tracking (Last 10 attempts)
    history = UserHistory.query.filter_by(user_id=user_id).order_by(UserHistory.timestamp.desc()).limit(10).all()

    overall_accuracy = float(user.accuracy or 0.0)

    # 2. Calculate Recent Accuracy (⚠️ FIX: Default to 0.5 or overall accuracy if no history)
    if history:
        correct_count = sum(1 for h in history if h.is_correct)
        recent_accuracy = correct_count / len(history)
    else:
        recent_accuracy = overall_accuracy if overall_accuracy > 0 else 0.5

    # 3. Calculate Improvement Rate
    improvement_rate = recent_accuracy - overall_accuracy

    return pd.DataFrame(
        [[
            overall_accuracy,
            float(user.avg_time or 0.0),
            float(user.attempts or 0.0),
            float(user.streak or 0.0),
            recent_accuracy,       
            improvement_rate       
        ]],
        columns=FEATURE_COLUMNS,
    )