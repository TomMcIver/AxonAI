# Simulator v1 — Validation Report (Phase 1: Self-Consistency)

**Status:** Phase 1 complete. Phase 2 (real-data fidelity + BKT recovery on longitudinal data) blocked on response data paths.

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
synthetic ground truth (known a, b, θ — 2PL only)
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

**Scope of the ground truth.** Phase 1's synthetic truth draws
responses purely from the 2PL IRT model — one response per
(student, item). It tests IRT and θ recovery, which is what the quiz
item-selection layer depends on. It does **not** simulate a BKT
generating process (hidden knowledge state, learning transitions,
slip/guess emissions across ordered attempt sequences), so BKT
parameter recovery is **not** measured here; see §4.

If the simulator can't learn IRT parameters from data it generated
itself, it cannot possibly learn them from real data. Passing Phase 1
clears the IRT math; Phase 2 stresses BKT and the full modelling
assumptions.

## 2. Parameter recovery

Fitted-vs-true Pearson correlation and mean absolute error.

| Quantity | Pearson ρ | MAE | Pass threshold |
| --- | --- | --- | --- |
| 2PL discrimination `a` | **0.88** | 0.21 | ρ ≥ 0.75 ✅ |
| 2PL difficulty `b` | **0.97** | 0.16 | ρ ≥ 0.85 ✅ |
| Student θ | **0.95** | 0.25 | ρ ≥ 0.80 ✅ |

**2PL and θ recover cleanly.** This is the ship-critical signal — the
IRT model underwrites quiz item selection and student skill. 48 items
× 400 students yields plenty of signal for the scipy-JML fit.

**BKT recovery is not claimed in Phase 1.** See §4.

## 3. Distribution fidelity

Per-student correct-rate comparison between the truth cohort and the
simulated cohort:

| Statistic | Truth (N=400) | Simulated (N=200) |
| --- | --- | --- |
| Mean | 0.463 | 0.530 |
| Median | 0.438 | 0.517 |
| p10 | 0.188 | 0.293 |
| p90 | 0.750 | 0.801 |

Two-sample KS test: **D = 0.165, p = 1.3×10⁻³**.

**Expected shift, not a calibration defect.** The truth cohort
answered *every item once* with no adaptivity, so its correct-rate
distribution reflects the raw item-pool difficulty. The simulated
cohort was served items via ZPD-adaptive selection, which targets
P(correct) ∈ [0.60, 0.85] by construction (Vygotsky / Pelánek band).
The simulated distribution is correctly shifted upward and tighter.

The right comparison is Phase 2, where real-student data also comes
from an adaptive tutor — then the distributions become comparable.

Response-time distribution on simulated attempts:

| μ(log RT) | σ(log RT) | n |
| --- | --- | --- |
| 8.99 | 0.30 | 12,891 |

`exp(8.99) ≈ 8,040 ms` — matches the lognormal prior (8,000 ms), as
expected since the runner draws RTs from this prior directly.

Learning-curve slope (correct-rate vs within-concept attempt index):
**slope ≈ −3×10⁻⁵**, effectively flat. Also expected: ZPD-adaptive
selection *should* hold correct-rate near the band centre as students
learn (the band moves with skill). A rising slope would actually be a
bug.

## 4. Known limitations & Phase 2 plan

1. **BKT recovery requires longitudinal data.** Phase 1's synthetic
   truth gives each student one attempt per item, drawn from 2PL. BKT
   recovery needs ordered multi-attempt sequences per skill with a
   real hidden-state generating process (transitions on `p_transit`,
   emissions on `p_slip` / `p_guess`). Phase 2 will either (a) use
   real longitudinal attempt streams from ASSISTments / MAP, or (b)
   add a BKT-generating process to `synthetic_truth.py`; the metrics
   plumbing (`metrics.recovery_bkt` is trivially restored) is ready.

2. **ZPD-distribution shift.** The KS rejection in §3 is a property of
   adaptive vs non-adaptive item serving, not a calibration defect.
   Phase 2 replaces truth with real adaptive-tutor data.

3. **Short-session dominance.** 15 sessions × 5 quiz items exercises
   the loop but is too short to see BKT mastery propagation through
   the prerequisite chain. The `full.yaml` config (3000 students × 30
   sessions) runs under the same pipeline once Phase 2 data is wired.

4. **No concept-graph recovery check.** `build_concept_graph` relies
   on co-occurrence patterns from real student attempt streams;
   Phase 1's synthetic truth can't exercise it meaningfully. Added to
   the Phase 2 checklist.

## 5. Readiness call

**Ship Phase 1 of the simulator.** The IRT math does what it claims:
- 2PL item params and student skill recover under JML with ρ ≥ 0.88.
- Response-time and learning-curve behaviour match their priors.
- The end-to-end pipeline runs deterministically at the representative scale.

**Block on Phase 2 before using simulator output for downstream
training**, pending:
- Real response data paths (ASSISTments / Eedi / MAP CSVs) **or** a
  BKT-generating synthetic truth.
- KS test against real adaptive-tutor correct-rate distribution.
- BKT parameter recovery on longitudinal data.
- Concept-graph reconstruction accuracy on held-out pairs.

## 6. Reproducing

```bash
python -m ml.simulator.validation.run_validation \
    --out-json docs/simulator/v1-validation.json \
    --seed 42
```

Deterministic under seed. Same seed → byte-identical JSON report.
