# Misconception detector — B3 retrieval evaluation

## Inputs

- Data source: synthetic catalogue of 200 entries
- Catalogue size: 200 (train 160 / test unseen 40)
- Model: `sentence-transformers/all-MiniLM-L6-v2` @ HEAD
- Device: cpu (pinned for determinism)
- top_k: 25
- Seed: 42
- Synthetic fallback: yes

## Results

| Split | n_queries | Recall@k | Threshold | Outcome |
|---|---|---|---|---|
| Seen (train IDs) | 160 | 1.000 | ≥0.6 | PASS |
| Unseen (test IDs) | 40 | 1.000 | ≥0.35 | PASS |

> **Note:** Results are from a synthetic catalogue (no Eedi CSV available).
> The queries are derived from catalogue names, so seen-split recall is an optimistic
> self-consistency check. Gate acceptance requires real Eedi data via S3 creds.

### Overall: PASS

## Interpretation

The bi-encoder retrieves candidates for B4's cross-encoder to rerank. Recall@25 is the fraction of evaluation queries for which the true misconception appears anywhere in the top-25 results. The seen-split threshold (≥0.6) is more demanding because the index contains the target entry; the unseen threshold (≥0.35) reflects the harder case where the model must generalise to new misconception classes. B4 (cross-encoder rerank) will improve precision@1 from this candidate set.

*Elapsed: 783.6s*
