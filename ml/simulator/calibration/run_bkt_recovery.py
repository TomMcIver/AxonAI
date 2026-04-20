"""Phase 2 PR A2 — BKT parameter-recovery diagnostic.

Tests whether the BKT EM fitter is identifiable at the sequence lengths
present in the calibrated dataset. For each skill in
`real_bkt_params.parquet`:

    1. Treat the calibrated (p_init, p_transit, p_slip, p_guess) as
       ground truth.
    2. Simulate a cohort of N synthetic students, each producing a
       fixed-length binary response sequence from the BKT generative
       model (no items / IRT — this is a BKT-only test).
    3. Refit BKT on the synthetic cohort via the existing `fit_bkt`
       (grouping by user_id, with an increasing synthetic `start_time`
       so the sequence order is preserved).
    4. Report |recovered - true| per parameter; a skill is considered
       "recovered" when all four params are within `TOLERANCE` of the
       truth.

Two sequence-length regimes are reported:
    - **Empirical**: median length set to `n_responses / n_students`
      from the calibrated frame (so the test reflects the actual data
      regime and answers "is this identifiable here?").
    - **Extended**: fixed length (default 20) to answer "would it be
      identifiable with more data?".

Spec acceptance: recovery within ±0.05 for ≥80% of skills under the
extended regime. The empirical-regime result is reported as context
(the expected failure mode is short-sequence identifiability).

Determinism: per-skill seed is `seed * 1000 + skill_id`.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ml.simulator.calibration.fit_bkt import fit_bkt

# Spec gate.
TOLERANCE = 0.05
PASS_FRACTION_REQUIRED = 0.80

# Simulation knobs: not psychometric constants, just sizing dials.
DEFAULT_N_STUDENTS = 500  # per skill, both regimes
DEFAULT_EXTENDED_LEN = 20
# Used when a skill has n_students == 0 in the input (shouldn't happen,
# defensive): fall back to this empirical length.
_FALLBACK_EMPIRICAL_LEN = 5


@dataclass(frozen=True)
class RecoveryRow:
    skill_id: int
    p_init_true: float
    p_init_hat: float
    p_transit_true: float
    p_transit_hat: float
    p_slip_true: float
    p_slip_hat: float
    p_guess_true: float
    p_guess_hat: float
    seq_len: int
    n_students: int
    max_abs_error: float
    within_tolerance: bool


def _simulate_bkt_cohort(
    *,
    p_init: float,
    p_transit: float,
    p_slip: float,
    p_guess: float,
    n_students: int,
    seq_len: int,
    skill_id: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate a DataFrame of (user_id, problem_id, correct, skill_id, start_time).

    Each user answers `seq_len` times under the BKT generative model.
    `start_time` is a monotonically increasing integer so `fit_bkt`'s
    sort preserves sequence order.
    """
    rows = []
    time_counter = 0
    for u in range(n_students):
        known = rng.random() < p_init
        for t in range(seq_len):
            if known:
                correct = rng.random() > p_slip  # 1 - p_slip correct
            else:
                correct = rng.random() < p_guess
            rows.append((u, t, bool(correct), skill_id, time_counter))
            time_counter += 1
            # Learning transition AFTER the observation (matches fit_bkt).
            if not known and rng.random() < p_transit:
                known = True
    return pd.DataFrame(
        rows,
        columns=["user_id", "problem_id", "correct", "skill_id", "start_time"],
    )


def _empirical_seq_len(row: pd.Series) -> int:
    n_students = int(row["n_students"]) if row["n_students"] else 0
    n_responses = int(row["n_responses"]) if row["n_responses"] else 0
    if n_students <= 0:
        return _FALLBACK_EMPIRICAL_LEN
    return max(1, round(n_responses / n_students))


