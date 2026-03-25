"""
database.py — All SQLite operations for the Cognitive Learning Analytics System.

Design principles:
  - Every public function opens its own connection and closes it when done.
  - WAL journal mode allows concurrent reads alongside writes.
  - UNIQUE constraint on (session_code, student_name) prevents duplicate submissions.
"""

import sqlite3
import contextlib
import math
from pathlib import Path

import config


@contextlib.contextmanager
def _connect():
    """
    Context manager yielding a committed-and-closed SQLite connection.
    WAL mode enables safe concurrent access between teacher and student apps.
    """
    conn = sqlite3.connect(
        str(config.DB_PATH),
        check_same_thread=False,
        timeout=10,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema ────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they do not already exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_code  TEXT    PRIMARY KEY,
                teacher_id    TEXT    NOT NULL,
                topic         TEXT    NOT NULL,
                question      TEXT    NOT NULL,
                threshold     INTEGER NOT NULL DEFAULT 75,
                created_at    TEXT    NOT NULL,
                is_active     INTEGER NOT NULL DEFAULT 1,
                inference_ai  TEXT
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                session_code     TEXT    NOT NULL,
                student_name     TEXT    NOT NULL,
                response         TEXT    NOT NULL,
                score            REAL    NOT NULL,
                status           TEXT    NOT NULL,
                reason           TEXT    NOT NULL,
                missing_keywords TEXT    NOT NULL DEFAULT '',
                submitted_at     TEXT    NOT NULL,
                plagiarism_rate  REAL    NOT NULL DEFAULT 0.0,
                UNIQUE (session_code, student_name),
                FOREIGN KEY (session_code) REFERENCES sessions(session_code)
            );

            CREATE TABLE IF NOT EXISTS concept_coverage (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                session_code     TEXT    NOT NULL,
                keyword          TEXT    NOT NULL,
                cluster          TEXT    NOT NULL DEFAULT '',
                coverage_ratio   REAL    NOT NULL DEFAULT 0.0,
                gap_index        REAL    NOT NULL DEFAULT 1.0,
                flagged          INTEGER NOT NULL DEFAULT 0,
                UNIQUE (session_code, keyword),
                FOREIGN KEY (session_code) REFERENCES sessions(session_code)
            );
        """)
        # Migrate: add missing_keywords column to older DBs that lack it
        try:
            conn.execute(
                "ALTER TABLE submissions ADD COLUMN missing_keywords TEXT NOT NULL DEFAULT ''"
            )
        except sqlite3.OperationalError:
            pass  # column already exists

        # Migrate: add inference_ai column to older DBs
        try:
            conn.execute(
                "ALTER TABLE sessions ADD COLUMN inference_ai TEXT"
            )
        except sqlite3.OperationalError:
            pass

        # Migrate: add plagiarism_rate column to older DBs
        try:
            conn.execute(
                "ALTER TABLE submissions ADD COLUMN plagiarism_rate REAL NOT NULL DEFAULT 0.0"
            )
        except sqlite3.OperationalError:
            pass


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


def update_session_inference(session_code: str, inference_text: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET inference_ai = ? WHERE session_code = ?",
            (inference_text, session_code),
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
    missing_keywords: str,
    submitted_at: str,
    plagiarism_rate: float = 0.0,
) -> tuple[bool, str]:
    """
    Insert a student submission.
    Returns (True, success_msg) or (False, error_msg) on duplicate.
    """
    try:
        with _connect() as conn:
            conn.execute(
                """INSERT INTO submissions
                   (session_code, student_name, response, score,
                    status, reason, missing_keywords, submitted_at, plagiarism_rate)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_code, student_name, response,
                 score, status, reason, missing_keywords, submitted_at, plagiarism_rate),
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
    """Returns engagement counts plus class-level statistics."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT status, score FROM submissions WHERE session_code = ?",
            (session_code,),
        ).fetchall()

    statuses = [r["status"] for r in rows]
    scores   = [r["score"]  for r in rows]
    total    = len(statuses)
    engaged  = statuses.count("Engaged")
    partial  = statuses.count("Partially Engaged")
    disengaged = statuses.count("Disengaged")
    present  = engaged + partial

    mean_score = round(sum(scores) / total, 2) if total else 0.0
    variance   = sum((s - mean_score) ** 2 for s in scores) / total if total else 0.0
    std_score  = round(math.sqrt(variance), 2)

    return {
        "total":           total,
        "present":         present,
        "engaged":         engaged,
        "partial":         partial,
        "disengaged":      disengaged,
        "engagement_rate": round((present / total) * 100, 1) if total else 0.0,
        "mean_score":      mean_score,
        "std_score":       std_score,
    }


# ── Concept Coverage ──────────────────────────────────────────────────────────

def upsert_concept_coverage(
    session_code: str,
    keyword: str,
    cluster: str,
    coverage_ratio: float,
    gap_index: float,
    flagged: int,
) -> None:
    """Insert or replace coverage record for a (session, keyword) pair."""
    with _connect() as conn:
        conn.execute(
            """INSERT INTO concept_coverage
               (session_code, keyword, cluster, coverage_ratio, gap_index, flagged)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_code, keyword)
               DO UPDATE SET
                   coverage_ratio = excluded.coverage_ratio,
                   gap_index      = excluded.gap_index,
                   flagged        = excluded.flagged""",
            (session_code, keyword, cluster, coverage_ratio, gap_index, flagged),
        )


def get_concept_gaps(session_code: str) -> list[dict]:
    """Return all concept coverage rows for a session, sorted by gap_index desc."""
    with _connect() as conn:
        rows = conn.execute(
            """SELECT keyword, cluster, coverage_ratio, gap_index, flagged
               FROM concept_coverage
               WHERE session_code = ?
               ORDER BY gap_index DESC""",
            (session_code,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Topic Progression (multi-session) ────────────────────────────────────────

def get_topic_progression(teacher_id: str, topic: str) -> list[dict]:
    """
    Return per-session mean scores for a given teacher + topic combination.
    Used to build the line chart of topic mastery progression over time.
    """
    with _connect() as conn:
        rows = conn.execute(
            """SELECT s.session_code, s.created_at,
                      AVG(sub.score) AS mean_score,
                      COUNT(sub.id)  AS student_count
               FROM sessions s
               LEFT JOIN submissions sub ON sub.session_code = s.session_code
               WHERE s.teacher_id = ? AND LOWER(s.topic) = LOWER(?)
               GROUP BY s.session_code
               ORDER BY s.created_at ASC""",
            (teacher_id, topic),
        ).fetchall()
    return [dict(r) for r in rows]
