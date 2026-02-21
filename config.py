"""
config.py — Central configuration for Cognitive Attendance System.
All paths, thresholds, credentials, and constants live here.
"""

from pathlib import Path
import random

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR       = Path(__file__).parent
MODEL_DIR      = BASE_DIR / "model"
DB_PATH        = BASE_DIR / "attendance.db"
ML_MODEL_PATH  = MODEL_DIR / "ml_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.pkl"

# ── Scoring Thresholds ────────────────────────────────────────────────────────

ENGAGED_THRESHOLD = 75   # score >= this → "Engaged"   → Present
PARTIAL_THRESHOLD = 50   # score >= this → "Partially Engaged" → Present
ML_WEIGHT         = 70   # max ML contribution to final score

# ── UI ────────────────────────────────────────────────────────────────────────

REFRESH_INTERVAL = 5     # seconds between teacher dashboard refreshes

# ── Teacher Credentials (demo) ────────────────────────────────────────────────
# Format: { teacher_id: password }
TEACHER_CREDENTIALS: dict[str, str] = {
    "DEMO": "demo123",
    "T001": "teacher1",
    "T002": "teacher2",
}

# ── Question Bank ─────────────────────────────────────────────────────────────

QUESTION_BANK: dict[str, list[str]] = {
    "recursion": [
        "Explain recursion in one sentence.",
        "What is the role of the base case in recursion?",
        "Why is a base case essential in recursive functions?",
        "How does recursion differ from iteration?",
    ],
    "sorting": [
        "What is the purpose of sorting algorithms?",
        "Explain how Bubble Sort works in one sentence.",
        "Why is time complexity important when choosing a sorting algorithm?",
        "What makes Quick Sort faster than Bubble Sort on average?",
    ],
    "ai": [
        "What is Artificial Intelligence in one sentence?",
        "What is the difference between ML and AI?",
        "Explain supervised learning in one sentence.",
        "What is the role of training data in machine learning?",
    ],
    "oop": [
        "What is the concept of encapsulation in OOP?",
        "Explain inheritance in one sentence.",
        "Why is polymorphism useful in object-oriented design?",
    ],
    "data structures": [
        "What is the difference between a stack and a queue?",
        "Explain linked lists in one sentence.",
        "When would you use a hash map over an array?",
    ],
}


def generate_question(topic: str) -> str:
    """Return a random question for the given topic, or a generic fallback."""
    key = topic.strip().lower()
    if key in QUESTION_BANK:
        return random.choice(QUESTION_BANK[key])
    return f"Explain the concept of '{topic}' in one sentence."
