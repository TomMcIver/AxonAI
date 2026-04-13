import React, { useRef, useState, useEffect, useCallback, useMemo } from 'react';
import { getConcepts } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';
import ErrorState from './ErrorState';

/* ── CONSTANTS ── */

const DIFF = {
  5: { label: 'Very Hard', color: '#EF4444', bg: 'rgba(239,68,68,0.08)', text: '#B91C1C' },
  4: { label: 'Hard',      color: '#F97316', bg: 'rgba(249,115,22,0.08)', text: '#C2410C' },
  3: { label: 'Medium',    color: '#F59E0B', bg: 'rgba(245,158,11,0.08)', text: '#B45309' },
  2: { label: 'Easy',      color: '#10B981', bg: 'rgba(16,185,129,0.08)', text: '#047857' },
  1: { label: 'Foundation',color: '#10B981', bg: 'rgba(16,185,129,0.08)', text: '#047857' },
};

const RANKS = [5, 4, 3, 2, 1];

const GLASS = {
  background: 'rgba(255,255,255,0.5)',
  backdropFilter: 'blur(16px) saturate(140%)',
  WebkitBackdropFilter: 'blur(16px) saturate(140%)',
  border: '1px solid rgba(255,255,255,0.6)',
  borderRadius: 20,
  boxShadow: '0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.7)',
};

/* ── SMALL HELPERS ── */

function wrapLabel(name, maxLen = 13) {
  if (name.length <= maxLen) return [name];
  const breakAt = name.lastIndexOf(' ', maxLen);
  if (breakAt > 0) {
    const line1 = name.slice(0, breakAt);
    const rest = name.slice(breakAt + 1);
    return [line1, rest.length > maxLen ? rest.slice(0, maxLen - 1) + '…' : rest];
  }
  return [name.slice(0, maxLen - 1) + '…'];
}

// BFS to find full ancestor + descendant chains from a selected node
function getFullPath(nodeId, edges) {
  const ancestors = new Set();
  const ancestorEdgeIdx = new Set();
  let frontier = [nodeId];
  while (frontier.length) {
    const next = [];
    frontier.forEach(id => {
      edges.forEach((e, i) => {
        if (e.concept_id === id && !ancestors.has(e.prerequisite_concept_id)) {
          ancestors.add(e.prerequisite_concept_id);
          ancestorEdgeIdx.add(i);
          next.push(e.prerequisite_concept_id);
        }
      });
    });
    frontier = next;
  }

  const descendants = new Set();
  const descendantEdgeIdx = new Set();
  frontier = [nodeId];
  while (frontier.length) {
    const next = [];
    frontier.forEach(id => {
      edges.forEach((e, i) => {
        if (e.prerequisite_concept_id === id && !descendants.has(e.concept_id)) {
          descendants.add(e.concept_id);
          descendantEdgeIdx.add(i);
          next.push(e.concept_id);
        }
      });
    });
    frontier = next;
  }

  return { ancestors, descendants, ancestorEdgeIdx, descendantEdgeIdx };
}

function DiffDot({ level, size = 10 }) {
  const cfg = DIFF[level] || DIFF[3];
  return (
    <span style={{
      display: 'inline-block', width: size, height: size,
      borderRadius: '50%', background: cfg.color, flexShrink: 0,
    }} />
  );
}

function DiffBadge({ level }) {
  const cfg = DIFF[level] || DIFF[3];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600,
      background: cfg.bg, color: cfg.text,
      fontFamily: "'Lexend', sans-serif",
    }}>
      <DiffDot level={level} size={7} />
      Lvl {level} — {cfg.label}
    </span>
  );
}

function QBadge({ count }) {
  if (!count && count !== 0) return null;
  return (
    <span style={{
      padding: '1px 7px', borderRadius: 20, fontSize: 10, fontWeight: 600,
      background: 'rgba(15,118,110,0.08)', color: '#0F766E',
      fontFamily: "'Lexend', sans-serif", whiteSpace: 'nowrap', flexShrink: 0,
    }}>
      {count} Q
    </span>
  );
}

/* ── SIDEBAR ── */

