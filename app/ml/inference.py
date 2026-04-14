from pathlib import Path
import joblib
from app.core.logger import logger

BASE_DIR = Path(__file__).resolve().parents[2]

_word_model = None
_word_le = None
_user_model = None
_user_le = None


def load_word_model():
    global _word_model, _word_le

    if _word_model is not None:
        return True

    try:
        _word_model = joblib.load("models/word_model.pkl")
        _word_le = joblib.load("models/label_encoder.pkl")
        logger.info("Word model loaded successfully")
        return True
    except Exception as e:
        logger.warning(f"Word model not loaded: {e}")
        return False


def load_user_model():
    global _user_model, _user_le

    if _user_model is not None:
        return True

    try:
        _user_model = joblib.load("models/user_model.pkl")
        _user_le = joblib.load("models/user_label_encoder.pkl")
        logger.info("User model loaded successfully")
        return True
    except Exception as e:
        logger.warning(f"User model not loaded: {e}")
        return False


def predict_user_level(features_df):
    if load_user_model():
        try:
            pred = _user_model.predict(features_df)
            return _user_le.inverse_transform(pred)[0]
        except Exception:
            logger.exception("User prediction failed")

    return "beginner" 
    
def predict_word_difficulty(features_df):
    if load_word_model():
        try:
            pred = _word_model.predict(features_df)
            return _word_le.inverse_transform(pred)[0]
        except Exception:
            logger.exception("Word prediction failed")

    return None
