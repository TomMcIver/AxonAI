# Simulator Phase 2 — Plan & Audit

**Status:** Audit. No implementation in this PR. Gate B does not open until all Gate A PRs merge.

**Branch:** `claude/axonai-simulator-phase-2-3xiHF`

**Scope:** Close the four Phase 1 deferrals (Gate A) and ship the moat
layer — misconception activation, detection, explanation-style
selection, LLM tutor, and dynamic rewriting (Gate B).

---

## 1. v1 state audit

### 1.1 Phase 1 merge verification

All Phase 1 PRs confirmed merged into `main` (walked `git log --oneline`
on the current branch, which tracks `main`):

| PR   | Commit   | Summary                                                   |
| ---- | -------- | --------------------------------------------------------- |
| #82  | a45f43a  | `feat(simulator): package skeleton`                       |
| —    | d81d89b  | `feat(simulator): psychometrics core`                     |
| —    | eeb6ebc  | `feat(simulator): dataset loaders`                        |
| #86  | b3ae544  | `feat(simulator): calibration — 2PL, BKT EM, priors`      |
| —    | 8c619ef  | `feat(simulator): concept graph + item bank`              |
| —    | 31ecadb  | `feat(simulator): student profile, generator, dynamics`   |
| —    | b48d3e5  | `feat(simulator): teach → quiz → revise loop + runner`    |
| —    | 3c240aa  | `feat(simulator): IO + CLI + sim_* shadow tables`         |
| —    | 4b6040d  | `feat(simulator): Phase 1 validation — self-consistency`  |
| —    | 4650107  | `fix(simulator): address Copilot review on PR 10`         |
| —    | 3a62adb  | `fix(simulator): cross-platform install + ASCII output`   |
| #92  | 6cf973e  | Phase 1 ship-to-main merge                                |

No divergence from the Phase 1 plan detected.

### 1.2 `ml/simulator/` tree

```
ml/simulator/
├── __init__.py / __main__.py / cli.py / cli_smoke.py
├── config.py                 # SimulationConfig dataclass
├── configs/                  # full.yaml, small.yaml
├── calibration/              # fit_2pl.py, fit_bkt.py, priors.py
├── data/                     # assistments_loader, eedi_misconceptions_loader,
│                             # map_loader, concept_graph, item_bank
├── io/                       # shadow table writers
├── loop/                     # quiz, revise, teach (stub), runner
├── migrations/               # 0001_is_simulated.sql
├── psychometrics/            # irt_2pl, bkt, elo, hlr
├── student/                  # profile, generator, dynamics
└── validation/               # run_validation + truth generator
```

Matches the Phase 1 plan. `student/profile.py` reserves
`misconception_susceptibility: dict[int, float]` as the empty seam that
PR B1 will populate. `loop/quiz.py:simulate_response` today returns
`(is_correct, response_time_ms)` and makes no distractor choice —
PR B2 replaces this with the misconception-weighted variant behind a
`response_model` config flag. `loop/teach.py` is an intentional stub
that PR B7 will replace with the real LLM call.

### 1.3 Phase 1 deferrals (recap)

From `docs/simulator/v1-validation.md §4`:

1. **BKT recovery not measured** on Phase 1's synthetic truth (one
   attempt per item; no hidden-state process). → Gate A PR A2.
2. **KS rejection on correct-rate distribution** (truth = non-adaptive;
   sim = ZPD-adaptive). → Gate A PR A2.
3. **Short-session dominance** (15 × 5 too short for BKT mastery
   propagation). → addressed implicitly by the Gate A real-data run at
   `full.yaml` scale (3000 students × 10 weeks).
4. **No concept-graph recovery check** against held-out pairs. → Gate A
   PR A3.

---

## 2. Dataset paths and access

### 2.1 S3 credential state (BLOCKER for execution)

**This audit session cannot reach S3.** Neither the `aws` CLI nor
`boto3` is installed, and no `AWS_*` env vars are set:

```
$ aws --version     # aws: command not found
$ python3 -c 'import boto3'  # ModuleNotFoundError
$ env | grep AWS_   # (empty)
```

Before Gate A PR A1 can execute, the operator must:

1. `pip install boto3 awscli` (or add to `simulator` optional deps).
2. Run `aws sts get-session-token --duration-seconds 3600` locally.
3. Pass the three values plus `AWS_DEFAULT_REGION=ap-southeast-2` into
   the Claude Code session environment.
4. Extend `ml/simulator/data/*_loader.py` with an S3 path branch (if
   path starts with `s3://`, stream via `boto3.client('s3').get_object`
   into `pandas.read_csv(BytesIO(...))`).

