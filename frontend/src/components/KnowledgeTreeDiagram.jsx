import React, {
  useCallback, useEffect, useMemo, useRef, useState,
} from 'react';
import { buildPrerequisiteTreeDatum } from '../utils/prerequisiteTree';
import {
  ancestorIdSet,
  boundsFromNodes,
  edgeKey,
  layoutTidyTree,
  linkPathOrthogonal,
  normId,
  pathEdgeKeySet,
} from '../utils/tidyTreeLayout';
import { DEPTH_BAND_FILLS, DEPTH_LABELS } from '../constants/graphDepthBands';

export { DEPTH_BAND_FILLS };

const NODE_W = 132;
const NODE_H = 58;
const MARGIN = 24;
/** Padding (CSS px) around each sibling-group hull; left/right use full pad; vertical target is this, shared when groups stack. */
const DEPTH_CLUSTER_PAD_PX = 16;
/** Minimum vertical pad (px) above/below the node hull inside a group tint; raised after layout gap so bands rarely collapse to flush. */
const DEPTH_CLUSTER_PAD_FLOOR_PX = 8;
/** Small margin reserved between stacked group tints when splitting vertical pad. */
const DEPTH_CLUSTER_SPLIT_EPS_PX = 1;

/** Mastery swatches (same semantics as KnowledgeGraphNew / student detail). */
export const MASTERY_LEGEND = [
  { fill: '#16a34a', label: 'Strong (≥70%)' },
  { fill: '#f97316', label: 'Developing (51–69%)' },
  { fill: '#dc2626', label: 'Focus (≤50%)' },
  { fill: '#9ca3af', label: 'Not assessed' },
];

/**
 * Equal top+bottom pad per sibling-group hull (depth-cluster rects).
 *
 * Same code for “padded” vs “stretched” looks: there is no second branch. One group alone in a depth column (n≤1)
 * keeps full pMax. Many single-node groups stacked share the vertical gap between hulls; p[i]+p[i+1] is capped by
 * that gap, so vp shrinks and bands hug the orange. Tall multi-node groups look roomier because pink space between
 * oranges is mostly sibling layout gap inside the hull, not outer vp.
 */
function solveSymmetricColumnPads(list, pMax, margin, pFloor) {
  const n = list.length;
  const p = new Array(n).fill(pMax);
  if (n <= 1) {
    return p.map((v) => Math.max(pFloor, v));
  }
  for (let iter = 0; iter < 160; iter += 1) {
    let changed = false;
    for (let i = 0; i < n - 1; i += 1) {
      const rawGap = list[i + 1].nodeMinY - list[i].nodeMaxY;
      const maxSum = Math.max(0, rawGap - margin);
      let a = p[i];
      let b = p[i + 1];
      if (a + b <= maxSum + 1e-6) continue;
      if (maxSum <= 0) {
        a = 0;
        b = 0;
      } else {
        const scale = maxSum / (a + b);
        a *= scale;
        b *= scale;
        a = Math.min(pMax, Math.max(0, a));
        b = Math.min(pMax, Math.max(0, b));
        if (a + b > maxSum) {
          const s = maxSum / (a + b);
          a *= s;
          b *= s;
        }
      }
      if (Math.abs(a - p[i]) > 1e-4 || Math.abs(b - p[i + 1]) > 1e-4) {
        p[i] = a;
        p[i + 1] = b;
        changed = true;
      }
    }
    if (!changed) break;
  }
  if (pFloor > 0) {
    for (let i = 0; i < n; i += 1) {
      p[i] = Math.max(p[i], pFloor);
    }
    for (let iter = 0; iter < 160; iter += 1) {
      let changed = false;
      for (let i = 0; i < n - 1; i += 1) {
        const rawGap = list[i + 1].nodeMinY - list[i].nodeMaxY;
        const maxSum = Math.max(0, rawGap - margin);
        if (p[i] + p[i + 1] <= maxSum + 1e-6) continue;
        const scale = maxSum / (p[i] + p[i + 1]);
        let a = p[i] * scale;
        let b = p[i + 1] * scale;
        a = Math.min(pMax, Math.max(0, a));
        b = Math.min(pMax, Math.max(0, b));
        if (a + b > maxSum) {
          const s = maxSum / (a + b);
          a *= s;
          b *= s;
        }
        if (Math.abs(a - p[i]) > 1e-4 || Math.abs(b - p[i + 1]) > 1e-4) {
          p[i] = a;
          p[i + 1] = b;
          changed = true;
        }
      }
      if (!changed) break;
    }
  }
  return p;
}

