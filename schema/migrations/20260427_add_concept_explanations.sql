CREATE TABLE IF NOT EXISTS concept_explanations (
    id SERIAL PRIMARY KEY,
    concept_id INTEGER NOT NULL REFERENCES concepts(id),
    explanation_text TEXT NOT NULL,
    worked_example TEXT NOT NULL,
    common_misconception TEXT,
    year_level SMALLINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_concept_explanations_concept_id
ON concept_explanations(concept_id);
