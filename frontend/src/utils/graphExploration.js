import { normId } from './tidyTreeLayout';

/** Concepts with no incoming prerequisite edge (DAG roots / entry points). */
export function getRootConceptIds(concepts, edges, limit = 12) {
  if (!concepts?.length) return [];
  const childIds = new Set();
  (edges || []).forEach((e) => childIds.add(normId(e.concept_id)));
  const roots = concepts
    .filter((c) => !childIds.has(normId(c.id)))
    .map((c) => normId(c.id));
  const sorted = [...new Set(roots)].sort((a, b) => Number(a) - Number(b));
  return sorted.slice(0, limit);
}

/**
 * Next concepts along strongest “unlocks” edges (forward in learning direction).
 * Picks up to `max` distinct targets from edges where prerequisite_concept_id === id.
 */
export function forwardUnlockIds(id, edges, max = 2) {
  const nid = normId(id);
  const out = (edges || []).filter((e) => normId(e.prerequisite_concept_id) === nid);
  const sorted = [...out].sort((a, b) => (b.strength ?? 0) - (a.strength ?? 0));
  const seen = new Set();
  const res = [];
  for (const e of sorted) {
    const t = normId(e.concept_id);
    if (seen.has(t)) continue;
    seen.add(t);
    res.push(t);
    if (res.length >= max) break;
  }
  return res;
}
