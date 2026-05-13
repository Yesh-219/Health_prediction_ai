"""
Train RandomForest on synthetic disease–symptom data and save model.pkl next to this file.
Run from project root:  python backend/ml_model/train.py
Or from backend:        python ml_model/train.py
"""
from __future__ import annotations

import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

symptoms = [
    "itching",
    "skin_rash",
    "continuous_sneezing",
    "shivering",
    "chills",
    "joint_pain",
    "stomach_pain",
    "acidity",
    "vomiting",
    "fatigue",
    "weight_gain",
    "weight_loss",
    "restlessness",
    "lethargy",
    "cough",
    "high_fever",
    "headache",
    "yellowish_skin",
    "dark_urine",
    "nausea",
    "loss_of_appetite",
    "pain_behind_the_eyes",
    "back_pain",
    "constipation",
    "abdominal_pain",
    "diarrhoea",
    "mild_fever",
    "muscle_pain",
]

diseases = [
    "Fungal infection",
    "Allergy",
    "GERD",
    "Drug Reaction",
    "Peptic ulcer disease",
    "Gastroenteritis",
    "Bronchial Asthma",
    "Hypertension",
    "Migraine",
    "Cervical spondylosis",
    "Malaria",
    "Chicken pox",
    "Dengue",
    "Typhoid",
    "Hepatitis A",
    "Common Cold",
    "Covid-19",
]


def generate_mock_data(samples: int = 1000) -> tuple[pd.DataFrame, pd.Series]:
    data = []
    labels = []
    np.random.seed(42)

    for _ in range(samples):
        disease_idx = np.random.randint(0, len(diseases))
        disease = diseases[disease_idx]
        row = np.zeros(len(symptoms))

        if disease == "Fungal infection":
            idx = [0, 1]
        elif disease == "Allergy":
            idx = [2, 3, 4]
        elif disease == "GERD":
            idx = [6, 7, 8, 14]
        elif disease == "Peptic ulcer disease":
            idx = [8, 19, 24]
        elif disease == "Migraine":
            idx = [16, 7, 19]
        elif disease == "Malaria":
            idx = [4, 8, 15, 16, 27]
        elif disease == "Common Cold":
            idx = [2, 3, 4, 14, 15, 16, 27]
        elif disease == "Covid-19":
            idx = [2, 14, 15, 9, 27, 26]
        else:
            idx = np.random.choice(len(symptoms), np.random.randint(3, 6), replace=False)

        for i in idx:
            row[i] = 1
        if np.random.rand() > 0.5:
            row[np.random.randint(0, len(symptoms))] = 1

        data.append(row)
        labels.append(disease)

    return pd.DataFrame(data, columns=symptoms), pd.Series(labels)


def train_model() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "model.pkl")

    print("Generating synthetic training rows...")
    X, y = generate_mock_data(2000)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training RandomForestClassifier...")
    rf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)
    acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"Holdout accuracy (demo data): {acc:.4f}")

    with open(out_path, "wb") as f:
        pickle.dump({"model": rf, "symptoms": symptoms, "classes": rf.classes_}, f)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    train_model()
