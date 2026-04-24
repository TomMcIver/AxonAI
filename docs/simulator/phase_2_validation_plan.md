# Simulator Phase 2 — Comprehensive Validation Plan

**Branch:** `claude/phase-2-validation-vCSGR`
**Date:** 2026-04-24
**Status:** Phase 1 (planning). No implementation in this document.

---

## 1. Simulator state audit

### 1.1 Phase 2 PR merge status

All Gate A and Gate B PRs are merged **into this branch**. They are not yet merged into `origin/main`.

| PR | # | Title | Outcome |
|----|---|-------|---------|
| A1 | #94 | Real-dataset calibration | PASS (2PL); BKT plausibility FAIL → remediated (§4) |
| A3 | #95 | Concept-graph held-out validation | FAIL → remediated (§4) |
| A2 | #96 | BKT recovery + population KS | BKT recovery PASS; KS FAIL → remediated (§4) |
| — | #97 | Gate A exit summary | — |
| B1 | #98 | Misconception susceptibility sampler | PASS |
| B6 | #99 | Explanation-style selector | PASS |
| B3 | — | Misconception detector retrieval | PASS |
| B2 | — | Misconception-weighted response model | PASS |
| B4 | — | Misconception detector cross-encoder rerank | PASS |
| B5 | — | Detector integration into loop | PASS |
| B7 | — | LLM tutor integration | PASS (with gap — see §2.2) |
| B8 | — | Question rewriter | PASS |
| B9 | — | Rewriter equivalence verifier | PASS |
| B10 | — | Rewriter sample-testing harness | PASS |
| B11 | — | Integration + v2 validation run | PASS (dry run, 80 students) |
| B12 | #109 | Ablation study | PASS (different conditions than spec — see §2.3) |

### 1.2 Directory tree

```
ml/simulator/
├── __init__.py / __main__.py / cli.py / cli_smoke.py
├── config.py                  # SimulationConfig dataclass
├── configs/                   # full.yaml (3000s × 10w), small.yaml (10s × 1w)
├── calibration/               # fit_2pl, fit_bkt, priors, leakage_check,
│                              # run_b1/b3/b4 diagnostics, bkt_recovery,
│                              # concept_graph_validation, population_ks, run_real
├── data/                      # assistments_loader, eedi_misconceptions_loader,
│                              # map_loader, s3_io, concept_graph, item_bank
├── io/                        # local_writer (parquet), postgres_writer (shadow)
├── loop/                      # quiz, revise, teach, runner, explanation_style,
│                              # llm_tutor, rewriter, verifier
├── migrations/                # 0001_is_simulated.sql
├── misconception/             # detector, reranker, response_model, retrieval
├── psychometrics/             # irt_2pl, bkt, elo, hlr
├── student/                   # profile, generator, dynamics, misconceptions
└── validation/                # pipeline (Phase 1), phase2_pipeline (B11),
                               # ablation (B12), metrics, rewriter_harness,
                               # synthetic_truth, run_validation
```

---

## 2. Known gaps (findings from this audit)

### 2.1 Config gap — feature toggles missing

`SimulationConfig` (in `config.py`) has no fields for Phase 2 feature toggles:

| Missing field | Purpose |
|---|---|
| `response_model` | `"uniform"` (v1) vs `"misconception_weighted"` (v2) |
| `detector_enabled` | Whether `MisconceptionDetector` is active in the loop |
| `tutor_enabled` | Whether `LLMTutor` is called in the teach step |
| `rewriter_enabled` | Whether `QuestionRewriter` is applied to quiz items |

The existing configs (`full.yaml`, `small.yaml`) also do not cover the Phase 2 target scale: 500 students × 12 weeks × 5 sessions/week × 45 minutes/session, seed 42.

**Resolution:** PR-1.5 (see §5.1) adds these four fields to `SimulationConfig` and a new `configs/phase2_full.yaml` with the target values.

### 2.2 LLM cache gap — B7 has no cache

`LLMTutor.generate_explanation` (`loop/llm_tutor.py`) makes a live API call on every invocation. There is no deduplication, in-memory cache, or disk cache. The spec requires reporting "LLM cache hit rate" — that metric cannot be produced without a cache layer.

This matters at scale: 500 students × 12 weeks × 5 sessions/week × 1 teach call/session = 30,000 calls. Many will be for the same (concept_id, explanation_style) pair.

**Resolution:** PR-1.75 (see §5.2) adds an LRU / deterministic dict-keyed cache keyed on `(concept_id, explanation_style)` inside `LLMTutor`, with a hit-rate counter.

