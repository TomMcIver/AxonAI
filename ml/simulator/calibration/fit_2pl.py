"""Fit 2PL IRT on a responses DataFrame.

The spec allows either `py-irt` (MCMC/VI) or `mirt` via `rpy2` for the
production-scale fit. For v1 tests and the ASSISTments sample-sized fit
we use a pure-scipy Joint Maximum Likelihood (JML) path — fast, zero
heavy deps, statistically adequate at the scale we test here. `py-irt`
can replace `_fit_jml` in a follow-up without changing this module's
public API.

Model
-----
    P(correct | theta_i, a_j, b_j) = 1 / (1 + exp(-a_j * (theta_i - b_j)))

Joint log-likelihood is maximised over {theta_i}, {(a_j, b_j)} with
identifiability constraints:

    mean(theta) = 0        # implied by centring residuals each iter
    a_j in [A_MIN, A_MAX]  # discrimination bounds
    b_j in [B_MIN, B_MAX]  # difficulty bounds

20% of per-item responses are held out for AUC/calibration evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from scipy.optimize import minimize

# Identifiability bounds on IRT params. Values follow common practice for
# secondary-school math items (see Baker & Kim 2004, ch. 7).
A_MIN = 0.3
A_MAX = 3.0
B_MIN = -4.0
B_MAX = 4.0

# Heldout split per item. Spec: 20% heldout, pass rate >= 85% on val.
HELDOUT_FRACTION = 0.20

# Optimiser tolerances. Tight enough for JML on ASSISTments sample scale.
_OPT_MAXITER = 300
_OPT_FTOL = 1e-6


@dataclass(frozen=True)
class Fit2PLResult:
    """Output of fit_2pl."""

    item_params: pd.DataFrame      # item_id, a, b, n_responses, heldout_auc, heldout_calibration_err
    theta_estimates: pd.DataFrame  # user_id, theta
    converged: bool
    n_iter: int
    train_log_likelihood: float


def _logistic(z: np.ndarray) -> np.ndarray:
    # Numerically stable logistic via np.where on the sign of z.
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    exp_z = np.exp(z[~pos])
    out[~pos] = exp_z / (1.0 + exp_z)
    return out


def _split_heldout(
    df: pd.DataFrame,
    rng: np.random.Generator,
    fraction: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-item heldout split: within each item, hold out `fraction` rows."""
    train_parts = []
    test_parts = []
    for _, group in df.groupby("problem_id"):
        n = len(group)
        n_test = max(1, int(round(n * fraction))) if n >= 5 else 0
        shuffled = group.sample(frac=1.0, random_state=int(rng.integers(2**31)))
        test_parts.append(shuffled.iloc[:n_test])
        train_parts.append(shuffled.iloc[n_test:])
    # Keep the source DataFrame index so leakage checks can assert that
    # no source row appears on both sides of the split. Downstream code
    # in this module uses `.map(...).to_numpy()` and `.groupby(...)` so
    # the index-preserving change is safe.
    return pd.concat(train_parts), pd.concat(test_parts)


