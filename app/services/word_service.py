from pathlib import Path
import random

import pandas as pd

from app.core.logger import logger
from app.ml.inference import predict_user_level
from app.services.user_service import get_user_features
from app.services.evaluation_service import generate_word_data

BASE_DIR = Path(__file__).resolve().parents[2]
WORDS_CSV_PATH = BASE_DIR / "data" / "words.csv"

_words_df = None


def _load_words_df():
    global _words_df

    if _words_df is not None:
        return _words_df

    try:
        df = pd.read_csv(WORDS_CSV_PATH)
    except Exception:
        logger.exception("Failed loading words data from %s", WORDS_CSV_PATH)
        _words_df = pd.DataFrame(columns=["word", "difficulty"])
        return _words_df

    required_columns = {"word", "difficulty"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        logger.error("Words CSV missing required columns: %s", ", ".join(missing_columns))
        _words_df = pd.DataFrame(columns=["word", "difficulty"])
        return _words_df

    _words_df = df
    return _words_df


def get_word_for_user(user_id):
    user_features = get_user_features(user_id)
    df = _load_words_df()

    if df.empty:
        return {"error": "Word dataset is unavailable"}

    level = predict_user_level(user_features)
    normalized_level = str(level).strip().lower()

    mapping = {
        "beginner": "easy",
        "intermediate": "medium",
        "advanced": "hard"
    }

    difficulty = mapping.get(normalized_level, "easy")

    filtered = df[df["difficulty"].astype(str).str.lower() == difficulty]

    if len(filtered) == 0:
        return {"error": f"No words found for difficulty '{difficulty}'"}

    word = random.choice(filtered["word"].values)

    return generate_word_data(difficulty, normalized_level, str(word))