Row 4 is a small loader change that belongs in PR A1 — the spec says
"Loaders in `ml/simulator/data/` will detect S3 paths" but the current
loaders only take local paths. This will be called out as part of A1's
first commit, not a separate PR.

### 2.2 Declared paths (not verified — no S3 access this session)

| Dataset                    | S3 path                                                                       | Used by       |
| -------------------------- | ----------------------------------------------------------------------------- | ------------- |
| ASSISTments Skill Builder  | `s3://axonai-datasets-924300129944/assistments/2012-2013-data-with-predictions-4-final.csv` | A1, A2, A3    |
| Eedi 2024 Kaggle folder    | `s3://axonai-datasets-924300129944/eedi_mining_misconceptions/`               | B1, B3        |
| MAP Kaggle folder          | `s3://axonai-datasets-924300129944/map_misunderstandings/`                    | B4            |

**Concern.** The Phase 1 plan referenced ASSISTments **2009-2010**
Skill Builder; the Phase 2 spec points at a **2012-2013** CSV filename.
These are different releases with different skill taxonomies. Either
the filename is a typo, or the taxonomy that feeds the concept graph
and the gold prerequisite edges must be derived from the 2012-2013
release. Flagged as clarifying question Q1 below.

File-size / row-count verification is deferred to PR A1's first step;
this audit session cannot do it.

---

## 3. Dependency audit (not installed yet)

Gate B needs the following new deps on top of the existing `simulator`
extras:

| Package                    | Purpose                                    | Gate B PRs  |
| -------------------------- | ------------------------------------------ | ----------- |
| `boto3>=1.34`              | S3 reads                                   | A1 (early)  |
| `sentence-transformers>=3` | Retriever embeddings (MiniLM-L6-v2)        | B3          |
| `torch` (CPU)              | Backing `sentence-transformers` + reranker | B3, B4      |
| `anthropic>=0.39`          | Default LLM client                         | B7, B8, B9  |
| `openai>=1.93` (already)   | Alternate LLM client                       | B7, B8, B9  |
| `pytest-asyncio>=0.23`     | Async LLM call tests                       | B7+         |
| `scikit-learn>=1.4`        | Calibration metrics, classifier baselines  | A1, B3, B4  |
| `matplotlib` (already dev) | QQ plots for KS test                       | A2          |

Register these in `pyproject.toml` under a new `simulator-phase-2`
extras group. Do not add yet — the audit PR adds no deps.

**Token-budget concern.** The LLM-using PRs (B7, B8, B9) each report
their token spend per the non-negotiable. The Phase 2 spec caps the
full B11 run at $500 across 3000 students × 10 weeks × 3 sessions ≈
90k sessions. That is ~$0.0055 / session, which is very tight once
rewriter verification (two LLM calls per variant) is included. The
budget likely only survives with aggressive caching + cheap-tier
models (haiku-4.5 / gpt-4o-mini). Flagged as clarifying question Q3.

---

## 4. Architecture — Gate A + Gate B

### 4.1 Gate A (three PRs, sequential, all block Gate B)

**PR A1 — Real-dataset calibration.**
- S3 branch added to `assistments_loader.py`, `eedi_misconceptions_loader.py`, `map_loader.py`.
- Run `fit_2pl` on full ASSISTments → `data/processed/real_item_params.parquet`.
- Run `fit_bkt` per skill → `data/processed/real_bkt_params.parquet`.
- Run `derive_priors` → `data/processed/real_student_priors.json`.
- Add `ml/simulator/calibration/leakage_check.py`; run it; include output in fit report.
- Diagnostics: `validation/phase_2/real_2pl_fit_report.md`, `real_bkt_fit_report.md`.
- Acceptance: 2PL converges ≥85% of items with ≥150 real responses; BKT slip/guess/p_transit in plausible bands for ≥75% of skills; real-vs-synthetic gap reported honestly.

**PR A2 — BKT recovery + population KS test.**
- Simulate cohort per skill from PR A1's BKT params; refit; report ±0.05 recovery for ≥80% of skills → `validation/phase_2/bkt_recovery.md`.
- 3000 synthetic students × 10 weeks from `real_student_priors.json`; compute θ distribution; KS vs. ASSISTments-inferred θ; QQ plot.
- Acceptance: KS p > 0.05 OR documented pedagogically plausible shift.

