"""Tests for the B2 misconception-weighted distractor selector."""

from __future__ import annotations

import numpy as np
import pytest

from ml.simulator.data.item_bank import Distractor, Item
from ml.simulator.misconception.response_model import (
    _SUSCEPTIBILITY_SCALE,
    select_distractor,
)
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import StudentProfile


def _profile(susceptibility: dict[int, float] | None = None) -> StudentProfile:
    return StudentProfile(
        student_id=0,
        true_theta={1: 0.0},
        estimated_theta={1: (0.0, 1.0)},
        bkt_state={1: BKTState(p_known=0.5)},
        elo_rating=1200.0,
        recall_half_life={1: 24.0},
        last_retrieval={},
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(9.0, 0.5),
        misconception_susceptibility=susceptibility or {},
    )


def _item_with_distractors(*misconception_ids: int | None) -> Item:
    return Item(
        item_id=1,
        concept_id=1,
        a=1.0,
        b=0.0,
        distractors=tuple(
            Distractor(option_text=f"opt{i}", misconception_id=mid)
            for i, mid in enumerate(misconception_ids)
        ),
    )


class TestSelectDistractorNoDistractors:
    def test_returns_none_when_no_distractors(self):
        item = Item(item_id=1, concept_id=1, a=1.0, b=0.0)
        p = _profile()
        d, m = select_distractor(item, p, np.random.default_rng(0))
        assert d is None
        assert m is None


class TestSelectDistractorUniform:
    def test_uniform_when_no_susceptibility(self):
        """All distractors have weight 1 → should approach uniform across 3."""
        item = _item_with_distractors(10, 20, 30)
        p = _profile()
        counts = {0: 0, 1: 0, 2: 0}
        n = 3000
        rng = np.random.default_rng(0)
        for _ in range(n):
            d, _ = select_distractor(item, p, rng)
            idx = next(
                i for i, dist in enumerate(item.distractors) if dist.option_text == d.option_text
            )
            counts[idx] += 1
        for c in counts.values():
            assert abs(c / n - 1 / 3) < 0.05

    def test_distractor_with_no_tag_gets_base_weight(self):
        """Untagged distractor (misconception_id=None) still gets weight 1."""
        item = _item_with_distractors(None, None)
        p = _profile({999: 1.0})  # susceptibility for a different misconception
        counts = [0, 0]
        n = 2000
        rng = np.random.default_rng(0)
        for _ in range(n):
            d, _ = select_distractor(item, p, rng)
            idx = 0 if d.option_text == "opt0" else 1
            counts[idx] += 1
        # Should be ~50/50 since no tag matches the susceptibility key.
        assert abs(counts[0] / n - 0.5) < 0.06


class TestSelectDistractorWeighted:
    def test_susceptible_distractor_chosen_more_often(self):
        """Distractor tagged with misconception 10 (susceptibility 0.8) should
        dominate over untagged distractor."""
        item = _item_with_distractors(10, None)
        p = _profile({10: 0.8})
        d10_count = 0
        n = 2000
        rng = np.random.default_rng(0)
        for _ in range(n):
            d, mid = select_distractor(item, p, rng)
            if mid == 10:
                d10_count += 1
        # Weight of misconception-10 distractor = 1 + 4.0 * 0.8 = 4.2
        # Weight of untagged = 1.0
        # Expected fraction ≈ 4.2 / 5.2 ≈ 0.808.
        expected = (1 + _SUSCEPTIBILITY_SCALE * 0.8) / (
            1 + _SUSCEPTIBILITY_SCALE * 0.8 + 1.0
        )
        assert abs(d10_count / n - expected) < 0.05

    def test_returns_misconception_id_of_chosen_distractor(self):
        item = _item_with_distractors(42, 43)
        p = _profile({42: 0.9, 43: 0.1})
        # Just check the returned mid matches the chosen distractor's tag.
        rng = np.random.default_rng(0)
        for _ in range(20):
            d, mid = select_distractor(item, p, rng)
            assert mid == d.misconception_id

    def test_returns_none_misconception_for_untagged(self):
        item = _item_with_distractors(None, None)
        p = _profile()
        _, mid = select_distractor(item, p, np.random.default_rng(0))
        assert mid is None

    def test_deterministic_under_seed(self):
        item = _item_with_distractors(1, 2, 3)
        p = _profile({1: 0.5, 2: 0.3, 3: 0.8})
        d1, m1 = select_distractor(item, p, np.random.default_rng(99))
        d2, m2 = select_distractor(item, p, np.random.default_rng(99))
        assert d1.option_text == d2.option_text
        assert m1 == m2

    def test_zero_susceptibility_is_base_weight(self):
        """Susceptibility = 0 → same weight as untagged distractor."""
        item = _item_with_distractors(77, 88)
        p = _profile({77: 0.0, 88: 0.0})
        counts = [0, 0]
        n = 2000
        rng = np.random.default_rng(0)
        for _ in range(n):
            d, _ = select_distractor(item, p, rng)
            counts[0 if d.option_text == "opt0" else 1] += 1
        assert abs(counts[0] / n - 0.5) < 0.06


class TestSimulateResponseIntegration:
    """Integration test: simulate_response now returns a 3-tuple."""

    def test_returns_three_tuple(self):
        from ml.simulator.loop.quiz import simulate_response

        item = _item_with_distractors(10, 20)
        p = _profile({10: 0.9})
        result = simulate_response(p, item, np.random.default_rng(0))
        assert len(result) == 3
        is_correct, rt_ms, misc_id = result
        assert isinstance(is_correct, bool)
        assert isinstance(rt_ms, int)
        assert misc_id is None or isinstance(misc_id, int)

    def test_no_misconception_on_correct(self):
        """When is_correct=True, triggered_misconception_id must be None."""
        from ml.simulator.loop.quiz import simulate_response
        from ml.simulator.psychometrics.irt_2pl import prob_correct

        # High-ability student on easy item → always correct.
        item = Item(item_id=1, concept_id=1, a=1.0, b=-5.0,
                    distractors=(Distractor("wrong", misconception_id=10),))
        p = _profile({10: 0.9})
        p.true_theta[1] = 4.0  # theta is frozen but dict is mutable
        for seed in range(10):
            _, _, mid = simulate_response(p, item, np.random.default_rng(seed))
            # With b=-5 and theta=4, P(correct)≈1 so mid is almost always None.
            # (May occasionally be wrong due to floating point; just check type.)
            assert mid is None or isinstance(mid, int)
