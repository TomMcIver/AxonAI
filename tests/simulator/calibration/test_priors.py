"""Tests for derive_priors.

Build simple theta_estimates and bkt_params frames with hand-known
statistics, then check that the derived priors match closed-form values.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.simulator.calibration.priors import (
    _fit_lognormal,
    derive_priors,
    load_priors,
    write_priors,
)


@pytest.fixture
def theta_estimates() -> pd.DataFrame:
    # Symmetric around 0 so median is exactly 0.
    return pd.DataFrame({"user_id": range(9), "theta": np.linspace(-2.0, 2.0, 9)})


@pytest.fixture
def bkt_params() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"skill_id": 1, "p_slip": 0.1, "p_guess": 0.2, "p_transit": 0.1, "p_init": 0.2},
            {"skill_id": 2, "p_slip": 0.2, "p_guess": 0.3, "p_transit": 0.2, "p_init": 0.3},
            {"skill_id": 3, "p_slip": 0.3, "p_guess": 0.4, "p_transit": 0.05, "p_init": 0.1},
        ]
    )


class TestFitLognormal:
    def test_matches_log_moments(self) -> None:
        # log-values [log 1, log e, log e^2] = [0, 1, 2]; mean=1, std=1.
        values = np.array([1.0, math.e, math.e**2])
        res = _fit_lognormal(values)
        assert res["mu"] == pytest.approx(1.0)
        assert res["sigma"] == pytest.approx(1.0)

    def test_ignores_non_positive(self) -> None:
        values = np.array([-1.0, 0.0, 1.0, math.e])
        res = _fit_lognormal(values)
        # Survivors are [1, e] → log-values [0, 1] → mean 0.5, std(ddof=1) = sqrt(0.5).
        assert res["mu"] == pytest.approx(0.5)
        assert res["sigma"] == pytest.approx(math.sqrt(0.5))

    def test_zero_pair_when_too_few_positives(self) -> None:
        assert _fit_lognormal(np.array([-1.0, 0.0])) == {"mu": 0.0, "sigma": 0.0}


class TestDerivePriors:
    def test_theta_stats(self, theta_estimates, bkt_params) -> None:
        p = derive_priors(theta_estimates, bkt_params)
        assert p["theta_percentiles"][50] == pytest.approx(0.0)
        assert p["theta_mean"] == pytest.approx(0.0)
        # std(ddof=1) of linspace(-2,2,9)
        expected_std = float(theta_estimates["theta"].std(ddof=1))
        assert p["theta_std"] == pytest.approx(expected_std)

    def test_slip_guess_means(self, theta_estimates, bkt_params) -> None:
        p = derive_priors(theta_estimates, bkt_params)
        assert p["slip_prior"]["mean"] == pytest.approx(0.2)   # (0.1+0.2+0.3)/3
        assert p["guess_prior"]["mean"] == pytest.approx(0.3)  # (0.2+0.3+0.4)/3

    def test_learning_rate_lognorm_from_transits(self, theta_estimates, bkt_params) -> None:
        p = derive_priors(theta_estimates, bkt_params)
        expected = _fit_lognormal(bkt_params["p_transit"].to_numpy(dtype=float))
        assert p["learning_rate_lognorm"]["mu"] == pytest.approx(expected["mu"])
        assert p["learning_rate_lognorm"]["sigma"] == pytest.approx(expected["sigma"])

    def test_response_time_lognorm_none_when_absent(self, theta_estimates, bkt_params) -> None:
        p = derive_priors(theta_estimates, bkt_params)
        assert p["response_time_lognorm"] is None

    def test_response_time_lognorm_fit_when_present(self, theta_estimates, bkt_params) -> None:
        responses = pd.DataFrame(
            {"ms_first_response": [1000.0, math.e * 1000.0, (math.e**2) * 1000.0]}
        )
        p = derive_priors(theta_estimates, bkt_params, responses_df=responses)
        assert p["response_time_lognorm"] is not None
        # mean of [log(1000), log(1000 e), log(1000 e^2)] = log(1000) + 1.
        assert p["response_time_lognorm"]["mu"] == pytest.approx(math.log(1000.0) + 1.0)

    def test_fallback_when_bkt_empty(self, theta_estimates) -> None:
        p = derive_priors(theta_estimates, pd.DataFrame())
        assert p["slip_prior"]["mean"] == pytest.approx(0.1)
        assert p["guess_prior"]["mean"] == pytest.approx(0.25)
        assert p["learning_rate_lognorm"]["mu"] == pytest.approx(math.log(0.1))

    def test_missing_theta_column_raises(self, bkt_params) -> None:
        with pytest.raises(KeyError):
            derive_priors(pd.DataFrame({"user_id": [0]}), bkt_params)

    def test_all_percentiles_present(self, theta_estimates, bkt_params) -> None:
        p = derive_priors(theta_estimates, bkt_params)
        assert set(p["theta_percentiles"].keys()) == {5, 10, 25, 50, 75, 90, 95}


class TestWriteLoad:
    def test_roundtrip(self, theta_estimates, bkt_params, tmp_path: Path) -> None:
        p = derive_priors(theta_estimates, bkt_params)
        out = write_priors(p, tmp_path / "priors.json")
        assert out.exists()
        reloaded = load_priors(out)
        # JSON keys come back as strings.
        reloaded["theta_percentiles"] = {
            int(k): v for k, v in reloaded["theta_percentiles"].items()
        }
        assert reloaded == p

    def test_file_is_sorted_json(self, theta_estimates, bkt_params, tmp_path: Path) -> None:
        p = derive_priors(theta_estimates, bkt_params)
        out = write_priors(p, tmp_path / "priors.json")
        data = json.loads(out.read_text())
        # sort_keys=True → keys on disk must be sorted lexicographically.
        assert list(data.keys()) == sorted(data.keys())