def _recover_one(
    row: pd.Series, seq_len: int, n_students: int, seed: int
) -> RecoveryRow:
    skill_id = int(row["skill_id"])
    rng = np.random.default_rng(seed * 1000 + skill_id)
    df = _simulate_bkt_cohort(
        p_init=float(row["p_init"]),
        p_transit=float(row["p_transit"]),
        p_slip=float(row["p_slip"]),
        p_guess=float(row["p_guess"]),
        n_students=n_students,
        seq_len=seq_len,
        skill_id=skill_id,
        rng=rng,
    )
    fit = fit_bkt(df)
    # Single skill → single row.
    if len(fit) != 1:
        raise RuntimeError(
            f"fit_bkt returned {len(fit)} rows for a single-skill cohort "
            f"(skill_id={skill_id})"
        )
    hat = fit.iloc[0]
    errors = {
        "p_init": abs(hat["p_init"] - row["p_init"]),
        "p_transit": abs(hat["p_transit"] - row["p_transit"]),
        "p_slip": abs(hat["p_slip"] - row["p_slip"]),
        "p_guess": abs(hat["p_guess"] - row["p_guess"]),
    }
    max_err = float(max(errors.values()))
    return RecoveryRow(
        skill_id=skill_id,
        p_init_true=float(row["p_init"]),
        p_init_hat=float(hat["p_init"]),
        p_transit_true=float(row["p_transit"]),
        p_transit_hat=float(hat["p_transit"]),
        p_slip_true=float(row["p_slip"]),
        p_slip_hat=float(hat["p_slip"]),
        p_guess_true=float(row["p_guess"]),
        p_guess_hat=float(hat["p_guess"]),
        seq_len=seq_len,
        n_students=n_students,
        max_abs_error=max_err,
        within_tolerance=max_err <= TOLERANCE,
    )


def _regime(
    bkt_params: pd.DataFrame,
    *,
    seq_len_fn,
    regime_name: str,
    n_students: int,
    seed: int,
) -> pd.DataFrame:
    print(f"[A2] BKT recovery regime '{regime_name}' on {len(bkt_params)} skills...")
    t0 = time.time()
    rows = []
    for _, skill_row in bkt_params.iterrows():
        seq_len = seq_len_fn(skill_row)
        if seq_len < 2:  # BKT needs >=2 obs to be meaningful
            seq_len = 2
        rows.append(_recover_one(skill_row, seq_len, n_students, seed))
    df = pd.DataFrame([r.__dict__ for r in rows])
    df["regime"] = regime_name
    print(
        f"[A2] '{regime_name}' done in {time.time() - t0:.1f}s; "
        f"{df['within_tolerance'].mean():.1%} of skills within ±{TOLERANCE}"
    )
    return df


