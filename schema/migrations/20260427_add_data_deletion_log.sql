CREATE TABLE IF NOT EXISTS data_deletion_log (
    id BIGSERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_by VARCHAR(255) NOT NULL,
    rows_deleted JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_data_deletion_log_student_id
    ON data_deletion_log (student_id);

CREATE INDEX IF NOT EXISTS idx_data_deletion_log_deleted_at
    ON data_deletion_log (deleted_at DESC);
