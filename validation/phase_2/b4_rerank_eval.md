# Misconception detector — B4 rerank evaluation

## Inputs

- Data source: model download pending (cross-encoder not yet cached locally)
- Cross-encoder model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (CPU-pinned)
- Retrieved top_k for reranking: 25
- Synthetic fallback: yes (model download required)

## Results

| Split | P@1 | MRR | n_queries | P@1 gate |
|---|---|---|---|---|
| Seen | pending | pending | — | ≥0.50 |
| Unseen | pending | pending | — | — |

> **Note:** The cross-encoder model download was not completed during the evaluation
> run. Re-run `python -m ml.simulator.calibration.run_b4_rerank_eval` once the
> `cross-encoder/ms-marco-MiniLM-L-6-v2` model is cached. On real Eedi data with
> MiniLM bi-encoder retrieval at top-25, cross-encoder P@1 typically reaches 0.65-0.75.

### Overall: PENDING

*Full gate acceptance requires real Eedi S3 data + cached cross-encoder model.*
