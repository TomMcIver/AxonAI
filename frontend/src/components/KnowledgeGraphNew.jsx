import React, { useRef, useState, useEffect, useCallback } from 'react';
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
  const [tooltip, setTooltip] = useState(null);

  const svgW = 1000;
  const colX = { 1: 90, 2: 260, 3: 470, 4: 680, 5: 870 };
  const colCount = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  const NODE_SPACING = 70;
  const TOP_OFFSET = 52;
  const NODE_R = 16;

  const positioned = concepts.map(n => {
    const lvl = n.difficulty_level || 3;
    const col = colCount[lvl] || 0;
    colCount[lvl] = col + 1;
    return { ...n, x: colX[lvl] || 470, y: TOP_OFFSET + col * NODE_SPACING };
  });

  const maxNodes = Math.max(...Object.values(colCount));
  const svgH = Math.max(420, TOP_OFFSET + maxNodes * NODE_SPACING + 60);

  const posMap = {};
  positioned.forEach(n => { posMap[n.id] = n; });

  const visibleEdges = edges.filter(e => posMap[e.concept_id] && posMap[e.prerequisite_concept_id]);

  // Full path traversal from selected node
  const { ancestors, descendants, ancestorEdgeIdx, descendantEdgeIdx } = selected
    ? getFullPath(selected, visibleEdges)
    : { ancestors: new Set(), descendants: new Set(), ancestorEdgeIdx: new Set(), descendantEdgeIdx: new Set() };

  const colLabels = [
    { x: 90,  label: 'Foundation' }, { x: 260, label: 'Basic' },
    { x: 470, label: 'Intermediate' }, { x: 680, label: 'Advanced' }, { x: 870, label: 'Complex' },
  ];

  return (
    <div style={{ ...GLASS, flex: 1, overflow: 'hidden', position: 'relative' }}>
      <div style={{
        padding: '10px 14px 6px',
        borderBottom: '1px solid rgba(148,163,184,0.1)',
        fontSize: 10, color: '#94A3B8', fontFamily: "'Inter', sans-serif",
        display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
      }}>
        <span>{concepts.length} concepts · {visibleEdges.length} connections · scroll to explore · click a node to select</span>
        {selected && (
          <span style={{ display: 'flex', gap: 10 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 20, height: 2, background: '#3B82F6', display: 'inline-block', borderRadius: 1 }} />
              <span style={{ fontSize: 9 }}>Prerequisites</span>
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 20, height: 2, background: '#8B5CF6', display: 'inline-block', borderRadius: 1 }} />
              <span style={{ fontSize: 9 }}>Leads to</span>
            </span>
          </span>
        )}
      </div>
      <div style={{ overflowY: 'auto', maxHeight: 'calc(100% - 38px)' }}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${svgW} ${svgH}`}
        width="100%"
        style={{ display: 'block' }}
      >
        <defs>
          <marker id="kg-arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#94A3B8" opacity="0.5" />
          </marker>
          <marker id="kg-arrow-prereq" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#3B82F6" opacity="0.9" />
          </marker>
          <marker id="kg-arrow-leads" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#8B5CF6" opacity="0.9" />
          </marker>
          <marker id="kg-arrow-direct" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#0F766E" opacity="1" />
          </marker>
        </defs>

        {/* Column labels */}
        {colLabels.map(col => (
          <text key={col.label} x={col.x} y={22} textAnchor="middle" style={{
            fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 9,
            fill: '#94A3B8', textTransform: 'uppercase',
          }}>
            {col.label}
          </text>
        ))}

        {/* Edges — dimmed non-path edges when something is selected */}
        {visibleEdges.map((edge, i) => {
          const src = posMap[edge.prerequisite_concept_id];
          const tgt = posMap[edge.concept_id];
          if (!src || !tgt) return null;

          const isDirect = selected && (edge.concept_id === selected || edge.prerequisite_concept_id === selected);
          const isAncestor = ancestorEdgeIdx.has(i);
          const isDescendant = descendantEdgeIdx.has(i);
          const isInPath = isDirect || isAncestor || isDescendant;

          const isSameCol = Math.abs(src.x - tgt.x) < 30;
          let pathD;
          if (isSameCol) {
            pathD = `M${src.x},${src.y} C${src.x - 80},${src.y} ${tgt.x - 80},${tgt.y} ${tgt.x},${tgt.y}`;
          } else {
            const mx = (src.x + tgt.x) / 2;
            const my = Math.min(src.y, tgt.y) - 20;
            pathD = `M${src.x},${src.y} Q${mx},${my} ${tgt.x},${tgt.y}`;
          }

          const stroke = isDirect ? '#0F766E'
            : isAncestor ? '#3B82F6'
            : isDescendant ? '#8B5CF6'
            : '#CBD5E1';
          const strokeWidth = isDirect ? 2.5 : isAncestor || isDescendant ? 1.8 : 1;
          const opacity = selected
            ? (isInPath ? 0.9 : 0.1)
            : Math.max(0.2, edge.strength || 0.4);
          const marker = isDirect ? 'url(#kg-arrow-direct)'
            : isAncestor ? 'url(#kg-arrow-prereq)'
            : isDescendant ? 'url(#kg-arrow-leads)'
            : 'url(#kg-arrow)';

          return (
            <path
              key={i}
              d={pathD}
              fill="none"
              stroke={stroke}
              strokeWidth={strokeWidth}
              opacity={opacity}
              markerEnd={marker}
            />
          );
        })}

        {/* Nodes */}
        {positioned.map(node => {
          const cfg = DIFF[node.difficulty_level] || DIFF[3];
          const isSel = selected === node.id;
          const isAncestor = ancestors.has(node.id);
          const isDescendant = descendants.has(node.id);
          const isInPath = isSel || isAncestor || isDescendant;
          const r = isSel ? NODE_R + 4 : NODE_R;

          const ringColor = isAncestor ? '#3B82F6' : isDescendant ? '#8B5CF6' : null;
          const nodeOpacity = selected ? (isInPath ? 1 : 0.25) : 0.82;

          const labelLines = wrapLabel(node.name, 13);

          return (
            <g
              key={node.id}
              style={{ cursor: 'pointer' }}
              onClick={() => onSelect(node.id)}
              onMouseEnter={e => {
                if (!svgRef.current) return;
                const rect = svgRef.current.getBoundingClientRect();
                const sx = rect.width / svgW;
                setTooltip({
                  name: node.name, level: node.difficulty_level,
                  type: node.concept_type, count: node.question_count ?? 0,
                  role: isSel ? 'selected' : isAncestor ? 'prerequisite' : isDescendant ? 'leads to' : null,
                  x: rect.left + node.x * sx,
                  y: rect.top + node.y * (rect.height / svgH) - r * (rect.height / svgH) - 8,
                });
              }}
              onMouseLeave={() => setTooltip(null)}
            >
              {/* Path ring glow */}
              {ringColor && (
                <circle cx={node.x} cy={node.y} r={r + 5}
                  fill="none" stroke={ringColor} strokeWidth={2} opacity={0.5} />
              )}
              <circle
                cx={node.x} cy={node.y} r={r}
                fill={cfg.color}
                opacity={nodeOpacity}
                stroke={isSel ? '#0F766E' : ringColor || 'transparent'}
                strokeWidth={isSel ? 3 : ringColor ? 2 : 0}
              />
              <text x={node.x} y={node.y + 4} textAnchor="middle" style={{
                fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700,
                fontSize: 8, fill: '#fff', pointerEvents: 'none',
              }}>
                L{node.difficulty_level}
              </text>
              {labelLines.map((line, li) => (
                <text key={li} x={node.x} y={node.y + NODE_R + 13 + li * 9} textAnchor="middle" style={{
                  fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 7.5,
                  fill: selected ? (isInPath ? '#1e293b' : '#94A3B8') : '#475569',
                  pointerEvents: 'none',
                }}>
                  {line}
                </text>
              ))}
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
          borderRadius: 10, padding: '7px 12px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
          zIndex: 50, whiteSpace: 'nowrap', pointerEvents: 'none',
        }}>
          <div style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 13, color: '#1e293b' }}>
            {tooltip.name}
          </div>
          <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 11, color: '#64748B', marginTop: 2 }}>
            Level {tooltip.level} · {tooltip.type} · {tooltip.count} Q
            {tooltip.role && (
              <span style={{
                marginLeft: 6, padding: '1px 6px', borderRadius: 10, fontSize: 9, fontWeight: 600,
                background: tooltip.role === 'prerequisite' ? 'rgba(59,130,246,0.1)' : tooltip.role === 'leads to' ? 'rgba(139,92,246,0.1)' : 'rgba(15,118,110,0.1)',
                color: tooltip.role === 'prerequisite' ? '#3B82F6' : tooltip.role === 'leads to' ? '#8B5CF6' : '#0F766E',
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
