"""Tests for loop.quiz."""

from __future__ import annotations

import math

import numpy as np
import pytest

from ml.simulator.data.item_bank import Item, ItemBank
from ml.simulator.loop.quiz import select_next_item, simulate_response
from ml.simulator.psychometrics.bkt import BKTState
from ml.simulator.student.profile import StudentProfile


def _profile(theta_by_concept: dict[int, float]) -> StudentProfile:
    return StudentProfile(
        student_id=1,
        true_theta=dict(theta_by_concept),
        estimated_theta={c: (0.0, 1.0) for c in theta_by_concept},
        bkt_state={c: BKTState(p_known=0.2) for c in theta_by_concept},
        elo_rating=1200.0,
        recall_half_life={c: 24.0 for c in theta_by_concept},
        last_retrieval={},
        learning_rate=0.1,
        slip=0.1,
        guess=0.25,
        engagement_decay=0.95,
        response_time_lognorm_params=(math.log(8000.0), 0.3),
        attempts_history=[],
    )


def _bank(items: list[Item]) -> ItemBank:
    return ItemBank(items)


class TestSelectNextItem:
    def test_returns_none_when_no_items(self) -> None:
        bank = _bank([Item(item_id=1, concept_id=99, a=1.0, b=0.0)])
        p = _profile({1: 0.0})
        assert select_next_item(p, bank, concept_id=1) is None

    def test_picks_in_band_item_closest_to_centre(self) -> None:
        # theta = 0.0 with a = 1.0: item b controls P(correct) = sigmoid(-b).
        # b=-0.4 → P≈0.60, b=-1.0 → P≈0.73, b=-2.0 → P≈0.88
        items = [
            Item(item_id=10, concept_id=1, a=1.0, b=-0.4),
            Item(item_id=11, concept_id=1, a=1.0, b=-1.0),
            Item(item_id=12, concept_id=1, a=1.0, b=-2.0),
        ]
        bank = _bank(items)
        p = _profile({1: 0.0})
        picked = select_next_item(p, bank, concept_id=1)
        # ZPD centre = 0.725. b=-1.0 gives ~0.731, closest to centre.
        assert picked.item_id == 11

    def test_falls_back_to_closest_when_none_in_band(self) -> None:
        # All items outside [0.60, 0.85].
        items = [
            Item(item_id=10, concept_id=1, a=1.0, b=5.0),   # P ~ 0.007
            Item(item_id=11, concept_id=1, a=1.0, b=-5.0),  # P ~ 0.993
            Item(item_id=12, concept_id=1, a=1.0, b=3.0),   # P ~ 0.047
        ]
        bank = _bank(items)
        p = _profile({1: 0.0})
        picked = select_next_item(p, bank, concept_id=1)
        # b=-5.0 gives 0.993, closer to 0.85 than the others are to 0.60.
        assert picked is not None
        assert picked.item_id == 11


class TestSimulateResponse:
    def test_very_easy_item_almost_always_correct(self) -> None:
        p = _profile({1: 0.0})
        item = Item(item_id=10, concept_id=1, a=2.0, b=-4.0)  # P very close to 1
        rng = np.random.default_rng(0)
        wins = sum(simulate_response(p, item, rng)[0] for _ in range(200))
        assert wins > 190

    def test_very_hard_item_almost_always_wrong(self) -> None:
        p = _profile({1: 0.0})
        item = Item(item_id=10, concept_id=1, a=2.0, b=4.0)  # P very close to 0
        rng = np.random.default_rng(0)
        wins = sum(simulate_response(p, item, rng)[0] for _ in range(200))
        assert wins < 10

    def test_response_time_positive_and_lognormalish(self) -> None:
        p = _profile({1: 0.0})
        item = Item(item_id=10, concept_id=1, a=1.0, b=0.0)
        rng = np.random.default_rng(0)
        rts = [simulate_response(p, item, rng)[1] for _ in range(200)]
        assert all(rt > 0 for rt in rts)
        # Mean should be in the ballpark of exp(mu) = ~8000.
        assert 4000 < np.mean(rts) < 16000

    def test_deterministic_given_seed(self) -> None:
        p = _profile({1: 0.5})
        item = Item(item_id=10, concept_id=1, a=1.2, b=0.3)
        rng_a = np.random.default_rng(42)
        rng_b = np.random.default_rng(42)
        assert simulate_response(p, item, rng_a) == simulate_response(p, item, rng_b)
