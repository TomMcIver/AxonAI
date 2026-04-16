import { buildPrerequisiteTreeDatum } from './prerequisiteTree';
import { layoutTidyTree, normId } from './tidyTreeLayout';

/**
 * Map concept id → depth index (0 = Fundamentals … 5 = Further), using the same
 * tidy tree as the graph (strongest parent per child).
 */
export function computeDepthIndexByConceptId(concepts, prerequisites) {
  const map = new Map();
  if (!concepts?.length) return map;
  try {
    const root = buildPrerequisiteTreeDatum(concepts, prerequisites || []);
    const layout = layoutTidyTree(root);
    layout.nodes.forEach((node) => {
      const raw = node.data?._layout?.depth;
      if (raw == null) return;
      const idx = Math.max(0, Math.min(5, Math.floor(raw)));
      const id = normId(node.id);
      map.set(id, idx);
      map.set(String(id), idx);
    });
    return map;
  } catch {
    return map;
  }
}