/**
 * One rounded depth tint per sibling group (same parent in the tidy tree): a single block around that branch.
 * Stacked groups in a column share vertical gap between blocks via solveSymmetricColumnPads (symmetric vp).
 */
function useDepthClusterBoxes(layout) {
  return useMemo(() => {
    if (!layout?.nodes?.length || !layout.hGap) return [];
    const hGap = layout.hGap;
    const pad = DEPTH_CLUSTER_PAD_PX;
    const parentOf = layout.parentOf || {};
    const groups = new Map();
    layout.nodes.forEach((n) => {
      const d = n.data?._layout?.depth;
      const depth = typeof d === 'number' ? d : Math.max(0, Math.round(n.x / hGap));
      const pid = parentOf[n.id];
      const groupKey = pid != null
        ? `${depth}::p${normId(pid)}`
        : `${depth}::n${normId(n.id)}`;
      if (!groups.has(groupKey)) groups.set(groupKey, []);
      groups.get(groupKey).push(n);
    });

    const drafts = [];
    groups.forEach((ns, groupKey) => {
      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;
      const first = ns[0];
      const d = typeof first.data?._layout?.depth === 'number'
        ? first.data._layout.depth
        : Math.max(0, Math.round(first.x / hGap));
      ns.forEach((n) => {
        minX = Math.min(minX, n.x - NODE_W / 2);
        maxX = Math.max(maxX, n.x + NODE_W / 2);
        minY = Math.min(minY, n.y - NODE_H / 2);
        maxY = Math.max(maxY, n.y + NODE_H / 2);
      });
      drafts.push({
        key: `cluster-${groupKey}`,
        d,
        minX,
        maxX,
        nodeMinY: minY,
        nodeMaxY: maxY,
      });
    });

    const byDepth = new Map();
    drafts.forEach((dr) => {
      if (!byDepth.has(dr.d)) byDepth.set(dr.d, []);
      byDepth.get(dr.d).push(dr);
    });

    const boxes = [];
    byDepth.forEach((list) => {
      list.sort((a, b) => a.nodeMinY - b.nodeMinY);
      const vPads = solveSymmetricColumnPads(
        list,
        pad,
        DEPTH_CLUSTER_SPLIT_EPS_PX,
        DEPTH_CLUSTER_PAD_FLOOR_PX,
      );
      list.forEach((dr, i) => {
        const vp = vPads[i];
        boxes.push({
          key: dr.key,
          x: dr.minX - pad,
          y: dr.nodeMinY - vp,
          width: dr.maxX - dr.minX + pad * 2,
          height: dr.nodeMaxY - dr.nodeMinY + vp * 2,
          fill: DEPTH_BAND_FILLS[dr.d % DEPTH_BAND_FILLS.length],
          rx: 12,
        });
      });
    });
    return boxes.sort((a, b) => a.x - b.x || a.y - b.y);
  }, [layout]);
}

