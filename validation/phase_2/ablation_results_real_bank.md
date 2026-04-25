# Phase 2 — investor ablation (**real** 2PL bank + Eedi)
**Generated (UTC):** 2026-04-25T00:27:18.856953+00:00Z

## 0. Provenance

- **Item params (Gate A):** `data/processed/real_item_params.parquet`
- **BKT map:** `data/processed/real_bkt_params.parquet`
- **Eedi (distractor→misconception):** `s3://axonai-datasets-924300129944/eedi_mining_misconceptions/`
- **ASSISTments (skill join):** `s3://axonai-datasets-924300129944/assistments/2012-2013-data-with-predictions-4-final.csv`
- **Pre-subsample bank0:** 4211 items; **with Eedi distractors (QuestionId=problem_id overlap):** 37
- **Subsample used in sim:** 212 items; **concepts (sorted chain):** `[5, 75, 77, 79, 82, 84, 92, 93, 95, 103, 106, 278]`
- **Sparse Eedi overlap:** on this dataset only **37** matched items carry tagged distractors; most practice draws use ASSISTments-only items with *empty* `distractors` — so the weighted distractor model rarely runs. Expect **v1_uniform ≈ v2_misconception** on Elo unless overlap grows.
- **Misconception IDs in sampler (count):** 58; id map: tags from items + Eedi only
- *Graph:* linear chain `skill[0]→…→skill[n-1]` in sorted skill_id order (ablation control, not curriculum truth).

## 1. Headline: v2 – v1 (paired, same 500 students)
- Elo gain/hr, %Δ vs v1: **0.0000**
- TTM (median att.), % “faster” than v1: **0.0000**
- Retention @ 7d (cohort mean), % lift vs v1: **0.0000**

### Investor headline claim check (+55% / −25% / +19% vs baseline)

Compare magnitudes in §1 to the investor deck. Differences v1↔v2 on Elo/retention can appear if wrong-answer paths use extra random draws, so subsequent Bernoulli outcomes diverge. If lifts stay ~0% while Eedi is present, 2PL correctness remains the dominant state update; the headline +55% / −25% / +19% is **not** supported in sim.

## 2. Conditions

| Condition | Elo gain/hr (mean) | TTM (median) | Ret @7d | Ret @30d |
|---|---:|---:|---:|---:|
| `v1_uniform` | -124.3332 | 263.0 | 0.3803 | 0.2621 |
| `v2_misconception_only` | -124.3332 | 263.0 | 0.3803 | 0.2621 |
| `v2_full` | -124.3332 | 263.0 | 0.3803 | 0.2621 |
| `no_tutor_control` | -365.0518 | nan | 0.0344 | 0.0178 |

## 3. Paired p: v2 vs v1

- `elo_gain_per_hr`: 1.0
- `time_to_mastery`: 1.0
- `retention_7d`: 1.0
- `retention_30d`: 1.0

## 4. Paired p: v2 vs no_tutor_control

- `elo_gain_per_hr`: 1.0689911408016437e-188
- `time_to_mastery`: 1.0
- `retention_7d`: 5.597632217306145e-202
- `retention_30d`: 2.4626170610616383e-193
