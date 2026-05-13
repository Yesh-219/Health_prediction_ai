"""
Free-text symptom parsing: split tokens, normalize, and fuzzy-match to the ML vocabulary.
Uses the standard library (difflib) — easy to explain in a project report.
"""
from __future__ import annotations

import re
from difflib import get_close_matches
from typing import Any


def _normalize_phrase(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _build_lookup_keys(symptoms_list: list[str]) -> tuple[list[str], dict[str, str]]:
    """Map many surface forms (underscore / space / compact) to canonical symptom names."""
    keys: list[str] = []
    key_to_canonical: dict[str, str] = {}
    for sym in symptoms_list:
        variants = {
            sym.lower(),
            sym.replace("_", " ").lower(),
            sym.replace("_", "").lower(),
        }
        for v in variants:
            if v not in key_to_canonical:
                key_to_canonical[v] = sym
                keys.append(v)
    return keys, key_to_canonical


# Everyday words → canonical dataset columns (helps free-text like "fever, rash").
TOKEN_ALIASES: dict[str, list[str]] = {
    "fever": ["high_fever", "mild_fever"],
    "fevr": ["high_fever", "mild_fever"],
    "temperature": ["high_fever"],
    "rash": ["skin_rash"],
    "vomit": ["vomiting"],
    "throwing": ["vomiting"],
    "nausea": ["nausea"],
    "headache": ["headache"],
    "cough": ["cough"],
    "cold": ["continuous_sneezing"],
    "sneeze": ["continuous_sneezing"],
    "sneezing": ["continuous_sneezing"],
    "tired": ["fatigue"],
    "fatigue": ["fatigue"],
    "pain": ["joint_pain", "stomach_pain", "back_pain", "abdominal_pain"],
    "stomach": ["stomach_pain", "abdominal_pain"],
    "belly": ["abdominal_pain", "stomach_pain"],
    "diarrhea": ["diarrhoea"],
    "loose": ["diarrhoea"],
    "chill": ["chills"],
    "shiver": ["shivering"],
}


def _split_symptom_phrases(text: str) -> list[str]:
    """Split user text on commas, semicolons, newlines, and 'and'."""
    if not text or not text.strip():
        return []
    t = text.replace("\n", ",").replace(";", ",")
    parts: list[str] = []
    for chunk in t.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        for sub in re.split(r"\band\b", chunk, flags=re.IGNORECASE):
            sub = sub.strip(" .")
            if sub:
                parts.append(sub)
    return parts


def parse_symptom_text(text: str, symptoms_list: list[str]) -> dict[str, Any]:
    """
    Returns:
      matched: canonical symptom strings (unique, order preserved)
      unmatched_tokens: raw tokens with no good match
      did_you_mean: [{ "typed": "...", "suggestion": "human readable", "canonical": "snake_case" }]
    """
    keys, key_to_canonical = _build_lookup_keys(symptoms_list)
    unique_keys = list(dict.fromkeys(keys))

    matched: list[str] = []
    seen: set[str] = set()
    unmatched_tokens: list[str] = []
    did_you_mean: list[dict[str, str]] = []

    for phrase in _split_symptom_phrases(text):
        p = _normalize_phrase(phrase)
        underscored = p.replace(" ", "_")

        # Shortcut: common spoken words
        if p in TOKEN_ALIASES:
            # One canonical symptom per user token (avoids double-counting e.g. two fever flags).
            for cand in TOKEN_ALIASES[p]:
                if cand in symptoms_list and cand not in seen:
                    seen.add(cand)
                    matched.append(cand)
                    break
            continue

        # Exact / alias hit
        if underscored in symptoms_list:
            canon = underscored
        elif p in key_to_canonical:
            canon = key_to_canonical[p]
        elif underscored in key_to_canonical:
            canon = key_to_canonical[underscored]
        else:
            # Fuzzy match against all surface keys
            guess = get_close_matches(p, unique_keys, n=1, cutoff=0.72)
            if not guess:
                guess = get_close_matches(underscored, unique_keys, n=1, cutoff=0.72)
            if guess:
                canon = key_to_canonical[guess[0]]
                human = canon.replace("_", " ")
                if p != guess[0] and underscored != canon:
                    did_you_mean.append(
                        {
                            "typed": phrase,
                            "suggestion": human,
                            "canonical": canon,
                        }
                    )
            else:
                unmatched_tokens.append(phrase)
                continue

        if canon not in seen:
            seen.add(canon)
            matched.append(canon)

    return {
        "matched": matched,
        "unmatched_tokens": unmatched_tokens,
        "did_you_mean": did_you_mean,
    }
