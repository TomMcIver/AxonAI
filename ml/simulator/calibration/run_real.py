"""Orchestrator for Phase 2 PR A1 — real-dataset calibration.

Pulls the full ASSISTments CSV (via `data.assistments_loader` which
accepts `s3://` URIs), filters to IRT-stable items, runs the existing
`fit_2pl` + `fit_bkt` + `derive_priors` modules against real data, and
writes parquet + JSON artefacts plus markdown diagnostic reports under
`validation/phase_2/`.

Determinism: master seed controls the train/heldout split. Default
matches Phase 1 (`seed=42`).

No magic numbers specific to the real-data path — defaults come from
the existing calibration modules. One knob is exposed:

    max_students_for_2pl
        Caps the student universe passed into the 2PL JML fit. The real
        ASSISTments 2012-2013 release has ~47k users; the JML
        optimiser's parameter vector is (n_students + 2 * n_items),
        which at 47k users + ~7k items is ~61k params and fits with
        L-BFGS-B in reasonable time on CPU. This knob exists so
        smaller re-runs don't have to change fit_2pl.py.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ml.simulator.calibration.fit_2pl import (
    HELDOUT_FRACTION,
    _logistic,
    _split_heldout,
    fit_2pl,
    write_fit_report as write_2pl_report,
    write_item_params,
)
from ml.simulator.calibration.fit_bkt import (
    fit_bkt,
    write_bkt_params,
    write_fit_report as write_bkt_report,
)
from ml.simulator.calibration.leakage_check import run as run_leakage_check
from ml.simulator.calibration.priors import derive_priors, write_priors
from ml.simulator.data.assistments_loader import (
    DEFAULT_MIN_RESPONSES_PER_ITEM,
    load_responses,
)

# Caps used on real ASSISTments to keep the JML tractable without
# dropping items. 47k users is the 2012-2013 release universe; leaving
# it at the real value is the default. Reducing to (say) 20k is a
# faster re-run knob. Not a magic threshold — just a user-facing dial.
DEFAULT_MAX_USERS_FOR_2PL = None  # None => use every user
# Cap on per-skill sequence count for BKT EM. 185 skills with >=500
# responses; capping students per skill keeps the per-skill EM fit
# bounded in time. Empty => use all.
DEFAULT_MAX_USERS_PER_SKILL_FOR_BKT = 5000


def _subsample_users(
    df: pd.DataFrame, max_users: Optional[int], seed: int
) -> pd.DataFrame:
    if max_users is None:
        return df
    users = df["user_id"].unique()
    if len(users) <= max_users:
        return df
    rng = np.random.default_rng(seed)
    pick = rng.choice(users, size=max_users, replace=False)
    return df[df["user_id"].isin(pick)].copy()


def _subsample_users_per_skill(
    df: pd.DataFrame, max_users_per_skill: Optional[int], seed: int
) -> pd.DataFrame:
    if max_users_per_skill is None:
        return df
    rng = np.random.default_rng(seed)
    parts = []
    for skill_id, skill_df in df.groupby("skill_id"):
        users = skill_df["user_id"].unique()
        if len(users) > max_users_per_skill:
            pick = rng.choice(users, size=max_users_per_skill, replace=False)
            skill_df = skill_df[skill_df["user_id"].isin(pick)]
        parts.append(skill_df)
    return pd.concat(parts, ignore_index=True)


def _append_real_vs_synthetic_note(
    report_path: Path,
    leakage_summary: str,
    item_params: pd.DataFrame,
    synthetic_b_pearson: float = 0.97,
) -> None:
    """Append Phase 1 comparison block + leakage summary to a 2PL report."""
    auc = item_params["heldout_auc"].dropna()
    lines = [
        "",
        "## Real-vs-synthetic gap (Phase 1 baseline)",
        "",
        f"Phase 1 self-consistency reported Pearson rho(fitted b, true b) = "
        f"**{synthetic_b_pearson:.2f}** on 48 items × 400 synthetic students.",
        "",
        f"Real ASSISTments heldout AUC: mean = {auc.mean():.3f}, median = {auc.median():.3f}, "
        f"{(auc >= 0.75).mean():.1%} of items with AUC >= 0.75.",
        "",
        "Self-consistency is the tighter benchmark by design (the fit "
        "is recovering the same generating process that produced the "
        "data). A drop from synthetic to real is expected and does not "
        "by itself indicate a fitting defect. The specific thresholds "
        "in the Phase 2 acceptance criteria (2PL converges on >=85% of "
        "items with >=150 responses) are reported above under "
        "`converged_at_bounds` and `n_converged_items`.",
        "",
        leakage_summary,
    ]
    with report_path.open("a") as f:
        f.write("\n".join(lines) + "\n")


def _count_converged_items(item_params: pd.DataFrame) -> tuple[int, int, float]:
    """Count how many items have fit params *not pinned* at the bounds.

    Returns (n_converged, n_total, fraction). An item is "converged" if
    neither `a` nor `b` sits at the identifiability bounds enforced in
    fit_2pl (A_MIN/A_MAX, B_MIN/B_MAX).
    """
    from ml.simulator.calibration.fit_2pl import A_MIN, A_MAX, B_MIN, B_MAX

    eps = 1e-3
    at_bound = (
        (item_params["a"] <= A_MIN + eps)
        | (item_params["a"] >= A_MAX - eps)
        | (item_params["b"] <= B_MIN + eps)
        | (item_params["b"] >= B_MAX - eps)
    )
    n_converged = int((~at_bound).sum())
    n_total = int(len(item_params))
    return n_converged, n_total, (n_converged / n_total) if n_total else 0.0


def run(
    csv_path: str,
    out_dir: str = "data/processed",
    report_dir: str = "validation/phase_2",
    seed: int = 42,
    min_responses_per_item: int = DEFAULT_MIN_RESPONSES_PER_ITEM,
    max_users_for_2pl: Optional[int] = DEFAULT_MAX_USERS_FOR_2PL,
    max_users_per_skill_for_bkt: Optional[int] = DEFAULT_MAX_USERS_PER_SKILL_FOR_BKT,
) -> None:
    t0 = time.time()
    out = Path(out_dir)
    reports = Path(report_dir)
    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    print(f"[A1] loading ASSISTments responses from {csv_path}")
    responses = load_responses(csv_path, min_responses_per_item=min_responses_per_item)
    t1 = time.time()
    print(
        f"[A1] loaded {len(responses):,} responses, "
        f"{responses['user_id'].nunique():,} users, "
        f"{responses['problem_id'].nunique():,} items, "
        f"{responses['skill_id'].nunique():,} skill values "
        f"(load+filter elapsed {t1 - t0:.1f}s)"
    )

    # 2PL fit — optionally subsample users.
    responses_2pl = _subsample_users(responses, max_users_for_2pl, seed)
    if len(responses_2pl) != len(responses):
        print(
            f"[A1] 2PL fit user subsample: "
            f"{responses_2pl['user_id'].nunique():,} users "
            f"(cap={max_users_for_2pl})"
        )

    print(f"[A1] fitting 2PL on {len(responses_2pl):,} responses...")
    t2 = time.time()
    result = fit_2pl(responses_2pl, seed=seed)
    print(
        f"[A1] 2PL done in {time.time() - t2:.1f}s, "
        f"converged={result.converged}, n_iter={result.n_iter}"
    )

    # Leakage check — re-derive the same split for transparency.
    rng = np.random.default_rng(seed)
    train_df, test_df = _split_heldout(responses_2pl, rng, HELDOUT_FRACTION)
    leakage = run_leakage_check(train_df, test_df)
    print(
        f"[A1] leakage check: duplicate_rows={leakage.duplicate_rows}, "
        f"shared_items={leakage.shared_items}"
    )
    if not leakage.passed:
        raise RuntimeError(
            f"leakage check failed: {leakage.duplicate_rows} duplicate rows "
            "across train/heldout. Abort."
        )

    # Persist parquet + markdown.
    item_params_path = out / "real_item_params.parquet"
    write_item_params(result, item_params_path)
    n_conv, n_total, frac = _count_converged_items(result.item_params)
    print(
        f"[A1] items with params off-bounds: {n_conv}/{n_total} ({frac:.1%})"
    )

    two_pl_report = reports / "real_2pl_fit_report.md"
    write_2pl_report(result, two_pl_report)
    # Append real-vs-synthetic + leakage summary.
    _append_real_vs_synthetic_note(
        two_pl_report,
        leakage.summary_markdown(),
        result.item_params,
    )
    # Also append the converged-off-bounds summary.
    with two_pl_report.open("a") as f:
        f.write(
            "\n"
            f"## Off-bounds convergence\n\n"
            f"- Items fit: {n_total}\n"
            f"- Items with a, b both strictly inside identifiability bounds: "
            f"{n_conv} ({frac:.1%})\n"
            f"- Spec acceptance (>=85%): {'PASS' if frac >= 0.85 else 'FAIL'}\n"
        )

    # Theta estimates persist alongside item params for downstream use.
    theta_path = out / "real_theta_estimates.parquet"
    theta_path.parent.mkdir(parents=True, exist_ok=True)
    result.theta_estimates.to_parquet(theta_path, index=False)

    # BKT fit per skill — drops skill_id == -1 inside fit_bkt.
    bkt_input = _subsample_users_per_skill(
        responses, max_users_per_skill_for_bkt, seed
    )
    print(
        f"[A1] fitting BKT per skill on {len(bkt_input):,} responses "
        f"({bkt_input['skill_id'].nunique()} skill values)"
    )
    t3 = time.time()
    bkt_df = fit_bkt(bkt_input)
    print(f"[A1] BKT done in {time.time() - t3:.1f}s")

    bkt_params_path = out / "real_bkt_params.parquet"
    write_bkt_params(bkt_df, bkt_params_path)

    bkt_report = reports / "real_bkt_fit_report.md"
    write_bkt_report(bkt_df, bkt_report)
    # Append "plausible-bands" summary to bkt report.
    slip_ok = bkt_df["p_slip"].between(0.02, 0.20)
    guess_ok = bkt_df["p_guess"].between(0.10, 0.35)
    tr_ok = bkt_df["p_transit"].between(0.05, 0.40)
    all_ok = slip_ok & guess_ok & tr_ok
    pct = (all_ok.mean() if len(bkt_df) else 0.0) * 100
    with bkt_report.open("a") as f:
        f.write(
            "\n"
            f"## Plausible-band coverage\n\n"
            f"Spec: p_slip in [0.02, 0.20], p_guess in [0.10, 0.35], "
            f"p_transit in [0.05, 0.40].\n\n"
            f"- Skills meeting all three: {int(all_ok.sum())} / {len(bkt_df)} "
            f"({pct:.1f}%)\n"
            f"- p_slip in band: {int(slip_ok.sum())}\n"
            f"- p_guess in band: {int(guess_ok.sum())}\n"
            f"- p_transit in band: {int(tr_ok.sum())}\n"
            f"- Spec acceptance (>=75%): {'PASS' if pct >= 75 else 'FAIL'}\n"
        )

    # Priors — use the 2PL theta estimates + BKT params + raw responses.
    priors = derive_priors(result.theta_estimates, bkt_df, responses)
    priors_path = out / "real_student_priors.json"
    write_priors(priors, priors_path)

    # Summary line to stdout.
    print(
        "[A1] artefacts:\n"
        f"  - {item_params_path}\n"
        f"  - {theta_path}\n"
        f"  - {bkt_params_path}\n"
        f"  - {priors_path}\n"
        f"  - {two_pl_report}\n"
        f"  - {bkt_report}"
    )
    print(f"[A1] total elapsed {time.time() - t0:.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 2 PR A1 real-dataset calibration.")
    ap.add_argument(
        "--csv",
        default="s3://axonai-datasets-924300129944/assistments/"
        "2012-2013-data-with-predictions-4-final.csv",
        help="Local path or s3:// URI for the ASSISTments responses CSV.",
    )
    ap.add_argument("--out-dir", default="data/processed")
    ap.add_argument("--report-dir", default="validation/phase_2")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--min-responses-per-item",
        type=int,
        default=DEFAULT_MIN_RESPONSES_PER_ITEM,
    )
    ap.add_argument(
        "--max-users-for-2pl",
        type=int,
        default=DEFAULT_MAX_USERS_FOR_2PL or 0,
        help="0 means all users.",
    )
    ap.add_argument(
        "--max-users-per-skill-for-bkt",
        type=int,
        default=DEFAULT_MAX_USERS_PER_SKILL_FOR_BKT or 0,
        help="0 means all users.",
    )
    args = ap.parse_args()
    run(
        csv_path=args.csv,
        out_dir=args.out_dir,
        report_dir=args.report_dir,
        seed=args.seed,
        min_responses_per_item=args.min_responses_per_item,
        max_users_for_2pl=args.max_users_for_2pl or None,
        max_users_per_skill_for_bkt=args.max_users_per_skill_for_bkt or None,
    )


if __name__ == "__main__":
    main()
