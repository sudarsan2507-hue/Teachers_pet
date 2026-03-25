"""
config.py — Central configuration for Cognitive Learning Analytics System.
All paths, thresholds, credentials, scoring constants, and keyword clusters live here.
"""

from pathlib import Path
import random
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"Failed to initialize Groq client: {e}")
    groq_client = None

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent
MODEL_DIR       = BASE_DIR / "model"
DB_PATH         = BASE_DIR / "attendance.db"
ML_MODEL_PATH   = MODEL_DIR / "ml_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.pkl"

# ── Hybrid Scoring Constants ──────────────────────────────────────────────────
# Score_final = ALPHA * Score_ML + BETA * Score_rule   (ALPHA + BETA = 1, ALPHA > BETA)
# Score_ML  is on scale 0–70  (max_prob * 70)
# Score_rule is on scale 0–30 (rule engine scaled to RULE_MAX)

ALPHA    = 0.70   # ML component weight
BETA     = 0.30   # Rule-based component weight
RULE_MAX = 30     # Max points the rule engine can contribute

# Rule-based sub-weights (must sum to 1.0)
W1_KEYWORD  = 0.40   # Keyword coverage ratio
W2_CLUSTER  = 0.30   # Concept cluster coverage
W3_LENGTH   = 0.20   # Normalized length factor
W4_PENALTY  = 0.10   # Off-topic / uncertainty penalty scalar

TARGET_WORD_COUNT = 20  # Word count at which L = 1.0

# ── Understanding Thresholds ──────────────────────────────────────────────────

ENGAGED_THRESHOLD = 75   # Understanding % >= this → "Engaged"
PARTIAL_THRESHOLD = 50   # Understanding % >= this → "Partially Engaged"
GAP_THRESHOLD     = 0.60  # Gap_Index above this → concept flagged for reinforcement

# ── UI ────────────────────────────────────────────────────────────────────────

REFRESH_INTERVAL = 5     # seconds between teacher dashboard auto-refresh

# ── Teacher Credentials (demo) ────────────────────────────────────────────────

TEACHER_CREDENTIALS: dict[str, str] = {
    "DEMO": "demo123",
    "T001": "teacher1",
    "T002": "teacher2",
}

# ── Concept Keywords & Clusters per Topic ─────────────────────────────────────
# Each topic maps to a list of (cluster_name, [keywords]) tuples.
# K = fraction of all keywords present in the response.
# C = fraction of clusters with at least one keyword hit.

CONCEPT_KEYWORDS: dict[str, list[tuple[str, list[str]]]] = {
    "recursion": [
        ("definition",   ["recursion", "recursive", "itself", "calls itself"]),
        ("base case",    ["base case", "base", "stopping condition", "termination"]),
        ("stack",        ["stack", "call stack", "stack overflow", "frame"]),
        ("comparison",   ["iteration", "loop", "iterative", "vs loop"]),
    ],
    "sorting": [
        ("purpose",      ["sort", "sorting", "order", "arrange"]),
        ("algorithms",   ["bubble sort", "quick sort", "merge sort", "insertion sort"]),
        ("complexity",   ["time complexity", "big o", "o(n)", "efficiency"]),
        ("mechanism",    ["swap", "partition", "divide", "pivot", "compare"]),
    ],
    "ai": [
        ("definition",   ["artificial intelligence", "ai", "intelligence", "machine"]),
        ("ml vs ai",     ["machine learning", "ml", "subset", "deeper learning"]),
        ("learning",     ["supervised", "unsupervised", "training", "learning"]),
        ("data",         ["training data", "dataset", "data", "features", "labels"]),
    ],
    "oop": [
        ("encapsulation", ["encapsulation", "private", "hidden", "data hiding"]),
        ("inheritance",   ["inheritance", "inherit", "parent", "child", "extends"]),
        ("polymorphism",  ["polymorphism", "override", "overload", "many forms"]),
        ("abstraction",   ["abstraction", "interface", "abstract", "class"]),
    ],
    "data structures": [
        ("stack vs queue", ["stack", "queue", "lifo", "fifo", "last in"]),
        ("linked list",    ["linked list", "node", "pointer", "next", "chain"]),
        ("hash map",       ["hash map", "hashmap", "hash table", "key", "dictionary"]),
        ("array",          ["array", "index", "random access", "contiguous"]),
    ],
}

# Off-topic / uncertainty phrases that trigger the penalty (P)
PENALTY_PHRASES: list[str] = [
    "i don't know", "dont know", "not sure", "no idea",
    "i have no idea", "idk", "don't understand",
]


def get_topic_clusters(topic: str) -> list[tuple[str, list[str]]]:
    """Return cluster list for the topic, falling back to an empty list."""
    return CONCEPT_KEYWORDS.get(topic.strip().lower(), [])


def get_all_keywords(topic: str) -> list[str]:
    """Flat list of all expected keywords for a topic."""
    keywords = []
    for _, kws in get_topic_clusters(topic):
        keywords.extend(kws)
    return keywords


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
    
    if groq_client:
        try:
            prompt = (
                f"Generate a single, clear, conceptual question suitable for computer science students to test their understanding of the topic: '{topic}'.\n"
                "Rules:\n"
                "1. The question must be technically accurate and self-consistent.\n"
                "2. Do not include introductory text, quotes, or numbering.\n"
                "3. Output ONLY the question text.\n"
                "4. Keep it concise (maximum 30 words)."
            )
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a computer science professor writing a short attendance question."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_completion_tokens=50,
            )
            return chat_completion.choices[0].message.content.strip().strip('"')
        except Exception as e:
            print(f"Groq API question generation failed: {e}")

    if key in QUESTION_BANK:
        return random.choice(QUESTION_BANK[key])
    return f"Explain the concept of '{topic}' in one sentence."
