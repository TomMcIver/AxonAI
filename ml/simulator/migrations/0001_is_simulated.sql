-- Simulator v1 — shadow tables for synthetic student data.
--
-- Mirrors the production response/session schema 1:1 but lives in its
-- own namespace so analytics on real users never sees synthetic rows.
-- Every row carries `is_simulated BOOLEAN NOT NULL DEFAULT TRUE` — the
-- default exists so accidental inserts without the flag still land as
-- simulated, never as real.
--
-- Apply with:  python -m ml.simulator migrate
-- Rollback with: DROP TABLE sim_attempts, sim_sessions, sim_teach, sim_revise;

CREATE TABLE IF NOT EXISTS sim_teach (
    id           BIGSERIAL PRIMARY KEY,
    run_id       TEXT        NOT NULL,
    student_id   BIGINT      NOT NULL,
    concept_id   BIGINT      NOT NULL,
    time         TIMESTAMPTZ NOT NULL,
    is_simulated BOOLEAN     NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS sim_teach_run_student_idx
    ON sim_teach (run_id, student_id);

CREATE TABLE IF NOT EXISTS sim_attempts (
    id               BIGSERIAL PRIMARY KEY,
    run_id           TEXT        NOT NULL,
    student_id       BIGINT      NOT NULL,
    concept_id       BIGINT      NOT NULL,
    item_id          BIGINT      NOT NULL,
    is_correct       BOOLEAN     NOT NULL,
    time             TIMESTAMPTZ NOT NULL,
    response_time_ms INTEGER     NOT NULL,
    is_simulated     BOOLEAN     NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS sim_attempts_run_student_idx
    ON sim_attempts (run_id, student_id);
CREATE INDEX IF NOT EXISTS sim_attempts_item_idx
    ON sim_attempts (item_id);

CREATE TABLE IF NOT EXISTS sim_revise (
    id           BIGSERIAL PRIMARY KEY,
    run_id       TEXT        NOT NULL,
    student_id   BIGINT      NOT NULL,
    concepts     BIGINT[]    NOT NULL,
    time         TIMESTAMPTZ NOT NULL,
    is_simulated BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS sim_sessions (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              TEXT        NOT NULL,
    student_id          BIGINT      NOT NULL,
    session_index       INTEGER     NOT NULL,
    time                TIMESTAMPTZ NOT NULL,
    attempts_in_session INTEGER     NOT NULL,
    is_simulated        BOOLEAN     NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS sim_sessions_run_student_idx
    ON sim_sessions (run_id, student_id);
