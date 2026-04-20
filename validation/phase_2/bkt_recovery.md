# BKT parameter recovery

## Inputs

- BKT ground truth: `data/processed/real_bkt_params.parquet` (157 skills)
- Seed: `42`
- Synthetic students per skill: 500
- Tolerance: ±0.05 on each of (p_init, p_transit, p_slip, p_guess)
- Spec acceptance (extended regime): ≥ 80% of skills within tolerance

## Headline

| Regime | Seq length | Skills within ±0.05 | Spec |
|---|---|---|---|
| Empirical (seq_len = n_responses / n_students) | variable | 40.1% (63/157) | context |
| Extended (fixed seq_len = 20) | 20 | 80.9% (127/157) | ≥ 80% → PASS |

### Overall: PASS

## Per-parameter error (extended regime)

- p_init:     mean_err=0.024, median_err=0.019, p90_err=0.052
- p_transit:  mean_err=0.012, median_err=0.005, p90_err=0.033
- p_slip:     mean_err=0.003, median_err=0.002, p90_err=0.008
- p_guess:    mean_err=0.013, median_err=0.005, p90_err=0.042

## Per-parameter error (empirical regime)

- p_init:     mean_err=0.054, median_err=0.035, p90_err=0.130
- p_transit:  mean_err=0.056, median_err=0.028, p90_err=0.147
- p_slip:     mean_err=0.030, median_err=0.011, p90_err=0.105
- p_guess:    mean_err=0.039, median_err=0.020, p90_err=0.091

## Interpretation

The empirical regime uses the same average sequence length as the real
ASSISTments calibration (median 2 attempts
per user-skill). The extended regime uses a fixed 20
attempts per user to isolate identifiability-in-principle from
identifiability-given-available-data.

- **Empirical recovery** is the upper bound on what the real BKT fit
  could be doing given the data at hand. Low empirical recovery means
  the limitation is data (short sequences), not algorithm.
- **Extended recovery** tests the EM itself. Low extended recovery
  would indicate a bug in `fit_bkt`.

Skills whose ground-truth params sit at the EM bounds (e.g. p_transit
pinned to 0.01 or 0.5) are especially hard to recover because the
simulator produces near-degenerate sequences; these were flagged in
`real_bkt_fit_report.md` and are expected to lower the recovery rate.

If the spec gate passes, the interpretation is:
the EM identifies the 4 BKT parameters at seq_len=20
for ≥ 80% of skills. The gap between extended
and empirical recovery (40.8 pp) is the
cost of the 2012-2013 release's short user-skill sequences.

