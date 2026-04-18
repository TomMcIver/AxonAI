# AxonAI Simulator v1 — plan

Session: `011PZhsWvu9gwP5Gv2K6UH83`

Phase 1 deliverable. No simulator code in this PR — planning only. Wait for approval before starting Phase 2.

---

## 1. Repo state

### Legacy-ML deletion status

**Python deletion (PR #79, merged):** complete. The following are all absent from the tree:

- `agents/main_tutor_agent.py`, `agents/quiz_builder_agent.py`, `agents/progression_analyzer.py`, `agents/mastery_tracking_agent.py`, `agents/admin_ai_dashboard.py`, `agents/student_ai_analyzer.py`
- `ml/features/{mastery,risk,engagement,teaching_strategy,student_filters}.py`
- `ml/trainers/{base,mastery,risk,engagement,teaching_strategy}.py`
- `ml/{pipeline,lambda_handler}.py`
- `config/ai_config.py`

**Tracked SQLite artifacts (PR #80, draft, pending merge):** cleans up `instance/school_management.db` and `school_ai.db`. Both are binary artifacts; `.gitignore` already covers `*.db` so they won't return. `app.py` regenerates the SQLite fallback on startup, so no code change needed.

**Stale residue in `ml/`** (still present, flagged for decision — see ambiguities §6):

- `ml/README.md` — describes the deleted scikit-learn pipeline
- `ml/config.py` — AWS Secrets Manager + S3 bucket for the deleted pipeline
- `ml/db.py` — RDS connection helper (Secrets Manager-based) that the deleted pipeline used
- `ml/excluded_students.py` — demo-student allowlist for the deleted training code; imports `from db import get_connection`, so it breaks without `ml/db.py`
- `ml/requirements.txt` — tiny standalone file for the deleted Lambda packaging
- `ml/__init__.py` — docstring already says *"legacy training pipeline removed; simulator v2 rebuild pending"*

None of these are referenced by live app code (`app.py`, `main.py`, `routes/`, `services/`, `core/`). `grep` for `from ml` / `import ml` across the repo returns nothing in live paths — confirms they're dead.

### Current layout (top level)

```
app.py              main.py             pyproject.toml      requirements.txt
DATABASE_SCHEMA.md  README.md           uv.lock             vercel.json
config/             core/               frontend/           instance/
ml/                 models/             routes/             schema/
scripts/            services/           templates/          utils/
```

No existing `data/`, `docs/`, or `tests/` directories at the repo root.

### Proposed simulator package path

Prompt default: `axonai/ml/simulator/`.

**I recommend `ml/simulator/` instead** and want your sign-off. Rationale:

- This repo has **no `axonai/` namespace package**. Top-level modules are flat (`core/`, `ml/`, `routes/`, `services/`, …). Introducing `axonai/ml/simulator/` would create a mixed layout with only the simulator under the namespace.
- `ml/__init__.py` already signals the intent ("simulator v2 rebuild pending").
- Keeps imports short: `from ml.simulator.psychometrics import irt_2pl`.
- CLI in PR 9 becomes `python -m ml.simulator` rather than `python -m axonai.ml.simulator`.

Either works; flag if you prefer the prompt default.

### Dataset paths

Prompt states:

- `data/raw/eedi_mining_misconceptions/`
- `data/raw/map_misunderstandings/`
- `data/raw/assistments_2009_2010/`
- Sample data at `data/raw/*_sample/` for tests.

None of these paths exist in the repo yet. PR 4 is blocked until the sample data is checked in (or provided via Git LFS / the path is confirmed). `data/processed/` will be gitignored with a `.gitkeep`.

---

## 2. Dependency audit

Current `pyproject.toml` is app-focused (Flask, SQLAlchemy, OpenAI, etc.). `requirements.txt` adds FastAPI/boto3 for the Lambda API. Neither covers numerical/psychometric stacks.

### Additions needed for simulator

| Package        | Purpose                                                        | PR needing it |
|----------------|----------------------------------------------------------------|---------------|
| `numpy`        | Array math (IRT, BKT, HLR, Elo)                                | PR 3 |
| `scipy`        | Optimisation, stats (KS-test, log-normal, logistic)            | PR 3, PR 10 |
| `pandas`       | DataFrames for loaders and IRT fitting                         | PR 4, PR 5 |
| `pyarrow`      | Parquet IO (`data/processed/`)                                 | PR 4 |
| `pyyaml`       | `configs/*.yaml` for simulation configs                        | PR 2, PR 9 |
| `pydantic`     | Config validation (already in `requirements.txt` v2, not in `pyproject.toml`) | PR 2 |
| `networkx`     | Concept graph (DAG operations: prerequisites, topo sort)       | PR 6 |
| `py-irt`       | 2PL IRT fitting (primary path)                                 | PR 5 |
| `matplotlib`   | Validation plots (time-to-mastery, calibration, θ distribution) | PR 10 |
| `pytest`       | Test runner (no test infra currently)                          | PR 2+ |
| `pytest-xdist` | Parallel tests (optional)                                      | PR 2 |

Dev-only: `matplotlib`, `pytest*`. Consider a `[project.optional-dependencies]` group `simulator` + `simulator-dev`.

`py-irt` fallback: prompt allows `mirt` via `rpy2` as an alternative. I propose **not** installing `rpy2` by default — add only if `py-irt` fit fails calibration. Flag if you want both available.

`pydantic` version: `requirements.txt` pins `>=2.0.0`. Keep v2 for simulator too.

---

## 3. Architecture (from your spec)

Reproducing for confirmation — no new requirements introduced here.

### Package layout (proposed at `ml/simulator/`)

```
ml/simulator/
├── __init__.py
├── config.py                       # Frozen SimulationConfig dataclass
├── cli.py                          # python -m ml.simulator {calibrate|run|validate}
├── psychometrics/
│   ├── __init__.py
│   ├── irt_2pl.py                  # prob_correct, sample_response, log_likelihood
│   ├── bkt.py                      # BKTParams, BKTState, update, predict_correct
│   ├── elo.py                      # expected, update, k_factor
│   └── hlr.py                      # predict_recall, update_half_life
├── data/
│   ├── __init__.py
│   ├── assistments_loader.py       # responses_df, skills_df; filter <150 resp
│   ├── eedi_misconceptions_loader.py  # questions, options, distractor→miscon, catalogue
│   ├── map_loader.py               # explanations_df (loader only, v1)
│   ├── concept_graph.py            # ConceptGraph (networkx); prereq/succ/topo_next
│   └── item_bank.py                # ItemBank (items with a, b, distractor miscon meta)
├── calibration/
│   ├── __init__.py
│   ├── fit_2pl.py                  # py-irt fit; 20% heldout; → item_params.parquet
│   ├── fit_bkt.py                  # EM per skill; → bkt_params.parquet
│   └── priors.py                   # student_priors.json from calibrated artefacts
├── student/
│   ├── __init__.py
│   ├── profile.py                  # StudentProfile dataclass
│   ├── generator.py                # StudentGenerator (seeded, deterministic)
│   └── dynamics.py                 # apply_practice, apply_forgetting
├── loop/
│   ├── __init__.py
│   ├── teach.py                    # v1 stub — emit TEACH event
│   ├── revise.py                   # HLR-driven revision list (recall ∈ (0.40, 0.70))
│   ├── quiz.py                     # ZPD select + simulate_response (v1: uniform distractor)
│   └── runner.py                   # TermRunner — yields event records
├── io/
│   ├── __init__.py
│   ├── postgres_writer.py          # Writes with is_simulated=True; migration added here
│   └── local_writer.py             # Parquet output
└── configs/
    ├── small.yaml                  # dev/smoke
    └── full.yaml                   # PR 10: 3000 students × 10 weeks

tests/simulator/                    # mirrors package layout; one test file per module
data/raw/*_sample/                  # sample inputs (checked in)
data/raw/*/                         # full inputs (gitignored)
data/processed/                     # parquet + json artefacts (gitignored + .gitkeep)
validation/                         # fit reports, plots, v1_results.md
```

### Module specs

Faithful to the spec. Key invariants re-stated:

- **`config.py`** — Frozen `SimulationConfig` dataclass. Every constant has a source comment (paper/dataset). No magic numbers anywhere else.
- **`psychometrics/*`** — pure functions, no IO. Hand-computed unit tests.
- **`data/*_loader.py`** — each caches to parquet under `data/processed/`; tests load `*_sample/` and check schema + row counts.
- **`calibration/*`** — outputs `item_params.parquet`, `bkt_params.parquet`, `student_priors.json`; fit reports under `validation/`.
- **`student/profile.py`** — `misconception_susceptibility` is a reserved empty dict in v1 (v2 seam).
- **`loop/quiz.py`** — `simulate_response` is the single v2-replacement seam. v1 uniform distractor.
- **`io/postgres_writer.py`** — **every row `is_simulated=True`**. Migration adds the column if missing. Non-negotiable.
- **`cli.py`** — three subcommands: `calibrate`, `run --config`, `validate --run-id`.

### Validation criteria (for PR 10)

All seven must pass. Reproduced verbatim from the spec:

1. IRT recovery on ASSISTments heldout — AUC ≥ 0.75, calibration err < 0.05, pass ≥ 85% items.
2. Simulator round-trip — refit 2PL on sim output; (a, b) within ±0.2/±0.15 logits of truth, ≥ 85%.
3. BKT posterior agreement — P(known) > 0.85 within 3 attempts of threshold crossing, ≥ 85%.
4. Elo convergence — rolling std (window 10) < 50 within 30 attempts, ≥ 80% students.
5. Time-to-mastery — unimodal log-normal-ish, mean 8–20 attempts → `validation/time_to_mastery.png`.
6. Calibration curve — deciles within 0.05 of diagonal → `validation/calibration.png`.
7. Population sanity — KS-test simulated θ vs ASSISTments empirical, p > 0.05 → `validation/theta_distribution.png`.

### Non-negotiables (reproduced for ack)

- Frontend is off-limits.
- `is_simulated=True` on every simulator row.
- No magic numbers outside `config.py`.
- Deterministic given seed.
- No LLM calls in v1.
- Math only.
- Eedi loaded but not used in v1 response model (clean seam in `loop/quiz.py`).
- MAP loaded only; no v1 training.

---

## 4. PR plan

Each PR carries its own branch and the session ID. "Parallel-safe with" = can be developed in a separate session without waiting.

| PR   | Title                                               | Depends on | Parallel-safe with | One-line summary |
|------|-----------------------------------------------------|------------|--------------------|------------------|
| 2    | `feat(simulator): package skeleton`                 | Phase 1 OK | —                  | Create `ml/simulator/` tree, empty stubs with docstrings, add deps to `pyproject.toml`, pytest infra, import-only tests. |
| 3    | `feat(simulator): psychometrics core`               | PR 2       | PR 4               | IRT 2PL, BKT, Elo, HLR as pure functions; hand-computed unit tests. No IO. |
| 4    | `feat(simulator): dataset loaders`                  | PR 2       | PR 3               | ASSISTments, Eedi 2024, MAP loaders; sample-data tests; parquet caches under `data/processed/`. |
| 5    | `feat(simulator): calibration layer`                | PR 3, PR 4 | —                  | Fit 2PL IRT + per-skill BKT on ASSISTments; derive student priors; write fit reports to `validation/`. |
| 6    | `feat(simulator): concept graph + item bank`        | PR 4, PR 5 | PR 7 (partial)     | `ConceptGraph` from ASSISTments skill hierarchy; `ItemBank` with calibrated (a, b) + Eedi distractor metadata. |
| 7    | `feat(simulator): student profile + dynamics`       | PR 3, PR 5 | PR 6               | `StudentProfile`, `StudentGenerator` (seeded), `apply_practice` / `apply_forgetting` dynamics. |
| 8    | `feat(simulator): loop + runner`                    | PR 3, PR 6, PR 7 | —            | `teach` stub, HLR `revise`, ZPD `quiz.select_next_item` + `simulate_response`, `TermRunner` event stream. |
| 9    | `feat(simulator): io layer + CLI + migration`       | PR 8       | —                  | `postgres_writer` w/ `is_simulated` migration, `local_writer` parquet, `python -m ml.simulator {calibrate,run,validate}`. |
| 10   | `feat(simulator): full validation run`              | PR 9       | —                  | 3000 students × 10 weeks; all 7 validation gates pass; plots + `validation/v1_results.md`. |

### Sequencing visual

```
PR 2 ─┬─ PR 3 ──┐
      └─ PR 4 ──┴─ PR 5 ─┬─ PR 6 ─┐
                         └─ PR 7 ─┴─ PR 8 ─ PR 9 ─ PR 10
```

PR 3 and PR 4 can run in parallel sessions immediately after PR 2 merges.
PR 6 and PR 7 can run in parallel after PR 5 merges (PR 6 wants the calibrated item bank; PR 7 wants priors; both are independent of each other).

---

## 5. Concerns and open questions

Flagging before Phase 2.

### Ambiguities — need a call from you

1. **Package path.** `ml/simulator/` (recommended) vs the prompt default `axonai/ml/simulator/`. See §1.
2. **Stale `ml/` residue.** `ml/README.md`, `ml/config.py`, `ml/db.py`, `ml/excluded_students.py`, `ml/requirements.txt` describe the deleted pipeline. Options:
   - **(a)** Delete all in a follow-up cleanup PR before PR 2. Cleanest.
   - **(b)** Delete as part of PR 2. Keeps the cleanup bundled with the skeleton.
   - **(c)** Leave them; simulator ignores them. Weakest — `ml/excluded_students.py` does `from db import get_connection` referencing `ml/db.py`; if `db.py` stays, `excluded_students.py` still works, but it's dead code with no consumers.
   My recommendation: **(a)** — small follow-up deletion PR while Phase 1 is in review.
3. **`io/postgres_writer.py`'s `db.py`.** The spec says *"writes to production schema via `db.py`"*. Does that mean:
   - re-using `ml/db.py` (Secrets Manager-based, production RDS), or
   - introducing a new DB helper inside `ml/simulator/io/` with a different auth path?
   If the former, I need to keep `ml/db.py` (contradicting ambiguity 2). If the latter, I'll add a simulator-local DB helper.
4. **`is_simulated` migration format.** No `migrations/` directory exists in this repo. `schema/rds_postgres_schema.sql` is the single schema dump (1400+ lines). Options:
   - Add `schema/migrations/NNNN_add_is_simulated.sql` and run manually, OR
   - Edit `schema/rds_postgres_schema.sql` to add `is_simulated BOOLEAN NOT NULL DEFAULT FALSE` to every event table, OR
   - Introduce Alembic (bigger lift). Which do you want?
5. **Which tables need `is_simulated`?** The spec says *"every row"*. I read that as every event-writing table the simulator touches (responses/attempts, teach events, revision events, session metadata). I'll list exact tables from `rds_postgres_schema.sql` in PR 9. Confirm this interpretation (or give the canonical list).
6. **ASSISTments skill hierarchy for the concept graph.** ASSISTments 2009-2010 distributes skills as flat labels per row; the hierarchy/DAG is not in that dataset natively. Options: (a) derive empirical prerequisite edges from co-occurrence/ordering, (b) use the Khan Academy / Eedi concept taxonomy if you have a crosswalk, (c) hand-curated. This affects PR 6. Which do you prefer?
7. **Response-time model.** Spec has `response_time_lognorm_params` on `StudentProfile` but no module for fitting it. Will ASSISTments timestamps drive this in `calibration/priors.py`, or is it a pure prior? I'll assume **empirical fit in `priors.py`** unless told otherwise.
8. **Test directory.** Proposed `tests/simulator/` mirroring the package layout. Flag if you'd rather have tests colocated (`ml/simulator/psychometrics/tests/…`).

### Non-blocking notes

- No `pytest` / CI infra exists in this repo yet. PR 2 introduces pytest; CI hookup can be a separate concern.
- `ml/__init__.py` is a one-line docstring; safe to extend to export the simulator subpackage in PR 2.
- Prompt references a `db.py` in PR 9's `postgres_writer` but does not specify its path. Addressed in question 3 above.
- Full ASSISTments, Eedi, and MAP datasets are on your local machine only. PR 4 CI tests must run against sample data only; the full-dataset calibration run in PR 5 will be executed by you locally (or you'll need to share via LFS/external storage). I'll call this out in the PR 4/5 descriptions.
- `validation/` directory does not yet exist. Created in PR 5 (first fit report) with `.gitkeep`.

---

## 6. What I need from you before Phase 2

- Approval of this plan.
- Decisions on ambiguities 1–8 above (especially 1, 2, 3, 4, 6).
- Confirmation that PR #80 (SQLite artifact cleanup) should merge before PR 2 starts.
- Sample data for ASSISTments, Eedi 2024, MAP committed (or path/method confirmed) before PR 4.
- Heads-up if you want additional non-negotiables beyond the eight already listed.

Once you approve and answer the ambiguities, I'll start PR 2 on a fresh branch.
