"""Run the self-consistency validation and emit a JSON report.

Usage:
    python -m ml.simulator.validation.run_validation \
        --out-json docs/simulator/v1-validation.json \
        [--parquet-dir data/processed/runs] [--seed 42]

Default scale is a middleweight recovery run (~400 truth students ×
~48 items, ~200 simulated students × 15 sessions) — tractable on a
laptop, noisy enough that the numbers are informative. The full 3000 ×
10-week run lands once real data paths are wired up (Phase 2).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from ml.simulator.validation.pipeline import run_validation


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ml.simulator.validation.run_validation")
    p.add_argument("--out-json", required=True, help="Write report JSON here.")
    p.add_argument("--parquet-dir", default=None,
                   help="If set, also stream simulated events to this dir.")
    p.add_argument("--run-id", default="validation")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n-truth-students", type=int, default=400)
    p.add_argument("--n-skills", type=int, default=4)
    p.add_argument("--items-per-skill", type=int, default=12)
    p.add_argument("--n-sim-students", type=int, default=200)
    p.add_argument("--n-sessions", type=int, default=15)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = run_validation(
        n_truth_students=args.n_truth_students,
        n_skills=args.n_skills,
        items_per_skill=args.items_per_skill,
        n_sim_students=args.n_sim_students,
        n_sessions=args.n_sessions,
        seed=args.seed,
        parquet_output_dir=args.parquet_dir,
        run_id=args.run_id,
    )
    out = Path(args.out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2))
    print(f"[validation] wrote {out}")
    print(f"  2PL: a ρ={report.recovery_2pl['a_pearson']:.2f} "
          f"| b ρ={report.recovery_2pl['b_pearson']:.2f}")
    print(f"  θ  : ρ={report.recovery_theta['theta_pearson']:.2f} "
          f"MAE={report.recovery_theta['theta_mae']:.2f}")
    print(f"  KS : D={report.correct_rate_ks['ks_statistic']:.3f} "
          f"p={report.correct_rate_ks['ks_pvalue']:.3g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