### 2.3 Ablation divergence — B12 ≠ spec-defined ablation

The existing B12 ablation (`ml/simulator/validation/ablation.py`) is a correct and passing module, but its conditions and metrics differ from what the comprehensive validation spec requires.

| Axis | B12 (existing) | Spec (required for investor report) |
|---|---|---|
| **Conditions** | `full`, `no_susceptibility`, `no_detector`, `default_style_only`, `no_slow_students` | `v1_uniform`, `v2_misconception_only`, `v2_full`, `no_tutor_control` |
| **Primary metric** | `bkt_growth`, `correct_rate`, `style_distribution` | Elo gain/hr, time-to-mastery (median attempts), retention @ 7d and 30d |
| **Ordering claim** | Not stated | Monotonic: `v2_full > v2_misconception_only > v1_uniform > no_tutor_control` |
| **Stats** | None | 95% CI, pairwise p-values |

**Why both exist:**

B12 is a feature-level ablation — it answers "does removing component X break the loop?" and validates that each Gate B feature is wired correctly. It was appropriate for the Gate B merge gate.

The spec's four-condition ablation is a *comparative performance study* — it answers "does the v2 stack outperform v1 and random baselines, and by how much?" It uses investor-facing metrics (Elo gain, retention) not available in B12's scope.

These are complementary, not redundant. Both will be preserved. The new ablation lives in a separate module and PR (see §5.4).

### 2.4 `is_simulated` implementation — boolean or inferred?

The spec states: "`is_simulated=True` on every row". The actual implementation varies by table:

| Location | Implementation |
|---|---|
| `io/local_writer.py` (line 61, 143) | Literal `row["is_simulated"] = True` stamped on every row before write |
| `io/postgres_writer.py` (line 59) | Literal `row["is_simulated"] = True` stamped on every row before write |
| `loop/rewriter.py` (line 142) | `is_simulated: bool = True` as a dataclass field default on `RewriteRecord` |
| `loop/verifier.py` (line 100) | `is_simulated: bool = True` as a dataclass field default on `VerificationResult` |
| Invariant check (`phase2_pipeline.py` line 216–223) | Checks `a.explanation_style is not None` — **not** `a.is_simulated == True` |

The invariant check in B11 uses `explanation_style is not None` as a proxy for "this record was written by the simulator." This works in practice (only the simulator sets `explanation_style`), but it is not the same as checking the literal `is_simulated` boolean field.

**Clarifying question for the user: Is the `is_simulated` proxy implementation acceptable, or is it a blocker? Specifically — does the investor data-integrity check require a literal `is_simulated=True` column queryable from outside the simulator (e.g. a Postgres WHERE clause), or is the field's presence on the in-memory records sufficient?** This determines whether `_check_is_simulated_invariant` needs to be rewritten before Phase 2 integration runs.

---

## 3. Component checklist

| Component | Module path | Key public API | Unit tests | Limitations |
|---|---|---|---|---|
| **Psychometrics** | `ml/simulator/psychometrics/` | `prob_correct()`, `sample_response()`, `log_likelihood()` (IRT); `BKTState.update()`, `predict_correct()`; `elo.update()`, `k_factor()`; `hlr.predict_recall()`, `update_half_life()` | 4 files, 55 tests | HLR half-life is per-concept, not per-item |
| **Loaders / IO** | `ml/simulator/data/`, `ml/simulator/io/` | `AssistmentsLoader`, `EediMisconceptionLoader`, `MapLoader`; `LocalParquetWriter`, `PostgresWriter` | 7 files, 64 tests | Postgres writer requires live DSN; not exercised in CI |
| **Calibration** | `ml/simulator/calibration/` | `fit_2pl()`, `fit_bkt()`, `derive_priors()`, `leakage_check()` | 8 files, 69 tests | BKT p_transit error >0.05 on ~20% of skills (documented, §4) |
| **Student** | `ml/simulator/student/` | `StudentProfile`, `StudentGenerator.sample_profile()`, `apply_practice()`, `apply_forgetting()`, `SusceptibilitySampler.draw()` | 4 files, 53 tests | Prior θ distribution has thinner tails than real (§4) |
| **Loop** | `ml/simulator/loop/` | `TermRunner.run()`, `select_next_item()`, `simulate_response()`, `select_revision_concepts()` | 8 files, 119 tests | No v1/v2/detector/tutor/rewriter toggles in runner (§2.1) |
| **Misconception detector** | `ml/simulator/misconception/` | `MisconceptionDetector.predict()`, `retrieval.retrieve()`, `reranker.rerank()`, `select_distractor()` | 4 files, 59 tests | In B11 pipeline used in "tagged shortcut" mode (no real retrieval index) |
| **LLM tutor + rewriter** | `ml/simulator/loop/` | `LLMTutor.generate_explanation()`, `ExplanationStyleSelector`, `QuestionRewriter.rewrite()`, `RewriteVerifier.verify()` | 8 files, 119 tests (shared with loop) | No cache on LLMTutor (§2.2); rewriter requires live API key |

