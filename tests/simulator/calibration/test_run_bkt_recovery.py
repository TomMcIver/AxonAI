"""Unit tests for the BKT parameter-recovery runner.

Uses hand-built cohorts to verify the simulator honours the generative
model and that `_recover_one` returns the expected shape.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.simulator.calibration.run_bkt_recovery import (
    TOLERANCE,
    _empirical_seq_len,
    _recover_one,
    _simulate_bkt_cohort,
)


def test_simulate_all_known_gives_near_one_correct_rate():
    rng = np.random.default_rng(0)
    df = _simulate_bkt_cohort(
        p_init=1.0,        # everyone starts known
        p_transit=0.0,
        p_slip=0.0,        # never slips
        p_guess=0.0,       # doesn't matter: never in unknown state
        n_students=50,
        seq_len=10,
        skill_id=7,
        rng=rng,
    )
    # With p_slip=0 and everyone known, every response must be correct.
    assert df["correct"].all()
    assert len(df) == 500
    assert set(df["skill_id"]) == {7}
    # start_time must be strictly increasing across the whole frame.
    assert df["start_time"].is_monotonic_increasing


def test_simulate_none_known_respects_guess_rate():
    rng = np.random.default_rng(0)
    df = _simulate_bkt_cohort(
        p_init=0.0,        # nobody starts known
        p_transit=0.0,     # and nobody learns
        p_slip=0.0,
        p_guess=0.25,
        n_students=2000,
        seq_len=5,
        skill_id=9,
        rng=rng,
    )
    rate = df["correct"].mean()
    assert abs(rate - 0.25) < 0.03  # binomial SE ~ 0.004 for n=10k


def test_recover_one_interior_params_recovers_within_tolerance():
    # Interior params, long sequences, large cohort → EM should recover easily.
    row = pd.Series(
        {
            "skill_id": 42,
            "p_init": 0.3,
            "p_transit": 0.15,
            "p_slip": 0.08,
            "p_guess": 0.22,
            "n_students": 500,
            "n_responses": 10_000,
        }
    )
    out = _recover_one(row, seq_len=25, n_students=500, seed=1)
    assert out.skill_id == 42
    assert out.seq_len == 25
    assert out.max_abs_error <= TOLERANCE, (
        f"recovery failed: max_err={out.max_abs_error:.3f}, "
        f"p_init_hat={out.p_init_hat}, p_transit_hat={out.p_transit_hat}, "
        f"p_slip_hat={out.p_slip_hat}, p_guess_hat={out.p_guess_hat}"
    )
    assert out.within_tolerance


def test_empirical_seq_len_rounds_ratio():
    row = pd.Series({"n_students": 100, "n_responses": 250})
    assert _empirical_seq_len(row) == 2  # banker's rounding of 2.5 → 2
    row = pd.Series({"n_students": 100, "n_responses": 251})
    assert _empirical_seq_len(row) == 3


def test_empirical_seq_len_handles_zero_students():
    row = pd.Series({"n_students": 0, "n_responses": 0})
    # Fallback constant; not the 0/0 NaN.
    assert _empirical_seq_len(row) >= 1


def test_simulate_is_seed_deterministic():
    rng_a = np.random.default_rng(7)
    rng_b = np.random.default_rng(7)
    df_a = _simulate_bkt_cohort(
        p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25,
        n_students=10, seq_len=5, skill_id=1, rng=rng_a,
    )
    df_b = _simulate_bkt_cohort(
        p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25,
        n_students=10, seq_len=5, skill_id=1, rng=rng_b,
    )
    pd.testing.assert_frame_equal(df_a, df_b)
