"""
AI VOCAB PROJECT
Model Comparison — Word Difficulty Model
Run: python compare_word_models.py
"""

import pandas as pd
import numpy as np
import warnings, os
warnings.filterwarnings('ignore')
os.makedirs('plots', exist_ok=True)

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier

from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
df = pd.read_csv("final_df.csv")

# Drop bad rows
df = df.dropna()

# Encode target
le = LabelEncoder()
df["difficulty_encoded"] = le.fit_transform(df["difficulty"])

# FEATURES (IMPORTANT)
feature_cols = ["length", "vowels", "unique_chars", "frequency"]

X = df[feature_cols]
y = df["difficulty_encoded"]

# ─────────────────────────────────────────────
# 2. TRAIN TEST SPLIT
# ─────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ─────────────────────────────────────────────
# 3. MODELS
# ─────────────────────────────────────────────
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000),
    'Naive Bayes': GaussianNB(),
    'KNN': KNeighborsClassifier(n_neighbors=7),
    'Decision Tree': DecisionTreeClassifier(max_depth=6),
    'SVM': SVC(probability=True),
    'AdaBoost': AdaBoostClassifier(n_estimators=100),
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=150, max_depth=5),
}

print("=" * 65)
print(f"{'Model':<22} {'Accuracy':>9} {'ROC-AUC':>9} {'F1':>9} {'CV-AUC':>9}")
print("=" * 65)

results = []

# ─────────────────────────────────────────────
# 4. TRAIN + EVALUATE
# ─────────────────────────────────────────────
for name, clf in models.items():

    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', clf)
    ])

    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)

    # Multi-class ROC AUC
    auc = roc_auc_score(y_test, y_prob, multi_class='ovr')

    f1 = f1_score(y_test, y_pred, average='weighted')

    cv = cross_val_score(pipe, X, y, cv=3, scoring='roc_auc_ovr').mean()

    results.append({
        'Model': name,
        'Accuracy': acc,
        'ROC_AUC': auc,
        'F1': f1,
        'CV_AUC': cv
    })

    print(f"{name:<22} {acc*100:>8.2f}% {auc:>9.4f} {f1:>9.4f} {cv:>9.4f}")

print("=" * 65)

# ─────────────────────────────────────────────
# 5. SORT RESULTS
# ─────────────────────────────────────────────
results_df = pd.DataFrame(results).sort_values('ROC_AUC', ascending=False)

# ─────────────────────────────────────────────
# 6. PLOT
# ─────────────────────────────────────────────
metrics = ['Accuracy', 'ROC_AUC', 'F1']

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

for ax, metric in zip(axes, metrics):
    vals = results_df.set_index('Model')[metric]
    vals.plot(kind='barh', ax=ax)
    ax.set_title(metric)
    ax.set_xlim(0.5, 1.0)

plt.tight_layout()
plt.savefig('plots/word_model_comparison.png', dpi=150)
plt.close()

# ─────────────────────────────────────────────
# 7. BEST MODEL
# ─────────────────────────────────────────────
best = results_df.iloc[0]

print(f"\nBest model: {best['Model']} (ROC-AUC: {best['ROC_AUC']:.4f})")
print("Chart saved to plots/word_model_comparison.png")