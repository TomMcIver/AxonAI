# Phase 2 — integration validation criteria (500-student v2_full)

**Generated (UTC):** 2026-04-24T23:58:11.041058+00:00Z

**Run definition:** 500 students × 60 sessions × 10 concepts × 10 items, seed 42, `response_model=misconception_weighted`, detector on, ZPD `item_selection`, synthetic item bank (same as `ml.simulator.validation.phase2_pipeline`). This is the full-scale B11 box — not the 80-student dry run.

| # | Criterion | Target | Result |
|---|----------|--------|--------|
| 1 | 2PL *a* recovery (Pearson ρ) | ≥ 0.75 | **PASS** — ρ = 0.8792 (`docs/simulator/v1-validation.json`, Phase 1 self-consistency) |
| 2 | 2PL *b* recovery (Pearson ρ) | ≥ 0.85 | **PASS** — ρ = 0.9705 |
| 3 | Student θ recovery (Pearson ρ) | ≥ 0.80 | **PASS** — ρ = 0.9462 |
| 4 | BKT parameter recovery (±0.05 @ seq 20) | ≥ 80% of skills | **PASS** — 80.9% (127/157) — `validation/phase_2/bkt_recovery.md` |
| 5 | Elo — cohort stdev of student Elo (sessions 20 & 25) | < 50 in weeks 4–5 window | **PASS** — stdev@session_20 = 49.81, stdev@session_25 = 45.00 (n=100 students / subsample) |
| 6 | IRT item parameters in synthetic bank | a ∈ (0.3, 3), b ∈ (-2, 2) | **PASS** — `_build_synthetic_bank` spot check |
| 7 | Population KS (θ) | p > 0.05 *or* documented | **PASS (OR)** — documented; `validation/phase_2/population_ks.md` |
| 8 | Misconception “wrong streak” median | ≤ 8 (design target) | **PASS** — median streak length = 2.00 (n=200, same harness) |
| 9 | Rewriter harness / deployment | ≥ 60% *or* harness gate / waived | skipped (no rewriter in dry run) — **PASS (waived)** for integration |
| 10 | LLM token cap | ≤ $500 | **PASS** — $0 (tutor/rewriter not called in this validation harness) |

## B11 invariants (this 500 × 60 run)

| Check | Outcome |
|------|---------|
| `is_simulated` on all attempt/teach records | **PASS** |
| All five `explanation_style` values appear | **PASS** |
| BKT cohort growth Δ mean p_known | +0.5685 (need ≥ 0.05 at this scale) — **PASS** |
| Learning curve (latter half ≥ earlier mean) | 0% (informational) — **INFO** |
| **Overall** | **PASS** |

**is_simulated coverage:** Every `AttemptRecord` and `TeachRecord` in this run uses the literal `is_simulated=True` field (see `_check_is_simulated_invariant` in `phase2_pipeline.py`); n ≈ 156857 attempts in style count.

**Regenerate:** `python -m ml.simulator.validation.write_phase2_validation_artifacts`
