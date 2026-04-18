"""Tests for the BKT EM fitter.

Strategy: generate sequences from known BKT params, fit, check recovery
within tolerance. Also covers degeneracy clipping, column requirements,
and writer roundtrip.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.simulator.calibration.fit_bkt import (
    _degeneracy_clip,
    _forward_backward,
    fit_bkt,
    write_bkt_params,
    write_fit_report,
)


def _simulate_bkt(
    n_students: int,
    seq_len: int,
    p_init: float,
    p_transit: float,
    p_slip: float,
    p_guess: float,
    seed: int = 0,
) -> list[np.ndarray]:
    """Emit response sequences under the BKT generative model."""
    rng = np.random.default_rng(seed)
    sequences = []
    for _ in range(n_students):
        k = 1 if rng.random() < p_init else 0
        seq = []
        for _ in range(seq_len):
            # Emit
            if k == 1:
                correct = 0 if rng.random() < p_slip else 1
            else:
                correct = 1 if rng.random() < p_guess else 0
            seq.append(correct)
            # Transit (only 0 -> 1).
            if k == 0 and rng.random() < p_transit:
                k = 1
        sequences.append(np.array(seq, dtype=int))
    return sequences


def _sequences_to_df(sequences: list[np.ndarray], skill_id: int = 7) -> pd.DataFrame:
    rows = []
    for user_id, seq in enumerate(sequences):
        for t, correct in enumerate(seq):
            rows.append(
                {
                    "user_id": user_id,
                    "problem_id": t,  # unique per step so we have a valid column
                    "skill_id": skill_id,
                    "correct": bool(correct),
                    "start_time": pd.Timestamp("2024-01-01") + pd.Timedelta(minutes=t),
                }
            )
    return pd.DataFrame(rows)


class TestDegeneracyClip:
    def test_no_change_when_below_threshold(self) -> None:
        s, g = _degeneracy_clip(0.1, 0.2)
        assert s == 0.1 and g == 0.2

    def test_pulls_back_when_exceeding(self) -> None:
        s, g = _degeneracy_clip(0.5, 0.5)
        # With EPS = 0.01, s + g must be <= 0.99.
        assert s + g <= 0.99 + 1e-9


class TestForwardBackward:
    def test_gamma_rows_sum_to_one(self) -> None:
        obs = np.array([1, 0, 1, 1, 0])
        gamma, _, _ = _forward_backward(
            obs, p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25
        )
        np.testing.assert_allclose(gamma.sum(axis=1), 1.0, atol=1e-9)

    def test_log_likelihood_finite(self) -> None:
        obs = np.array([1, 0, 1, 1, 0])
        _, _, ll = _forward_backward(
            obs, p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25
        )
        assert np.isfinite(ll)

    def test_xi_non_negative(self) -> None:
        obs = np.array([0, 0, 1, 1, 1])
        _, xi, _ = _forward_backward(
            obs, p_init=0.2, p_transit=0.3, p_slip=0.1, p_guess=0.2
        )
        assert xi >= 0.0


class TestFitBkt:
    def test_missing_columns_raise(self) -> None:
        with pytest.raises(KeyError):
            fit_bkt(pd.DataFrame({"user_id": [0], "correct": [True]}))

    def test_skill_id_negative_one_excluded(self) -> None:
        seqs = _simulate_bkt(
            n_students=20, seq_len=10,
            p_init=0.2, p_transit=0.15, p_slip=0.1, p_guess=0.2,
            seed=0,
        )
        df = _sequences_to_df(seqs, skill_id=7)
        untagged = _sequences_to_df(seqs[:5], skill_id=-1)
        merged = pd.concat([df, untagged]).reset_index(drop=True)
        params = fit_bkt(merged)
        assert -1 not in set(params["skill_id"])
        assert 7 in set(params["skill_id"])

    def test_result_schema(self) -> None:
        seqs = _simulate_bkt(
            n_students=20, seq_len=10,
            p_init=0.2, p_transit=0.15, p_slip=0.1, p_guess=0.2,
            seed=1,
        )
        df = _sequences_to_df(seqs, skill_id=3)
        params = fit_bkt(df)
        assert set(params.columns) == {
            "skill_id",
            "p_init",
            "p_transit",
            "p_slip",
            "p_guess",
            "converged",
            "n_iter",
            "final_ll",
            "n_students",
            "n_responses",
        }
        row = params.iloc[0]
        assert row["n_students"] == 20
        assert row["n_responses"] == 20 * 10

    def test_degeneracy_constraint_holds(self) -> None:
        seqs = _simulate_bkt(
            n_students=30, seq_len=15,
            p_init=0.3, p_transit=0.2, p_slip=0.15, p_guess=0.25,
            seed=2,
        )
        df = _sequences_to_df(seqs, skill_id=5)
        params = fit_bkt(df)
        row = params.iloc[0]
        assert row["p_slip"] + row["p_guess"] < 1.0

    def test_recovers_low_slip_low_guess_regime(self) -> None:
        # Clean regime: small slip/guess, moderate transit — EM should be in
        # the ballpark of the true params.
        true_slip = 0.08
        true_guess = 0.18
        seqs = _simulate_bkt(
            n_students=80, seq_len=20,
            p_init=0.25, p_transit=0.18,
            p_slip=true_slip, p_guess=true_guess,
            seed=3,
        )
        df = _sequences_to_df(seqs, skill_id=9)
        params = fit_bkt(df)
        row = params.iloc[0]
        # Generous tolerance — JML/EM for BKT is known to be biased, but
        # should at least separate the right regime.
        assert abs(row["p_slip"] - true_slip) < 0.15
        assert abs(row["p_guess"] - true_guess) < 0.2
        # Transit should be noticeably > 0.
        assert row["p_transit"] > 0.02

    def test_multiple_skills(self) -> None:
        frames = []
        for skill_id in [1, 2, 3]:
            seqs = _simulate_bkt(
                n_students=15, seq_len=10,
                p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.2,
                seed=skill_id,
            )
            frames.append(_sequences_to_df(seqs, skill_id=skill_id))
        df = pd.concat(frames).reset_index(drop=True)
        params = fit_bkt(df)
        assert len(params) == 3
        assert list(params["skill_id"]) == [1, 2, 3]


class TestWriters:
    def test_params_roundtrip(self, tmp_path: Path) -> None:
        seqs = _simulate_bkt(
            n_students=10, seq_len=8,
            p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.2,
            seed=0,
        )
        df = _sequences_to_df(seqs, skill_id=11)
        params = fit_bkt(df)
        out = write_bkt_params(params, tmp_path / "bkt.parquet")
        assert out.exists()
        reloaded = pd.read_parquet(out)
        pd.testing.assert_frame_equal(
            params.reset_index(drop=True), reloaded.reset_index(drop=True)
        )

    def test_report_written(self, tmp_path: Path) -> None:
        seqs = _simulate_bkt(
            n_students=10, seq_len=8,
            p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.2,
            seed=0,
        )
        df = _sequences_to_df(seqs, skill_id=11)
        params = fit_bkt(df)
        out = write_fit_report(params, tmp_path / "report.md")
        body = out.read_text()
        assert "# BKT fit report" in body
        assert "Skills fit: 1" in body
