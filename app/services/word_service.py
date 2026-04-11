from app.db.database import db
from app.db.models import NLPWord
import json
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


# def get_word_for_user(user_id):
#     user_features = get_user_features(user_id)
#     df = _load_words_df()

#     if df.empty:
#         return {"error": "Word dataset is unavailable"}

#     level = predict_user_level(user_features)
#     normalized_level = str(level).strip().lower()

#     mapping = {
#         "beginner": "easy",
#         "intermediate": "medium",
#         "advanced": "hard"
#     }

#     difficulty = mapping.get(normalized_level, "easy")

#     filtered = df[df["difficulty"].astype(str).str.lower() == difficulty]

#     if len(filtered) == 0:
#         return {"error": f"No words found for difficulty '{difficulty}'"}

#     word = random.choice(filtered["word"].values)

#     return generate_word_data(difficulty, normalized_level, str(word))


def select_word_ml(df, target_difficulty):
    sample_df = df.sample(100)  # sample subset for speed

    feature_cols = ["length", "vowels", "unique_chars", "syllables", "bigram_rarity", "familiarity"]

    candidates = []

    for _, row in sample_df.iterrows():
        features = pd.DataFrame([[
            row.get("length", 0),
            row.get("vowels", 0),
            row.get("unique_chars", 0),
            row.get("syllables", 0),
            row.get("bigram_rarity", 0),
            row.get("familiarity", 0)
        ]], columns=feature_cols)

        pred = predict_word_difficulty(features)

        if pred == target_difficulty:
            candidates.append(row["word"])

    if candidates:
        return random.choice(candidates)

    return random.choice(sample_df["word"].values)

def get_word_for_user(user_id):
    user_features = get_user_features(user_id)
    df = _load_words_df()

    if df.empty:
        return {"error": "Word dataset is unavailable"}

    level = predict_user_level(user_features)
    normalized_level = str(level).strip().lower()

    mapping = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}
    difficulty = mapping.get(normalized_level, "easy")

    # filtered = df[df["difficulty"].astype(str).str.lower() == difficulty]
    # word = random.choice(filtered["word"].values) if len(filtered) > 0 else "resilient"
    filtered = df  # use full dataset
    
    word = select_word_ml(filtered, difficulty)
    # Generate the content via LLM
    word_data = generate_word_data(difficulty, normalized_level, str(word))
    
    # SAVE TO DATABASE FOR FUTURE ML TRAINING
    try:
        existing_word = NLPWord.query.filter_by(word=str(word)).first()
        if not existing_word and "meaning" in word_data:
            mcq_data = word_data.get("mcq", {})
            new_nlp_word = NLPWord(
                word=str(word),
                difficulty=difficulty,
                meaning=word_data.get("meaning", ""),
                example=word_data.get("example", ""),
                mcq_question=mcq_data.get("question", ""),
                mcq_options=json.dumps(mcq_data.get("options", [])),
                mcq_correct=mcq_data.get("correct_option", "")
            )
            db.session.add(new_nlp_word)
            db.session.commit()
    except Exception as e:
        logger.error(f"Failed to save NLP word to DB: {e}")
        db.session.rollback()

    return word_data