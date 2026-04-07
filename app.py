from flask import Flask, request,jsonify
import joblib
import pandas as pd
import random

df = pd.read_csv("data/words.csv")

#load models
word_model = joblib.load("models/word_model.pkl")
user_model = joblib.load("models/user_model.pkl")

word_le = joblib.load("models/label_encoder.pkl")
user_le = joblib.load("models/user_label_encoder.pkl")


def get_word_for_user(user_features):

    # 1. predict user level
    level_encoded = user_model.predict(user_features)
    level = user_le.inverse_transform(level_encoded)[0]

    # 2. map level → difficulty
    mapping = {
        "beginner": "easy",
        "intermediate": "medium",
        "advanced": "hard"
    }

    difficulty = mapping[level]
    # 3. filter dataset
    filtered = df[df["difficulty"] == difficulty]

    # 4. pick random word
    word = random.choice(filtered["word"].values)

    return {
        "word": word,
        "difficulty": difficulty,
        "user_level": level
    }


app=Flask(__name__)

@app.route("/")
def home():
    return "AI Vocabulary Trainer Running 🚀 "


@app.route("/get_word", methods=["POST"])
def get_word():
    
    data = request.json
     # input features from frontend
    user_features = [[
        data["accuracy"],
        data["avg_time"],
        data["attempts"],
        data["streak"]
    ]]

    result = get_word_for_user(user_features)
    
    return jsonify(result)

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    data = request.json

    correct = data["is_correct"]
    return jsonify({
        "status": "received",
        "correct": correct
    })  

if __name__ == "__main__":
    app.run(debug=True)