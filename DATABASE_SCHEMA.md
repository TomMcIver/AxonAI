# AxonAI PostgreSQL — database schema (source of truth)

This document is the **canonical data-model reference** for the AxonAI monorepo. It combines:

1. **Live PostgreSQL metadata** — tables, exact data types, nullability, defaults, primary keys, foreign keys, indexes, and row counts. This block is **machine-generated** from `pg_catalog` / `information_schema` and must be refreshed whenever the physical schema changes.
2. **Application reference** — how the Flask-SQLAlchemy models and Lambda/FastAPI SQL map to relational tables (useful for developers; the live block remains authoritative for physical details).

---

## 1. How to refresh the live catalog

### 1a. Canonical DDL file (`schema/rds_postgres_schema.sql`)

The **authoritative** table definitions, constraints, and indexes are captured with:

```bash
pg_dump --schema-only --no-owner --no-privileges
```

against database **`postgres`** on the RDS instance (see §2). On **AWS Cloud Shell**, the stock `pg_dump` is often **15.x** while the server is **17.x**, which aborts with a version mismatch. Use a **PostgreSQL 17+** client—for example the **`postgres:17-alpine`** image:

```bash
REGION=ap-southeast-2
SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id axonai/db/credentials --region "$REGION" --query SecretString --output text)
export PGHOST=$(echo "$SECRET_JSON" | jq -r '.host')
export PGPORT=$(echo "$SECRET_JSON" | jq -r '.port // 5432')
export PGUSER=$(echo "$SECRET_JSON" | jq -r '.username')
export PGPASSWORD=$(echo "$SECRET_JSON" | jq -r '.password')
export PGDATABASE=postgres

docker run --rm -e PGPASSWORD="$PGPASSWORD" postgres:17-alpine \
  pg_dump --schema-only --no-owner --no-privileges \
    -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  > schema/rds_postgres_schema.sql
```

Commit **`schema/rds_postgres_schema.sql`**. Dumps from **pg_dump 17+** may include `\restrict` / `\unrestrict` lines with a token (PostgreSQL/psql “restricted” import mode). **Keep them** in the file you use for **`psql -f`** restores; they are safe to leave in the repo.

The **PGDG** RPM `https://download.postgresql.org/.../amzn/2023-x86_64/pgdg-redhat-repo-latest.noarch.rpm` often **404s** on current Amazon Linux 2023 images; Docker avoids that.

### 1b. Optional: JSON snapshot + Markdown injector (Python)

Credentials are loaded from Secrets Manager (`axonai/db/credentials` in `ap-southeast-2` by default). Use database **`postgres`** for this RDS instance:

```powershell
$env:AWS_REGION = "ap-southeast-2"
$env:AXONAI_DB_HOST = "axonai-db-prod.cl6susyag7hl.ap-southeast-2.rds.amazonaws.com"
$env:AXONAI_DB_NAME = "postgres"
python scripts/extract_rds_schema.py --output-json schema/axonai_snapshot.json
python scripts/render_database_schema_md.py --json schema/axonai_snapshot.json --output DATABASE_SCHEMA.md
```

The renderer replaces only the material between the **AXONAI_DB_LIVE_SCHEMA** HTML comment pair in this file (search the raw Markdown for that string). Keep those comments in place.

**Note:** Local extraction can still fail with **connection timeout** if the RDS security group does not allow your IP; use Cloud Shell or a host inside the VPC if needed.

---

## 2. AWS RDS environment (metadata)

| Property | Value |
|----------|--------|
| Region | `ap-southeast-2` |
| DB instance identifier | `axonai-db-prod` |
| Engine | PostgreSQL **17.6** |
| Endpoint (AWS) | `axonai-db-prod.cl6susyag7hl.ap-southeast-2.rds.amazonaws.com` |
| Publicly accessible | `true` |
| VPC security group (active) | `sg-057077b137030c2b0` |
| Secrets Manager secret | `axonai/db/credentials` (username / password / host / port — **never commit secret values**) |
| **Database name on this instance** | **`postgres`** — `SELECT datname FROM pg_database` shows only `postgres` and `rdsadmin`; application tables live in **`public`**. There is **no** separate `axonai` database on this RDS unless you create one. |