**PR A3 — Concept-graph held-out validation.**
- Gold standard: 20–40 prerequisite edges from ASSISTments skill taxonomy docs + hand-curated standard algebra/arithmetic progressions → `data/gold/assistments_prereq_edges.json`.
- Build graph from 80% of responses; test gold edges; report precision/recall/F1 → `validation/phase_2/concept_graph_validation.md`.
- Acceptance: recall ≥ 0.60, precision ≥ 0.40, OR documented remediation.

**Gate A exit:** PR A1/A2/A3 merged, acceptance criteria met or
remediations applied, `docs/simulator/phase_2_gate_a_summary.md`
published.

### 4.2 Gate B (twelve PRs)

| PR   | Title                                   | Depends on  | Parallel with |
| ---- | --------------------------------------- | ----------- | ------------- |
| B1   | Misconception susceptibility            | Gate A      | —             |
| B2   | Misconception-weighted response model   | B1          | B3, B4        |
| B3   | Misconception detector — retrieval      | Gate A      | B1, B2        |
| B4   | Misconception detector — rerank         | B3          | B2            |
| B5   | Detector integration into loop          | B2, B4      | —             |
| B6   | Explanation-style selector              | Gate A      | B1–B5         |
| B7   | LLM tutor integration                   | B6          | B8            |
| B8   | Question rewriter                       | Gate A      | B7, B9        |
| B9   | Rewriter equivalence verifier           | B8          | B7            |
| B10  | Rewriter sample-testing harness         | B9          | —             |
| B11  | Integration + v2 validation run         | B1–B10      | —             |
| B12  | Ablation study                          | B11         | —             |

All acceptance criteria from the Phase 2 spec carry unchanged. Per-PR
deliverables reproduced in `docs/simulator/phase_2_plan.md §5`.

### 4.3 Flagged architectural concerns

1. **Concept-id scheme mismatch.** `StudentProfile.misconception_susceptibility` is keyed `dict[int, float]`, but Eedi 2024 misconceptions are labelled by string IDs (`Misconception_123`). Either widen the key type to `int | str`, or establish a deterministic int-mapping of Eedi IDs in B1. The plan assumes an int-mapping table committed as `data/processed/eedi_misconception_id_map.json`.

2. **Determinism vs. LLM inference.** Sentence-transformer inference and cross-encoder reranking are only deterministic if seeds, device, and float precision are pinned. CPU inference with a pinned model revision + `torch.manual_seed` is stable. GPU inference is not guaranteed stable. B3/B4 should pin to CPU for evaluation runs; document any GPU-side regeneration as non-deterministic.

3. **Rewriter blast radius.** B8 introduces LLM-written items into the loop. Even with B9 (equivalence verifier) and B10 (drift harness), rewritten variants never touch the real-student DB — `is_simulated=True` invariant plus the Phase 2 non-goal "No live RDS writes from LLM-generated content" prevents this. Explicit acceptance gate in B11: verify every rewritten item emitted during the run has `is_simulated=True`.

4. **Explanation-style selector rule gaps.** The five rules cover common cases but leave combinations ambiguous: e.g., high-confidence misconception AND BKT=not-learned — does `contrast_with_misconception` win or `worked_example`? Rules are ordered in the spec (misconception rule first), so first-match-wins is the obvious tie-break, but this should be stated explicitly in B6's docstring and tested.

5. **Detector seen-vs-unseen split.** B3 requires 20% of misconceptions to be **unseen in training**. The Eedi catalogue has ~2500 misconceptions, so 500 held-out. Splitting by misconception (not by row) is a column-disjoint split that imitates the Kaggle test-time distribution. The loader needs a deterministic-seeded split helper; spec does not mandate one.

---

## 5. Per-PR deliverable reproduction

Full Gate A + Gate B per-PR specifications are reproduced verbatim
from the Phase 2 brief and kept here as the single source of truth
Claude Code will execute from. Any deviation during execution must
update this file in the relevant PR.

_(Spec reproduced in the linked sections of the prompt; this file
tracks only divergences as they arise.)_

---

## 6. Clarifying questions

See `§7` of the PR description; five questions surfaced. Gate A
execution is **blocked** on Q1 (ASSISTments release version),
unblocked on Q3 (LLM provider choice) because A1–A3 are LLM-free.

---

## 7. Non-goals (restated)

- Frontend work.
- Real-student pilot integration.
- Teacher-facing misconception UI.
- Bandit-based selector (v3).
- NCEA alignment.
- Non-math subjects.
- Voice I/O.
- Live RDS writes from LLM-generated content.

---

## 8. Next action

Await approval on this plan + answers to the five clarifying questions
(§7 of PR description). No code or deps land in this PR.