def _write_report(
    report_path: Path,
    *,
    bkt_params_path: str,
    seed: int,
    emp: pd.DataFrame,
    ext: pd.DataFrame,
    n_students: int,
    extended_len: int,
) -> None:
    emp_pass = float(emp["within_tolerance"].mean())
    ext_pass = float(ext["within_tolerance"].mean())
    spec_pass = ext_pass >= PASS_FRACTION_REQUIRED

    def _param_stats(df: pd.DataFrame, name: str) -> str:
        err = (df[f"{name}_hat"] - df[f"{name}_true"]).abs()
        return (
            f"mean_err={err.mean():.3f}, median_err={err.median():.3f}, "
            f"p90_err={err.quantile(0.9):.3f}"
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as f:
        f.write(
            f"""# BKT parameter recovery

## Inputs

- BKT ground truth: `{bkt_params_path}` ({len(emp)} skills)
- Seed: `{seed}`
- Synthetic students per skill: {n_students}
- Tolerance: ±{TOLERANCE} on each of (p_init, p_transit, p_slip, p_guess)
- Spec acceptance (extended regime): ≥ {PASS_FRACTION_REQUIRED:.0%} of skills within tolerance

## Headline

| Regime | Seq length | Skills within ±{TOLERANCE} | Spec |
|---|---|---|---|
| Empirical (seq_len = n_responses / n_students) | variable | {emp_pass:.1%} ({int(emp['within_tolerance'].sum())}/{len(emp)}) | context |
| Extended (fixed seq_len = {extended_len}) | {extended_len} | {ext_pass:.1%} ({int(ext['within_tolerance'].sum())}/{len(ext)}) | ≥ {PASS_FRACTION_REQUIRED:.0%} → {'PASS' if spec_pass else 'FAIL'} |

### Overall: {'PASS' if spec_pass else 'FAIL'}

## Per-parameter error (extended regime)

- p_init:     {_param_stats(ext, 'p_init')}
- p_transit:  {_param_stats(ext, 'p_transit')}
- p_slip:     {_param_stats(ext, 'p_slip')}
- p_guess:    {_param_stats(ext, 'p_guess')}

## Per-parameter error (empirical regime)

- p_init:     {_param_stats(emp, 'p_init')}
- p_transit:  {_param_stats(emp, 'p_transit')}
- p_slip:     {_param_stats(emp, 'p_slip')}
- p_guess:    {_param_stats(emp, 'p_guess')}

## Interpretation

The empirical regime uses the same average sequence length as the real
ASSISTments calibration (median {int(emp['seq_len'].median())} attempts
per user-skill). The extended regime uses a fixed {extended_len}
attempts per user to isolate identifiability-in-principle from
identifiability-given-available-data.

- **Empirical recovery** is the upper bound on what the real BKT fit
  could be doing given the data at hand. Low empirical recovery means
  the limitation is data (short sequences), not algorithm.
- **Extended recovery** tests the EM itself. Low extended recovery
  would indicate a bug in `fit_bkt`.

Skills whose ground-truth params sit at the EM bounds (e.g. p_transit
pinned to 0.01 or 0.5) are especially hard to recover because the
simulator produces near-degenerate sequences; these were flagged in
`real_bkt_fit_report.md` and are expected to lower the recovery rate.

If the spec gate {'passes' if spec_pass else 'fails'}, the interpretation is:
""" + (
                f"""the EM identifies the 4 BKT parameters at seq_len={extended_len}
for ≥ {PASS_FRACTION_REQUIRED:.0%} of skills. The gap between extended
and empirical recovery ({(ext_pass - emp_pass) * 100:.1f} pp) is the
cost of the 2012-2013 release's short user-skill sequences.
"""
                if spec_pass
                else f"""the EM does not identify at ±{TOLERANCE} for {(1 - ext_pass) * 100:.0f}%
of skills even at seq_len={extended_len}. The dominant failure mode is
likely bound-pinned ground-truth parameters: the M-step clip in
fit_bkt (`_P_TRANSIT_BOUNDS = (0.01, 0.5)`, etc.) means that when the
true param lies at a bound, the simulator's draws from that bound
match a wide neighbourhood of fitted values. Remediation options:
(1) relax the tolerance; (2) exclude bound-pinned skills from the
spec denominator (only test skills with interior ground-truth params);
(3) increase seq_len further (diminishing returns at seq_len > 50);
(4) switch to Bayesian BKT with informative priors.
"""
            ) + """
"""
        )


def run(
    bkt_params_path: str = "data/processed/real_bkt_params.parquet",
    report_path: str = "validation/phase_2/bkt_recovery.md",
    details_path: str = "data/processed/bkt_recovery_details.parquet",
    seed: int = 42,
    n_students: int = DEFAULT_N_STUDENTS,
    extended_len: int = DEFAULT_EXTENDED_LEN,
) -> None:
    t0 = time.time()
    params = pd.read_parquet(bkt_params_path)
    print(f"[A2] loaded {len(params)} calibrated skills from {bkt_params_path}")

    emp = _regime(
        params,
        seq_len_fn=_empirical_seq_len,
        regime_name="empirical",
        n_students=n_students,
        seed=seed,
    )
    ext = _regime(
        params,
        seq_len_fn=lambda _row: extended_len,
        regime_name=f"extended_{extended_len}",
        n_students=n_students,
        seed=seed + 1,
    )

    details = pd.concat([emp, ext], ignore_index=True)
    Path(details_path).parent.mkdir(parents=True, exist_ok=True)
    details.to_parquet(details_path, index=False)

    _write_report(
        Path(report_path),
        bkt_params_path=bkt_params_path,
        seed=seed,
        emp=emp,
        ext=ext,
        n_students=n_students,
        extended_len=extended_len,
    )
    print(f"[A2] wrote {report_path}")
    print(f"[A2] wrote {details_path}")
    print(f"[A2] total elapsed {time.time() - t0:.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 2 PR A2 BKT recovery.")
    ap.add_argument(
        "--bkt-params", default="data/processed/real_bkt_params.parquet"
    )
    ap.add_argument(
        "--report", default="validation/phase_2/bkt_recovery.md"
    )
    ap.add_argument(
        "--details", default="data/processed/bkt_recovery_details.parquet"
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-students", type=int, default=DEFAULT_N_STUDENTS)
    ap.add_argument("--extended-len", type=int, default=DEFAULT_EXTENDED_LEN)
    args = ap.parse_args()
    run(
        bkt_params_path=args.bkt_params,
        report_path=args.report,
        details_path=args.details,
        seed=args.seed,
        n_students=args.n_students,
        extended_len=args.extended_len,
    )


if __name__ == "__main__":
    main()
