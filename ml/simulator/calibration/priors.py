"""Derive student-trait priors from calibrated artefacts + raw data.

Output shape (written to data/processed/student_priors.json):

    {
        "theta_percentiles": {p: v for p in [5, 10, 25, 50, 75, 90, 95]},
        "theta_mean": float,
        "theta_std": float,
        "slip_prior": {"mean": float, "std": float},
        "guess_prior": {"mean": float, "std": float},
        "learning_rate_lognorm": {"mu": float, "sigma": float},
        "response_time_lognorm": {"mu": float, "sigma": float} | null,
    }

Student-side stats are derived from the fit_2pl theta_estimates frame.
Slip/guess priors from the fit_bkt frame. Learning-rate lognorm is fit
from the per-skill p_transit distribution. Response time lognorm is fit
from `ms_first_response` on the raw responses if the column is present.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Percentiles reported in the priors file. 5/95 bound the wings; 25/75
# form the IQR; 50 is the median. Spec § config.py eventually references.
_THETA_PERCENTILES = (5, 10, 25, 50, 75, 90, 95)


def _fit_lognormal(values: np.ndarray) -> dict:
    """Return (mu, sigma) for a log-normal fit via log moments.

    Drops non-positive values; returns zeros if fewer than two survive.
    """
    pos = values[values > 0]
    if len(pos) < 2:
        return {"mu": 0.0, "sigma": 0.0}
    log_vals = np.log(pos)
    return {"mu": float(log_vals.mean()), "sigma": float(log_vals.std(ddof=1))}


def derive_priors(
    theta_estimates: pd.DataFrame,
    bkt_params: pd.DataFrame,
    responses_df: Optional[pd.DataFrame] = None,
) -> dict:
    """Combine fit_2pl + fit_bkt outputs into a student-priors dict."""
    if "theta" not in theta_estimates.columns:
        raise KeyError("theta_estimates must contain a 'theta' column")

    thetas = theta_estimates["theta"].to_numpy(dtype=float)
    theta_percentiles = {
        int(p): float(np.percentile(thetas, p)) for p in _THETA_PERCENTILES
    }

    if len(bkt_params):
        slip_values = bkt_params["p_slip"].to_numpy(dtype=float)
        guess_values = bkt_params["p_guess"].to_numpy(dtype=float)
        transit_values = bkt_params["p_transit"].to_numpy(dtype=float)
        slip_prior = {"mean": float(slip_values.mean()), "std": float(slip_values.std(ddof=1) if len(slip_values) > 1 else 0.0)}
        guess_prior = {"mean": float(guess_values.mean()), "std": float(guess_values.std(ddof=1) if len(guess_values) > 1 else 0.0)}
        learning_rate_lognorm = _fit_lognormal(transit_values)
    else:
        slip_prior = {"mean": 0.1, "std": 0.0}
        guess_prior = {"mean": 0.25, "std": 0.0}
        learning_rate_lognorm = {"mu": math.log(0.1), "sigma": 0.0}

    # Response time: fit lognormal to ms_first_response if present.
    response_time_lognorm = None
    if (
        responses_df is not None
        and "ms_first_response" in responses_df.columns
        and responses_df["ms_first_response"].notna().any()
    ):
        rt = responses_df["ms_first_response"].dropna().to_numpy(dtype=float)
        response_time_lognorm = _fit_lognormal(rt)

    return {
        "theta_percentiles": theta_percentiles,
        "theta_mean": float(thetas.mean()),
        "theta_std": float(thetas.std(ddof=1) if len(thetas) > 1 else 0.0),
        "slip_prior": slip_prior,
        "guess_prior": guess_prior,
        "learning_rate_lognorm": learning_rate_lognorm,
        "response_time_lognorm": response_time_lognorm,
    }


def write_priors(priors: dict, out_path: Path | str) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(priors, indent=2, sort_keys=True) + "\n")
    return out_path


def load_priors(in_path: Path | str) -> dict:
    return json.loads(Path(in_path).read_text())