**Total: 35 test files, 419 test functions.**

---

## 4. Gate A remediation record

Three Gate A acceptance criteria were remediated rather than passed. These are documented honestly here and will appear in the investor report's "Assumptions & Limitations" section.

### 4.1 BKT plausibility (A1) — FAIL, accepted

- **Spec:** BKT p_slip / p_guess / p_transit in plausible bands for ≥75% of skills.
- **Result:** 12.7% (20/157 skills).
- **Root cause:** The 2012-2013 ASSISTments release has median 1.97 attempts per user per skill — too few for EM to identify p_transit. This is a data density problem, not a model defect.
- **Decision:** Accepted weaker fits. Downstream modules (TermRunner, StudentGenerator) use `p_known` not raw params, so the ±0.05 error does not propagate to the core learning signal. A2's recovery test confirms EM is identifiable at seq_len=20 (80.9% within ±0.05).

### 4.2 Population KS test (A2) — FAIL, accepted as pedagogically plausible

- **Spec:** KS p > 0.05 on θ distribution (synthetic vs. ASSISTments-inferred).
- **Result:** p = 1.7×10⁻¹³, statistic 0.074. Mean/std match to within 0.03/0.01; the failure is driven by heavier real-data tails (p95 real +2.43 vs. simulated +1.98).
- **Root cause:** A mixture-of-classrooms effect in real data that a single Gaussian prior cannot capture.
- **Decision:** Accepted as a documented plausible shift. The generator-level mismatch is smaller than the loop-level drift Phase 2 will introduce anyway. If Phase 2 integration flags the same tail problem, the prior will be switched to a Student-t fit.

### 4.3 Concept-graph validation (A3) — FAIL, gate relaxed

- **Spec:** Direct-edge recall ≥ 0.60, precision ≥ 0.40 vs. hand-curated gold edges.
- **Result:** Direct recall 0.074, precision 0.040. Path recall 0.556.
- **Root cause:** Gold edges reference skills at a finer granularity than the graph nodes (~32.5% loss); the builder's transitive reduction collapses direct edges to transitive paths (~32.5% loss); residual heuristic misses (~30%).
- **Decision:** Gate relaxed to path-recall (0.556) for Gate B. `TermRunner` traverses the DAG via topological sort and `prerequisites()`, both of which respect transitive reachability — so path recall is the operationally relevant metric. Noted as an open risk in B11.

---

## 5. Phase 2 execution plan

### 5.1 PR-1.5 — Config + feature toggles

**Title:** `feat(simulator): add Phase 2 feature toggles to SimulationConfig`

- Add four boolean/string fields to `SimulationConfig`: `response_model`, `detector_enabled`, `tutor_enabled`, `rewriter_enabled`.
- Add `configs/phase2_full.yaml`: 500 students, 12 weeks, 5 sessions/week, 45 min/session, seed 42, all Phase 2 features on.
- Add `configs/phase2_ablation_v1.yaml`, `phase2_ablation_v2_misconception_only.yaml`, `phase2_ablation_no_tutor_control.yaml` for the four-condition ablation.
- Wire toggles into `TermRunner` so it respects them.
- Tests: ensure old configs still load; new configs parse correctly; runner uses correct feature path per toggle.

### 5.2 PR-1.75 — LLM tutor cache hotfix

**Title:** `fix(simulator): add deterministic LRU cache to LLMTutor`

- Add a `dict`-backed cache keyed on `(concept_id, explanation_style)` to `LLMTutor`.
- Add `cache_hits: int` and `cache_misses: int` counters, exposed via a `cache_hit_rate` property.
- Cache is seeded-deterministic: same inputs always get same cached output (no stale TTL in simulation context).
- Tests: mock client, verify cache deduplicates calls; verify hit rate reported correctly.

### 5.3 Phase 2 — Full integration run

**PR title:** `test(simulator): full end-to-end integration run (500 students, 12 weeks, v2_full)`

Using `configs/phase2_full.yaml`. Deliverables as specified in the mission brief:

- `validation/phase_2/integration_run_logs.txt`
- `validation/phase_2/integration_data_integrity.md`
- `validation/phase_2/component_spot_checks.md`
- `validation/phase_2/integration_validation_criteria.md`
- Four diagnostic plots (θ distribution, Elo convergence, misconception activation, detector confidence)

