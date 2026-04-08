from pathlib import Path
import warnings

import joblib

from app.core.logger import logger

BASE_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = BASE_DIR / "models"

_user_model = None
_user_le = None
_model_load_attempted = False


def _load_user_model_assets():
    global _user_model, _user_le, _model_load_attempted

    if _model_load_attempted:
        return _user_model is not None and _user_le is not None

    _model_load_attempted = True

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _user_model = joblib.load(MODELS_DIR / "user_model.pkl")
            _user_le = joblib.load(MODELS_DIR / "user_label_encoder.pkl")
        return True
    except Exception:
        logger.warning(
            "Could not load model assets from %s. Falling back to rule-based leveling.",
            MODELS_DIR,
        )
        return False


def predict_user_level(features):
    if _load_user_model_assets():
        try:
            level_encoded = _user_model.predict(features)
            return str(_user_le.inverse_transform(level_encoded)[0]).lower()
        except Exception:
            logger.exception("Model prediction failed. Falling back to heuristics.")

    # Fallback: infer user level from basic metrics.
    row = features.iloc[0]
    accuracy = float(row.get("accuracy", 0.0))
    attempts = float(row.get("attempts", 0.0))
    streak = float(row.get("streak", 0.0))

    if accuracy >= 0.85 and attempts >= 30 and streak >= 5:
        return "advanced"
    if accuracy >= 0.6 and attempts >= 10:
        return "intermediate"
    return "beginner"
