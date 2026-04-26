"""Thin adapter for API-time misconception detection.

This wraps the simulator detector interface so API routes can call a
single function with plain strings.
"""

from __future__ import annotations

import logging

from ml.simulator.data.item_bank import Distractor, Item
from ml.simulator.misconception.detector import MisconceptionDetector
from ml.simulator.student.profile import StudentProfile

logger = logging.getLogger("axonai")


def _build_stub_profile() -> StudentProfile:
    """Create the minimal student profile shape needed by detector.predict()."""
    return StudentProfile(
        student_id=0,
        true_theta={},
        estimated_theta={},
        bkt_state={},
        elo_rating=0.0,
        recall_half_life={},
        last_retrieval={},
        learning_rate=0.0,
        slip=0.0,
        guess=0.0,
        engagement_decay=0.0,
        response_time_lognorm_params=(0.0, 1.0),
        attempts_history=[],
        misconception_susceptibility={1001: 0.85, 1002: 0.55},
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


def detect_misconception(question_text, wrong_answer, concept_name):
    """Return (misconception_text, confidence) or (None, None).

    This function never raises; failures are logged and converted to a null result.
    """
    try:
        detector = MisconceptionDetector(use_tagged_shortcut=True)
        profile = _build_stub_profile()
        item = _build_stub_item(str(question_text or ""), str(wrong_answer or ""), str(concept_name or ""))

        hint = detector.predict(profile, item)
        if hint is None:
            return (None, None)

        confidence = float(hint.confidence)
        misconception_text = f"misconception_{hint.misconception_id}"
        return (misconception_text, confidence)
    except Exception as exc:
        logger.warning("Misconception detector unavailable: %s", exc)
        return (None, None)
