from flask import Blueprint, jsonify
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

model_bp = Blueprint("model", __name__)
BASE_DIR = Path(__file__).resolve().parents[2]

# -----------------------------
# FEATURE ORDER (MUST MATCH TRAINING)
# -----------------------------
FEATURES = [
    "Frequency", "syllables", "bigram_rarity", "familiarity",
    "length", "vowels", "unique_chars", "synsets", "depth", "lemmas"
]

# -----------------------------
# 1. MODEL RESULTS API
# -----------------------------
@model_bp.route("/results", methods=["GET"])
def get_model_results():
    try:
        path = BASE_DIR / "DataLab" / "model_results.json"

        if not path.exists():
            return jsonify({"error": f"File not found: {path}"}), 404

        with open(path) as f:
            data = json.load(f)

        return jsonify(data)

    except Exception as e:
        print("ERROR IN RESULTS:", str(e))
        return jsonify({"error": str(e)}), 500


# -----------------------------
# 2. VISUAL DATA API
# -----------------------------
@model_bp.route("/visual-data", methods=["GET"])
def get_visual_data():
    try:
        # -----------------------------
        # LOAD DATA
        # -----------------------------
        df_path = BASE_DIR / "data" / "final_df.csv"

        if not df_path.exists():
            return jsonify({"error": f"Dataset not found: {df_path}"}), 404

        df = pd.read_csv(df_path)

        # Validate columns
        for col in FEATURES + ["difficulty"]:
            if col not in df.columns:
                return jsonify({"error": f"Missing column: {col}"}), 500

        df_sample = df.sample(min(1000, len(df)), random_state=42).copy()

        label_map = {"easy": 0, "intermediate": 1, "hard": 2}
        df_sample["label"] = df_sample["difficulty"].map(label_map)

        scatter = df_sample[["Frequency", "length", "label"]].to_dict(orient="records")

        # -----------------------------
        # LOAD MODELS
        # -----------------------------
        model_names = ["logistic_regression", "decision_tree", "random_forest", "svm"]
        models = {}

        for name in model_names:
            model_path = BASE_DIR / f"DataLab/{name}.pkl"

            if not model_path.exists():
                print(f"[WARNING] Missing model: {name}")
                continue

            models[name] = joblib.load(model_path)

        scaler_path = BASE_DIR / "DataLab/scaler.pkl"
        scaler = joblib.load(scaler_path) if scaler_path.exists() else None

        # -----------------------------
        # CREATE GRID
        # -----------------------------
        x_min, x_max = df_sample["Frequency"].min(), df_sample["Frequency"].max()
        y_min, y_max = df_sample["length"].min(), df_sample["length"].max()

        xx, yy = np.meshgrid(
            np.linspace(x_min, x_max, 20),
            np.linspace(y_min, y_max, 20)
        )

        base_row = df_sample.iloc[0]

        boundaries = {}

        # -----------------------------
        # GENERATE DECISION BOUNDARIES
        # -----------------------------
        for name, model in models.items():
            grid_points = []

            try:
                for i in range(xx.shape[0]):
                    for j in range(xx.shape[1]):

                        sample = base_row.copy()
                        sample["Frequency"] = xx[i][j]
                        sample["length"] = yy[i][j]

                        features = np.array([sample[f] for f in FEATURES]).reshape(1, -1)

                        if scaler and name in ["logistic_regression", "svm"]:
                            features = scaler.transform(features)

                        pred = model.predict(features)[0]

                        grid_points.append({
                            "x": float(xx[i][j]),
                            "y": float(yy[i][j]),
                            "label": int(pred)
                        })

                boundaries[name] = grid_points

            except Exception as e:
                print(f"[ERROR] Model failed: {name} → {str(e)}")
                boundaries[name] = []  # prevent crash

        return jsonify({
            "scatter": scatter,
            "boundaries": boundaries
        })

    except Exception as e:
        print("ERROR IN VISUAL-DATA:", str(e))
        return jsonify({"error": str(e)}), 500


# -----------------------------
# 3. TEST ROUTE (DEBUG)
# -----------------------------
@model_bp.route("/test", methods=["GET"])
def test():
    return {"msg": "model routes working"}