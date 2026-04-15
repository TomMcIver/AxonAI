/**
 * Softer cohort display for class-wide concept maps so a few very low or very high
 * students don’t make the whole map look “broken” or “perfect”.
 * Uses a mild shrink toward the cohort mid-band (transparently labeled in UI).
 */
export function fairCohortDisplayMastery(raw) {
  if (raw == null || raw === undefined || Number.isNaN(raw)) return null;
  const x = typeof raw === 'number' && raw > 1 ? raw / 100 : raw;
  const clamped = Math.max(0, Math.min(1, x));
  const mid = 0.52;
  const factor = 0.68;
  return Math.max(0, Math.min(1, mid + (clamped - mid) * factor));
}

/** Build concept_id → 0–1 score map from /class/{id}/concept-summary for graph fills. */
export function masteryMapFromClassSummary(summary) {
  const list = summary?.concepts;
  if (!Array.isArray(list)) return null;
  const map = {};
  list.forEach((row) => {
    const id = row.concept_id;
    if (id == null) return;
    const fair = fairCohortDisplayMastery(row.avg_mastery);
    if (fair != null) {
      map[id] = fair;
      map[String(id)] = fair;
    }
  });
  return Object.keys(map).length ? map : null;
}

function normScore(raw) {
  if (raw == null || raw === undefined || Number.isNaN(raw)) return null;
  const v = typeof raw === 'number' && raw > 1 ? raw / 100 : raw;
  return Math.max(0, Math.min(1, v));
}

/** Median of numeric array (even count → average of two middle values). Less sensitive to outliers than mean. */
function medianScores(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  const mid = Math.floor(n / 2);
  if (n % 2 === 1) return sorted[mid];
  return (sorted[mid - 1] + sorted[mid]) / 2;
}

/**
 * When /class/.../concept-summary is empty, build a cohort map from individual GET /student/{id}/mastery payloads.
 * Per concept we use the **median** mastery across learners so a few high achievers don’t inflate the class colour.
 * Then the same fair display transform as the class-summary path.
 */
export function aggregateClassMasteryFromIndividualMasteries(masteryResponses, subjectFilter = null) {
  if (!Array.isArray(masteryResponses) || masteryResponses.length === 0) return null;
  const byConcept = new Map();
  masteryResponses.forEach((resp) => {
    const rows = resp?.concepts;
    if (!Array.isArray(rows)) return;
    rows.forEach((c) => {
      if (subjectFilter != null && c.subject != null && c.subject !== subjectFilter) return;
      const id = c.concept_id;
      if (id == null) return;
      const v = normScore(c.mastery_score);
      if (v == null) return;
      if (!byConcept.has(id)) byConcept.set(id, []);
      byConcept.get(id).push(v);
    });
  });
  const map = {};
  byConcept.forEach((scores, id) => {
    if (!scores.length) return;
    const central = medianScores(scores);
    if (central == null) return;
    const fair = fairCohortDisplayMastery(central);
    if (fair != null) {
      map[id] = fair;
      map[String(id)] = fair;
    }
  });
  return Object.keys(map).length ? map : null;
}
