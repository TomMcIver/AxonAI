# AxonAI ML training pipeline

Batch training jobs read learner telemetry from **Amazon RDS (PostgreSQL)**, train lightweight **scikit-learn** models, upload artifacts to **S3**, and append scored outputs to **`model_predictions`**. Scheduling is intended to run this code on **AWS Lambda** (e.g. EventBridge cron) or manually.

Credentials for RDS are loaded **only** from **AWS Secrets Manager** (`axonai/db/credentials` by default). Nothing is hardcoded.

## Models

| Model | Algorithm | Predicts | Labels / target |
|-------|-----------|----------|-----------------|
| **Mastery** | Logistic regression (with `StandardScaler`) | Whether a student is likely to maintain strong mastery | `1` if mean `mastery_score` across concepts ≥ 0.65; if everyone is on one side of that cut, a **median split** on mean mastery is used instead |
| **Risk** | Logistic regression | Whether a student is **at risk** | `1` if `overall_risk_score` ≥ 0.4 **or** (has quiz data and average quiz % below 50) |
| **Engagement** | Ridge regression | Continuous **overall engagement** | `overall_engagement_score` from `student_learning_profiles` |
| **Teaching strategy** | Logistic regression | Whether a **pedagogical_memory** row represents a successful strategy pattern | `1` if `success_rate` ≥ 0.5 |

Feature definitions match the production tables listed in the monorepo spec (`students`, `student_learning_profiles`, `conversations`, `messages`, `concept_mastery_states`, `quiz_sessions`, `pedagogical_memory`, `student_concept_flags`, `model_predictions`).

## Layout

- `config.py` — region (`ap-southeast-2`), S3 bucket, Secrets Manager secret id, DB name default
- `db.py` — `get_connection()` using `psycopg2` + Secrets Manager JSON (`username`, `password`, `host`, `port`, optional `dbname`/`database`)
- `features/*.py` — `build_*_dataset()` → `Dataset(features=DataFrame, labels=Series)`
- `trainers/*.py` — fit models, return `TrainResult`
- `pipeline.py` — orchestrates training, S3 upload, RDS inserts
- `lambda_handler.py` — Lambda entry point calling `run_pipeline()`

## S3 artifacts

Bucket: `axonai-model-artifacts-924300129944` (override with `AXONAI_MODEL_ARTIFACTS_BUCKET`).

Each trained model is stored as:

- `models/<type>/latest/model.joblib`
- `models/<type>/<UTC-timestamp>/model.joblib`

The joblib payload includes the fitted estimator, feature column names, and training metrics.

## Running locally

Python **3.11+**, AWS credentials with `secretsmanager:GetSecretValue`, RDS network access, and `s3:PutObject` on the artifacts bucket.

```bash
cd /path/to/AxonAI
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r ml/requirements.txt
set AWS_REGION=ap-southeast-2
python ml/pipeline.py
```

Environment variables:

| Variable | Purpose |
|----------|---------|
| `AWS_REGION` | Defaults to `ap-southeast-2` |
| `AXONAI_DB_SECRET_ID` | Secrets Manager secret id (default `axonai/db/credentials`) |
| `AXONAI_DB_NAME` | Database name if not in the secret (default `axonai`) |
| `AXONAI_MODEL_ARTIFACTS_BUCKET` | S3 bucket override |
| `AXONAI_ML_MIN_STUDENTS` | Minimum **distinct students** required to train (default `5`) |

Training is skipped gracefully when fewer than the minimum number of students have usable rows.

## Lambda

Package the `ml/` tree (or install as a layer), set the handler to `lambda_handler.handler`, and attach an IAM role that allows Secrets Manager read, S3 writes to the artifacts bucket, and VPC access to RDS if the database is private.

EventBridge can invoke the function on a schedule; the handler returns a JSON summary of each model’s status (`ok`, `skipped`, or `error`).

## RDS note

The live instance may use database name `postgres` or `axonai` depending on environment. Put the correct `dbname` / `database` field in the Secrets Manager JSON, or set `AXONAI_DB_NAME` when running locally.
