"""ASSISTments Skill Builder 2009-2010 loader — Heffernan & Heffernan (2014).

Implemented in PR 4. This is the IRT/BKT calibration dataset for v1.

Planned output:
    responses_df: one row per (student, problem) response with timestamp, skill_id
    skills_df:    one row per skill with id, name, hierarchy metadata

Filter: items with < 150 responses dropped (IRT stability per G. Brown).
Cache: data/processed/assistments.parquet
"""
