"""
Lightweight rule-based health assistant (no external LLM API).
Extend KEYWORD_RULES for demo / viva — students can explain this easily.
"""
from __future__ import annotations

import re
from typing import Callable


def _clean(msg: str) -> str:
    return re.sub(r"\s+", " ", msg.strip().lower())


KEYWORD_RULES: list[tuple[re.Pattern[str], str | Callable[[str], str]]] = [
    (
        re.compile(r"\b(bmi|body mass)\b"),
        "BMI is weight (kg) divided by height (m) squared. Under 18.5 is underweight, 18.5–24.9 is normal, "
        "25–29.9 is overweight, and 30+ is obese. Use our BMI page for tailored food tips — this app is not a substitute for a doctor.",
    ),
    (
        re.compile(r"\b(fever|temperature)\b"),
        "For fever: rest, fluids, and light meals. If fever is high, prolonged, or you have breathing difficulty, "
        "please consult a doctor urgently. You can log symptoms in PredictAI for educational pattern matching only.",
    ),
    (
        re.compile(r"\b(headache|migraine)\b"),
        "Headaches can be tension, migraine, dehydration, or something more serious. Hydrate, rest your eyes, "
        "and reduce screen glare. Seek care for sudden severe headache, neck stiffness, or neurological symptoms.",
    ),
    (
        re.compile(r"\b(cold|flu|cough|sneez)\b"),
        "Colds and flu-like illness need rest, warm fluids, and good nutrition. Wash hands, mask if unwell around others. "
        "See a clinician if breathing is hard, fever is persistent, or you are high-risk.",
    ),
    (
        re.compile(r"\b(stomach|nausea|vomit|diarr|loose)\b"),
        "Digestive upset: prioritize oral rehydration and bland foods. Avoid heavy spices and alcohol. "
        "Get medical help for blood in vomit/stool, severe pain, or signs of dehydration.",
    ),
    (
        re.compile(r"\b(diet|food|eat|nutrition)\b"),
        "A balanced plate (vegetables, protein, whole grains) supports recovery. Our BMI and disease pages show "
        "example foods — personalize with a dietitian for medical conditions.",
    ),
    (
        re.compile(r"\b(water|hydrat|drink)\b"),
        "Aim for steady water intake through the day (more if fever or diarrhea). Plain water, ORS, or coconut water "
        "(if suitable) can help — avoid excess sugary drinks.",
    ),
    (
        re.compile(r"\b(doctor|emergency|urgent|severe)\b"),
        "If symptoms are severe, sudden, or worsening — contact emergency services or visit a hospital. "
        "PredictAI is an educational project and must not replace professional diagnosis.",
    ),
    (
        re.compile(r"\b(symptom|predict|disease)\b"),
        "Type symptoms in plain language on the Disease Predictor page (e.g. 'fever, headache'). "
        "We map them to a dataset vocabulary and run a Random Forest model for the top 3 likely labels — for learning only.",
    ),
    (
        re.compile(r"\b(thank|thanks)\b"),
        "You're welcome. Stay hydrated and take care — and use clinical services when in doubt.",
    ),
    (
        re.compile(r"\b(hi|hello|hey)\b"),
        "Hello! I'm the PredictAI rule-based assistant. Ask about BMI, diet, fever, cough, stomach issues, or how the predictor works.",
    ),
]


def reply_to_message(message: str) -> str:
    text = _clean(message)
    if not text:
        return "Please type a short health-related question."

    for pattern, response in KEYWORD_RULES:
        if pattern.search(text):
            return response if isinstance(response, str) else response(text)

    return (
        "I match simple keywords only (demo chatbot). Try asking about BMI, fever, headache, cough, stomach problems, "
        "diet, hydration, or how symptom prediction works. For personal diagnosis, please consult a qualified doctor."
    )
