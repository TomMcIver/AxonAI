# Phase 2 — investor ablation (**real** 2PL bank + Eedi)
**Generated (UTC):** 2026-04-25T05:39:22.031667+00:00Z

## 0. Provenance

- **Item params (Gate A):** `data/processed/real_item_params.parquet`
- **BKT map:** `data/processed/real_bkt_params.parquet`
- **Eedi (distractor→misconception):** `s3://axonai-datasets-924300129944/eedi_mining_misconceptions/`
- **ASSISTments (skill join):** `s3://axonai-datasets-924300129944/assistments/2012-2013-data-with-predictions-4-final.csv`
- **Verified crosswalk file:** `data\processed\gate_a_eedi_verified_crosswalk.csv`; **use verified-only bank:** True (**21** assist to Eedi rows loaded)
- **Pre-subsample bank0:** 6 items; **with non-empty distractor lists (tags optional per option):** 6
- **Subsample used in sim:** 6 items; **concepts (sorted chain):** `[25, 280, 281, 346]`
- **Eedi join mode:** `gate_a_eedi_verified_crosswalk.csv` (verified only). Each bank item takes distractor and misconception fields from the **mapped** Eedi QuestionId (not identity problem_id=QuestionId).
- **Misconception IDs in sampler (count):** 9; id map: tags from items + Eedi only
- *Graph:* linear chain `skill[0] -> ... -> skill[n-1]` in sorted skill_id order (ablation control, not curriculum truth).

## 1. Headline: v2 – v1 (paired, same 500 students)
- Elo gain/hr, %Δ vs v1: **0.0000**
- TTM (median att.), % “faster” than v1: **0.0000**
- Retention @ 7d (cohort mean), % lift vs v1: **0.0000**

### Investor headline claim check (+55% / −25% / +19% vs baseline)

Compare magnitudes in §1 to the investor deck. With the verified crosswalk, all 6 bank0 items reference Eedi distractor/misconception metadata (tags may still be empty if Eedi has no options for that QuestionId). Differences v1 to v2 on Elo/retention can appear if wrong-answer paths use extra random draws, so subsequent Bernoulli outcomes diverge. If lifts stay around 0% while v2 is active, 2PL correctness remains the dominant state update; a strong investor-style headline is **not** supported in sim.

## 2. Conditions

| Condition | Elo gain/hr (mean) | TTM (median) | Ret @7d | Ret @30d |
|---|---:|---:|---:|---:|
| `v1_uniform` | -118.9863 | 67.0 | 0.3579 | 0.2649 |
| `v2_misconception_only` | -118.9863 | 67.0 | 0.3579 | 0.2649 |
| `v2_full` | -118.9863 | 67.0 | 0.3579 | 0.2649 |
| `no_tutor_control` | -152.3074 | 94.0 | 0.3205 | 0.2377 |

## 3. Paired p: v2 vs v1

- `elo_gain_per_hr`: 1.0
- `time_to_mastery`: 1.0
- `retention_7d`: 1.0
- `retention_30d`: 1.0

## 4. Paired p: v2 vs no_tutor_control

- `elo_gain_per_hr`: 0.03701366785334948
- `time_to_mastery`: 0.00812229476353951
- `retention_7d`: 4.262657072604453e-05
- `retention_30d`: 0.00019562864008137307
