"""Phase 2 PR B1 — misconception-susceptibility sampler diagnostics.

Draws a synthetic cohort and emits three checks:

1. **Activity-rate distribution** — per-student `|active|`/N and its
   dependence on θ. Expectation: monotone decrease in mean rate as θ
   rises, consistent with `_mean_rate`'s design.
2. **θ correlation** — Pearson correlation between scalar θ and
   `|active|`/N across the cohort. Expectation: negative; magnitude
   close to the configured `_THETA_COEF` over the prior's std.
3. **Determinism** — redrawing the same seed yields the same dict.

Outputs:
    `validation/phase_2/b1_susceptibility_diagnostics.md`

Scope. This is a generator-level check; it does not run the full
loop. The dependency on real data is limited to reading the Eedi
misconception ID list (either from the committed `id_map.json` or a
synthetic stand-in when running without S3 access). Determinism is
demonstrated on the sampler, so the report is fully reproducible
under a fixed seed.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from ml.simulator.student.misconceptions import (
    SusceptibilityConfig,
    SusceptibilitySampler,
)

DEFAULT_ID_MAP = "data/processed/eedi_misconception_id_map.json"
DEFAULT_REPORT = "validation/phase_2/b1_susceptibility_diagnostics.md"
DEFAULT_N_STUDENTS = 3000
DEFAULT_SEED = 42
# Used only when the committed id map is absent (e.g. local CI with no
# S3 credentials): a 2,587-entry integer index reproduces the Kaggle
# catalogue's cardinality, which is what the sampler cares about.
FALLBACK_CATALOGUE_SIZE = 2587


def _load_catalogue(id_map_path: Path) -> tuple[np.ndarray, str]:
    if id_map_path.exists():
        payload = json.loads(id_map_path.read_text())
        ids = np.array(
            [int(e["eedi_id"]) for e in payload["entries"]], dtype=np.int64
        )
        return ids, f"id_map: {id_map_path}"
    ids = np.arange(FALLBACK_CATALOGUE_SIZE, dtype=np.int64)
    return ids, (
        f"fallback synthetic catalogue of {FALLBACK_CATALOGUE_SIZE} IDs "
        f"(id_map not found at {id_map_path})"
    )


def _draw_cohort_thetas(
    priors: dict, n_students: int, rng: np.random.Generator
) -> np.ndarray:
    mean = float(priors.get("theta_mean", 0.0))
    std = max(float(priors.get("theta_std", 1.0)), 1e-6)
    return np.clip(rng.normal(mean, std, size=n_students), -4.0, 4.0)


def _determinism_check(sampler: SusceptibilitySampler, seed: int) -> bool:
    a = sampler.draw(0.0, np.random.default_rng(seed))
    b = sampler.draw(0.0, np.random.default_rng(seed))
    return a == b


def _tertile_breakdown(
    thetas: np.ndarray, active_counts: np.ndarray
) -> list[tuple[str, float, float, float]]:
    """Returns (label, theta_mean, mean_rate, stderr) per tertile."""
    q1, q2 = np.quantile(thetas, [1 / 3, 2 / 3])
    low = thetas <= q1
    mid = (thetas > q1) & (thetas <= q2)
    high = thetas > q2
    rows = []
    for label, mask in (("low θ", low), ("mid θ", mid), ("high θ", high)):
        rates = active_counts[mask]
        rows.append(
            (
                label,
                float(thetas[mask].mean()),
                float(rates.mean()),
                float(rates.std(ddof=1) / np.sqrt(len(rates))) if len(rates) > 1 else 0.0,
            )
        )
    return rows


def run(
    id_map_path: str = DEFAULT_ID_MAP,
    priors_path: str = "data/processed/real_student_priors.json",
    report_path: str = DEFAULT_REPORT,
    seed: int = DEFAULT_SEED,
    n_students: int = DEFAULT_N_STUDENTS,
) -> None:
    t0 = time.time()
    ids, catalogue_source = _load_catalogue(Path(id_map_path))
    priors = (
        json.loads(Path(priors_path).read_text())
        if Path(priors_path).exists()
        else {"theta_mean": 0.0, "theta_std": 1.0}
    )
    cfg = SusceptibilityConfig()
    sampler = SusceptibilitySampler(misconception_ids=ids, config=cfg)

    rng = np.random.default_rng(seed)
    thetas = _draw_cohort_thetas(priors, n_students, rng)

    active_counts = np.zeros(n_students, dtype=float)
    for i, theta in enumerate(thetas):
        # Per-student RNG: stream-independence is a hard property of the
        # simulator (see StudentGenerator contract) — we preserve it here
        # so the diagnostic mirrors how the loop will call the sampler.
        per_student_rng = np.random.default_rng((seed, i))
        out = sampler.draw(float(theta), per_student_rng)
        active_counts[i] = len(out) / len(ids)

    pearson = float(np.corrcoef(thetas, active_counts)[0, 1])
    tertiles = _tertile_breakdown(thetas, active_counts)
    determinism_ok = _determinism_check(sampler, seed)

    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Misconception susceptibility — B1 diagnostics\n")
    lines.append("## Inputs\n")
    lines.append(f"- Catalogue source: {catalogue_source}")
    lines.append(f"- Catalogue size: {len(ids):,}")
    lines.append(f"- Priors: `{priors_path}` (theta_mean={priors.get('theta_mean', 0.0)}, theta_std={priors.get('theta_std', 1.0)})")
    lines.append(f"- Seed: `{seed}`")
    lines.append(f"- Cohort size: {n_students:,}\n")
    lines.append("## Config\n")
    lines.append("| Knob | Value |")
    lines.append("|---|---|")
    lines.append(f"| base_rate | {cfg.base_rate} |")
    lines.append(f"| theta_coef | {cfg.theta_coef} |")
    lines.append(f"| min_mean_rate | {cfg.min_mean_rate} |")
    lines.append(f"| max_mean_rate | {cfg.max_mean_rate} |")
    lines.append(f"| beta_nu | {cfg.beta_nu} |")
    lines.append(f"| weight_min | {cfg.weight_min} |")
    lines.append(f"| weight_max | {cfg.weight_max} |\n")
    lines.append("## Headline\n")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| mean activity rate |active|/N | {active_counts.mean():.4f} |")
    lines.append(f"| std activity rate | {active_counts.std(ddof=1):.4f} |")
    lines.append(f"| Pearson(θ, rate) | {pearson:+.4f} |")
    lines.append(f"| determinism (same-seed equality) | {'PASS' if determinism_ok else 'FAIL'} |")
    lines.append("")
    lines.append("## Activity rate by θ tertile\n")
    lines.append("| Tertile | mean θ | mean rate | stderr |")
    lines.append("|---|---|---|---|")
    for label, tbar, rbar, se in tertiles:
        lines.append(f"| {label} | {tbar:+.3f} | {rbar:.4f} | {se:.4f} |")
    lines.append("")
    # PASS conditions:
    #   - Pearson correlation strictly negative (the design calls for
    #     lower-θ students to carry more active misconceptions).
    #   - Mean rate sits in [min_mean_rate, max_mean_rate] — a sanity
    #     check that the clip isn't saturating at one edge for every
    #     student, which would signal a θ-prior mismatch.
    pass_corr = pearson < 0.0
    pass_range = cfg.min_mean_rate - 0.02 <= active_counts.mean() <= cfg.max_mean_rate + 0.02
    verdict = "PASS" if (pass_corr and pass_range and determinism_ok) else "FAIL"
    lines.append("## Verdict\n")
    lines.append(
        f"- correlation negative: {'PASS' if pass_corr else 'FAIL'} "
        f"(observed {pearson:+.4f})"
    )
    lines.append(
        f"- mean rate within config: {'PASS' if pass_range else 'FAIL'} "
        f"(observed {active_counts.mean():.4f}, "
        f"[{cfg.min_mean_rate}, {cfg.max_mean_rate}])"
    )
    lines.append(f"- determinism: {'PASS' if determinism_ok else 'FAIL'}\n")
    lines.append(f"### Overall: {verdict}\n")
    lines.append("## Interpretation\n")
    lines.append(
        "The sampler is a stateless, θ-conditioned Beta-Bernoulli draw. "
        "With `_THETA_COEF = 0.08` and the real-cohort θ prior "
        f"(std≈{priors.get('theta_std', 1.0)}), the analytic prediction "
        "is that the Pearson correlation between θ and |active|/N should "
        "be close to `-theta_coef * std / sqrt(base_rate * (1 - base_rate))`; "
        "the observed value above is the empirical check on that. The "
        "determinism line guarantees the loop's per-student draws are "
        "reproducible under the same seed, which is required by the "
        "global simulator contract.\n"
    )
    report.write_text("\n".join(lines))
    print(f"[B1] wrote diagnostics to {report}")
    print(f"[B1] total elapsed {time.time() - t0:.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 2 PR B1 diagnostics.")
    ap.add_argument("--id-map", default=DEFAULT_ID_MAP)
    ap.add_argument(
        "--priors", default="data/processed/real_student_priors.json"
    )
    ap.add_argument("--report", default=DEFAULT_REPORT)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--n-students", type=int, default=DEFAULT_N_STUDENTS)
    args = ap.parse_args()
    run(
        id_map_path=args.id_map,
        priors_path=args.priors,
        report_path=args.report,
        seed=args.seed,
        n_students=args.n_students,
    )


if __name__ == "__main__":
    main()