/** Fixed overlay inside the SVG viewport (not affected by pan/zoom). */
function SvgColourLegend({ width, showMastery }) {
  const pad = 8;
  const legendW = 136;
  const row = 13;
  const depthRows = DEPTH_BAND_FILLS.length;
  const masteryRows = showMastery ? MASTERY_LEGEND.length : 0;
  const x0 = Math.max(pad, width - legendW - pad);
  const y0 = pad;
  let y = y0 + 12;
  const titleY = y;
  y += 12;
  const depthSubY = y;
  y += 10;
  const depthStartY = y;
  y += depthRows * row + 6;
  let masterySubY = 0;
  let masteryStartY = 0;
  if (showMastery) {
    masterySubY = y;
    y += 11;
    masteryStartY = y;
    y += masteryRows * row;
  }
  y += 8;
  const boxH = y - y0;

  return (
    <g className="graph-svg-legend" pointerEvents="none" aria-hidden="true">
      <rect
        x={x0 - 6}
        y={y0}
        width={legendW}
        height={boxH}
        rx={8}
        fill="#fffef4"
        stroke="#2c2418"
        strokeWidth={1.2}
        opacity={0.98}
      />
      <text
        x={x0}
        y={titleY}
        fontSize={9}
        fontWeight={700}
        fill="#1e293b"
        fontFamily="Inter, system-ui, sans-serif"
      >
        Colour key
      </text>
      <text x={x0} y={depthSubY} fontSize={7.5} fill="#64748b" fontFamily="Inter, system-ui, sans-serif">
        Depth (left → right)
      </text>
      {DEPTH_BAND_FILLS.map((fill, i) => {
        const yy = depthStartY + i * row;
        return (
          <g key={`d-${i}`}>
            <rect
              x={x0}
              y={yy - 8}
              width={14}
              height={10}
              rx={2}
              fill={fill}
              stroke="#2c2418"
              strokeWidth={0.85}
            />
            <text x={x0 + 20} y={yy} fontSize={8} fill="#334155" fontFamily="Inter, system-ui, sans-serif">
              {DEPTH_LABELS[i] ?? `Level ${i}`}
            </text>
          </g>
        );
      })}
      {showMastery && (
        <>
          <text x={x0} y={masterySubY} fontSize={7.5} fill="#64748b" fontFamily="Inter, system-ui, sans-serif">
            Mastery (nodes)
          </text>
          {MASTERY_LEGEND.map((m, i) => {
            const yy = masteryStartY + i * row;
            return (
              <g key={`m-${m.label}`}>
                <rect
                  x={x0}
                  y={yy - 8}
                  width={14}
                  height={10}
                  rx={2}
                  fill={m.fill}
                  stroke="#2c2418"
                  strokeWidth={0.85}
                />
                <text x={x0 + 20} y={yy} fontSize={8} fill="#334155" fontFamily="Inter, system-ui, sans-serif">
                  {m.label}
                </text>
              </g>
            );
          })}
        </>
      )}
    </g>
  );
}

function computeInitialMatrix(width, height, bounds, comfortFactor = 0.62) {
  const w = Math.max(32, width);
  const h = Math.max(32, height);
  const bw = Math.max(bounds.width, 1);
  const bh = Math.max(bounds.height, 1);
  const cx = bounds.x + bounds.width / 2;
  const cy = bounds.y + bounds.height / 2;
  const fit = Math.min(w / bw, h / bh)
    * (1 - (MARGIN * 2) / Math.min(w, h));
  const k = Math.min(1.45, Math.max(0.42, fit * comfortFactor));
  const tx = w / 2 - k * cx;
  const ty = h / 2 - k * cy;
  return { k, tx, ty };
}

/** Layout viewport from element. Skip near-zero reads (flex not laid out yet) to avoid 1×1 SVG + broken matrix. */
function readContainerSize(el) {
  if (!el) return { width: 640, height: 520 };
  const w = el.clientWidth;
  const h = el.clientHeight;
  if (w < 16 || h < 16) return null;
  return { width: w, height: h };
}

/** Borders use only the tidy-tree prerequisite path (root → selected), not the full DAG. */
function strokeForNode(id, selectedId, treePathIds) {
  if (selectedId == null) return { stroke: '#2c2418', strokeWidth: 3 };
  const nid = normId(id);
  const sid = normId(selectedId);
  if (!treePathIds.has(nid)) return { stroke: '#2c2418', strokeWidth: 2.5, muted: true };
  if (nid === sid) return { stroke: '#1d4ed8', strokeWidth: 4 };
  return { stroke: '#2563eb', strokeWidth: 3 };
}

/** Pixel-based lines so labels stay centered inside the node rect (tspan + em was misaligned under zoom). */
const LABEL_FONT_PX = 7;
const LABEL_LINE_H = 11;

function TreeNodeLabels({ lines }) {
  const safe = lines.filter(Boolean);
  if (safe.length === 0) return null;
  const n = safe.length;
  const total = (n - 1) * LABEL_LINE_H;
  const baseY = -total / 2;
  return safe.map((line, i) => (
    <text
      key={i}
      x={0}
      y={baseY + i * LABEL_LINE_H}
      textAnchor="middle"
      dominantBaseline="central"
      fill="#2c2418"
      style={{
        fontSize: LABEL_FONT_PX,
        fontFamily: 'Press Start 2P, Inter, system-ui, sans-serif',
        pointerEvents: 'none',
      }}
    >
      {line.length > 22 ? `${line.slice(0, 20)}…` : line}
    </text>
  ));
}

