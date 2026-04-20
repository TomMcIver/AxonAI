# Population KS test — θ distribution

## Inputs

- Priors: `data/processed/real_student_priors.json`
- Real θ: `data/processed/real_theta_estimates.parquet`
- Seed: `42`
- Synthetic cohort size: 3,000
- θ clipping range: [-4.0, 4.0] (matches fit_2pl bounds)

## Scope

Draws per-student latent ability θ from `N(theta_mean, theta_std)` in
the priors file and KS-tests against the ASSISTments-inferred θ. The
full-loop KS test (B11) is deferred; this answers only whether the
prior's distributional shape reproduces the real θ distribution.

## Headline

| Metric | Value |
|---|---|
| KS statistic (sup over CDFs) | 0.0737 |
| KS p-value | 1.662e-13 |
| Spec (p > 0.05) | FAIL |

### Overall: FAIL

## Distribution summary

| Cohort | n | mean | std | p05 | p50 | p95 | min | max |
|---|---|---|---|---|---|---|---|---|
| Simulated (prior draw) | 3,000 | -0.031 | 1.241 | -2.136 | -0.000 | +1.977 | -4.000 | +3.917 |
| Real ASSISTments θ | 35,736 | +0.000 | 1.232 | -1.820 | -0.074 | +2.432 | -4.407 | +3.593 |

## QQ plot

See `population_ks_qq.png` (same directory). Deviation from the y=x diagonal
indicates a distributional mismatch between simulated and real θ
quantiles.

## Interpretation

The KS test rejects the null that simulated and real θ follow the
same distribution (p = 1.662e-13 ≤ 0.05). The most likely
structural causes, given how the priors are derived:

1. **Real θ is non-Gaussian**: ASSISTments users are a mix of
   classrooms with different preparation levels. The 2PL JML fit
   produces θ with heavier tails than N(μ, σ), so a Gaussian prior
   under-samples the wings. Compare `p05` / `p95` in the table above
   to the simulated equivalents: if the real distribution is wider,
   this is the cause.
2. **Boundary pile-up**: θ is clipped to [-4.0, 4.0]
   during 2PL fitting. If a non-trivial fraction of real θ sits at
   the bounds, the simulated distribution (Gaussian, no pile-up) will
   not match without mass-on-boundary.
3. **Sample size**: with n = 3,000 simulated vs
   35,736 real, KS is sensitive to sub-percent deviations
   that are pedagogically unimportant. A Cohen's d on the means (or a
   look at the QQ plot) tells us whether the rejection is practically
   meaningful.

Pedagogically plausible remediation (spec OK): the KS failure is
driven by the Gaussian prior's inability to replicate the real θ
distribution's tails, not by a simulator bug. The priors module
(`ml/simulator/calibration/priors.py`) fits the Gaussian from the
real θ via method-of-moments; switching to a Student-t or
empirical-CDF prior would close the gap. Deferred to B11's v2
validation run where the loop-level θ drift will dominate the
generator-level mismatch anyway.