**Hostnames:** Application code and Lambda environment variables sometimes reference **`axonai-db-prod.cyxvx9k9pnsx.ap-southeast-2.rds.amazonaws.com`**, while the RDS API reports **`…cl6susyag7hl…`** for instance `axonai-db-prod`. Confirm which endpoint is current in your AWS console; use the matching host when connecting.

---

<!-- AXONAI_DB_LIVE_SCHEMA_START -->

## Live PostgreSQL catalog (pg_catalog)

**Full DDL (source of truth):** **`schema/rds_postgres_schema.sql`** — `pg_dump --schema-only` from database **`postgres`**, server **17.6** (regenerate with §1a after schema changes).

---

<!-- AXONAI_DB_LIVE_SCHEMA_END -->

---

## 3. Flask-SQLAlchemy models (`models/models.py`)

PostgreSQL table names follow SQLAlchemy defaults (lowercased class names). Reserved identifiers such as `user` and `class` are quoted by PostgreSQL as needed.

### Association: `class_users`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `class_id` | Integer | PK, FK → `class.id` |
| `user_id` | Integer | PK, FK → `user.id` |

### `user`

| Column | Type (ORM) | Nullable |
|--------|------------|----------|
| `id` | Integer | PK |
| `role` | String(20) | NOT NULL |
| `first_name` | String(50) | NOT NULL |
| `last_name` | String(50) | NOT NULL |
| `photo_url` | String(200) | YES |
| `created_at` | DateTime | default utcnow |
| `is_active` | Boolean | default true |
| `age` | Integer | YES |
| `gender` | String(20) | YES |
| `ethnicity` | String(100) | YES |
| `date_of_birth` | Date | YES |
| `year_level` | String(20) | YES |
| `primary_language` | String(50) | YES |
| `secondary_language` | String(50) | YES |
| `learning_difficulty` | String(100) | YES |
| `extracurricular_activities` | Text (JSON string) | YES |
| `major_life_event` | String(200) | YES |
| `attendance_rate` | Float | YES |
| `learning_style` | String(50) | YES |
| `interests` | Text (JSON string) | YES |
| `academic_goals` | Text | YES |
| `preferred_difficulty` | String(20) | YES |

**Relationships (ORM):** classes (M:M via `class_users`), assignment submissions, grades, chat messages, etc.

### `class`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `name` | String(100) | NOT NULL |
| `description` | Text | YES |
| `subject` | String(50) | YES |
| `teacher_id` | Integer | NOT NULL, FK → `user.id` |
| `ai_model_id` | Integer | FK → `ai_model.id` |
| `created_at` | DateTime | default |
| `is_active` | Boolean | default true |

### `assignment`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `title` | String(200) | NOT NULL |
| `description` | Text | YES |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `due_date` | DateTime | YES |
| `max_points` | Integer | default 100 |
| `created_at` | DateTime | default |
| `is_active` | Boolean | default true |

### `assignment_submission`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `assignment_id` | Integer | NOT NULL, FK → `assignment.id` |
| `student_id` | Integer | NOT NULL, FK → `user.id` |
| `content` | Text | YES |
| `file_path` | String(200) | YES |
| `file_name` | String(200) | YES |
| `submitted_at` | DateTime | default |

### `grade`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `assignment_id` | Integer | NOT NULL, FK → `assignment.id` |
| `student_id` | Integer | NOT NULL, FK → `user.id` |
| `submission_id` | Integer | FK → `assignment_submission.id` |
| `grade` | Float | YES |
| `feedback` | Text | YES |
| `graded_at` | DateTime | default |
| `graded_by` | Integer | NOT NULL, FK → `user.id` |

### `content_file`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `name` | String(200) | NOT NULL |
| `file_path` | String(200) | NOT NULL |
| `file_type` | String(50) | NOT NULL |
| `uploaded_by` | Integer | NOT NULL, FK → `user.id` |
| `uploaded_at` | DateTime | default |

