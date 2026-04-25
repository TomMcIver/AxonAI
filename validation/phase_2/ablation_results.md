# Phase 2 — investor ablation (four conditions)

**Generated (UTC):** 2026-04-25T00:01:09.699561+00:00Z
**Students / sessions:** 500 × 60 (same as `phase_2_validation.yaml`: 12 weeks × 5 sessions, rounded to 60 total sessions in harness)

Per-student Elo is **global** student rating; **Elo gain/hr** = `(elo_end − 1200) / study_hours` where study hours =
sum of attempt `response_time_ms` / 3.6e6. **Time-to-mastery** = number of attempts when *all* concepts first reach BKT p_known ≥ 0.85,
or censored (excluded) if not reached. **Retention @ 7d/30d** = mean of per-concept `hlr.predict_recall(h, {7|30}×24 hours)` on the final profile.

**Paired *t* tests** (one-tailed where a higher Elo, higher retention, or a lower TTM is better; same 500 `student_id`s).

## 1. Condition means / medians

| Condition | Elo gain/hr (mean) | Time-to-mastery (median att.) | Ret @ 7d (mean) | Ret @ 30d (mean) |
|---|---:|---:|---:|---:|
| `v1_uniform` | -92.9607 | 296.0 | 0.2423 | 0.1378 |
| `v2_misconception_only` | -92.9607 | 296.0 | 0.2423 | 0.1378 |
| `v2_full` | -92.9607 | 296.0 | 0.2423 | 0.1378 |
| `no_tutor_control` | -422.5458 | nan | 0.0120 | 0.0033 |

## 2. Paired tests — v2_full vs v1_uniform

| Metric | p-value (paired, one-tailed) |
|---|---:|
| elo_gain_per_hr | 1.000000 |
| time_to_mastery | 1.000000 |
| retention_7d | 1.000000 |
| retention_30d | 1.000000 |

## 3. Paired tests — v2_full vs no_tutor_control

| Metric | p-value (paired, one-tailed) |
|---|---:|
| elo_gain_per_hr | 1.98e-257 |
| time_to_mastery | 1.000000 |
| retention_7d | 2.54e-130 |
| retention_30d | 4.13e-118 |

## 4. Interpretation (read before sign-off)

- **v1_uniform vs v2_misconception_only — identical Elo/TTM/retention in this harness.** The Bernoulli draw for 2PL correctness is the first (and only) `rng` call that affects *whether* the student is correct; the misconception-weighted distractor path only changes `triggered_misconception_id` after a wrong answer, not `P(correct)` or the Elo/BKT/HLR updates. With the same per-student `TermRunner` seed, **v1 and v2 trajectories are therefore identical** on these metrics.
- **Primary contrast with instructional signal:** `no_tutor_control` (uniform + **random** item in bank) often fails to reach BKT mastery for all concepts within 60 sessions — TTM is censored (shown as `nan`), and the comparison vs v2 is on **Elo gain/hr** and **retention** where the effect is very large. Where both TTM values are finite, a paired TTM test is meaningful; otherwise the TTM p-value is **not interpretable** (treated as N/A; reported as 1.0 in the table).
- **`v2_full`** duplicates **`v2_misconception_only`** when `llm_tutor` is not attached; tutor/rewriter are logging-only until coupled to the learning state.

## 5. Regenerate

- `python -m ml.simulator.validation.write_phase2_validation_artifacts`
- `validation/phase_2/ablation_results.json`

