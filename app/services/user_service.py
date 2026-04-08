from app.db.models import UserStats
import pandas as pd

FEATURE_COLUMNS = ["accuracy", "avg_time", "attempts", "streak"]


def get_user_features(user_id):
    user = UserStats.query.filter_by(user_id=user_id).first()

    if not user:
        return pd.DataFrame([[0.0, 0.0, 0.0, 0.0]], columns=FEATURE_COLUMNS)

    return pd.DataFrame(
        [
            [
                float(user.accuracy or 0.0),
                float(user.avg_time or 0.0),
                float(user.attempts or 0.0),
                float(user.streak or 0.0),
            ]
        ],
        columns=FEATURE_COLUMNS,
    )
