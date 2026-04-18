"""Fit BKT per skill via EM on a responses DataFrame.

Classic forward-backward EM for the BKT HMM:
    Hidden state  K_t ∈ {known, not-known}
    Observation   y_t ∈ {correct, wrong}

Parameters per skill (see bkt.py):
    p_init, p_transit, p_slip, p_guess

Degeneracy constraint (Beck & Chang, 2007):  p_slip + p_guess < 1.
If EM drifts into the degenerate region we clamp back to the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# EM tolerance / iteration cap. Values are conservative defaults —
# ASSISTments fits converge well within these.
_EM_MAX_ITER = 200
_EM_TOL = 1e-5

# Beck-Chang degeneracy guard: we constrain p_slip + p_guess <= 1 - EPS.
_DEGEN_EPS = 0.01
# Bounded priors to keep EM stable on skills with few students.
_P_INIT_BOUNDS = (0.01, 0.99)
_P_TRANSIT_BOUNDS = (0.01, 0.5)
_P_SLIP_BOUNDS = (0.01, 0.3)
_P_GUESS_BOUNDS = (0.01, 0.4)

# Default starting point for EM.
_INIT = dict(p_init=0.2, p_transit=0.1, p_slip=0.1, p_guess=0.25)


@dataclass(frozen=True)
class BKTFitStats:
    skill_id: int
    converged: bool
    n_iter: int
    final_ll: float


def _student_sequences(responses_df: pd.DataFrame) -> list[np.ndarray]:
    """Group responses by user, sorted by start_time if present.

    Returns a list of 0/1 arrays (one per student).
    """
    if "start_time" in responses_df.columns:
        df = responses_df.sort_values(["user_id", "start_time"])
    else:
        df = responses_df.sort_values("user_id")
    return [g["correct"].to_numpy(dtype=int) for _, g in df.groupby("user_id")]


def _clip(value: float, bounds: tuple[float, float]) -> float:
    return max(bounds[0], min(bounds[1], value))


def _degeneracy_clip(p_slip: float, p_guess: float) -> tuple[float, float]:
    if p_slip + p_guess > 1.0 - _DEGEN_EPS:
        excess = (p_slip + p_guess) - (1.0 - _DEGEN_EPS)
        p_slip -= excess / 2
        p_guess -= excess / 2
    return max(p_slip, _P_SLIP_BOUNDS[0]), max(p_guess, _P_GUESS_BOUNDS[0])


def _forward_backward(
    obs: np.ndarray,
    p_init: float,
    p_transit: float,
    p_slip: float,
    p_guess: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Standard forward-backward on BKT HMM.

    Returns (gamma, xi_sum, log_likelihood):
        gamma[t, k] = P(K_t = k | obs)
        xi_sum     = sum over t of P(K_t=0, K_{t+1}=1 | obs)
                     (only the 'learning' transition is non-trivial in BKT;
                      forgetting P(K_t=1 -> K_{t+1}=0) is assumed 0.)
    """
    T = len(obs)
    # Emission: [P(obs | K=0), P(obs | K=1)]
    emit = np.empty((T, 2))
    for t, o in enumerate(obs):
        emit[t, 0] = p_guess if o == 1 else (1.0 - p_guess)       # not-known
        emit[t, 1] = (1.0 - p_slip) if o == 1 else p_slip         # known

    # Forward pass with rescaling for numerical stability.
    alpha = np.empty((T, 2))
    scale = np.empty(T)
    alpha[0, 0] = (1.0 - p_init) * emit[0, 0]
    alpha[0, 1] = p_init * emit[0, 1]
    scale[0] = alpha[0].sum()
    alpha[0] /= scale[0]
    for t in range(1, T):
        # Transition: only 0 -> 1 non-zero; 1 stays at 1.
        # P(K_t = 0) = P(K_{t-1}=0) * (1 - p_transit)
        # P(K_t = 1) = P(K_{t-1}=1) + P(K_{t-1}=0) * p_transit
        predict0 = alpha[t - 1, 0] * (1.0 - p_transit)
        predict1 = alpha[t - 1, 1] + alpha[t - 1, 0] * p_transit
        alpha[t, 0] = predict0 * emit[t, 0]
        alpha[t, 1] = predict1 * emit[t, 1]
        scale[t] = alpha[t].sum()
        alpha[t] /= scale[t]

    # Backward pass.
    beta = np.empty((T, 2))
    beta[T - 1] = 1.0
    for t in range(T - 2, -1, -1):
        # beta[t, k] = sum_k' P(K_{t+1}=k' | K_t=k) * emit[t+1, k'] * beta[t+1, k']
        # For k=0 (not known): transitions to 0 w.p. 1 - p_transit, to 1 w.p. p_transit.
        beta[t, 0] = (
            (1.0 - p_transit) * emit[t + 1, 0] * beta[t + 1, 0]
            + p_transit * emit[t + 1, 1] * beta[t + 1, 1]
        )
        # For k=1 (known): stays known w.p. 1.
        beta[t, 1] = emit[t + 1, 1] * beta[t + 1, 1]
        # Rescale by the same factor alpha used.
        beta[t] /= scale[t + 1]

    # Posterior state probabilities.
    gamma = alpha * beta
    gamma_sum = gamma.sum(axis=1, keepdims=True)
    gamma_sum[gamma_sum == 0] = 1.0
    gamma /= gamma_sum

    # Expected count of (K_{t-1} = 0) -> (K_t = 1) transitions.
    # xi[t-1] = alpha[t-1, 0] * p_transit * emit[t, 1] * beta[t, 1] / scale[t]
    xi_sum = 0.0
    for t in range(1, T):
        xi_sum += alpha[t - 1, 0] * p_transit * emit[t, 1] * beta[t, 1] / scale[t]

    log_likelihood = float(np.log(scale).sum())
    return gamma, xi_sum, log_likelihood


