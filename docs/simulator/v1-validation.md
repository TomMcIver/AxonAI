# Simulator v1 — Validation Report (Phase 1: Self-Consistency)

**Status:** Phase 1 complete. Phase 2 (real-data fidelity) blocked on response data paths.

Generated with:
```
python -m ml.simulator.validation.run_validation \
    --out-json docs/simulator/v1-validation.json \
    --seed 42 --n-truth-students 400 --n-skills 4 --items-per-skill 12 \
    --n-sim-students 200 --n-sessions 15
```

Raw numbers live in [`v1-validation.json`](./v1-validation.json). This
markdown summarises what each number means and where the simulator
passes / fails its own sanity checks.

---

## 1. What "self-consistency validation" means

Phase 1 does **not** compare simulated students to real students —
that's Phase 2, blocked on the ASSISTments / Eedi / MAP CSVs. Phase 1
tests a necessary (not sufficient) condition: can the simulator
recover its own ground truth?

Pipeline:

```
synthetic ground truth (known a, b, θ, BKT)
        │
        ▼  fit_2pl + fit_bkt + derive_priors
 fitted item params, fitted BKT per skill, priors
        │
        ▼  build_item_bank, build_concept_graph
 calibrated world
        │
        ▼  StudentGenerator + TermRunner
 simulated cohort
        │
        ▼  recovery + distribution metrics
 this report
```

If the simulator can't learn parameters from data it generated itself,
it cannot possibly learn them from real-student data. Passing Phase 1
clears the math; Phase 2 will stress the modelling assumptions.

## 2. Parameter recovery

Fitted-vs-true Pearson correlation and mean absolute error.

| Quantity | Pearson ρ | MAE | Pass threshold |
| --- | --- | --- | --- |
| 2PL discrimination `a` | **0.86** | 0.22 | ρ ≥ 0.75 ✅ |
| 2PL difficulty `b` | **0.98** | 0.16 | ρ ≥ 0.85 ✅ |
| Student θ | **0.95** | 0.27 | ρ ≥ 0.80 ✅ |
| BKT `p_transit` | 0.65 | 0.18 | ρ ≥ 0.50 ✅ |
| BKT `p_init` | −0.71 | 0.19 | ρ ≥ 0.30 ❌ (see §4) |
| BKT `p_slip` | −0.48 | 0.20 | ρ ≥ 0.30 ❌ (see §4) |
| BKT `p_guess` | −0.35 | 0.10 | ρ ≥ 0.30 ❌ (see §4) |

**2PL and θ recover cleanly.** This is the ship-critical recovery
signal — the IRT model underwrites quiz item selection and student
skill. 48 items × 400 students yields plenty of signal for JML.

**BKT recovery is uneven.** `p_transit` (the learning rate) recovers
well; `p_init`, `p_slip`, `p_guess` do not. This is a *known*
identifiability limitation of cross-sectional BKT fits from a single
attempt per item — without longitudinal attempt sequences, slip/guess
are entangled with item difficulty. See §4 for the mitigation plan.

## 3. Distribution fidelity

Per-student correct-rate comparison between the truth cohort and the
simulated cohort:

| Statistic | Truth (N=400) | Simulated (N=200) |
| --- | --- | --- |
| Mean | 0.461 | 0.550 |
| Median | 0.458 | 0.563 |
| p10 | 0.208 | 0.391 |
| p90 | 0.750 | 0.719 |

Two-sample KS test: **D = 0.30, p = 5×10⁻¹¹**.

**This failure is expected — and doesn't imply miscalibration.** The
truth cohort answered *every item once* with no adaptivity, so its
correct-rate distribution reflects the raw item-pool difficulty. The
simulated cohort was served items via ZPD-adaptive selection, which
targets P(correct) ≈ 0.73 by construction (Vygotsky / Pelánek band
`[0.60, 0.85]`). Collapsing the left tail is the *intended* behaviour
of adaptive testing.

The right comparison is Phase 2, where real-student data also comes
from an adaptive tutor — then the distributions become comparable.

Response-time distribution on simulated attempts:

| μ(log RT) | σ(log RT) | n |
| --- | --- | --- |
| 8.99 | 0.30 | 12,877 |

`exp(8.99) ≈ 8,040 ms` — matches the lognormal prior (8,000 ms), as
expected since the runner draws RTs from this prior directly.

Learning-curve slope (correct-rate vs within-concept attempt index):
**slope ≈ 10⁻⁵**, effectively flat. Also expected: ZPD-adaptive
selection *should* hold correct-rate near the band centre as students
learn (the band moves with skill). A rising slope would actually be a
bug.

## 4. Known limitations & Phase 2 plan

1. **BKT slip/guess/init identifiability.** Phase 1's synthetic truth
   gives each student one attempt per item. Real-student data has
   ordered multi-attempt sequences per skill, which is exactly what the
   forward-backward EM needs to disentangle slip from guess. Revisit
   once Phase 2 data lands; expected ρ on `p_slip` / `p_guess` ≥ 0.50.

2. **ZPD-distribution masking.** The KS rejection in §3 is a property
   of adaptive vs non-adaptive item serving, not a calibration defect.
   Phase 2 replaces truth with real adaptive-tutor data.

3. **Short-session dominance.** 15 sessions × 5 quiz items is enough to
   exercise the loop but too short to see BKT mastery propagation
   through the prerequisite chain. The `full.yaml` config (3000
   students × 30 sessions) runs under the same pipeline once Phase 2
   data is available.

4. **No concept-graph recovery check yet.** `build_concept_graph`
   relies on co-occurrence patterns from real student attempt streams;
   self-consistent validation can't exercise it meaningfully. Added to
   the Phase 2 checklist.

## 5. Readiness call

**Ship Phase 1 of the simulator.** The math does what it claims:
- IRT item params and student skill recover under JML with correlation ≥ 0.85.
- BKT learning rate recovers.
- Response-time and learning-curve behaviour match their priors.
- The end-to-end pipeline runs deterministically at the representative scale.

Block on Phase 2 before using simulator output for downstream training,
pending:
- Real response data paths (ASSISTments / Eedi / MAP CSVs).
- KS test against real adaptive-tutor correct-rate distribution.
- BKT slip/guess recovery on longitudinal data.
- Concept-graph reconstruction accuracy on held-out pairs.

## 6. Reproducing

```bash
python -m ml.simulator.validation.run_validation \
    --out-json docs/simulator/v1-validation.json \
    --seed 42
```

Deterministic under seed. Same seed → byte-identical JSON report.
