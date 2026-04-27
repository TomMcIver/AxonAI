"""Thin adapter for API-time misconception detection."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from ml.simulator.data.item_bank import Distractor, Item
from ml.simulator.misconception.detector import MisconceptionDetector
from ml.simulator.student.profile import StudentProfile

logger = logging.getLogger("axonai")


def _connect():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        dbname=os.environ.get("DB_NAME", "postgres"),
        connect_timeout=10,
    )


@contextmanager
def _db_cursor():
    conn = _connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
    finally:
        cur.close()
        conn.close()


def _load_student_profile(student_id: int) -> StudentProfile:
    with _db_cursor() as cur:
        cur.execute(
            """
            SELECT overall_engagement_score
            FROM student_learning_profiles
            WHERE student_id = %s
            LIMIT 1
            """,
            (student_id,),
        )
        profile_row = cur.fetchone() or {}

    engagement = float(profile_row.get("overall_engagement_score") or 0.0)
    return StudentProfile(
        student_id=student_id,
        true_theta={},
        estimated_theta={},
        bkt_state={},
        elo_rating=0.0,
        recall_half_life={},
        last_retrieval={},
        learning_rate=0.0,
        slip=0.0,
        guess=0.0,
        engagement_decay=max(0.0, 1.0 - engagement),
        response_time_lognorm_params=(0.0, 1.0),
        attempts_history=[],
        misconception_susceptibility={},
    )


def _build_stub_item(question_text: str, wrong_answer: str, concept_name: str) -> Item:
    """Create a minimal Item carrying distractor text for retrieval proxy mode."""
    option_text = f"Question: {question_text}\nWrong answer: {wrong_answer}\nConcept: {concept_name}"
    return Item(
        item_id=0,
        concept_id=0,
        a=1.0,
        b=0.0,
        distractors=(
            Distractor(option_text=option_text, misconception_id=1001),
            Distractor(
                option_text=f"Alternative wrong path for {concept_name}: {wrong_answer}",
                misconception_id=1002,
            ),
        ),
    )


def _lookup_misconception_text(misconception_id: int) -> str | None:
    with _db_cursor() as cur:
        cur.execute(
            """
            SELECT
                COALESCE(name, misconception_text, description) AS text_value
            FROM misconceptions
            WHERE id = %s
            LIMIT 1
            """,
            (misconception_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    text_value = row.get("text_value")
    return str(text_value) if text_value else None


def detect_misconception(student_id, question_text, wrong_answer, concept_name):
    """Return (misconception_text, confidence) or (None, None).

    This function never raises; failures are logged and converted to a null result.
    """
    try:
        detector = MisconceptionDetector(use_tagged_shortcut=True)
        profile = _load_student_profile(int(student_id))
        item = _build_stub_item(str(question_text or ""), str(wrong_answer or ""), str(concept_name or ""))

        hint = detector.predict(profile, item)
        if hint is None:
            return (None, None)

        confidence = float(hint.confidence)
        misconception_text = _lookup_misconception_text(int(hint.misconception_id))
        return (misconception_text, confidence)
    except Exception as exc:
        logger.warning("Misconception detector unavailable: %s", exc)
        return (None, None)
