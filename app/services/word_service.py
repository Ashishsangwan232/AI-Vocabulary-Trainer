import json
import random
import pandas as pd
from pathlib import Path

from app.db.database import db
from app.db.models import NLPWord, UserHistory
from app.core.logger import logger
from app.ml.inference import predict_user_level, predict_word_difficulty
from app.services.user_service import get_user_features
from app.services.evaluation_service import generate_word_data

BASE_DIR = Path(__file__).resolve().parents[2]
WORDS_CSV_PATH = BASE_DIR / "data" / "final_df.csv"

_words_df = None

def _load_words_df():
    global _words_df
    if _words_df is not None:
        return _words_df
    try:
        df = pd.read_csv(WORDS_CSV_PATH)
    except Exception:
        logger.exception("Failed loading words data")
        return pd.DataFrame(columns=["word", "difficulty"])

    _words_df = df
    return _words_df

def select_word_ml_ranked(df, effective_user_score):
    """Ranks words by mathematical distance to the user's effective score."""
    
    # ⚠️ THE FIX: Stratified Sampling to guarantee a mix of difficulties
    short_words = df[df['length'] <= 5].sample(min(50, len(df[df['length'] <= 5])))
    med_words = df[(df['length'] > 5) & (df['length'] <= 8)].sample(min(50, len(df[(df['length'] > 5) & (df['length'] <= 8)])))
    long_words = df[df['length'] > 8].sample(min(50, len(df[df['length'] > 8])))
    
    sample_df = pd.concat([short_words, med_words, long_words])

    feature_cols = [
        "Frequency", "syllables", "bigram_rarity", "familiarity",
        "length", "vowels", "unique_chars", "synsets", "depth", "lemmas",
    ]
    diff_map = {"easy": 1.0, "medium": 2.0, "hard": 3.0}
    scored_candidates = []

    for _, row in sample_df.iterrows():
        features = pd.DataFrame([[
            row.get("Frequency", 0.0), row.get("syllables", 0), row.get("bigram_rarity", 0.0),
            row.get("familiarity", 0.0), row.get("length", 0), row.get("vowels", 0),
            row.get("unique_chars", 0), row.get("synsets", 0.0), row.get("depth", 0.0), row.get("lemmas", 0.0)
        ]], columns=feature_cols)

        pred_label = predict_word_difficulty(features)
        if not pred_label:
            pred_label = "medium"

        word_base_score = diff_map.get(pred_label, 2.0)
        length_modifier = min(max((row.get("length", 5) - 6) * 0.05, -0.2), 0.2)
        continuous_word_score = word_base_score + length_modifier
        distance = abs(effective_user_score - continuous_word_score)

        scored_candidates.append({
            "word": row["word"], "distance": distance, "difficulty": pred_label
        })

    scored_candidates.sort(key=lambda x: x["distance"])
    best_match = random.choice(scored_candidates[:3])
    return best_match["word"], best_match["difficulty"]

def get_word_for_user(user_id):
    user_features = get_user_features(user_id)
    df = _load_words_df()

    if df.empty:
        return {"error": "Word dataset is unavailable"}

    level = predict_user_level(user_features)
    normalized_level = str(level).strip().lower()

    target_word = None
    target_difficulty = "medium"
    is_review = False

    # ⚠️ SRS LOGIC: 30% chance to fetch a previously failed word
    if random.random() < 0.30:
        failed_history = UserHistory.query.filter_by(user_id=user_id, is_correct=False).order_by(db.func.random()).first()
        if failed_history:
            target_word = failed_history.word
            is_review = True
            
            # Find the word in the dataframe to get its features for difficulty prediction
            word_row = df[df['word'] == target_word]
            if not word_row.empty:
                # We could run the ML model here, but for a review word, let's just default to 'medium' 
                # or grab it from the NLPWord table if it exists. We'll use a safe fallback.
                target_difficulty = "review" 

    # If no review word was selected, proceed with ML ranking
    # If no review word was selected, proceed with ML ranking
    # If no review word was selected, proceed with ML ranking
    if not target_word:
        overall_acc = float(user_features.iloc[0]["accuracy"])
        recent_acc = float(user_features.iloc[0]["recent_accuracy"])
        improvement = float(user_features.iloc[0]["improvement_rate"])
        streak = float(user_features.iloc[0]["streak"])

        level_map = {"beginner": 1.0, "intermediate": 2.0, "advanced": 3.0}
        base_score = level_map.get(normalized_level, 1.0)

        # ⚠️ CRITICAL FIX: Increased multipliers to ensure the score crosses difficulty thresholds!
        # If recent_acc is 1.0 (100%), raw_adjustment becomes +1.0, easily pushing them to the next level.
        raw_adjustment = (recent_acc - 0.5) * 2.0 + (improvement * 0.5)

        # DIFFICULTY SMOOTHING LOGIC
        if raw_adjustment < 0:
            # Dampen drops by 50% if they have an overall good history (>60%)
            dampener = 0.5 if overall_acc > 0.60 else 1.0
            streak_buffer = min(streak * 0.05, 0.2) # Max 0.2 protection from a good streak
            
            smoothed_adjustment = (raw_adjustment * dampener) + streak_buffer
        else:
            # Let them climb fast if they are doing well!
            smoothed_adjustment = raw_adjustment

        # Cap the swing to max +/- 1.2 levels per jump
        smoothed_adjustment = max(-1.2, min(1.2, smoothed_adjustment))
        
        effective_score = max(1.0, min(3.0, base_score + smoothed_adjustment))
        
        # Fetch Ranked Word
        target_word, target_difficulty = select_word_ml_ranked(df, effective_score)
    # Generate LLM Content
    word_data = generate_word_data(target_difficulty, normalized_level, str(target_word))
    
    # Add the review flag to the payload sent to React
    word_data["is_review"] = is_review

    # Save to Database
    try:
        existing_word = NLPWord.query.filter_by(word=str(target_word)).first()
        if not existing_word and "meaning" in word_data:
            mcq_data = word_data.get("mcq", {})
            new_nlp_word = NLPWord(
                word=str(target_word), difficulty=target_difficulty,
                meaning=word_data.get("meaning", ""), example=word_data.get("example", ""),
                mcq_question=mcq_data.get("question", ""), mcq_options=json.dumps(mcq_data.get("options", [])),
                mcq_correct=mcq_data.get("correct_option", "")
            )
            db.session.add(new_nlp_word)
            db.session.commit()
    except Exception as e:
        logger.error(f"Failed to save NLP word to DB: {e}")
        db.session.rollback()

    return word_data