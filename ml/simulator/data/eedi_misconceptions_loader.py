"""Eedi 2024 — Mining Misconceptions in Mathematics loader.

Implemented in PR 4. Provides the misconception taxonomy and item-bank
distractor metadata. v1 response model ignores misconception_id; v2 will
weight distractor selection by susceptibility.

Planned output:
    questions_df
    answer_options_df
    distractor_misconception_map_df
    misconception_catalogue_df

Cache: data/processed/eedi_misconceptions.parquet
"""