### `ai_model`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `subject` | String(100) | NOT NULL |
| `model_name` | String(200) | NOT NULL |
| `fine_tuned_id` | String(200) | YES |
| `prompt_template` | Text | YES |
| `max_tokens` | Integer | default 1000 |
| `temperature` | Float | default 0.7 |
| `is_active` | Boolean | default true |
| `created_at` | DateTime | default |

### `chat_message`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `user_id` | Integer | NOT NULL, FK → `user.id` |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `ai_model_id` | Integer | NOT NULL, FK → `ai_model.id` |
| `message` | Text | NOT NULL |
| `response` | Text | NOT NULL |
| `message_type` | String(20) | NOT NULL |
| `context_data` | Text (JSON) | YES |
| `created_at` | DateTime | default |

### `token_usage`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `user_id` | Integer | NOT NULL, FK → `user.id` |
| `date` | Date | NOT NULL |
| `tokens_used` | Integer | NOT NULL |
| `requests_made` | Integer | NOT NULL |
| `created_at` | DateTime | default |

### `student_profile`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `user_id` | Integer | NOT NULL, FK → `user.id` |
| `learning_preferences` | Text (JSON) | YES |
| `study_patterns` | Text (JSON) | YES |
| `performance_metrics` | Text (JSON) | YES |
| `ai_interaction_history` | Text (JSON) | YES |
| `last_updated` | DateTime | default |

### `ai_interaction`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `user_id` | Integer | NOT NULL, FK → `user.id` |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `ai_model_id` | Integer | NOT NULL, FK → `ai_model.id` |
| `prompt` | Text | NOT NULL |
| `response` | Text | NOT NULL |
| `strategy_used` | String(100) | YES |
| `sub_topic` | String(50) | YES |
| `engagement_score` | Float | YES |
| `tokens_in` | Integer | NOT NULL |
| `tokens_out` | Integer | NOT NULL |
| `response_time_ms` | Integer | YES |
| `temperature` | Float | YES |
| `success_indicator` | Boolean | YES |
| `user_feedback` | Integer | YES |
| `linked_assignment_id` | Integer | FK → `assignment.id` |
| `linked_content_id` | Integer | FK → `content_file.id` |
| `context_data` | Text (JSON) | YES |
| `created_at` | DateTime | default |

### `failed_strategy`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `user_id` | Integer | NOT NULL, FK → `user.id` |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `strategy_name` | String(100) | NOT NULL |
| `failure_reason` | Text | YES |
| `failure_count` | Integer | default 1 |
| `last_attempted` | DateTime | default |
| `context_data` | Text (JSON) | YES |

### `optimized_profile`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `user_id` | Integer | NOT NULL, UNIQUE, FK → `user.id` |
| `current_pass_rate` | Float | YES |
| `predicted_pass_rate` | Float | YES |
| `engagement_level` | Float | YES |
| `mastery_scores` | Text (JSON) | YES |
| `best_time_of_day` | String(20) | YES |
| `optimal_session_length` | Integer | YES |
| `preferred_strategies` | Text (JSON) | YES |
| `avoided_strategies` | Text (JSON) | YES |
| `recent_topics` | Text (JSON) | YES |
| `struggle_areas` | Text (JSON) | YES |
| `strength_areas` | Text (JSON) | YES |
| `last_updated` | DateTime | default |

### `mini_test`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `created_by_ai` | Integer | NOT NULL, FK → `ai_model.id` |
| `test_type` | String(50) | NOT NULL |
| `difficulty_level` | String(20) | NOT NULL |
| `skills_tested` | Text (JSON) | NOT NULL |
| `questions` | Text (JSON) | NOT NULL |
| `created_at` | DateTime | default |

### `mini_test_response`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `test_id` | Integer | NOT NULL, FK → `mini_test.id` |
| `user_id` | Integer | NOT NULL, FK → `user.id` |
| `answers` | Text (JSON) | NOT NULL |
| `score` | Float | NOT NULL |
| `time_taken` | Integer | YES |
| `skill_scores` | Text (JSON) | YES |
| `completed_at` | DateTime | default |

