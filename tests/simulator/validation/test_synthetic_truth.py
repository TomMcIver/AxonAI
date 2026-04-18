"""Tests for the synthetic-truth generator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.simulator.validation.synthetic_truth import generate_ground_truth


class TestGenerateGroundTruth:
    def test_shape_matches_args(self) -> None:
        truth = generate_ground_truth(
            n_students=40, n_skills=3, items_per_skill=5, seed=0,
        )
        assert len(truth.theta_true) == 40
        assert len(truth.item_params) == 15
        assert len(truth.bkt_params) == 3
        assert len(truth.responses) == 40 * 15

    def test_schema_matches_calibrator_contract(self) -> None:
        truth = generate_ground_truth(n_students=10, n_skills=2, items_per_skill=3, seed=1)
        required = {"user_id", "problem_id", "correct", "skill_id"}
        assert required.issubset(set(truth.responses.columns))
        assert truth.responses["correct"].dtype == bool

    def test_deterministic_given_seed(self) -> None:
        a = generate_ground_truth(n_students=20, n_skills=2, items_per_skill=4, seed=7)
        b = generate_ground_truth(n_students=20, n_skills=2, items_per_skill=4, seed=7)
        pd.testing.assert_frame_equal(a.responses, b.responses)
        pd.testing.assert_frame_equal(a.item_params, b.item_params)

    def test_bkt_params_obey_degeneracy_bound(self) -> None:
        truth = generate_ground_truth(n_students=10, n_skills=5, items_per_skill=3, seed=2)
        for row in truth.bkt_params.itertuples(index=False):
            assert row.p_slip + row.p_guess < 1.0

    def test_harder_items_lower_correct_rate(self) -> None:
        truth = generate_ground_truth(n_students=400, n_skills=1, items_per_skill=10, seed=3)
        rates = truth.responses.groupby("problem_id")["correct"].mean()
        item_b = truth.item_params.set_index("problem_id")["b"]
        merged = pd.concat([rates.rename("rate"), item_b], axis=1)
        # Pearson correlation of b vs correct-rate should be strongly negative.
        corr = merged["rate"].corr(merged["b"])
        assert corr < -0.5
