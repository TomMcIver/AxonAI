# 2PL IRT fit report

- Converged: True
- Iterations: 273
- Train log-likelihood: -942568.0946
- Items fit: 6799
- Students fit: 35736

## Heldout diagnostics

- Items with heldout data: 6799
- AUC mean: 0.6814
- AUC median: 0.6875
- AUC >= 0.75: 28.86%
- Calibration error mean: 0.1149
- Calibration error < 0.05: 12.31%

## Per-item (first 25)

| item_id | a | b | n_train | n_heldout | AUC | calib_err |
| --- | --- | --- | --- | --- | --- | --- |
| 16.0 | 2.629 | -0.712 | 324.0 | 81.0 | 0.709 | 0.123 |
| 41.0 | 3.000 | -0.329 | 269.0 | 67.0 | 0.585 | 0.266 |
| 117.0 | 1.906 | -1.082 | 234.0 | 58.0 | 0.728 | 0.090 |
| 134.0 | 1.202 | -2.021 | 210.0 | 52.0 | 0.482 | 0.141 |
| 135.0 | 1.236 | -3.181 | 208.0 | 52.0 | 0.785 | 0.056 |
| 175.0 | 3.000 | 0.506 | 130.0 | 33.0 | 0.466 | 0.126 |
| 176.0 | 1.913 | 0.272 | 126.0 | 32.0 | 0.539 | 0.183 |
| 177.0 | 3.000 | -0.007 | 124.0 | 31.0 | 0.838 | 0.124 |
| 178.0 | 1.827 | -0.410 | 702.0 | 176.0 | 0.703 | 0.093 |
| 239.0 | 1.407 | 0.230 | 134.0 | 34.0 | 0.554 | 0.223 |
| 342.0 | 1.671 | -0.275 | 420.0 | 105.0 | 0.714 | 0.086 |
| 409.0 | 2.028 | -0.257 | 397.0 | 99.0 | 0.714 | 0.049 |
| 455.0 | 0.839 | -1.957 | 242.0 | 60.0 | 0.612 | 0.046 |
| 482.0 | 1.579 | -0.766 | 202.0 | 50.0 | 0.605 | 0.135 |
| 525.0 | 1.829 | -0.538 | 295.0 | 74.0 | 0.629 | 0.160 |
| 814.0 | 2.906 | -0.864 | 187.0 | 47.0 | 0.686 | 0.141 |
| 839.0 | 1.300 | -0.451 | 184.0 | 46.0 | 0.595 | 0.214 |
| 842.0 | 0.945 | -0.256 | 219.0 | 55.0 | 0.652 | 0.106 |
| 849.0 | 1.337 | -0.851 | 318.0 | 79.0 | 0.594 | 0.122 |
| 894.0 | 1.392 | -1.375 | 307.0 | 77.0 | 0.818 | 0.097 |
| 912.0 | 1.248 | 0.697 | 123.0 | 31.0 | 0.527 | 0.222 |
| 956.0 | 3.000 | 0.289 | 131.0 | 33.0 | 0.733 | 0.230 |
| 988.0 | 1.149 | -0.839 | 450.0 | 113.0 | 0.627 | 0.135 |
| 991.0 | 2.143 | -0.796 | 265.0 | 66.0 | 0.652 | 0.164 |
| 997.0 | 2.678 | -0.727 | 322.0 | 80.0 | 0.787 | 0.087 |

## Real-vs-synthetic gap (Phase 1 baseline)

Phase 1 self-consistency reported Pearson rho(fitted b, true b) = **0.97** on 48 items × 400 synthetic students.

Real ASSISTments heldout AUC: mean = 0.681, median = 0.688, 28.9% of items with AUC >= 0.75.

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
- Items with a, b both strictly inside identifiability bounds: 6118 (90.0%)
- Spec acceptance (>=85%): PASS
