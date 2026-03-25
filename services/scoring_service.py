"""
services/scoring_service.py

Thin wrapper around hybrid_engine.evaluate_response.
Accepts topic so the hybrid engine can use topic-specific keyword scoring.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hybrid_engine import evaluate_response  # noqa: E402


def score_response(
    response: str,
    topic: str = "",
    threshold: int = 75,
) -> tuple[float, str, str, str]:
    """
    Score a student response using the hybrid engine.

    Args:
        response:  The student's free-text answer.
        topic:     Session topic — used for keyword-based rule scoring.
        threshold: Engagement threshold.

    Returns:
        (score, status, reason_text, missing_keywords_text)
        - score:                 float 0–100  (Understanding_Percentage)
        - status:                "Engaged" | "Partially Engaged" | "Disengaged"
        - reason_text:           comma-joined explanation string
        - missing_keywords_text: pipe-joined list of absent concept keywords
    """
    score, status, reasons, missing_keywords = evaluate_response(
        response, topic=topic, engagement_threshold=threshold
    )
    reason_text           = ", ".join(reasons)           if reasons           else "Valid response"
    missing_keywords_text = " | ".join(missing_keywords) if missing_keywords else ""
    return score, status, reason_text, missing_keywords_text
