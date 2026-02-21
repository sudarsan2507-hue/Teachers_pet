"""
hybrid_engine.py

STRUCTURAL CHANGE ONLY: model loading converted from module-level (import-time)
to a thread-safe lazy initialiser. evaluate_response() is unchanged.

Thread safety: threading.Lock with double-checked locking ensures models are
loaded exactly once even under concurrent student submissions.
"""

import pickle
import threading
from pathlib import Path

from symbolic_engine import symbolic_score  # unchanged import

# ── Private model cache ────────────────────────────────────────────────────────

_model      = None
_vectorizer = None
_lock       = threading.Lock()


def _load_models():
    """
    Load ML models from disk on first call; return cached instances thereafter.
    Double-checked locking prevents redundant loads under concurrency.
    """
    global _model, _vectorizer

    if _model is None:                            # fast path (no lock needed after init)
        with _lock:
            if _model is None:                    # re-check inside lock
                base = Path(__file__).parent
                with open(base / "model" / "ml_model.pkl", "rb") as f:
                    _model = pickle.load(f)
                with open(base / "model" / "vectorizer.pkl", "rb") as f:
                    _vectorizer = pickle.load(f)

    return _model, _vectorizer


# ── Public API (logic unchanged) ──────────────────────────────────────────────

def evaluate_response(response, engagement_threshold=75):
    model, vectorizer = _load_models()

    vec   = vectorizer.transform([response])
    probs = model.predict_proba(vec)

    max_prob = max(probs[0])
    ml_score = max_prob * 70

    sym_score, reasons = symbolic_score(response)

    final_score = ml_score + sym_score

    if final_score >= engagement_threshold:
        status = "Engaged"
    elif final_score >= 50:
        status = "Partially Engaged"
    else:
        status = "Disengaged"

    return round(final_score, 2), status, reasons