"""
services/session_service.py

Orchestrates attendance session lifecycle and student submission flow.
All persistence is delegated to database.py.
All scoring is delegated to scoring_service.py (→ hybrid_engine).
"""

import random
import string
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import database
from services.scoring_service import score_response


# ── Session Code Generation ────────────────────────────────────────────────────

def _random_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def generate_session_code() -> str:
    """
    Generate a unique 6-character alphanumeric session code.
    Loops until a code not already in the database is found,
    preventing collisions even under concurrent session creation.
    """
    while True:
        code = _random_code()
        if not database.session_exists(code):
            return code


# ── Session CRUD ───────────────────────────────────────────────────────────────

def create_session(
    teacher_id: str,
    topic: str,
    question: str,
    threshold: int = 75,
) -> str:
    """Create a new attendance session and return its session code."""
    code = generate_session_code()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    database.create_session(code, teacher_id, topic, question, threshold, now)
    return code


def get_session(session_code: str) -> dict | None:
    return database.get_session(session_code)


def close_session(session_code: str) -> None:
    database.deactivate_session(session_code)


def get_teacher_sessions(teacher_id: str) -> list[dict]:
    return database.get_teacher_sessions(teacher_id)


# ── Student Submission Flow ────────────────────────────────────────────────────

def submit_student_response(
    session_code: str,
    student_name: str,
    response: str,
    threshold: int = 75,
) -> tuple[bool, str, float, str, str]:
    """
    Score the student's response and persist it.

    Returns:
        (success, message, score, status, reason)
        - success: False if duplicate submission detected by DB constraint
    """
    score, status, reason = score_response(response, threshold)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success, message = database.insert_submission(
        session_code, student_name, response, score, status, reason, now
    )
    return success, message, score, status, reason


def get_submissions(session_code: str) -> list[dict]:
    return database.get_submissions(session_code)


def get_session_summary(session_code: str) -> dict:
    return database.get_session_summary(session_code)