export default function KnowledgeTreeDiagram({
  concepts,
  edges,
  masteryMap,
  getNodeBasePresentation,
  selectedId,
  onNodeClick,
  mapOnly,
  showAllNodes,
  search,
  onZoomOutExpand,
  /** When set, camera refits only when this changes (avoids reset when selection expands the node list in map-only mode). */
  viewportLayoutKey,
  /** Fixed legend panel inside the SVG (top-right). */
  showLegend = true,
  /** Show mastery swatches when nodes use mastery colouring (e.g. class or student view). */
  showMasteryInLegend,
}) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const [size, setSize] = useState({ width: 640, height: 520 });
  const [matrix, setMatrix] = useState({ k: 1, tx: 0, ty: 0 });
  const panRef = useRef({
    dragging: false,
    startX: 0,
    startY: 0,
    origTx: 0,
    origTy: 0,
    moved: false,
  });
  /** Drop the click that often follows a pan (so it doesn’t clear selection). Timeout clears stale flags. */
  const eatNextBackgroundClearRef = useRef(false);
  const eatClearTimerRef = useRef(null);
  /** Last camera refit key: skip refit when only selection expands the graph (same key, new layout). */
  const lastFitKeyRef = useRef(null);

  /** Layout identity only (no mastery): avoids camera reset when colours/tooltips change. */
  const dataSig = useMemo(() => {
    const ids = concepts.map((c) => c.id).join(',');
    const es = edges
      .map((e) => `${e.prerequisite_concept_id}->${e.concept_id}`)
      .join('|');
    return `${ids}#${es}`;
  }, [concepts, edges]);

  const fitTriggerKey = viewportLayoutKey ?? dataSig;

  const rootDatum = useMemo(
    () => (concepts.length ? buildPrerequisiteTreeDatum(concepts, edges) : null),
    [concepts, edges],
  );

  const layout = useMemo(() => {
    if (!rootDatum) return null;
    try {
      return layoutTidyTree(rootDatum, { nodeW: NODE_W, nodeH: NODE_H });
    } catch {
      return null;
    }
  }, [rootDatum]);

  const layoutRef = useRef(layout);
  layoutRef.current = layout;

  const nodeById = useMemo(() => {
    const m = new Map();
    if (!layout) return m;
    layout.nodes.forEach((n) => m.set(n.id, n));
    return m;
  }, [layout]);

  const treePathIds = useMemo(() => {
    if (selectedId == null || !layout) return new Set();
    return ancestorIdSet(selectedId, layout.parentOf);
  }, [layout, selectedId]);

  const treePathEdgeKeys = useMemo(() => {
    if (selectedId == null || !layout) return new Set();
    return pathEdgeKeySet(selectedId, layout.parentOf);
  }, [layout, selectedId]);

  const depthClusterBoxes = useDepthClusterBoxes(layout);

  const legendShowMastery = showMasteryInLegend ?? Boolean(masteryMap);

  /** Floating tooltip (native SVG title is unreliable in some browsers). */
  const [hoverTip, setHoverTip] = useState(null);

  const sizeRef = useRef({ width: 640, height: 520 });

  const onResize = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const next = readContainerSize(el);
    if (!next) return;
    const { width: w, height: h } = next;
    const prev = sizeRef.current;
    if (w === prev.width && h === prev.height) return;
    sizeRef.current = { width: w, height: h };
    setSize({ width: w, height: h });
  }, []);

  useEffect(() => {
    onResize();
    const raf = requestAnimationFrame(onResize);
    const ro = new ResizeObserver(() => {
      window.requestAnimationFrame(onResize);
    });
    if (containerRef.current) ro.observe(containerRef.current);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [onResize]);

  // Fit view when fitTriggerKey changes. Retry until the container has real dimensions (flex can be 0×0 on first frames).
  useEffect(() => {
    if (!layout || layout.nodes.length === 0) return;
    if (lastFitKeyRef.current === fitTriggerKey) return;

    let cancelled = false;
    const tryFit = () => {
      if (cancelled) return;
      const el = containerRef.current;
      const s = readContainerSize(el);
      if (!s) {
        requestAnimationFrame(tryFit);
        return;
      }
      lastFitKeyRef.current = fitTriggerKey;
      const { width: w, height: h } = s;
      sizeRef.current = { width: w, height: h };
      setSize((prev) => (prev.width === w && prev.height === h ? prev : { width: w, height: h }));
      const b = boundsFromNodes(layout.nodes, NODE_W, NODE_H, MARGIN);
      setMatrix(computeInitialMatrix(w, h, b));
    };
    requestAnimationFrame(tryFit);
    return () => {
      cancelled = true;
    };
  }, [fitTriggerKey, layout]);

  // Refit when the container pixel size changes (viewport resize). Key-based effect above handles new graphs; this only fixes framing when width/height change (e.g. svh / layout settling).
  useEffect(() => {
    const lay = layoutRef.current;
    if (!lay?.nodes?.length) return;
    const b = boundsFromNodes(lay.nodes, NODE_W, NODE_H, MARGIN);
    setMatrix(computeInitialMatrix(size.width, size.height, b));
  }, [size.width, size.height]);

  useEffect(() => () => {
    if (eatClearTimerRef.current) window.clearTimeout(eatClearTimerRef.current);
  }, []);

  const wheelHandlerDepsRef = useRef({});
  wheelHandlerDepsRef.current = { mapOnly, showAllNodes, search };

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheelNative = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const rect = el.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const { mapOnly: mo, showAllNodes: san, search: se } = wheelHandlerDepsRef.current;
      setMatrix((prev) => {
        const scaleBy = Math.exp(-e.deltaY * 0.0012);
        let k = prev.k * scaleBy;
        k = Math.min(3.2, Math.max(0.18, k));
        const dx = (mx - prev.tx) / prev.k;
        const dy = (my - prev.ty) / prev.k;
        const tx = mx - dx * k;
        const ty = my - dy * k;
        return { k, tx, ty };
      });
    };
    el.addEventListener('wheel', onWheelNative, { passive: false });
    return () => el.removeEventListener('wheel', onWheelNative);
  }, [layout]);

  const onPointerDown = useCallback((e) => {
    if (e.button !== 0) return;
    if (e.target?.closest?.('.tree-nodes')) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    panRef.current = {
      dragging: true,
      startX: e.clientX,
      startY: e.clientY,
      origTx: matrix.tx,
      origTy: matrix.ty,
      moved: false,
    };
  }, [matrix.tx, matrix.ty]);

  const onPointerMove = useCallback((e) => {
    if (!panRef.current.dragging) return;
    const dx = e.clientX - panRef.current.startX;
    const dy = e.clientY - panRef.current.startY;
    if (dx * dx + dy * dy > 25) {
      panRef.current.moved = true;
    }
    setMatrix((m) => ({
      ...m,
      tx: panRef.current.origTx + dx,
      ty: panRef.current.origTy + dy,
    }));
  }, []);

  const onPointerUp = useCallback((e) => {
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
    if (panRef.current.dragging && panRef.current.moved) {
      eatNextBackgroundClearRef.current = true;
      if (eatClearTimerRef.current) window.clearTimeout(eatClearTimerRef.current);
      eatClearTimerRef.current = window.setTimeout(() => {
        eatNextBackgroundClearRef.current = false;
        eatClearTimerRef.current = null;
      }, 450);
    }
    panRef.current.dragging = false;
    panRef.current.moved = false;
  }, []);

  if (!concepts.length) {
    return (
      <div ref={containerRef} className="flex h-full min-h-0 w-full items-center justify-center text-sm text-slate-600">
        No concepts to display for this view.
      </div>
    );
  }

  if (!rootDatum || !layout || layout.nodes.length === 0) {
    return (
      <div ref={containerRef} className="flex h-full min-h-0 w-full items-center justify-center text-sm text-slate-600">
        Could not build tree layout for this graph.
      </div>
    );
  }

  return (
    <div
      className="relative h-full max-h-full min-w-0 w-full overflow-hidden"
      style={{ minHeight: 'min(400px, 55vh)' }}
    >
      <div
        ref={containerRef}
        className="absolute inset-0 min-h-0 min-w-0 overflow-hidden rounded-md border border-[#2c2418]/20 bg-[#fffef4] [touch-action:none] [overscroll-behavior:contain]"
      >
      {hoverTip && (
        <div
          className="pointer-events-none fixed z-[500] max-w-[min(100vw,18rem)] rounded-md border-2 border-[#2c2418] bg-[#fffef4] px-2 py-1.5 text-[11px] font-medium leading-snug text-[#2c2418] shadow-[3px_3px_0_#2c2418]"
          style={{
            left: Math.min(hoverTip.x + 14, typeof window !== 'undefined' ? window.innerWidth - 200 : hoverTip.x),
            top: hoverTip.y + 14,
          }}
        >
          {hoverTip.text}
        </div>
      )}
      <svg
        ref={svgRef}
        width={size.width}
        height={size.height}
        className="block max-h-full max-w-full cursor-grab touch-none select-none active:cursor-grabbing"
        role="img"
        aria-label="Prerequisite tree"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        onClick={(e) => {
          if (e.target !== e.currentTarget) return;
          if (eatNextBackgroundClearRef.current) {
            eatNextBackgroundClearRef.current = false;
            if (eatClearTimerRef.current) {
              window.clearTimeout(eatClearTimerRef.current);
              eatClearTimerRef.current = null;
            }
            return;
          }
          onNodeClick(null);
        }}
      >
        <g transform={`matrix(${matrix.k},0,0,${matrix.k},${matrix.tx},${matrix.ty})`}>
          <g className="depth-cluster-boxes" aria-hidden="true">
            {depthClusterBoxes.map((b) => (
              <rect
                key={b.key}
                x={b.x}
                y={b.y}
                width={b.width}
                height={b.height}
                rx={b.rx}
                ry={b.rx}
                fill={b.fill}
                stroke="rgba(44, 36, 24, 0.28)"
                strokeWidth={1.25}
              />
            ))}
          </g>
          <g className="tree-links" fill="none">
            {layout.links.map((link) => {
              const s = nodeById.get(link.source);
              const t = nodeById.get(link.target);
              if (!s || !t) return null;
              const ek = edgeKey(link.source, link.target);
              const onPath = treePathEdgeKeys.has(ek);
              const stroke = selectedId != null && onPath ? '#1d4ed8' : '#6b5a42';
              const opacity = selectedId != null && !onPath ? 0.12 : 0.72;
              const sw = onPath && selectedId != null ? 3.5 : 1.75;
              const sx = s.x + NODE_W / 2;
              const sy = s.y;
              const tx = t.x - NODE_W / 2;
              const ty = t.y;
              return (
                <path
                  key={ek}
                  d={linkPathOrthogonal(sx, sy, tx, ty)}
                  stroke={stroke}
                  strokeOpacity={opacity}
                  strokeWidth={sw}
                />
              );
            })}
          </g>
          <g className="tree-nodes">
            {layout.nodes.map((n) => {
              const base = getNodeBasePresentation(n.id);
              const { stroke, strokeWidth, muted } = strokeForNode(
                n.id,
                selectedId,
                treePathIds,
              );
              const lines = String(base.label || '').split('\n');
              const tip = base.tooltip != null && base.tooltip !== ''
                ? String(base.tooltip)
                : lines.join(' ');
              return (
                <g
                  key={n.id}
                  transform={`translate(${n.x},${n.y})`}
                  style={{ cursor: 'pointer' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onNodeClick(normId(n.id));
                  }}
                >
                  <title>{tip}</title>
                  <rect
                    x={-NODE_W / 2}
                    y={-NODE_H / 2}
                    width={NODE_W}
                    height={NODE_H}
                    rx={4}
                    fill={base.fill}
                    stroke={stroke}
                    strokeWidth={strokeWidth}
                    opacity={muted ? 0.22 : 1}
                    onPointerEnter={(e) => {
                      e.stopPropagation();
                      setHoverTip({ x: e.clientX, y: e.clientY, text: tip });
                    }}
                    onPointerMove={(e) => {
                      e.stopPropagation();
                      setHoverTip({ x: e.clientX, y: e.clientY, text: tip });
                    }}
                    onPointerLeave={(e) => {
                      e.stopPropagation();
                      setHoverTip(null);
                    }}
                  />
                  <TreeNodeLabels lines={lines} />
                </g>
              );
            })}
          </g>
        </g>
        {showLegend && (
          <SvgColourLegend width={size.width} showMastery={legendShowMastery} />
        )}
      </svg>
      <p className="pointer-events-none absolute bottom-2 left-3 right-3 text-[10px] leading-snug text-slate-500 sm:left-auto sm:max-w-sm sm:text-right">
        <span className="block sm:inline">Scroll to zoom · drag to pan.</span>{' '}
        <span className="text-slate-400">Tinted blocks group each branch (siblings); depth goes left → right.</span>
      </p>
      </div>
    </div>
  );
}
