from pathlib import Path
import warnings

import joblib

from app.core.logger import logger

BASE_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = BASE_DIR / "models"

_word_model = None
_word_le = None


def load_word_model():
    global _word_model, _word_le

    if _word_model is not None:
        return True

    try:
        _word_model = joblib.load(MODELS_DIR / "word_model.pkl")
        _word_le = joblib.load(MODELS_DIR / "label_encoder.pkl")
        return True
    except Exception:
        logger.warning("Word model not loaded, fallback to random.")
        return False


# def predict_user_level(features):
#     if _load_user_model_assets():
#         try:
#             level_encoded = _user_model.predict(features)
#             return str(_user_le.inverse_transform(level_encoded)[0]).lower()
#         except Exception:
#             logger.exception("Model prediction failed. Falling back to heuristics.")

#     # Fallback: infer user level from basic metrics.
#     row = features.iloc[0]
#     accuracy = float(row.get("accuracy", 0.0))
#     attempts = float(row.get("attempts", 0.0))
#     streak = float(row.get("streak", 0.0))

#     if accuracy >= 0.85 and attempts >= 30 and streak >= 5:
#         return "advanced"
#     if accuracy >= 0.6 and attempts >= 10:
#         return "intermediate"
#     return "beginner"


def predict_word_difficulty(features_df):
    if load_word_model():
        try:
            pred = _word_model.predict(features_df)
            return _word_le.inverse_transform(pred)[0]
        except Exception:
            logger.exception("Word prediction failed")

    return None