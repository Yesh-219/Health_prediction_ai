"""
Rule-based diet hints keyed by predicted disease (demo / educational dataset).
Falls back to sensible defaults when a disease is not listed.
"""

from __future__ import annotations

from typing import Any

DEFAULT_BUNDLE: dict[str, Any] = {
    "deficiencies": ["Vitamin C", "Zinc", "Hydration"],
    "foods_eat": ["Seasonal fruits", "Vegetables", "Whole grains", "Lentils", "Nuts"],
    "foods_avoid": ["Excess sugar", "Deep-fried food", "Very spicy meals"],
    "suggestions": [
        "Rest and hydrate well",
        "Eat balanced home-cooked meals",
        "Seek medical advice if symptoms worsen",
    ],
}

# Per-disease tweaks — keeps the demo interesting for viva / presentation.
DIET_BY_DISEASE: dict[str, dict[str, Any]] = {
    "Common Cold": {
        "deficiencies": ["Vitamin C", "Zinc"],
        "foods_eat": ["Citrus fruits", "Ginger tea", "Warm soups", "Honey (if suitable)", "Garlic"],
        "foods_avoid": ["Ice-cold drinks", "Greasy fast food", "Excess caffeine"],
        "suggestions": ["Steam inhalation", "Warm fluids", "Adequate sleep"],
    },
    "Covid-19": {
        "deficiencies": ["Vitamin D", "Zinc", "Protein"],
        "foods_eat": ["Protein-rich dal/eggs", "Fresh vegetables", "Fruits", "Turmeric milk (if suitable)"],
        "foods_avoid": ["Alcohol", "Smoking", "Junk food"],
        "suggestions": ["Isolate if advised", "Monitor oxygen/spO2 if available", "Follow local health guidelines"],
    },
    "Migraine": {
        "deficiencies": ["Magnesium", "Riboflavin (B2)"],
        "foods_eat": ["Leafy greens", "Nuts", "Whole grains", "Water-rich fruits"],
        "foods_avoid": ["Aged cheese", "Excess chocolate", "Skipped meals", "Loud stress triggers"],
        "suggestions": ["Regular sleep schedule", "Reduce screen glare", "Stay hydrated"],
    },
    "Malaria": {
        "deficiencies": ["Iron", "Folate"],
        "foods_eat": ["Pomegranate", "Spinach", "Citrus for iron absorption", "Light easy meals"],
        "foods_avoid": ["Alcohol", "Heavy oily food during acute illness"],
        "suggestions": ["Complete antimalarial treatment as prescribed", "Rest", "Immediate doctor care for high fever"],
    },
    "Dengue": {
        "deficiencies": ["Electrolytes", "Platelet-supporting nutrition (under medical care)"],
        "foods_eat": ["Oral rehydration", "Papaya leaf juice (only if your doctor agrees)", "Coconut water"],
        "foods_avoid": ["NSAIDs unless prescribed", "Alcohol"],
        "suggestions": ["Hospital guidance for dengue is essential", "Monitor warning signs"],
    },
    "Gastroenteritis": {
        "deficiencies": ["Electrolytes", "Fluids"],
        "foods_eat": ["ORS", "Rice kanji", "Banana", "Boiled potato"],
        "foods_avoid": ["Dairy (early phase)", "Spicy food", "Raw salads"],
        "suggestions": ["Small frequent meals", "Hydration first", "Doctor if blood in stool or high fever"],
    },
    "GERD": {
        "deficiencies": ["Fiber (balanced)"],
        "foods_eat": ["Oats", "Non-citrus fruits", "Lean proteins", "Small meals"],
        "foods_avoid": ["Late heavy dinners", "Excess coffee", "Very spicy/acidic triggers"],
        "suggestions": ["Walk after meals", "Elevate head while sleeping if advised"],
    },
    "Hypertension": {
        "deficiencies": ["Potassium (dietary)"],
        "foods_eat": ["Banana", "Leafy greens", "Low-fat dairy", "Berries"],
        "foods_avoid": ["Excess salt", "Processed snacks", "Pickles high in sodium"],
        "suggestions": ["Regular BP checks", "Daily walking", "Limit packaged food"],
    },
    "Hepatitis A": {
        "deficiencies": ["Calories during recovery", "Vitamins A/E via diet"],
        "foods_eat": ["Simple carbs", "Cooked vegetables", "Fruits", "Adequate water"],
        "foods_avoid": ["Alcohol", "Very fatty food during acute phase"],
        "suggestions": ["Hygiene & safe water", "Vaccination awareness", "Doctor follow-up"],
    },
}


def diet_for_disease(disease_name: str) -> dict[str, Any]:
    base = DEFAULT_BUNDLE.copy()
    extra = DIET_BY_DISEASE.get(disease_name)
    if not extra:
        return base
    out = base.copy()
    for k, v in extra.items():
        out[k] = v
    return out


def merge_diet_for_predictions(prediction_names: list[str]) -> dict[str, Any]:
    """Blend hints from top diseases (first match wins for lists)."""
    if not prediction_names:
        return DEFAULT_BUNDLE.copy()
    primary = diet_for_disease(prediction_names[0])
    return primary
