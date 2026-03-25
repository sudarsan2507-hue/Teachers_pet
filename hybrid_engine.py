"""
hybrid_engine.py — Hybrid Understanding Scoring Engine.

Fusion formula:
    Score_final = ALPHA * Score_ML + BETA * Score_rule
    (ALPHA=0.70, BETA=0.30, ALPHA + BETA = 1, ALPHA > BETA)

Score_ML   = max(predict_proba) × 70        → scale 0–70
Score_rule = symbolic_score(...)             → scale 0–30
Score_final is already on a 0–100 scale (Understanding_Percentage).

Thread safety: threading.Lock with double-checked locking ensures models
are loaded exactly once, even under concurrent student submissions.
"""

import pickle
import threading
from pathlib import Path

import config
from symbolic_engine import symbolic_score

# ── Private model cache ───────────────────────────────────────────────────────

_model      = None
_vectorizer = None
_lock       = threading.Lock()


def _load_models():
    """
    Load ML models on first call; return cached instances thereafter.
    Double-checked locking prevents redundant loads under concurrency.
    """
    global _model, _vectorizer

    if _model is None:                         # fast path — no lock after init
        with _lock:
            if _model is None:                 # re-check inside lock
                base = Path(__file__).parent
                with open(base / "model" / "ml_model.pkl", "rb") as f:
                    _model = pickle.load(f)
                with open(base / "model" / "vectorizer.pkl", "rb") as f:
                    _vectorizer = pickle.load(f)

    return _model, _vectorizer


# ── Public API ────────────────────────────────────────────────────────────────

def evaluate_response(
    response: str,
    topic: str = "",
    engagement_threshold: int = None,
) -> tuple[float, str, list[str], list[str]]:
    """
    Score a student's free-text response using the hybrid engine.

    Args:
        response:             Student response text.
        topic:                Session topic (for keyword-based rule scoring).
        engagement_threshold: Understanding % above which status = "Engaged".
                              Defaults to config.ENGAGED_THRESHOLD.

    Returns:
        (score, status, reasons, missing_keywords)
        - score:            float 0–100  (Understanding_Percentage)
        - status:           "Engaged" | "Partially Engaged" | "Disengaged"
        - reasons:          list of human-readable scoring signals
        - missing_keywords: concept keywords absent from the response
    """
    if engagement_threshold is None:
        engagement_threshold = config.ENGAGED_THRESHOLD

    # ── ML component ─────────────────────────────────────────────────────────
    model, vectorizer = _load_models()
    vec       = vectorizer.transform([response])
    probs     = model.predict_proba(vec)
    max_prob  = float(max(probs[0]))
    score_ml  = max_prob * 70          # Scale: 0–70

    # ── Rule-based component ─────────────────────────────────────────────────
    score_rule, reasons, missing_keywords = symbolic_score(response, topic)
    # score_rule is already on 0–30 scale (RULE_MAX=30)

    # ── Hybrid fusion ────────────────────────────────────────────────────────
    # Score_final = ALPHA * Score_ML + BETA * Score_rule
    # Both components are already on compatible scales that sum to 100 at max:
    #   max(Score_ML) = 70,  max(Score_rule) = 30
    #   ALPHA * 70 + BETA * 30 = 0.70*70 + 0.30*30 = 49 + 9 = 58  (conservative)
    # We normalise by re-scaling so that a perfect response → 100:
    max_possible = config.ALPHA * 70 + config.BETA * config.RULE_MAX
    raw_final    = config.ALPHA * score_ml + config.BETA * score_rule
    score_final  = (raw_final / max_possible) * 100 if max_possible > 0 else 0.0
    score_final  = round(min(score_final, 100.0), 2)

    # ── Engagement classification ────────────────────────────────────────────
    if score_final >= engagement_threshold:
        status = "Engaged"
    elif score_final >= config.PARTIAL_THRESHOLD:
        status = "Partially Engaged"
    else:
        status = "Disengaged"

    return score_final, status, reasons, missing_keywords