def _fit_skill(sequences: list[np.ndarray]) -> tuple[dict, bool, int, float]:
    p_init = _INIT["p_init"]
    p_transit = _INIT["p_transit"]
    p_slip = _INIT["p_slip"]
    p_guess = _INIT["p_guess"]

    prev_ll = -np.inf
    converged = False
    n_iter = 0
    for it in range(_EM_MAX_ITER):
        n_iter = it + 1
        # E-step + aggregated counts.
        gamma0_sum = 0.0       # sum of gamma[0] across sequences
        xi_total = 0.0         # total expected 0→1 transitions
        gamma_t0_sum = 0.0     # expected (K=0) count over t in {0..T-2}, all seqs
        gamma_k0_sum = 0.0     # expected (K=0) count over all t
        gamma_k1_sum = 0.0     # expected (K=1) count over all t
        correct_given_k0 = 0.0
        correct_given_k1 = 0.0
        ll_total = 0.0

        for obs in sequences:
            T = len(obs)
            gamma, xi_sum, ll = _forward_backward(
                obs, p_init, p_transit, p_slip, p_guess
            )
            ll_total += ll
            gamma0_sum += gamma[0, 1]
            xi_total += xi_sum
            if T > 1:
                gamma_t0_sum += gamma[:-1, 0].sum()
            gamma_k0_sum += gamma[:, 0].sum()
            gamma_k1_sum += gamma[:, 1].sum()
            correct_given_k0 += (gamma[:, 0] * obs).sum()
            correct_given_k1 += (gamma[:, 1] * obs).sum()

        n_seqs = len(sequences)

        # M-step.
        new_p_init = _clip(gamma0_sum / n_seqs, _P_INIT_BOUNDS)
        new_p_transit = _clip(
            xi_total / gamma_t0_sum if gamma_t0_sum > 0 else p_transit,
            _P_TRANSIT_BOUNDS,
        )
        # P(correct | not-known) = P(guess)
        new_p_guess = _clip(
            correct_given_k0 / gamma_k0_sum if gamma_k0_sum > 0 else p_guess,
            _P_GUESS_BOUNDS,
        )
        # P(wrong | known) = P(slip)
        new_p_slip = _clip(
            (gamma_k1_sum - correct_given_k1) / gamma_k1_sum if gamma_k1_sum > 0 else p_slip,
            _P_SLIP_BOUNDS,
        )
        new_p_slip, new_p_guess = _degeneracy_clip(new_p_slip, new_p_guess)

        if abs(ll_total - prev_ll) < _EM_TOL:
            converged = True
            p_init, p_transit, p_slip, p_guess = (
                new_p_init, new_p_transit, new_p_slip, new_p_guess,
            )
            prev_ll = ll_total
            break
        p_init, p_transit, p_slip, p_guess = (
            new_p_init, new_p_transit, new_p_slip, new_p_guess,
        )
        prev_ll = ll_total

    params = dict(
        p_init=p_init, p_transit=p_transit, p_slip=p_slip, p_guess=p_guess
    )
    return params, converged, n_iter, prev_ll


def fit_bkt(responses_df: pd.DataFrame) -> pd.DataFrame:
    """Fit BKT per skill. Returns a params DataFrame."""
    needed = {"user_id", "problem_id", "correct", "skill_id"}
    missing = needed - set(responses_df.columns)
    if missing:
        raise KeyError(f"fit_bkt requires columns {needed}; missing {missing}")

    rows = []
    for skill_id, skill_df in responses_df.groupby("skill_id"):
        if skill_id == -1:
            continue  # untagged responses — not a coherent skill
        sequences = _student_sequences(skill_df)
        if not sequences:
            continue
        params, converged, n_iter, ll = _fit_skill(sequences)
        rows.append(
            {
                "skill_id": int(skill_id),
                "p_init": params["p_init"],
                "p_transit": params["p_transit"],
                "p_slip": params["p_slip"],
                "p_guess": params["p_guess"],
                "converged": converged,
                "n_iter": n_iter,
                "final_ll": ll,
                "n_students": len(sequences),
                "n_responses": int(sum(len(s) for s in sequences)),
            }
        )
    return pd.DataFrame(rows).sort_values("skill_id").reset_index(drop=True)


def write_bkt_params(params_df: pd.DataFrame, out_path: Path | str) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    params_df.to_parquet(out_path, index=False)
    return out_path


def write_fit_report(params_df: pd.DataFrame, out_path: Path | str) -> Path:
    lines = [
        "# BKT fit report",
        "",
        f"- Skills fit: {len(params_df)}",
        f"- Converged: {int(params_df['converged'].sum())} / {len(params_df)}"
        if len(params_df)
        else "- No skills fit",
        "",
        "## Per-skill",
        "",
        "| skill_id | p_init | p_transit | p_slip | p_guess | n_students | n_iter | conv |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in params_df.iterrows():
        lines.append(
            f"| {row['skill_id']} | {row['p_init']:.3f} | {row['p_transit']:.3f} | "
            f"{row['p_slip']:.3f} | {row['p_guess']:.3f} | "
            f"{row['n_students']} | {row['n_iter']} | {row['converged']} |"
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")
    return out_path