function Sidebar({ concepts, selected, search, onSearch, onSelect }) {
  return (
    <div style={{
      width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column',
      ...GLASS, borderRadius: 16, overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 14px 10px',
        borderBottom: '1px solid rgba(148,163,184,0.12)',
      }}>
        <p style={{
          fontFamily: "'Lexend', sans-serif", fontWeight: 500, fontSize: 10,
          textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748B',
          margin: '0 0 8px 0',
        }}>
          {concepts.length} Concepts
        </p>
        <input
          type="text"
          placeholder="Search concepts…"
          value={search}
          onChange={e => onSearch(e.target.value)}
          style={{
            width: '100%', boxSizing: 'border-box',
            padding: '6px 10px',
            border: '1px solid rgba(148,163,184,0.25)',
            borderRadius: 8, fontSize: 13,
            background: 'rgba(255,255,255,0.6)',
            backdropFilter: 'blur(8px)',
            color: '#1e293b', outline: 'none',
            fontFamily: "'Inter', sans-serif",
          }}
        />
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
        {concepts.map(c => {
          const cfg = DIFF[c.difficulty_level] || DIFF[3];
          const isSel = selected === c.id;
          return (
            <div
              key={c.id}
              onClick={() => onSelect(c.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '7px 14px', cursor: 'pointer',
                background: isSel ? 'rgba(15,118,110,0.08)' : 'transparent',
                borderLeft: isSel ? '3px solid #0F766E' : '3px solid transparent',
                transition: 'background 120ms ease',
              }}
              onMouseEnter={e => { if (!isSel) e.currentTarget.style.background = 'rgba(148,163,184,0.08)'; }}
              onMouseLeave={e => { if (!isSel) e.currentTarget.style.background = 'transparent'; }}
            >
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: cfg.color, flexShrink: 0,
              }} />
              <span style={{
                flex: 1, fontSize: 12, color: isSel ? '#0F766E' : '#334155',
                fontFamily: "'Inter', sans-serif", fontWeight: isSel ? 600 : 400,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {c.name}
              </span>
              <QBadge count={c.question_count ?? 0} />
            </div>
          );
        })}
        {concepts.length === 0 && (
          <p style={{ textAlign: 'center', color: '#94A3B8', fontSize: 12, padding: '20px 0',
            fontFamily: "'Inter', sans-serif" }}>
            No concepts match
          </p>
        )}
      </div>
    </div>
  );
}

/* ── GRID VIEW ── */

