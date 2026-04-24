# Phase 2 PR B12 — Ablation Study Report

**Generated:** 2026-04-24T03:05:05.652327Z
**Baseline:** `full`

## Per-condition metrics

| Condition | n_attempts | cwm_rate | bkt_growth | correct_rate |
|-----------|-----------|----------|------------|--------------|
| `full` | 3185 | 0.088 | +0.0317 | 0.144 |
| `no_susceptibility` | 3161 | 0.000 | +0.0555 | 0.161 |
| `no_detector` | 3185 | 0.000 | +0.0317 | 0.144 |
| `default_style_only` | 3185 | 0.000 | +0.0317 | 0.144 |
| `no_slow_students` | 3185 | 0.088 | +0.0317 | 0.144 |

## Delta from baseline (condition − full)

| Condition | Δ cwm_rate | Δ bkt_growth | Δ correct_rate |
|-----------|-----------|--------------|----------------|
| `no_susceptibility` | -0.088 | +0.0238 | +0.017 |
| `no_detector` | -0.088 | +0.0000 | +0.000 |
| `default_style_only` | -0.088 | +0.0000 | +0.000 |
| `no_slow_students` | +0.000 | +0.0000 | +0.000 |

## Style distributions

**`full`**: analogy=33, concise_answer=415, contrast_with_misconception=279, hint=3, worked_example=2455
**`no_susceptibility`**: analogy=0, concise_answer=519, contrast_with_misconception=0, hint=7, worked_example=2635
**`no_detector`**: analogy=40, concise_answer=444, contrast_with_misconception=0, hint=3, worked_example=2698
**`default_style_only`**: analogy=0, concise_answer=3185, contrast_with_misconception=0, hint=0, worked_example=0
**`no_slow_students`**: analogy=0, concise_answer=448, contrast_with_misconception=279, hint=3, worked_example=2455
