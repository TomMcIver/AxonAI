"""MAP — Charting Student Math Misunderstandings (2025) loader.

Implemented in PR 4. Loader only in v1; parked for v2 detector training.
~15 questions × ~52k student free-text explanations with category +
misconception labels.

Planned output:
    explanations_df

Cache: data/processed/map_explanations.parquet
"""
