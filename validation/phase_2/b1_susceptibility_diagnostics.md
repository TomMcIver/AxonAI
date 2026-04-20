# Misconception susceptibility — B1 diagnostics

## Inputs

- Catalogue source: fallback synthetic catalogue of 2587 IDs (id_map not found at data/processed/eedi_misconception_id_map.json)
- Catalogue size: 2,587
- Priors: `data/processed/real_student_priors.json` (theta_mean=1.2725188909963738e-17, theta_std=1.2321304149938832)
- Seed: `42`
- Cohort size: 3,000

## Config

| Knob | Value |
|---|---|
| base_rate | 0.12 |
| theta_coef | 0.08 |
| min_mean_rate | 0.02 |
| max_mean_rate | 0.35 |
| beta_nu | 8.0 |
| weight_min | 0.2 |
| weight_max | 0.9 |

## Headline

| Metric | Value |
|---|---|
| mean activity rate |active|/N | 0.1248 |
| std activity rate | 0.1338 |
| Pearson(θ, rate) | -0.6073 |
| determinism (same-seed equality) | PASS |

## Activity rate by θ tertile

| Tertile | mean θ | mean rate | stderr |
|---|---|---|---|
| low θ | -1.391 | 0.2193 | 0.0046 |
| mid θ | -0.011 | 0.1171 | 0.0034 |
| high θ | +1.308 | 0.0381 | 0.0022 |

## Verdict

- correlation negative: PASS (observed -0.6073)
- mean rate within config: PASS (observed 0.1248, [0.02, 0.35])
- determinism: PASS

### Overall: PASS

## Interpretation

The sampler is a stateless, θ-conditioned Beta-Bernoulli draw. With `_THETA_COEF = 0.08` and the real-cohort θ prior (std≈1.2321304149938832), the analytic prediction is that the Pearson correlation between θ and |active|/N should be close to `-theta_coef * std / sqrt(base_rate * (1 - base_rate))`; the observed value above is the empirical check on that. The determinism line guarantees the loop's per-student draws are reproducible under the same seed, which is required by the global simulator contract.