def _fit_jml(
    student_idx: np.ndarray,
    item_idx: np.ndarray,
    y: np.ndarray,
    n_students: int,
    n_items: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool, int, float]:
    """Joint MLE: returns (theta, a, b, converged, n_iter, train_ll)."""
    # Param vector: [theta (n_students), a (n_items), b (n_items)]
    def unpack(x: np.ndarray):
        theta = x[:n_students]
        a = x[n_students : n_students + n_items]
        b = x[n_students + n_items :]
        return theta, a, b

    def neg_log_likelihood(x: np.ndarray) -> float:
        theta, a, b = unpack(x)
        z = a[item_idx] * (theta[student_idx] - b[item_idx])
        log_p = -np.logaddexp(0.0, -z)
        log_q = -np.logaddexp(0.0, z)
        ll = np.where(y, log_p, log_q).sum()
        return -ll

    def grad(x: np.ndarray) -> np.ndarray:
        theta, a, b = unpack(x)
        z = a[item_idx] * (theta[student_idx] - b[item_idx])
        p = _logistic(z)
        r = y.astype(float) - p  # residual

        # dLL/dtheta_i = sum_j a_j * r_ij
        d_theta = np.zeros(n_students)
        np.add.at(d_theta, student_idx, a[item_idx] * r)

        # dLL/da_j = sum_i (theta_i - b_j) * r_ij
        d_a = np.zeros(n_items)
        np.add.at(d_a, item_idx, (theta[student_idx] - b[item_idx]) * r)

        # dLL/db_j = sum_i -a_j * r_ij
        d_b = np.zeros(n_items)
        np.add.at(d_b, item_idx, -a[item_idx] * r)

        g = np.concatenate([d_theta, d_a, d_b])
        return -g  # negating because we minimise

    # Init: theta from student mean correctness, a=1.0, b=0.
    x0 = np.zeros(n_students + 2 * n_items)
    # Normalise student mean correctness into a rough theta via probit.
    # Simpler: start at 0 and let the optimiser move. Works for test sizes.
    x0[n_students : n_students + n_items] = 1.0   # a = 1.0

    bounds = (
        [(-4.0, 4.0)] * n_students
        + [(A_MIN, A_MAX)] * n_items
        + [(B_MIN, B_MAX)] * n_items
    )

    result = minimize(
        neg_log_likelihood,
        x0,
        jac=grad,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": _OPT_MAXITER, "ftol": _OPT_FTOL},
    )

    theta, a, b = unpack(result.x)
    # Centre theta to zero mean for identifiability — absorb shift into b.
    theta_mean = float(theta.mean())
    theta = theta - theta_mean
    b = b - theta_mean
    return theta, a, b, bool(result.success), int(result.nit), float(-result.fun)


