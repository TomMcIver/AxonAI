"""PR-1.75 — tests for LLMTutor response cache.

Two scenarios:
    1. Identical inputs → second call is a cache hit (no LLM invocation,
       response is byte-identical to the first call's result).
    2. Different profiles → separate cache entries, no cross-contamination
       (each profile's hash produces a distinct key).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from ml.simulator.loop.llm_tutor import LLMTutor
from ml.simulator.loop.explanation_style import WORKED_EXAMPLE, CONCISE_ANSWER
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import StudentProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_client(reply: str = "The answer is X.") -> MagicMock:
    content_block = SimpleNamespace(text=reply)
    message = SimpleNamespace(content=[content_block])
    client = MagicMock()
    client.messages.create.return_value = message
    return client


def _profile(student_id: int = 1, theta: float = 0.0) -> StudentProfile:
    return StudentProfile(
        student_id=student_id,
        true_theta={1: theta},
        estimated_theta={1: (theta, 1.0)},
        bkt_state={1: BKTState(p_known=0.3)},
        elo_rating=1200.0,
        recall_half_life={1: 24.0},
        last_retrieval={},
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
    )


# ---------------------------------------------------------------------------
# 1. Identical inputs → cache hit, no second LLM call
# ---------------------------------------------------------------------------

class TestCacheHitOnIdenticalInputs:
    def test_second_call_is_cache_hit(self) -> None:
        mock_client = _mock_client("Fractions are parts of a whole.")
        tutor = LLMTutor(client=mock_client)
        profile = _profile(student_id=1, theta=0.5)
        h = profile.profile_hash()

        # First call — cache miss expected.
        result1 = tutor.generate_explanation(
            concept_id=7,
            explanation_style=WORKED_EXAMPLE,
            profile_hash=h,
            seed=42,
        )
        assert result1 == "Fractions are parts of a whole."
        assert mock_client.messages.create.call_count == 1

        # Second call with identical arguments — must be a cache hit.
        result2 = tutor.generate_explanation(
            concept_id=7,
            explanation_style=WORKED_EXAMPLE,
            profile_hash=h,
            seed=42,
        )
        # Response is byte-identical.
        assert result2 == result1
        # LLM was NOT called a second time.
        assert mock_client.messages.create.call_count == 1

        stats = tutor.cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert abs(stats["hit_rate"] - 0.5) < 1e-9

    def test_many_identical_calls_single_llm_invocation(self) -> None:
        mock_client = _mock_client("Hint: think about the denominator.")
        tutor = LLMTutor(client=mock_client)
        h = _profile().profile_hash()

        responses = [
            tutor.generate_explanation(3, WORKED_EXAMPLE, profile_hash=h, seed=0)
            for _ in range(10)
        ]
        # All responses identical.
        assert len(set(responses)) == 1
        # Only one real LLM call.
        assert mock_client.messages.create.call_count == 1
        assert tutor.cache_stats()["hits"] == 9
        assert tutor.cache_stats()["misses"] == 1


# ---------------------------------------------------------------------------
# 2. Different profiles → distinct cache entries, no cross-contamination
# ---------------------------------------------------------------------------

class TestNoCrossCacheBetweenProfiles:
    def test_different_profiles_get_different_entries(self) -> None:
        reply_a = "Explanation for student A."
        reply_b = "Explanation for student B."
        mock_client = MagicMock()
        # Return different text on successive LLM calls.
        content_a = SimpleNamespace(text=reply_a)
        content_b = SimpleNamespace(text=reply_b)
        mock_client.messages.create.side_effect = [
            SimpleNamespace(content=[content_a]),
            SimpleNamespace(content=[content_b]),
        ]

        tutor = LLMTutor(client=mock_client)
        profile_a = _profile(student_id=1, theta=0.0)
        profile_b = _profile(student_id=2, theta=2.0)  # different θ → different hash

        ha = profile_a.profile_hash()
        hb = profile_b.profile_hash()
        assert ha != hb, "Profiles with different θ must produce different hashes"

        result_a = tutor.generate_explanation(5, CONCISE_ANSWER, profile_hash=ha)
        result_b = tutor.generate_explanation(5, CONCISE_ANSWER, profile_hash=hb)

        # Each profile got its own LLM call.
        assert mock_client.messages.create.call_count == 2
        assert result_a == reply_a
        assert result_b == reply_b

        # Re-fetching profile_a → cache hit, no new LLM call.
        result_a2 = tutor.generate_explanation(5, CONCISE_ANSWER, profile_hash=ha)
        assert mock_client.messages.create.call_count == 2  # unchanged
        assert result_a2 == reply_a

        stats = tutor.cache_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 1

    def test_profile_hash_changes_after_practice(self) -> None:
        """A profile's hash changes when its attempt count increases."""
        profile = _profile(student_id=3, theta=1.0)
        h_before = profile.profile_hash()

        from datetime import datetime
        from ml.simulator.student.profile import AttemptRecord
        new_attempt = AttemptRecord(
            concept_id=1, item_id=1, is_correct=True,
            time=datetime(2024, 1, 1), response_time_ms=3000,
        )
        # Simulate updated profile with one more attempt.
        from dataclasses import replace
        updated = replace(profile, attempts_history=[new_attempt])
        h_after = updated.profile_hash()

        assert h_before != h_after