**Acceptance gate:** `is_simulated` invariant passes (per §2.4 — pending clarification), all Phase 1 criteria 1–7 re-run, all Phase 2 criteria met or documented.

### 5.4 Phase 2 — New four-condition ablation

**PR title:** `test(simulator): four-config ablation study (v1 vs v2 vs detector-only vs no-tutor control)`

New module `ml/simulator/validation/ablation_investor.py` (distinct from existing `ablation.py` which is preserved). Four conditions:

| Condition | Response model | Detector | Tutor | Rewriter | Item selection |
|---|---|---|---|---|---|
| `v1_uniform` | uniform | off | off | off | ZPD |
| `v2_misconception_only` | weighted | on | off | off | ZPD |
| `v2_full` | weighted | on | on | on | ZPD |
| `no_tutor_control` | uniform | off | off | off | random |

Metrics: Elo gain/hr, median time-to-mastery (attempts), retention @ 7d and 30d, misconception resolution (median attempts), all with 95% CI. Pairwise p-values for key comparisons.

**Monotonic ordering check:** `v2_full > v2_misconception_only > v1_uniform > no_tutor_control` on Elo gain/hr. If the ordering fails, investigate and document; do not silently adjust.

Plots: `ablation_elo_gain.png`, `ablation_time_to_mastery.png`, `ablation_retention_curve.png`.
Investor summary: `validation/phase_2/ablation_investor_summary.md`.

### 5.5 Phase 3 — Investor report

**PR title:** `docs: simulator Phase 2 comprehensive validation report`

`docs/simulator/phase_2_investor_report.md`. Structure per mission brief: executive summary, architecture, Phase 1 validation, Phase 2 integration test, ablation results, assumptions & limitations, next steps, technical appendix.

---

## 6. Validation criteria

### Phase 1 criteria (re-run in Phase 2 integration PR)

| # | Criterion | Tool | Target |
|---|---|---|---|
| 1 | 2PL discrimination recovery | Pearson ρ | ≥ 0.75 |
| 2 | 2PL difficulty recovery | Pearson ρ | ≥ 0.85 |
| 3 | Student θ recovery | Pearson ρ | ≥ 0.80 |
| 4 | BKT recovery | param within ±0.05 | ≥ 80% of skills |
| 5 | Elo convergence | rolling std dev | < 50 by week 4–5 |
| 6 | Calibration curve | IRT | `a` ∈ (0.3, 3), `b` ∈ (−2, +2) |
| 7 | Population KS test | KS test | p > 0.05 or documented shift |

### Phase 2 criteria (new)

| # | Criterion | Target |
|---|---|---|
| 8 | Misconception resolution rate | Median ≤ 8 attempts |
| 9 | Rewriter deployment rate | ≥ 60% of quiz items as verified variants |
| 10 | Token spend | ≤ $500 total (Haiku at published rates) |

---

## 7. Report outline (Phase 3)

1. Executive summary (¼ page)
2. Simulator architecture — seven-component diagram, determinism guarantee (½ page)
3. Phase 1 validation — real-data calibration results, Gate A remediations stated factually (½ page)
4. Phase 2 integration test — 500s × 12w run, key stats, all criteria pass/fail (½ page)
5. Ablation study — four-condition table, ordering claim, p-values, what it means for the NZ pilot (1 page)
6. Assumptions & limitations — honest list, not hidden (¼ page)
7. Next steps & pilot strategy — NZ schools, 12-week intervention, success criterion (¼ page)
8. Technical appendix — model specs, detector architecture, rewriter pipeline (≤ ½ page)

---

## 8. Clarifying question

**Q1 (blocking for Phase 2 integration PR):**

The `is_simulated` invariant check in `phase2_pipeline.py` uses `explanation_style is not None` as a proxy — it does not query the literal `is_simulated=True` field that the IO writers stamp on rows. The IO writers do stamp the field correctly; the invariant check just doesn't use it.

**Does the data-integrity check need to verify the literal `is_simulated` field (i.e., a queryable boolean column in Postgres or a parquet column), or is verifying that `explanation_style` is populated sufficient for this validation pass?**

If the literal field must be checked: `_check_is_simulated_invariant` in `phase2_pipeline.py` needs to be rewritten to inspect `row["is_simulated"]` from the parquet output rather than the in-memory records. That is a small but explicit change that belongs in PR-1.5.

If the proxy is acceptable: no change needed; document it in the data-integrity report as a known implementation detail.
