"""Fit BKT per skill on ASSISTments via EM.

Implemented in PR 5.

Output: data/processed/bkt_params.parquet with columns
    skill_id, p_init, p_transit, p_slip, p_guess, converged, n_iter
Diagnostics: validation/bkt_fit_report.md
"""
