import os
import json
import ollama
from openai import OpenAI
from app.core.logger import logger

api_key = os.environ.get("OLLAMA_API_KEY")
cloud_host = "https://ollama.com"
MODEL_NAME = "gpt-oss:120b-cloud"

client_headers = {}
if api_key and "ollama.com" in cloud_host:
    client_headers = {"Authorization": f"Bearer {api_key}"}
    print(f"[INFO] Configuring Ollama client for cloud host: {cloud_host} with API key.")
elif not api_key and "ollama.com" in cloud_host:
    print(f"[WARN] Connecting to Ollama Cloud host ({cloud_host}) but OLLAMA_API_KEY not set.")
else:
    print(f"[INFO] Configuring Ollama client for host: {cloud_host}")

client = None
try:
    client = ollama.Client(
        host=cloud_host, headers=client_headers if client_headers else None
    )
    print("[INFO] Ollama client initialized.")
except Exception as e:
    print(f"[ERROR] Failed to initialize Ollama client: {e}")
    print("[WARN] AI service features depending on Ollama will be disabled or use fallbacks.")

def _clean_json_response(response_text: str) -> dict:
    """Helper to strip markdown formatting if the model wraps the JSON."""
    clean_text = response_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response: {response_text}")
        return {}


def generate_word_content(difficulty: str, word: str = None) -> dict:
    """Generates a definition, example, hint, and an MCQ for a specific word."""
    logger.info(f"Generating content and MCQ for word: {word} (Difficulty: {difficulty})")

    prompt = f"""
    You are an expert vocabulary tutor. 
    The student needs to learn the word: '{word}'. The difficulty level is {difficulty}.
    
    1. Provide a simple definition, a sentence using the word, and a hint.
    2. Create a Multiple Choice Question (MCQ) to test their understanding of the word. Provide 4 options and specify the exact string of the correct option.
    
    Respond ONLY with a valid JSON object matching this exact format:
    {{
        "meaning": "Clear definition here",
        "example": "A sentence using the word.",
        "hint": "A subtle clue about the word.",
        "mcq": {{
            "question": "Which scenario best demonstrates someone being '{word}'?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_option": "The exact text of the correct option"
        }}
    }}
    """

    try:
        # Correct Ollama syntax
        response = client.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a JSON-outputting API."},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.3}
        )
        content = response.get("message", {}).get("content", "")
        return _clean_json_response(content)
    except Exception as e:
        logger.error(f"Error generating word content: {str(e)}")
        raise e


def evaluate_answer(word: str, meaning: str, answer: str) -> dict:
    """Evaluates if the user's sentence demonstrates understanding of the word."""
    logger.info(f"Evaluating answer for '{word}'")

    prompt = f"""
    You are a strict but fair vocabulary tutor. 
    The target word is '{word}', which means '{meaning}'.
    The student provided the following answer/sentence to demonstrate their understanding: "{answer}"
    
    Evaluate their answer. Did they use the word correctly, or describe its meaning accurately?
    
    Respond ONLY with a valid JSON object matching this exact format, with no other text:
    {{
        "is_correct": true or false,
        "score": a float between 0.0 and 1.0,
        "feedback": "A short, encouraging explanation of why they are right or what they got wrong."
    }}
    """

    try:
        # Correct Ollama syntax
        response = client.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful JSON-outputting API."},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.1}
        )
        content = response.get("message", {}).get("content", "")
        return _clean_json_response(content)
    except Exception as e:
        logger.error(f"Error evaluating answer: {str(e)}")
        raise e


def generate_trivia_fact() -> str:
    """Generates a random etymology or vocabulary fact."""
    prompt = "Generate a single, fascinating, one-sentence trivia fact about the English language, word origins (etymology), or linguistics. Do not use quotes or introductory text. Just the fact."

    try:
        # Correct Ollama syntax
        response = client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7}
        )
        return response.get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.error(f"Error generating fact: {str(e)}")
        return "Shakespeare invented over 1,700 words that we still use today."