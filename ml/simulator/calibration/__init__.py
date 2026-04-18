"""Calibrate simulator parameters against ASSISTments responses.

Implemented in PR 5. Produces:
    data/processed/item_params.parquet      (fit_2pl)
    data/processed/bkt_params.parquet       (fit_bkt)
    data/processed/student_priors.json      (priors)
    validation/2pl_fit_report.md
    validation/bkt_fit_report.md
"""
