/**
 * Cohort / class mastery display bands (graph, snapshot, bars).
 * Developing: strictly above 50% and below 70%. Focus: at or below 50%.
 */
export const MASTERY_STRONG_MIN = 0.7;

/** @param {number|null|undefined} score01: 0–1 (or 0–100 from API, normalized by callers) */
export function normalizeMastery01(score01) {
  if (score01 == null || Number.isNaN(score01)) return null;
  const x = typeof score01 === 'number' && score01 > 1 ? score01 / 100 : score01;
  return Math.max(0, Math.min(1, x));
}

/** @returns {'strong'|'developing'|'focus'|'none'} */
export function masteryBandKey(score01) {
  const x = normalizeMastery01(score01);
  if (x == null) return 'none';
  if (x >= MASTERY_STRONG_MIN) return 'strong';
  if (x > 0.5) return 'developing';
  return 'focus';
}
