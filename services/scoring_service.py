"""
services/scoring_service.py

Thin wrapper around hybrid_engine.evaluate_response.
Does NOT contain any scoring logic — all scoring happens in hybrid_engine.py.
Converts the reasons list to a display string for storage.
"""

import sys
from pathlib import Path

# Ensure the project root is importable regardless of CWD
sys.path.insert(0, str(Path(__file__).parent.parent))

from hybrid_engine import evaluate_response  # noqa: E402


def score_response(response: str, threshold: int = 75) -> tuple[float, str, str]:
    """
    Score a student response using the hybrid engine.

    Args:
        response:  The student's free-text answer.
        threshold: Engagement threshold (default from config.ENGAGED_THRESHOLD).

    Returns:
        (score, status, reason_text)
        - score:       float, 0–100
        - status:      "Engaged" | "Partially Engaged" | "Disengaged"
        - reason_text: comma-joined explanation string
    """
    score, status, reasons = evaluate_response(response, threshold)
    reason_text = ", ".join(reasons) if reasons else "Valid response"
    return score, status, reason_text
