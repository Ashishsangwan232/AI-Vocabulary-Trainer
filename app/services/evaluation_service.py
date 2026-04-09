import re

from app.core.logger import logger

try:
    from app.services.nlp_api import generate_word_content, evaluate_answer
except ModuleNotFoundError:
    generate_word_content = None
    evaluate_answer = None


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _fallback_generate_word_content(difficulty, word):
    hint = word[0] + ("_" * max(len(word) - 1, 0)) if word else ""
    return {
        "meaning": f"A {difficulty} level word to practice.",
        "example": f"Use '{word}' in a sentence.",
        "hint": hint,
    }


def _fallback_evaluate_answer(word, meaning, answer):
    normalized_answer = _normalize_text(answer)
    normalized_meaning = _normalize_text(meaning)
    normalized_word = _normalize_text(word)

    exact_word_match = normalized_answer == normalized_word
    exact_meaning_match = (
        bool(normalized_meaning) and normalized_answer == normalized_meaning
    )

    return {
        "is_correct": exact_word_match or exact_meaning_match,
        "score": 1.0 if (exact_word_match or exact_meaning_match) else 0.0,
        "feedback": "Correct" if (exact_word_match or exact_meaning_match) else "Try again",
    }

def generate_word_data(difficulty, level, word):
    llm_content = None
    if generate_word_content is not None:
        try:
            llm_content = generate_word_content(difficulty, word=word)
        except TypeError:
            llm_content = generate_word_content(difficulty)
        except Exception:
            logger.exception("External content generation failed, using fallback content.")

    if not isinstance(llm_content, dict):
        llm_content = _fallback_generate_word_content(difficulty, word)

    llm_content["difficulty"] = difficulty
    llm_content["user_level"] = level
    llm_content["word"] = word

    if "definition" in llm_content and "meaning" not in llm_content:
        llm_content["meaning"] = llm_content.pop("definition")

    return llm_content


def evaluate_user_answer(word, meaning, answer):
    if evaluate_answer is not None:
        try:
            return evaluate_answer(word, meaning, answer)
        except Exception:
            logger.exception("External answer evaluation failed, using fallback.")

    return _fallback_evaluate_answer(word, meaning, answer)
