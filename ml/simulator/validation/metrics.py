"""Validation metrics for the simulator v1.

Two families:

1. **Parameter recovery** — how close are fitted (a, b, BKT params) to
   the known truth? Pearson correlation + mean absolute error.
2. **Distribution fidelity** — KS test on simulated vs reference
   correct-rate and response-time distributions.

All functions return plain dicts so the run_validation script can dump
a JSON report alongside the written markdown.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def recovery_2pl(
    true_params: pd.DataFrame,
    fitted_params: pd.DataFrame,
) -> dict:
    """Join on `problem_id` (truth) vs `item_id` (fit) and compare a, b.

    Returns correlations + MAE + sample size.
    """
    fit = fitted_params.rename(columns={"item_id": "problem_id"})
    merged = true_params.merge(
        fit[["problem_id", "a", "b"]].rename(columns={"a": "a_fit", "b": "b_fit"}),
        on="problem_id",
        how="inner",
    )
    return {
        "n_items": int(len(merged)),
        "a_pearson": float(stats.pearsonr(merged["a"], merged["a_fit"]).statistic),
        "a_mae": float(np.mean(np.abs(merged["a"] - merged["a_fit"]))),
        "b_pearson": float(stats.pearsonr(merged["b"], merged["b_fit"]).statistic),
        "b_mae": float(np.mean(np.abs(merged["b"] - merged["b_fit"]))),
    }


def recovery_theta(
    true_theta: pd.DataFrame,
    fitted_theta: pd.DataFrame,
) -> dict:
    """Correlation of fitted theta vs true theta per user."""
    merged = true_theta.merge(
        fitted_theta.rename(columns={"theta": "theta_fit"}),
        on="user_id",
        how="inner",
    )
    return {
        "n_users": int(len(merged)),
        "theta_pearson": float(stats.pearsonr(merged["theta"], merged["theta_fit"]).statistic),
        "theta_mae": float(np.mean(np.abs(merged["theta"] - merged["theta_fit"]))),
    }


def recovery_bkt(
    true_bkt: pd.DataFrame,
    fitted_bkt: pd.DataFrame,
) -> dict:
    """Per-param MAE + correlation across skills."""
    merged = true_bkt.merge(
        fitted_bkt,
        on="skill_id",
        how="inner",
        suffixes=("_true", "_fit"),
    )
    out: dict = {"n_skills": int(len(merged))}
    for p in ("p_init", "p_transit", "p_slip", "p_guess"):
        true_col = f"{p}_true"
        fit_col = f"{p}_fit"
        if true_col in merged.columns and fit_col in merged.columns:
            out[f"{p}_mae"] = float(np.mean(np.abs(merged[true_col] - merged[fit_col])))
            # Pearson on a constant array is undefined; skip quietly.
            if float(merged[true_col].std()) > 1e-12 and float(merged[fit_col].std()) > 1e-12:
                out[f"{p}_pearson"] = float(
                    stats.pearsonr(merged[true_col], merged[fit_col]).statistic
                )
    return out


def ks_correct_rate(
    simulated_per_user: np.ndarray,
    reference_per_user: np.ndarray,
) -> dict:
    """Two-sample KS on per-user correct rates."""
    res = stats.ks_2samp(simulated_per_user, reference_per_user)
    return {
        "ks_statistic": float(res.statistic),
        "ks_pvalue": float(res.pvalue),
        "sim_mean": float(np.mean(simulated_per_user)),
        "ref_mean": float(np.mean(reference_per_user)),
    }


def response_time_fit(rts_ms: np.ndarray) -> dict:
    """Fit log-normal to response times; report μ, σ of log(rt)."""
    positive = rts_ms[rts_ms > 0]
    if len(positive) < 2:
        return {"n": int(len(positive)), "mu": 0.0, "sigma": 0.0}
    log_rt = np.log(positive)
    return {
        "n": int(len(positive)),
        "mu": float(np.mean(log_rt)),
        "sigma": float(np.std(log_rt, ddof=1)),
    }


def learning_curve_slope(attempts: pd.DataFrame) -> dict:
    """Slope of correct-rate vs attempt index per concept (pooled).

    Expects columns: concept_id, is_correct. Returns OLS slope of
    correct vs within-concept attempt index, pooled across concepts.
    Positive slope = students learn; negative = degrading.
    """
    if len(attempts) < 10:
        return {"n": int(len(attempts)), "slope": 0.0}
    frames = []
    for _, group in attempts.groupby("concept_id"):
        idx = np.arange(len(group))
        frames.append(pd.DataFrame({
            "attempt_idx": idx,
            "is_correct": group["is_correct"].astype(float).values,
        }))
    pooled = pd.concat(frames, ignore_index=True)
    slope, intercept, *_ = stats.linregress(pooled["attempt_idx"], pooled["is_correct"])
    return {
        "n": int(len(pooled)),
        "slope": float(slope),
        "intercept": float(intercept),
    }