### `pattern_insight`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `pattern_type` | String(100) | NOT NULL |
| `pattern_description` | Text | NOT NULL |
| `applicable_criteria` | Text (JSON) | NOT NULL |
| `recommended_strategies` | Text (JSON) | NOT NULL |
| `success_rate` | Float | YES |
| `sample_size` | Integer | NOT NULL |
| `confidence_level` | Float | YES |
| `last_validated` | DateTime | default |
| `created_at` | DateTime | default |

### `predicted_grade`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `user_id` | Integer | NOT NULL, FK → `user.id` |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `current_trajectory` | Float | NOT NULL |
| `predicted_final_grade` | Float | NOT NULL |
| `confidence_level` | Float | NOT NULL |
| `factors_analyzed` | Text (JSON) | NOT NULL |
| `improvement_areas` | Text (JSON) | YES |
| `risk_factors` | Text (JSON) | YES |
| `prediction_date` | DateTime | default |

### `teacher_ai_insight`

| Column | Type (ORM) | Notes |
|--------|------------|--------|
| `id` | Integer | PK |
| `class_id` | Integer | NOT NULL, FK → `class.id` |
| `student_id` | Integer | NOT NULL, FK → `user.id` |
| `teacher_id` | Integer | NOT NULL, FK → `user.id` |
| `insight_type` | String(100) | NOT NULL |
| `summary` | Text | NOT NULL |
| `suggested_interventions` | Text (JSON) | NOT NULL |
| `failed_strategies` | Text (JSON) | YES |
| `successful_strategies` | Text (JSON) | YES |
| `engagement_analysis` | Text (JSON) | YES |
| `viewed_by_teacher` | Boolean | default false |
| `action_taken` | Text | YES |
| `generated_at` | DateTime | default |

**Naming note:** The FastAPI routes in `routes/lambda_new_routes.py` query a table named **`teacher_ai_insights`** (plural). Confirm whether production uses that name versus the ORM table `teacher_ai_insight`; the live snapshot in §2 resolves the physical name.

---

## 4. Lambda / FastAPI SQL (`routes/lambda_new_routes.py`)

These tables are referenced by the deployed API (knowledge graph, wellbeing, pedagogical memory). Column lists below are **from application SQL**; additional columns may exist on the server.

| Table | Columns referenced in repo SQL |
|-------|--------------------------------|
| `subjects` | `id`, `name` |
| `concepts` | `id`, `name`, `difficulty_level`, `concept_type`, `subject_id` |
| `concept_prerequisites` | `concept_id`, `prerequisite_concept_id`, `strength` |
| `quiz_questions` | `id`, `concept_id` |
| `concept_mastery_states` | `concept_id`, `class_id`, `mastery_score` |
| `teacher_ai_insights` | `student_summary`, `risk_narrative`, `recommended_interventions`, `teaching_approach_advice`, `generated_at`, `model_used`, `student_id`, `class_id` |
| `student_wellbeing_context` | `has_learning_support_plan`, `learning_support_details`, `has_medical_condition`, `medical_details`, `home_situation_flag`, `home_situation_notes`, `is_esol`, `attendance_percentage`, `student_id` |
| `pedagogical_memory` | `teaching_approach`, `success_rate`, `attempt_count`, `avg_messages_to_lightbulb`, `last_used_at`, `student_id` |

---

## 5. Other data stores (not this RDS schema)

Some **agents** under `agents/` use SQLite and tables such as `student_profiles` and `quizzes` with `?` placeholders. Those are **not** part of the production PostgreSQL schema documented here unless explicitly migrated.

---

## 6. Operational notes

- **Timezone:** Store timestamps in **UTC** in the application layer.
- **Character set:** UTF-8 (Te Reo and multilingual text).
- **Connection pool:** Lambda deployments typically use a small pool (see legacy notes in repo; tune for concurrency).

---

*Last manual edit of narrative sections: 2026-04-16. Replace the live block in §2 using the refresh commands in §1 after schema changes or on a regular cadence.*
