/**
 * Reduce prerequisite edges (DAG) to a single parent per child for tidy-tree layout:
 * pick the strongest incoming edge per node. Multiple natural roots become
 * children of a virtual root (hidden in the diagram).
 */

export function buildPrerequisiteTreeDatum(concepts, edges) {
  const ids = new Set(concepts.map((c) => c.id));
  const byId = Object.fromEntries(concepts.map((c) => [c.id, c]));

  const incoming = {};
  edges.forEach((e) => {
    if (!ids.has(e.concept_id) || !ids.has(e.prerequisite_concept_id)) return;
    const child = e.concept_id;
    if (!incoming[child]) incoming[child] = [];
    incoming[child].push({
      parent: e.prerequisite_concept_id,
      strength: e.strength ?? 0.5,
    });
  });

  const parentOf = {};
  for (const c of concepts) {
    const inc = incoming[c.id];
    if (!inc || inc.length === 0) continue;
    const best = inc.reduce((a, b) => ((b.strength ?? 0) > (a.strength ?? 0) ? b : a));
    parentOf[c.id] = best.parent;
  }

  function rebuildChildren() {
    const ch = {};
    Object.entries(parentOf).forEach(([cidStr, p]) => {
      const cid = Number(cidStr);
      if (!ch[p]) ch[p] = [];
      ch[p].push(cid);
    });
    return ch;
  }

  let children = rebuildChildren();
  let rootIds = concepts.map((c) => c.id).filter((id) => parentOf[id] == null);

  // Cycle in “strongest parent” choice: no roots. Break by un-parenting the smallest id.
  if (rootIds.length === 0 && concepts.length > 0) {
    const minId = Math.min(...concepts.map((c) => c.id));
    delete parentOf[minId];
    children = rebuildChildren();
    rootIds = concepts.map((c) => c.id).filter((id) => parentOf[id] == null);
  }

  function sortChildIds(list) {
    return list.slice().sort((a, b) => {
      const na = byId[a]?.name || String(a);
      const nb = byId[b]?.name || String(b);
      return na.localeCompare(nb, undefined, { sensitivity: 'base' });
    });
  }

  function toDatum(id) {
    const concept = byId[id];
    const kids = sortChildIds(children[id] || []).map(toDatum);
    return {
      id,
      virtual: false,
      concept,
      children: kids.length ? kids : undefined,
    };
  }

  if (rootIds.length === 1) {
    return toDatum(rootIds[0]);
  }

  return {
    id: '__virtual_root__',
    virtual: true,
    concept: null,
    children: sortChildIds(rootIds).map(toDatum),
  };
}
