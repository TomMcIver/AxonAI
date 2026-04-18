"""Fit 2PL IRT on ASSISTments responses.

Implemented in PR 5. Primary path: py-irt. Fallback: mirt via rpy2 if
detected. 20% heldout per item; diagnostics written to
validation/2pl_fit_report.md.

Output: data/processed/item_params.parquet with columns
    item_id, a (discrimination), b (difficulty), n_responses, heldout_auc
"""