function GridView({ concepts, edges, selected, hovered, onSelect, onHover, onLeave }) {
  const grouped = {};
  RANKS.forEach(r => { grouped[r] = []; });
  concepts.forEach(c => {
    const lvl = c.difficulty_level || 3;
    if (!grouped[lvl]) grouped[lvl] = [];
    grouped[lvl].push(c);
  });

  return (
    <div style={{ ...GLASS, flex: 1, padding: 16, display: 'flex', flexDirection: 'column', gap: 4, overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', marginBottom: 4 }}>
        <span style={{ fontSize: 10, color: '#94A3B8', fontFamily: "'Inter', sans-serif" }}>
          Hardest at top · lines show prerequisites
        </span>
      </div>
      {RANKS.map(rank => {
        const cfg = DIFF[rank] || DIFF[3];
        const items = grouped[rank] || [];
        return (
          <div key={rank} style={{
            display: 'flex', alignItems: 'flex-start', gap: 10, paddingBottom: 10,
            borderBottom: '1px solid rgba(148,163,184,0.08)',
          }}>
            {/* Level label */}
            <div style={{ width: 80, flexShrink: 0, paddingTop: 4 }}>
              <span style={{
                display: 'inline-block', padding: '2px 6px', borderRadius: 20,
                fontSize: 9, fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.06em', background: cfg.bg, color: cfg.text,
                fontFamily: "'Lexend', sans-serif",
              }}>
                Lvl {rank}
              </span>
              <p style={{ fontSize: 9, color: '#94A3B8', margin: '2px 0 0', fontFamily: "'Inter', sans-serif" }}>
                {cfg.label}
              </p>
            </div>

            {/* Concept chips */}
            <div style={{ flex: 1, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {items.length > 0 ? items.map(c => {
                const isSel = selected === c.id;
                const isHov = hovered === c.id;
                return (
                  <div
                    key={c.id}
                    onClick={() => onSelect(c.id)}
                    onMouseEnter={() => onHover(c.id)}
                    onMouseLeave={onLeave}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 5,
                      padding: '4px 10px', borderRadius: 8, cursor: 'pointer',
                      fontSize: 11, fontFamily: "'Inter', sans-serif",
                      border: isSel
                        ? '1.5px solid #0F766E'
                        : isHov
                          ? `1.5px solid ${cfg.color}`
                          : '1px solid rgba(148,163,184,0.2)',
                      background: isSel
                        ? 'rgba(15,118,110,0.1)'
                        : isHov
                          ? cfg.bg
                          : 'rgba(255,255,255,0.7)',
                      color: isSel ? '#0F766E' : '#334155',
                      boxShadow: isSel ? '0 0 0 2px rgba(15,118,110,0.15)' : 'none',
                      transition: 'all 140ms cubic-bezier(0.16,1,0.3,1)',
                      transform: isSel ? 'scale(1.03)' : 'scale(1)',
                      backdropFilter: 'blur(4px)',
                    }}
                  >
                    <DiffDot level={c.difficulty_level} size={7} />
                    <span style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.name}
                    </span>
                    {(c.question_count ?? 0) > 0 && (
                      <span style={{ fontSize: 9, color: '#0F766E', fontWeight: 600 }}>
                        {c.question_count}Q
                      </span>
                    )}
                  </div>
                );
              }) : (
                <span style={{ fontSize: 11, color: '#CBD5E1', fontStyle: 'italic', padding: '4px 0',
                  fontFamily: "'Inter', sans-serif" }}>
                  No concepts at this level
                </span>
              )}
            </div>
          </div>
        );
      })}

      {/* Legend */}
      <div style={{
        display: 'flex', gap: 16, flexWrap: 'wrap', paddingTop: 8,
        borderTop: '1px solid rgba(148,163,184,0.1)',
      }}>
        {RANKS.map(r => {
          const cfg = DIFF[r];
          return (
            <span key={r} style={{
              display: 'flex', alignItems: 'center', gap: 5,
              fontSize: 10, color: '#64748B', fontFamily: "'Inter', sans-serif",
            }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: cfg.color, display: 'inline-block' }} />
              {cfg.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}

/* ── MAP (SVG) VIEW ── */

function MapView({ concepts, edges, selected, onSelect }) {
  const svgRef = useRef(null);
  const scrollRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  /* ── Dynamic column layout based on actual difficulty levels ── */
  const levels = useMemo(
    () => [...new Set(concepts.map(c => c.difficulty_level || 3))].sort((a, b) => a - b),
    [concepts],
  );

  const svgW = 1060;
  const NODE_R = 18;
  const NODE_GAP = 92;
  const TOP = 56;
  const PAD_X = 80;

  const colX = useMemo(() => {
    const map = {};
    const span = svgW - PAD_X * 2;
    levels.forEach((lvl, i) => {
      map[lvl] = levels.length < 2 ? svgW / 2 : PAD_X + (i / (levels.length - 1)) * span;
    });
    return map;
  }, [levels]);

  const COL_NAMES = { 1: 'Foundation', 2: 'Basic', 3: 'Intermediate', 4: 'Advanced', 5: 'Complex' };

  /* ── Position nodes in their columns ── */
  const { positioned, svgH, posMap } = useMemo(() => {
    const counter = {};
    levels.forEach(l => { counter[l] = 0; });

    const nodes = concepts.map(n => {
      const lvl = n.difficulty_level || 3;
      const idx = counter[lvl] || 0;
      counter[lvl] = idx + 1;
      return { ...n, x: colX[lvl] || svgW / 2, y: TOP + idx * NODE_GAP };
    });

    const maxCol = Math.max(...Object.values(counter), 1);
    const h = Math.max(440, TOP + maxCol * NODE_GAP + 60);

    const pm = {};
    nodes.forEach(n => { pm[n.id] = n; });

    return { positioned: nodes, svgH: h, posMap: pm };
  }, [concepts, colX, levels]);

  const visibleEdges = useMemo(
    () => edges.filter(e => posMap[e.concept_id] && posMap[e.prerequisite_concept_id]),
    [edges, posMap],
  );

  /* ── Full BFS path when a node is selected ── */
  const pathData = useMemo(() => {
    if (!selected) return null;
    const info = getFullPath(selected, visibleEdges);
    const nodeIds = new Set([selected]);
    info.ancestors.forEach(id => nodeIds.add(id));
    info.descendants.forEach(id => nodeIds.add(id));
    return { ...info, nodeIds };
  }, [selected, visibleEdges]);

  /* ── Edge path generator ── */
  function edgePath(src, tgt) {
    const sameCol = Math.abs(src.x - tgt.x) < 20;
    if (sameCol) {
      const off = -54;
      return `M${src.x},${src.y} C${src.x + off},${src.y} ${tgt.x + off},${tgt.y} ${tgt.x},${tgt.y}`;
    }
    const mx = (src.x + tgt.x) / 2;
    const my = (src.y + tgt.y) / 2 - Math.abs(src.x - tgt.x) * 0.12;
    return `M${src.x},${src.y} Q${mx},${my} ${tgt.x},${tgt.y}`;
  }

  return (
    <div style={{ ...GLASS, flex: 1, overflow: 'hidden', position: 'relative' }}>
      {/* Info bar */}
      <div style={{
        padding: '10px 14px 6px',
        borderBottom: '1px solid rgba(148,163,184,0.1)',
        fontSize: 10, color: '#94A3B8', fontFamily: "'Inter', sans-serif",
        display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
      }}>
        <span>
          {concepts.length} concepts · {visibleEdges.length} connections · click a node to see its full learning path
        </span>
        {selected && (
          <span style={{ display: 'flex', gap: 12 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 20, height: 2.5, background: '#3B82F6', display: 'inline-block', borderRadius: 2 }} />
              <span style={{ fontSize: 9, fontWeight: 500 }}>Prerequisites (needs first)</span>
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 20, height: 2.5, background: '#8B5CF6', display: 'inline-block', borderRadius: 2 }} />
              <span style={{ fontSize: 9, fontWeight: 500 }}>Leads to (unlocks)</span>
            </span>
          </span>
        )}
      </div>

      <div ref={scrollRef} style={{ overflowY: 'auto', overflowX: 'auto', maxHeight: 'calc(100% - 38px)' }}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${svgW} ${svgH}`}
          width="100%"
          style={{ display: 'block', minWidth: 600 }}
        >
          <defs>
            <marker id="kg-arr-gray" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
              <polygon points="0 0, 7 2.5, 0 5" fill="#CBD5E1" opacity="0.5" />
            </marker>
            <marker id="kg-arr-blue" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
              <polygon points="0 0, 7 2.5, 0 5" fill="#3B82F6" opacity="0.85" />
            </marker>
            <marker id="kg-arr-purple" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
              <polygon points="0 0, 7 2.5, 0 5" fill="#8B5CF6" opacity="0.85" />
            </marker>
          </defs>

          {/* Column headers + guide lines */}
          {levels.map(lvl => {
            const x = colX[lvl];
            return (
              <g key={`col-${lvl}`}>
                <text x={x} y={24} textAnchor="middle" style={{
                  fontFamily: "'Lexend', sans-serif", fontWeight: 600, fontSize: 10,
                  fill: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em',
                }}>
                  {COL_NAMES[lvl] || `Level ${lvl}`}
                </text>
                <line x1={x} y1={36} x2={x} y2={svgH - 16}
                  stroke="#E2E8F0" strokeWidth={1} strokeDasharray="4 4" opacity={0.5}
                />
              </g>
            );
          })}

          {/* Edges — rendered behind nodes */}
          {visibleEdges.map((edge, i) => {
            const src = posMap[edge.prerequisite_concept_id];
            const tgt = posMap[edge.concept_id];
            if (!src || !tgt) return null;

            const isAncestorEdge = pathData && pathData.ancestorEdgeIdx.has(i);
            const isDescendantEdge = pathData && pathData.descendantEdgeIdx.has(i);
            const isPathEdge = isAncestorEdge || isDescendantEdge;

            const stroke = isAncestorEdge ? '#3B82F6' : isDescendantEdge ? '#8B5CF6' : '#CBD5E1';
            const sw = isPathEdge ? 2.5 : 0.8;
            const opacity = selected ? (isPathEdge ? 0.85 : 0.07) : 0.18;
            const marker = isAncestorEdge
              ? 'url(#kg-arr-blue)'
              : isDescendantEdge
                ? 'url(#kg-arr-purple)'
                : 'url(#kg-arr-gray)';

            return (
              <path key={i} d={edgePath(src, tgt)} fill="none"
                stroke={stroke} strokeWidth={sw} opacity={opacity} markerEnd={marker}
              />
            );
          })}

          {/* Nodes */}
          {positioned.map(node => {
            const cfg = DIFF[node.difficulty_level] || DIFF[3];
            const isSel = selected === node.id;
            const isInPath = pathData && pathData.nodeIds.has(node.id);
            const isAncestor = pathData && pathData.ancestors.has(node.id);
            const isDescendant = pathData && pathData.descendants.has(node.id);
            const r = isSel ? NODE_R + 3 : NODE_R;
            const nodeOpacity = selected ? (isInPath ? 1 : 0.22) : 0.9;

            const lines = wrapLabel(node.name, 12);
            const labelFill = selected ? (isInPath ? '#1e293b' : '#CBD5E1') : '#475569';

            return (
              <g key={node.id} style={{ cursor: 'pointer' }}
                onClick={() => onSelect(node.id)}
                onMouseEnter={e => {
                  if (!svgRef.current) return;
                  const rect = svgRef.current.getBoundingClientRect();
                  const sx = rect.width / svgW;
                  const sy = rect.height / svgH;
                  const scrollTop = scrollRef.current ? scrollRef.current.scrollTop : 0;
                  const role = isSel ? 'selected'
                    : isAncestor ? 'prerequisite'
                    : isDescendant ? 'unlocks'
                    : null;
                  setTooltip({
                    name: node.name, level: node.difficulty_level,
                    type: node.concept_type, count: node.question_count ?? 0, role,
                    x: rect.left + node.x * sx,
                    y: rect.top + node.y * sy - scrollTop * sy - 10,
                  });
                }}
                onMouseLeave={() => setTooltip(null)}
              >
                {/* Glow ring for path nodes */}
                {isInPath && (
                  <circle cx={node.x} cy={node.y} r={r + 5}
                    fill="none"
                    stroke={isSel ? '#0F766E' : isAncestor ? '#3B82F6' : '#8B5CF6'}
                    strokeWidth={2} opacity={0.25}
                  />
                )}
                {/* Main circle */}
                <circle cx={node.x} cy={node.y} r={r}
                  fill={cfg.color} opacity={nodeOpacity}
                  stroke={isSel ? '#0F766E' : isAncestor ? '#3B82F6' : isDescendant ? '#8B5CF6' : 'rgba(255,255,255,0.6)'}
                  strokeWidth={isSel ? 3 : isInPath ? 2.5 : 1}
                />
                {/* Level text inside circle */}
                <text x={node.x} y={node.y + 4} textAnchor="middle" style={{
                  fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700,
                  fontSize: 9, fill: '#fff', pointerEvents: 'none',
                }}>
                  L{node.difficulty_level}
                </text>
                {/* Label with background for readability */}
                {lines.map((line, li) => {
                  const ly = node.y + NODE_R + 8 + li * 13;
                  return (
                    <React.Fragment key={li}>
                      <rect
                        x={node.x - 38} y={ly - 8}
                        width={76} height={12}
                        fill="rgba(255,255,255,0.85)" rx={3}
                        opacity={nodeOpacity}
                      />
                      <text x={node.x} y={ly} textAnchor="middle" style={{
                        fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 9,
                        fill: labelFill, pointerEvents: 'none',
                      }}>
                        {line}
                      </text>
                    </React.Fragment>
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed', left: tooltip.x, top: tooltip.y - 8,
          transform: 'translateX(-50%)',
          background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid rgba(148,163,184,0.2)',
          borderRadius: 10, padding: '8px 14px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
          zIndex: 9999, whiteSpace: 'nowrap', pointerEvents: 'none',
        }}>
          <div style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 14, color: '#1e293b' }}>
            {tooltip.name}
          </div>
          <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 11, color: '#64748B', marginTop: 3 }}>
            Level {tooltip.level} · {tooltip.type} · {tooltip.count} questions
            {tooltip.role && (
              <span style={{
                marginLeft: 6, padding: '2px 8px', borderRadius: 10, fontSize: 9, fontWeight: 600,
                background: tooltip.role === 'prerequisite' ? 'rgba(59,130,246,0.1)'
                  : tooltip.role === 'unlocks' ? 'rgba(139,92,246,0.1)'
                  : 'rgba(15,118,110,0.1)',
                color: tooltip.role === 'prerequisite' ? '#3B82F6'
                  : tooltip.role === 'unlocks' ? '#8B5CF6'
                  : '#0F766E',
              }}>
                {tooltip.role}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── DETAIL PANEL ── */

function DetailPanel({ concept, concepts, edges, onSelect }) {
  if (!concept) {
    return (
      <div style={{
        width: 280, flexShrink: 0, ...GLASS, borderRadius: 16,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
      }}>
        <p style={{
          textAlign: 'center', color: '#94A3B8', fontSize: 12,
          fontFamily: "'Inter', sans-serif",
        }}>
          Click a concept to view details
        </p>
      </div>
    );
  }

  const prereqs = edges
    .filter(e => e.concept_id === concept.id)
    .map(e => {
      const pc = concepts.find(c => c.id === e.prerequisite_concept_id);
      return pc ? { ...pc, strength: e.strength } : null;
    })
    .filter(Boolean);

  const dependents = edges
    .filter(e => e.prerequisite_concept_id === concept.id)
    .map(e => {
      const dc = concepts.find(c => c.id === e.concept_id);
      return dc ? { ...dc, strength: e.strength } : null;
    })
    .filter(Boolean);

  const cfg = DIFF[concept.difficulty_level] || DIFF[3];

  return (
    <div style={{
      width: 280, flexShrink: 0, ...GLASS, borderRadius: 16,
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      {/* Concept header */}
      <div style={{
        padding: '16px 16px 12px',
        borderBottom: '1px solid rgba(148,163,184,0.12)',
        background: `linear-gradient(135deg, ${cfg.bg} 0%, transparent 100%)`,
      }}>
        <h3 style={{
          fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700,
          fontSize: 15, color: '#1e293b', margin: '0 0 8px 0', lineHeight: 1.3,
        }}>
          {concept.name}
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
          <DiffBadge level={concept.difficulty_level} />
          {concept.concept_type && (
            <span style={{
              fontSize: 10, color: '#64748B', textTransform: 'capitalize',
              fontFamily: "'Lexend', sans-serif",
            }}>
              {concept.concept_type}
            </span>
          )}
        </div>
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700,
            fontSize: 22, color: '#0F766E',
          }}>
            {concept.question_count ?? 0}
          </span>
          <span style={{ fontSize: 11, color: '#64748B', fontFamily: "'Lexend', sans-serif" }}>
            questions available
          </span>
        </div>
      </div>

      {/* Prerequisites */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <RelList
          title="Prerequisites"
          count={prereqs.length}
          items={prereqs}
          emptyMsg="Foundational — no prerequisites"
          onSelect={onSelect}
        />
        <RelList
          title="Required by"
          count={dependents.length}
          items={dependents}
          emptyMsg="Not required by any concept"
          onSelect={onSelect}
        />
      </div>
    </div>
  );
}

function RelList({ title, count, items, emptyMsg, onSelect }) {
  return (
    <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(148,163,184,0.08)' }}>
      <h5 style={{
        fontFamily: "'Lexend', sans-serif", fontWeight: 500, fontSize: 10,
        textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94A3B8',
        margin: '0 0 8px 0',
      }}>
        {title} ({count})
      </h5>
      {items.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {items.map(item => {
            const cfg = DIFF[item.difficulty_level] || DIFF[3];
            return (
              <div
                key={item.id}
                onClick={() => onSelect(item.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 7,
                  cursor: 'pointer', padding: '4px 6px', borderRadius: 7,
                  transition: 'background 120ms',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(148,163,184,0.1)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: cfg.color, flexShrink: 0 }} />
                <span style={{
                  flex: 1, fontSize: 11, color: '#334155',
                  fontFamily: "'Inter', sans-serif",
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {item.name}
                </span>
                <span style={{
                  fontSize: 9, color: '#0F766E', fontWeight: 600, flexShrink: 0,
                  fontFamily: "'Lexend', sans-serif",
                }}>
                  {(item.strength * 100).toFixed(0)}%
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <p style={{ fontSize: 11, color: '#CBD5E1', fontStyle: 'italic', margin: 0,
          fontFamily: "'Inter', sans-serif" }}>
          {emptyMsg}
        </p>
      )}
    </div>
  );
}

/* ── MAIN EXPORT ── */

export default function KnowledgeGraphNew({ subject = 'Mathematics', mapOnly = false }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [search, setSearch] = useState('');
  const [view, setView] = useState(mapOnly ? 'map' : 'grid'); // 'grid' | 'map'

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    setSelected(null);
    getConcepts(subject)
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [subject]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner message={`Loading ${subject} concepts…`} />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  const allConcepts = (data.concepts || []);
  const allEdges = (data.prerequisites || []);

  // Filter for search (used in sidebar + grid)
  const filtered = search
    ? allConcepts.filter(c => c.name.toLowerCase().includes(search.toLowerCase()))
    : allConcepts;

  const selectedConcept = selected ? allConcepts.find(c => c.id === selected) : null;

  function handleSelect(id) {
    setSelected(id);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, height: '100%' }}>
      {/* Top toolbar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 12, color: '#64748B', fontFamily: "'Inter', sans-serif" }}>
            <span style={{ fontWeight: 600, color: '#1e293b' }}>{allConcepts.length}</span> concepts ·{' '}
            <span style={{ fontWeight: 600, color: '#1e293b' }}>{allEdges.length}</span> links
          </div>
          {/* Inline search — shown in toolbar when mapOnly, otherwise search lives in sidebar */}
          {mapOnly && (
            <input
              type="text"
              placeholder="Search concepts…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                padding: '5px 10px',
                border: '1px solid rgba(148,163,184,0.25)',
                borderRadius: 8, fontSize: 12,
                background: 'rgba(255,255,255,0.6)',
                backdropFilter: 'blur(8px)',
                color: '#1e293b', outline: 'none',
                fontFamily: "'Inter', sans-serif",
                width: 200,
              }}
            />
          )}
        </div>

        {/* View toggle */}
        <div style={{
          display: 'inline-flex', borderRadius: 10, overflow: 'hidden',
          border: '1px solid rgba(148,163,184,0.25)',
          background: 'rgba(255,255,255,0.5)',
        }}>
          {['grid', 'map'].map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              style={{
                padding: '5px 14px', border: 'none', cursor: 'pointer',
                background: view === v ? '#0F766E' : 'transparent',
                color: view === v ? '#fff' : '#64748B',
                fontFamily: "'Lexend', sans-serif", fontSize: 12, fontWeight: 500,
                textTransform: 'capitalize', transition: 'all 160ms',
              }}
            >
              {v === 'grid' ? 'Grid' : 'Map'}
            </button>
          ))}
        </div>
      </div>

      {/* Panel layout — full 3-panel normally, centre-only when mapOnly */}
      <div style={{ display: 'flex', gap: 12, flex: 1, minHeight: 0, alignItems: 'stretch' }}>
        {!mapOnly && (
          <Sidebar
            concepts={filtered}
            selected={selected}
            search={search}
            onSearch={setSearch}
            onSelect={handleSelect}
          />
        )}

        {/* Center: visualization */}
        {view === 'grid' ? (
          <GridView
            concepts={filtered}
            edges={allEdges}
            selected={selected}
            hovered={hovered}
            onSelect={handleSelect}
            onHover={setHovered}
            onLeave={() => setHovered(null)}
          />
        ) : (
          <MapView
            concepts={allConcepts}
            edges={allEdges}
            selected={selected}
            onSelect={handleSelect}
          />
        )}

        {!mapOnly && (
          <DetailPanel
            concept={selectedConcept}
            concepts={allConcepts}
            edges={allEdges}
            onSelect={handleSelect}
          />
        )}
      </div>
    </div>
  );
}
