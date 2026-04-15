/**
 * Tidy tree layout (Reingold–Tilford style) without d3.
 * Coordinates: x = depth (left→right), y = breadth (top→bottom).
 */

const DEFAULT_NODE_W = 132;
const DEFAULT_NODE_H = 58;

/** After tidy placement, scale all Y (must combine with vGap math so nodes never overlap — see layout). */
export const DEFAULT_Y_COMPACT = 0.7;

/**
 * Minimum clear gap (CSS px) between two node rectangles after yCompact.
 * Larger values give adjacent depth-cluster bands room for vertical padding; too small and stacked single-node
 * groups share one narrow gap and tints collapse flush to the node (see KnowledgeTreeDiagram.solveSymmetricColumnPads).
 */
export const MIN_NODE_BORDER_GAP_PX = 40;

/** Extra vertical space (CSS px) inserted between top-level subtrees — lower = less white gap between Early / Core / Stretch blocks. */
export const REF_TOP_SUBTREE_GAP_PX = 11;

/**
 * Added to node width for each depth step (x): Fundamentals → Core → Stretch, etc.
 * Lower = depth columns sit closer horizontally; higher = more air between layers.
 */
export const DEPTH_COLUMN_STEP_EXTRA_PX = 64;

/** Normalize concept ids so tree maps and Sets stay consistent (API may use number or string). */
export function normId(id) {
  if (id == null) return null;
  const n = Number(id);
  return Number.isFinite(n) ? n : String(id);
}

/** Stable key for a directed tree edge (matches link source/target after normalization). */
export function edgeKey(parentId, childId) {
  return `${normId(parentId)}-${normId(childId)}`;
}

function sortChildren(nodes) {
  if (!nodes || nodes.length === 0) return [];
  return [...nodes].sort((a, b) => {
    const na = a.concept?.name || String(a.id);
    const nb = b.concept?.name || String(b.id);
    return na.localeCompare(nb, undefined, { sensitivity: 'base' });
  });
}

/**
 * @param {object} rootDatum — from buildPrerequisiteTreeDatum
 * @param {{ nodeW?: number, nodeH?: number, yCompact?: number }} opts — yCompact scales all Y (default {@link DEFAULT_Y_COMPACT})
 */
export function layoutTidyTree(rootDatum, opts = {}) {
  const nodeW = opts.nodeW ?? DEFAULT_NODE_W;
  const nodeH = opts.nodeH ?? DEFAULT_NODE_H;
  const yCompact = opts.yCompact ?? DEFAULT_Y_COMPACT;
  const hGap = nodeW + DEPTH_COLUMN_STEP_EXTRA_PX;
  // Unscaled row pitch: after y*yCompact, consecutive leaf centers must be ≥ nodeH + MIN_NODE_BORDER_GAP_PX.
  const minCenterPx = nodeH + MIN_NODE_BORDER_GAP_PX;
  const vGap = Math.max(
    Math.ceil(minCenterPx / yCompact),
    Math.round(hGap * 0.06),
  );
  /** Fractional leaf step between virtual-root children → ~REF_TOP_SUBTREE_GAP_PX in output. */
  const extraLeafBetweenTopSubtrees = REF_TOP_SUBTREE_GAP_PX / (vGap * yCompact);

  let leafY = 0;

  function visit(n, depth) {
    const kids = sortChildren(n.children);
    if (kids.length === 0) {
      const y = leafY * vGap;
      leafY += 1;
      n._layout = { x: depth * hGap, y, depth };
      return y;
    }
    const ys = kids.map((c) => visit(c, depth + 1));
    const y = (Math.min(...ys) + Math.max(...ys)) / 2;
    n._layout = { x: depth * hGap, y, depth };
    return y;
  }

  if (rootDatum.virtual && rootDatum.children?.length) {
    rootDatum.children.forEach((c, i) => {
      if (i > 0) {
        leafY += extraLeafBetweenTopSubtrees;
      }
      visit(c, 0);
    });
  } else {
    visit(rootDatum, 0);
  }

  const nodes = [];
  const links = [];
  const parentOf = {};

  function collect(n, parent) {
    if (!n.virtual) {
      nodes.push({
        id: normId(n.id),
        x: n._layout.x,
        y: n._layout.y * yCompact,
        data: n,
      });
      if (parent && !parent.virtual) {
        const cid = normId(n.id);
        const pid = normId(parent.id);
        parentOf[cid] = pid;
        links.push({ source: pid, target: cid });
      }
    }
    sortChildren(n.children).forEach((c) => collect(c, n));
  }

  collect(rootDatum, null);

  return { nodes, links, parentOf, nodeW, nodeH, hGap, vGap: vGap * yCompact, yCompact };
}

export function ancestorIdSet(selectedId, parentOf) {
  const s = new Set();
  let cur = normId(selectedId);
  const guard = new Set();
  while (cur != null && !guard.has(cur)) {
    guard.add(cur);
    s.add(cur);
    const p = parentOf[cur];
    cur = p != null ? normId(p) : null;
  }
  return s;
}

/** Ordered chain from root → selected along tree parent links. */
export function chainRootToSelected(selectedId, parentOf) {
  if (selectedId == null) return [];
  const up = [];
  let cur = normId(selectedId);
  const guard = new Set();
  while (cur != null && !guard.has(cur)) {
    guard.add(cur);
    up.push(cur);
    const p = parentOf[cur];
    cur = p != null ? normId(p) : null;
  }
  return up.reverse();
}

/** Tree edges on the root→selected path (same keys as link rendering uses). */
export function pathEdgeKeySet(selectedId, parentOf) {
  const keys = new Set();
  let cur = normId(selectedId);
  while (cur != null) {
    const p = parentOf[cur];
    if (p != null) {
      const pn = normId(p);
      keys.add(edgeKey(pn, cur));
      cur = pn;
    } else {
      cur = null;
    }
  }
  return keys;
}

/** Orthogonal connector for LR tree: parent (sx,sy) → child (tx,ty) */
export function linkPathOrthogonal(sx, sy, tx, ty) {
  const midx = (sx + tx) / 2;
  return `M ${sx} ${sy} L ${midx} ${sy} L ${midx} ${ty} L ${tx} ${ty}`;
}

export function boundsFromNodes(nodes, nodeW, nodeH, pad = 24) {
  if (nodes.length === 0) {
    return { x: 0, y: 0, width: 1, height: 1 };
  }
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  nodes.forEach((n) => {
    minX = Math.min(minX, n.x - nodeW / 2);
    maxX = Math.max(maxX, n.x + nodeW / 2);
    minY = Math.min(minY, n.y - nodeH / 2);
    maxY = Math.max(maxY, n.y + nodeH / 2);
  });
  return {
    x: minX - pad,
    y: minY - pad,
    width: maxX - minX + pad * 2,
    height: maxY - minY + pad * 2,
  };
}
