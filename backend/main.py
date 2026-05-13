"""
PredictAI backend: FastAPI + Random Forest disease prediction, SQLite history, PDF reports.
Important sections are marked for student presentations / viva.
"""
from __future__ import annotations

import json
import os
import pickle
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from chat_rules import reply_to_message
from diet_knowledge import merge_diet_for_predictions
from report_pdf import build_health_report_pdf
from symptom_parser import parse_symptom_text

app = FastAPI(title="PredictAI Disease Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "supersecretkey"  # Demo only — use env vars in production

# -----------------------------------------------------------------------------
# SQLite
# -----------------------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "health.db"))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            symptom_text TEXT,
            matched_symptoms TEXT NOT NULL,
            predictions TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()

# -----------------------------------------------------------------------------
# ML model (pickle from ml_model/train.py)
# -----------------------------------------------------------------------------

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml_model", "model.pkl")

ml_model = None
symptoms_list: list[str] = []
classes_list: list[str] = []

DEFAULT_SYMPTOMS_FALLBACK = [
    "itching",
    "skin_rash",
    "nodal_skin_eruptions",
    "continuous_sneezing",
    "shivering",
    "chills",
    "joint_pain",
    "stomach_pain",
    "acidity",
    "ulcers_on_tongue",
    "muscle_wasting",
    "vomiting",
    "burning_micturition",
    "fatigue",
    "weight_gain",
    "anxiety",
    "restlessness",
    "lethargy",
    "cough",
    "high_fever",
    "breathlessness",
    "sweating",
    "dehydration",
    "indigestion",
    "headache",
    "nausea",
    "back_pain",
    "constipation",
    "diarrhoea",
    "mild_fever",
]


def load_model() -> None:
    global ml_model, symptoms_list, classes_list
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            data = pickle.load(f)
        ml_model = data["model"]
        symptoms_list = list(data["symptoms"])
        classes_list = list(data.get("classes", getattr(ml_model, "classes_", [])))


# -----------------------------------------------------------------------------
# Severity & safety rules (symptom count)
# -----------------------------------------------------------------------------


def severity_label(symptom_count: int) -> str:
    if symptom_count <= 2:
        return "Mild"
    if symptom_count <= 4:
        return "Moderate"
    return "Severe"


def should_warn_doctor(symptom_count: int) -> bool:
    """Many simultaneous symptoms → urgent-care reminder (educational)."""
    return symptom_count >= 6


HEALTH_TIPS = [
    "Walk 20–30 minutes daily to support heart health and mood.",
    "Drink water regularly; mild dehydration often mimics fatigue and headache.",
    "Prioritize sleep (7–8 hours) — it helps immunity and focus.",
    "Add colorful vegetables to meals for fiber, vitamins, and minerals.",
    "Wash hands before eating to reduce stomach and respiratory infections.",
    "Take short screen breaks every hour to reduce eye strain and headaches.",
    "Limit ultra-processed snacks; whole foods are easier on digestion.",
    "If you are unwell for several days or feel worse, contact a clinician.",
]

# -----------------------------------------------------------------------------
# Pydantic models
# -----------------------------------------------------------------------------


class User(BaseModel):
    username: str
    password: str


class PredictRequest(BaseModel):
    """Send free text and/or already-mapped symptom codes."""

    symptom_text: str | None = Field(default=None, description="e.g. 'fever, headache, vomiting'")
    symptoms: list[str] = Field(default_factory=list, description="Canonical snake_case symptoms")


class BMIInput(BaseModel):
    weight_kg: float
    height_cm: float


class ChatInput(BaseModel):
    message: str


class PredictionItem(BaseModel):
    disease: str
    probability: float


class ReportPayload(BaseModel):
    symptom_text: str = ""
    matched_symptoms: list[str] = []
    predictions: list[PredictionItem] = []
    severity: str = ""
    doctor_warning: bool = False
    bmi: dict[str, Any] | None = None
    diet: dict[str, Any] | None = None
    suggestions: list[str] = []


# -----------------------------------------------------------------------------
# Auth (existing feature)
# -----------------------------------------------------------------------------


@app.post("/api/register")
def register(user: User) -> dict[str, str]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (user.username,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (user.username, hashed))
    conn.commit()
    conn.close()
    return {"message": "User registered successfully"}


@app.post("/api/login")
def login(user: User) -> dict[str, str]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (user.username,))
    row = cur.fetchone()
    conn.close()
    if not row or not bcrypt.checkpw(user.password.encode(), row["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = jwt.encode(
        {"sub": user.username, "exp": datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm="HS256",
    )
    if isinstance(token, bytes):
        token = token.decode()
    return {"access_token": token}


# -----------------------------------------------------------------------------
# Symptoms list for UI + fuzzy matching vocabulary
# -----------------------------------------------------------------------------


@app.get("/api/symptoms")
def get_symptoms() -> dict[str, list[str]]:
    load_model()
    syms = symptoms_list if symptoms_list else DEFAULT_SYMPTOMS_FALLBACK
    return {"symptoms": syms}


@app.get("/api/health-tip")
def daily_health_tip() -> dict[str, str]:
    return {"tip": random.choice(HEALTH_TIPS)}


# -----------------------------------------------------------------------------
# Symptom parsing (NLP-lite) — useful for demo
# -----------------------------------------------------------------------------


@app.post("/api/parse-symptoms")
def parse_symptoms(payload: dict[str, str]) -> dict[str, Any]:
    """Preview mapping without running the ML model."""
    load_model()
    vocab = symptoms_list if symptoms_list else DEFAULT_SYMPTOMS_FALLBACK
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text'")
    return parse_symptom_text(text, vocab)


# -----------------------------------------------------------------------------
# Prediction + diet + history
# -----------------------------------------------------------------------------


def _run_ml(symptoms: list[str]) -> list[dict[str, Any]]:
    load_model()
    vocab = symptoms_list if symptoms_list else DEFAULT_SYMPTOMS_FALLBACK
    if ml_model is None:
        return [
            {"disease": "Common Cold", "probability": 45.0},
            {"disease": "Influenza (Flu)", "probability": 30.0},
            {"disease": "Allergic Rhinitis", "probability": 25.0},
        ]

    vec = [0] * len(vocab)
    for sym in symptoms:
        if sym in vocab:
            vec[vocab.index(sym)] = 1
    # DataFrame keeps feature names aligned with training (avoids sklearn warnings).
    x_row = pd.DataFrame([vec], columns=vocab)
    probs = ml_model.predict_proba(x_row)[0]
    top_idx = probs.argsort()[-3:][::-1]
    class_names = list(ml_model.classes_)
    out: list[dict[str, Any]] = []
    for i in top_idx:
        label = class_names[i]
        out.append({"disease": str(label), "probability": float(probs[i] * 100)})
    return out


def _save_history(symptom_text: str, matched: list[str], predictions: list[dict[str, Any]]) -> None:
    conn = get_db()
    conn.execute(
        """
        INSERT INTO prediction_history(created_at, symptom_text, matched_symptoms, predictions)
        VALUES(?,?,?,?)
        """,
        (
            datetime.utcnow().isoformat() + "Z",
            symptom_text,
            json.dumps(matched),
            json.dumps(predictions),
        ),
    )
    conn.commit()
    # Keep table small for demo: drop older rows beyond 200
    cur = conn.execute("SELECT COUNT(*) AS c FROM prediction_history")
    count = cur.fetchone()["c"]
    if count > 200:
        conn.execute(
            """
            DELETE FROM prediction_history WHERE id NOT IN (
                SELECT id FROM (
                    SELECT id FROM prediction_history ORDER BY id DESC LIMIT 200
                )
            )
            """
        )
        conn.commit()
    conn.close()


@app.get("/api/history")
def prediction_history(limit: int = 5) -> dict[str, list[dict[str, Any]]]:
    limit = max(1, min(limit, 20))
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, created_at, symptom_text, matched_symptoms, predictions
        FROM prediction_history
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append(
            {
                "id": r["id"],
                "created_at": r["created_at"],
                "symptom_text": r["symptom_text"] or "",
                "matched_symptoms": json.loads(r["matched_symptoms"]),
                "predictions": json.loads(r["predictions"]),
            }
        )
    return {"items": items}


@app.post("/api/predict")
def predict_disease(data: PredictRequest) -> dict[str, Any]:
    load_model()
    vocab = symptoms_list if symptoms_list else DEFAULT_SYMPTOMS_FALLBACK

    raw_text = (data.symptom_text or "").strip()
    parsed = parse_symptom_text(raw_text, vocab) if raw_text else {"matched": [], "unmatched_tokens": [], "did_you_mean": []}

    # Merge explicit symptom codes with parsed
    merged: list[str] = []
    seen: set[str] = set()
    for s in list(data.symptoms) + parsed["matched"]:
        if s in vocab and s not in seen:
            seen.add(s)
            merged.append(s)

    if not merged:
        raise HTTPException(
            status_code=400,
            detail="No recognizable symptoms. Try comma-separated words like 'fever, headache, cough'.",
        )

    n = len(merged)
    sev = severity_label(n)
    doc_warn = should_warn_doctor(n)

    predictions = _run_ml(merged)
    top_names = [p["disease"] for p in predictions]
    diet = merge_diet_for_predictions(top_names)

    response = {
        "predictions": predictions,
        "severity": sev,
        "doctor_warning": doc_warn,
        "symptom_text": raw_text,
        "matched_symptoms": merged,
        "unmatched_tokens": parsed.get("unmatched_tokens", []),
        "did_you_mean": parsed.get("did_you_mean", []),
        "deficiencies": diet["deficiencies"],
        "foods": diet["foods_eat"],
        "foods_avoid": diet["foods_avoid"],
        "suggestions": diet["suggestions"],
    }

    _save_history(raw_text, merged, predictions)
    return response


# -----------------------------------------------------------------------------
# BMI (category + eat / avoid)
# -----------------------------------------------------------------------------


@app.post("/api/bmi")
def calculate_bmi(data: BMIInput) -> dict[str, Any]:
    height_m = data.height_cm / 100
    if height_m == 0:
        raise HTTPException(status_code=400, detail="Height cannot be zero")

    bmi = round(data.weight_kg / (height_m**2), 2)

    if bmi < 18.5:
        category = "Underweight"
        foods = ["Bananas", "Whole eggs", "Nuts and seeds", "Milk or curd", "Avocados", "Rice and dal"]
        foods_avoid = ["Skipping meals", "Excess junk food without a plan"]
        tips = [
            "Eat calorie-smart, nutrient-dense meals on a schedule.",
            "Add strength training 2–3x/week if your doctor agrees.",
            "Track weight weekly — slow, steady gain is healthier.",
        ]
    elif 18.5 <= bmi < 25:
        category = "Normal"
        foods = ["Lean proteins", "Vegetables", "Whole grains", "Fruits", "Healthy fats (nuts, olive oil)"]
        foods_avoid = ["Excess sugar", "Frequent fried snacks"]
        tips = [
            "Keep a balanced plate and stay hydrated.",
            "Aim for 150+ minutes of moderate activity weekly.",
            "Sleep 7–8 hours for recovery and appetite regulation.",
        ]
    elif 25 <= bmi < 30:
        category = "Overweight"
        foods = ["Leafy greens", "Oats", "Beans", "Berries", "High-fiber vegetables"]
        foods_avoid = ["Sugary beverages", "Late-night heavy meals", "Ultra-processed snacks"]
        tips = [
            "Try smaller portions and mindful eating.",
            "Walk after meals when possible.",
            "Reduce liquid calories (soda, sweet coffee).",
        ]
    else:
        category = "Obese"
        foods = ["Vegetables", "High-fiber foods", "Lean proteins", "Whole grains", "Legumes"]
        foods_avoid = ["Fried food", "Excess sweets", "Large portion buffets"]
        tips = [
            "Discuss a safe plan with a doctor or dietitian.",
            "Start with daily walking and gradual changes.",
            "Focus on habits you can sustain for months, not days.",
        ]

    return {
        "bmi": bmi,
        "status": category,
        "category": category,
        "foods": foods,
        "foods_avoid": foods_avoid,
        "tips": tips,
        "health_suggestions": tips,
    }


# -----------------------------------------------------------------------------
# Chatbot (rule-based)
# -----------------------------------------------------------------------------


@app.post("/api/chat")
def chat(data: ChatInput) -> dict[str, str]:
    return {"reply": reply_to_message(data.message)}


# -----------------------------------------------------------------------------
# PDF report (download)
# -----------------------------------------------------------------------------


@app.post("/api/report/pdf")
def download_report(payload: ReportPayload) -> Response:
    pdf_bytes = build_health_report_pdf(payload.model_dump())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="predictai_health_report.pdf"'},
    )
