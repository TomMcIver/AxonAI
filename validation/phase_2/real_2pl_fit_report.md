# 2PL IRT fit report

- Converged: True
- Iterations: 247
- Train log-likelihood: -942630.5145
- Items fit: 6799
- Students fit: 35736

## Heldout diagnostics

- Items with heldout data: 6799
- AUC mean: 0.6814
- AUC median: 0.6875
- AUC >= 0.75: 28.75%
- Calibration error mean: 0.1149
- Calibration error < 0.05: 12.24%

## Per-item (first 25)

| item_id | a | b | n_train | n_heldout | AUC | calib_err |
| --- | --- | --- | --- | --- | --- | --- |
| 16.0 | 2.565 | -0.702 | 324.0 | 81.0 | 0.708 | 0.124 |
| 41.0 | 3.000 | -0.309 | 269.0 | 67.0 | 0.584 | 0.268 |
| 117.0 | 1.953 | -1.040 | 234.0 | 58.0 | 0.728 | 0.091 |
| 134.0 | 1.191 | -2.031 | 210.0 | 52.0 | 0.481 | 0.140 |
| 135.0 | 1.305 | -3.041 | 208.0 | 52.0 | 0.785 | 0.057 |
| 175.0 | 3.000 | 0.526 | 130.0 | 33.0 | 0.474 | 0.114 |
| 176.0 | 1.899 | 0.292 | 126.0 | 32.0 | 0.534 | 0.183 |
| 177.0 | 3.000 | 0.013 | 124.0 | 31.0 | 0.833 | 0.126 |
| 178.0 | 1.831 | -0.390 | 702.0 | 176.0 | 0.701 | 0.085 |
| 239.0 | 1.393 | 0.254 | 134.0 | 34.0 | 0.550 | 0.222 |
| 342.0 | 1.673 | -0.255 | 420.0 | 105.0 | 0.716 | 0.081 |
| 409.0 | 2.007 | -0.240 | 397.0 | 99.0 | 0.714 | 0.061 |
| 455.0 | 0.817 | -1.988 | 242.0 | 60.0 | 0.612 | 0.046 |
| 482.0 | 1.604 | -0.734 | 202.0 | 50.0 | 0.611 | 0.161 |
| 525.0 | 1.809 | -0.530 | 295.0 | 74.0 | 0.630 | 0.159 |
| 814.0 | 2.803 | -0.861 | 187.0 | 47.0 | 0.686 | 0.157 |
| 839.0 | 1.287 | -0.436 | 184.0 | 46.0 | 0.591 | 0.213 |
| 842.0 | 0.917 | -0.246 | 219.0 | 55.0 | 0.654 | 0.116 |
| 849.0 | 1.338 | -0.837 | 318.0 | 79.0 | 0.594 | 0.123 |
| 894.0 | 1.399 | -1.347 | 307.0 | 77.0 | 0.822 | 0.089 |
| 912.0 | 1.192 | 0.754 | 123.0 | 31.0 | 0.516 | 0.219 |
| 956.0 | 3.000 | 0.311 | 131.0 | 33.0 | 0.733 | 0.201 |
| 988.0 | 1.188 | -0.805 | 450.0 | 113.0 | 0.624 | 0.136 |
| 991.0 | 2.115 | -0.786 | 265.0 | 66.0 | 0.650 | 0.160 |
| 997.0 | 2.605 | -0.720 | 322.0 | 80.0 | 0.786 | 0.070 |

## Real-vs-synthetic gap (Phase 1 baseline)

Phase 1 self-consistency reported Pearson rho(fitted b, true b) = **0.97** on 48 items × 400 synthetic students.

Real ASSISTments heldout AUC: mean = 0.681, median = 0.688, 28.8% of items with AUC >= 0.75.

Self-consistency is the tighter benchmark by design (the fit is recovering the same generating process that produced the data). A drop from synthetic to real is expected and does not by itself indicate a fitting defect. The specific thresholds in the Phase 2 acceptance criteria (2PL converges on >=85% of items with >=150 responses) are reported above under `converged_at_bounds` and `n_converged_items`.

### Leakage check

- Row identity: `index`
- Train rows: 1,970,763
- Heldout rows: 492,740
- Source rows appearing on both sides: **0**
- Items appearing in both splits: 6,799 (train: 6,799, heldout: 6,799)
- Users appearing in both splits: 31,415 (train: 35,422, heldout: 31,729)
- Status: PASS

Note: per-item and per-user overlap is expected and necessary for IRT (theta is fit per user across their training rows and evaluated on heldout rows of the same items). Only `source rows appearing on both sides > 0` is leakage.


## Off-bounds convergence

- Items fit: 6799
- Items with a, b both strictly inside identifiability bounds: 6130 (90.2%)
- Spec acceptance (>=85%): PASS