def _auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Mann-Whitney U based AUC. Falls back to 0.5 for single-class."""
    pos = y_score[y_true.astype(bool)]
    neg = y_score[~y_true.astype(bool)]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    # rank-based AUC via Mann-Whitney U.
    all_scores = np.concatenate([pos, neg])
    ranks = pd.Series(all_scores).rank().to_numpy()
    rank_pos = ranks[: len(pos)].sum()
    u = rank_pos - len(pos) * (len(pos) + 1) / 2
    return float(u / (len(pos) * len(neg)))


def _calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Expected calibration error over equal-width bins."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.searchsorted(bins, y_prob) - 1, 0, n_bins - 1)
    n = len(y_true)
    err = 0.0
    for b in range(n_bins):
        mask = idx == b
        if not mask.any():
            continue
        err += (mask.sum() / n) * abs(y_true[mask].mean() - y_prob[mask].mean())
    return float(err)


def fit_2pl(
    responses_df: pd.DataFrame,
    seed: int = 0,
    heldout_fraction: float = HELDOUT_FRACTION,
) -> Fit2PLResult:
    """Fit 2PL IRT to a responses DataFrame.

    Expects columns: user_id, problem_id, correct (from assistments_loader).
    """
    needed = {"user_id", "problem_id", "correct"}
    missing = needed - set(responses_df.columns)
    if missing:
        raise KeyError(f"fit_2pl requires columns {needed}; missing {missing}")

    rng = np.random.default_rng(seed)

    train_df, test_df = _split_heldout(responses_df, rng, heldout_fraction)

    # Index students and items from the TRAINING set (heldout items are a
    # subset of the same universe).
    users = sorted(responses_df["user_id"].unique().tolist())
    items = sorted(responses_df["problem_id"].unique().tolist())
    user_to_idx = {u: i for i, u in enumerate(users)}
    item_to_idx = {it: i for i, it in enumerate(items)}

    student_idx = train_df["user_id"].map(user_to_idx).to_numpy()
    item_idx = train_df["problem_id"].map(item_to_idx).to_numpy()
    y = train_df["correct"].to_numpy(dtype=bool)

    theta, a, b, converged, n_iter, train_ll = _fit_jml(
        student_idx, item_idx, y, n_students=len(users), n_items=len(items)
    )

    # Evaluate on heldout: per-item AUC and calibration error.
    heldout_auc_by_item: Dict[int, float] = {}
    heldout_cerr_by_item: Dict[int, float] = {}
    heldout_count_by_item: Dict[int, int] = {}
    if len(test_df):
        test_df = test_df.assign(
            _theta=test_df["user_id"].map(user_to_idx).map(lambda i: theta[i]),
        )
        for item_id, group in test_df.groupby("problem_id"):
            j = item_to_idx[item_id]
            z = a[j] * (group["_theta"].to_numpy() - b[j])
            p = _logistic(z)
            y_t = group["correct"].to_numpy(dtype=bool)
            heldout_auc_by_item[item_id] = _auc(y_t, p)
            heldout_cerr_by_item[item_id] = _calibration_error(y_t, p)
            heldout_count_by_item[item_id] = len(group)

    # Item params frame.
    item_rows = []
    train_counts = train_df.groupby("problem_id").size().to_dict()
    for item_id, j in item_to_idx.items():
        item_rows.append(
            {
                "item_id": item_id,
                "a": float(a[j]),
                "b": float(b[j]),
                "n_responses_train": int(train_counts.get(item_id, 0)),
                "n_responses_heldout": int(heldout_count_by_item.get(item_id, 0)),
                "heldout_auc": float(heldout_auc_by_item.get(item_id, float("nan"))),
                "heldout_calibration_err": float(
                    heldout_cerr_by_item.get(item_id, float("nan"))
                ),
            }
        )
    item_params = pd.DataFrame(item_rows).sort_values("item_id").reset_index(drop=True)

    theta_df = pd.DataFrame({"user_id": users, "theta": theta})

    return Fit2PLResult(
        item_params=item_params,
        theta_estimates=theta_df,
        converged=converged,
        n_iter=n_iter,
        train_log_likelihood=train_ll,
    )


def write_item_params(result: Fit2PLResult, out_path: Path | str) -> Path:
    """Persist the calibrated item params as parquet."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.item_params.to_parquet(out_path, index=False)
    return out_path


def write_fit_report(result: Fit2PLResult, out_path: Path | str) -> Path:
    """Markdown diagnostics report — heldout AUC and calibration summaries."""
    auc = result.item_params["heldout_auc"].dropna()
    cerr = result.item_params["heldout_calibration_err"].dropna()
    lines = [
        "# 2PL IRT fit report",
        "",
        f"- Converged: {result.converged}",
        f"- Iterations: {result.n_iter}",
        f"- Train log-likelihood: {result.train_log_likelihood:.4f}",
        f"- Items fit: {len(result.item_params)}",
        f"- Students fit: {len(result.theta_estimates)}",
        "",
        "## Heldout diagnostics",
        "",
        f"- Items with heldout data: {len(auc)}",
        f"- AUC mean: {auc.mean():.4f}" if len(auc) else "- AUC: (no heldout)",
        f"- AUC median: {auc.median():.4f}" if len(auc) else "",
        f"- AUC >= 0.75: {(auc >= 0.75).mean():.2%}" if len(auc) else "",
        f"- Calibration error mean: {cerr.mean():.4f}" if len(cerr) else "",
        f"- Calibration error < 0.05: {(cerr < 0.05).mean():.2%}" if len(cerr) else "",
        "",
        "## Per-item (first 25)",
        "",
        "| item_id | a | b | n_train | n_heldout | AUC | calib_err |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    head = result.item_params.head(25)
    for _, row in head.iterrows():
        lines.append(
            f"| {row['item_id']} | {row['a']:.3f} | {row['b']:.3f} | "
            f"{row['n_responses_train']} | {row['n_responses_heldout']} | "
            f"{row['heldout_auc']:.3f} | {row['heldout_calibration_err']:.3f} |"
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(l for l in lines if l is not None) + "\n")
    return out_path
