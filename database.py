"""
database.py — All SQLite operations for the Cognitive Attendance System.

Design principles:
  - Every public function opens its own connection and closes it when done.
  - WAL journal mode allows concurrent reads alongside writes.
  - The UNIQUE constraint on (session_code, student_name) prevents duplicates
    at the database level; duplicate inserts raise sqlite3.IntegrityError.
"""

import sqlite3
import contextlib
from pathlib import Path

import config


@contextlib.contextmanager
def _connect():
    """
    Context manager that yields a committed-and-closed SQLite connection.
    Uses WAL mode for safe concurrent access between teacher and student apps.
    """
    conn = sqlite3.connect(
        str(config.DB_PATH),
        check_same_thread=False,
        timeout=10,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safe concurrent readers + one writer
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema ─────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables if they do not already exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_code  TEXT    PRIMARY KEY,
                teacher_id    TEXT    NOT NULL,
                topic         TEXT    NOT NULL,
                question      TEXT    NOT NULL,
                threshold     INTEGER NOT NULL DEFAULT 75,
                created_at    TEXT    NOT NULL,
                is_active     INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                session_code  TEXT    NOT NULL,
                student_name  TEXT    NOT NULL,
                response      TEXT    NOT NULL,
                score         REAL    NOT NULL,
                status        TEXT    NOT NULL,
                reason        TEXT    NOT NULL,
                submitted_at  TEXT    NOT NULL,
                UNIQUE (session_code, student_name),
                FOREIGN KEY (session_code) REFERENCES sessions(session_code)
            );
        """)


# ── Sessions ──────────────────────────────────────────────────────────────────

def session_exists(code: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE session_code = ?", (code,)
        ).fetchone()
    return row is not None


def create_session(
    session_code: str,
    teacher_id: str,
    topic: str,
    question: str,
    threshold: int,
    created_at: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO sessions
               (session_code, teacher_id, topic, question, threshold, created_at, is_active)
               VALUES (?, ?, ?, ?, ?, ?, 1)""",
            (session_code, teacher_id, topic, question, threshold, created_at),
        )


def get_session(session_code: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_code = ?", (session_code,)
        ).fetchone()
    return dict(row) if row else None


def deactivate_session(session_code: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET is_active = 0 WHERE session_code = ?",
            (session_code,),
        )


def get_teacher_sessions(teacher_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE teacher_id = ? ORDER BY created_at DESC",
            (teacher_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Submissions ───────────────────────────────────────────────────────────────

def insert_submission(
    session_code: str,
    student_name: str,
    response: str,
    score: float,
    status: str,
    reason: str,
    submitted_at: str,
) -> tuple[bool, str]:
    """
    Insert a student submission.
    Returns (True, success_msg) or (False, error_msg).
    The UNIQUE constraint on (session_code, student_name) raises IntegrityError
    on duplicate submission, which is caught and returned as a clean message.
    """
    try:
        with _connect() as conn:
            conn.execute(
                """INSERT INTO submissions
                   (session_code, student_name, response, score,
                    status, reason, submitted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_code, student_name, response,
                 score, status, reason, submitted_at),
            )
        return True, "Response submitted successfully."
    except sqlite3.IntegrityError:
        return False, "Already submitted. Each student may submit only once per session."


def get_submissions(session_code: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """SELECT * FROM submissions
               WHERE session_code = ?
               ORDER BY submitted_at""",
            (session_code,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_session_summary(session_code: str) -> dict:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT status FROM submissions WHERE session_code = ?",
            (session_code,),
        ).fetchall()
    statuses = [r["status"] for r in rows]
    total    = len(statuses)
    engaged  = statuses.count("Engaged")
    partial  = statuses.count("Partially Engaged")
    absent   = statuses.count("Disengaged")
    present  = engaged + partial
    rate     = round((present / total) * 100, 1) if total else 0.0
    return {
        "total":           total,
        "present":         present,
        "absent":          absent,
        "engaged":         engaged,
        "partial":         partial,
        "disengaged":      absent,
        "engagement_rate": rate,
    }
