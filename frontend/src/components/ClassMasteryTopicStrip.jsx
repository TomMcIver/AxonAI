import React, { useEffect, useMemo, useState } from 'react';
import { getConcepts } from '../api/axonai';
import {
  DEPTH_BAND_FILLS,
  DEPTH_LABELS,
  clampDepthIndex,
  depthLabel,
} from '../constants/graphDepthBands';
import LoadingSpinner from './LoadingSpinner';
import { computeDepthIndexByConceptId } from '../utils/conceptDepthFromTree';
import { masteryBandKey } from '../constants/masteryBands';

/** Matches KnowledgeGraph difficulty scale (1 foundational → 5 very hard). */
const DIFFICULTY = {
  1: { label: 'Foundational' },
  2: { label: 'Easy' },
  3: { label: 'Medium' },
  4: { label: 'Hard' },
  5: { label: 'Very hard' },
};

const TOPIC_SORT = {
  weakest: { key: 'weakest', label: 'Weakest first' },
  on_track: { key: 'on_track', label: 'On track' },
  ahead: { key: 'ahead', label: 'Ahead' },
};

function normDifficulty(level) {
  const n = Number(level);
  if (!Number.isFinite(n)) return 3;
  return Math.min(5, Math.max(1, Math.round(n)));
}

function difficultyMeta(level) {
  const n = normDifficulty(level);
  return { level: n, ...(DIFFICULTY[n] || DIFFICULTY[3]) };
}

/**
 * Same mastery bands as the knowledge graph; use inline styles so colours always show
 * (Tailwind arbitrary classes may be missing from compiled.css).
 */
function masteryGraphTileStyle(score01, options = {}) {
  const { maxWidth = 176 } = options;
  const base = {
    borderRadius: 12,
    borderWidth: 1.5,
    borderStyle: 'solid',
    boxShadow: '0 4px 12px rgba(61, 43, 31, 0.12)',
    padding: '6px 10px',
    maxWidth,
    fontSize: 11,
    lineHeight: 1.35,
    fontWeight: 500,
    boxSizing: 'border-box',
    cursor: 'default',
  };
  if (score01 == null) {
    return {
      ...base,
      borderColor: '#9ca3af',
      background: '#f3f4f6',
      backgroundColor: '#f3f4f6',
      color: '#1e293b',
    };
  }
  const band = masteryBandKey(score01);
  if (band === 'strong') {
    return {
      ...base,
      borderColor: '#89B39F',
      background: '#EFF7F3',
      backgroundColor: '#EFF7F3',
      color: '#4A7362',
    };
  }
  if (band === 'developing') {
    return {
      ...base,
      borderColor: '#D4A785',
      background: '#FAF2EA',
      backgroundColor: '#FAF2EA',
      color: '#8B6348',
    };
  }
  /* Focus band in blossom pink family. */
  return {
    ...base,
    borderColor: '#D59AA9',
    background: '#FBEFF3',
    backgroundColor: '#FBEFF3',
    color: '#8A5563',
  };
}

function strandChipStyle(row) {
  const fill = DEPTH_BAND_FILLS[clampDepthIndex(row.depthIndex)] || '#e2e8f0';
  return {
    borderRadius: 12,
    border: '1px solid rgba(61, 43, 31, 0.2)',
    boxShadow: 'none',
    padding: '6px 10px',
    maxWidth: 200,
    fontSize: 11,
    lineHeight: 1.35,
    fontWeight: 500,
    boxSizing: 'border-box',
    cursor: 'default',
    background: fill,
    backgroundColor: fill,
    color: '#1e293b',
  };
}

function bandKey(score01) {
  const k = masteryBandKey(score01);
  if (k === 'none') return 'focus';
  return k;
}

function partitionByBand(items) {
  const strong = [];
  const developing = [];
  const focus = [];
  for (const c of items) {
    const b = bandKey(c.score);
    if (b === 'strong') strong.push(c);
    else if (b === 'developing') developing.push(c);
    else focus.push(c);
  }
  return { strong, developing, focus };
}

/** Topic-type summary rows: same Strong / Developing / Focus stacking as topic tiles (uses `avg`). */
function partitionStrandRows(strands) {
  const strong = [];
  const developing = [];
  const focus = [];
  for (const s of strands) {
    const b = bandKey(s.avg);
    if (b === 'strong') strong.push(s);
    else if (b === 'developing') developing.push(s);
    else focus.push(s);
  }
  const sortWithin = (arr) =>
    [...arr].sort(
      (a, b) =>
        (a.depthIndex ?? 0) - (b.depthIndex ?? 0) || String(a.name).localeCompare(String(b.name)),
    );
  return {
    strong: sortWithin(strong),
    developing: sortWithin(developing),
    focus: sortWithin(focus),
  };
}

/** Up to `maxTotal` topics, at most `maxPerBand` from each mastery colour band, order from parent sort. */
function pickBalancedByBand(sortedList, maxTotal = 15, maxPerBand = 5) {
  const counts = { focus: 0, developing: 0, strong: 0 };
  const out = [];
  for (const c of sortedList) {
    if (out.length >= maxTotal) break;
    const b = bandKey(c.score);
    if (counts[b] >= maxPerBand) continue;
    out.push(c);
    counts[b] += 1;
  }
  return out;
}

function sortTopicsStable(list, mode) {
  const arr = [...list];
  if (mode === 'weakest') {
    arr.sort((a, b) => a.score - b.score || String(a.name).localeCompare(String(b.name)));
  } else if (mode === 'ahead') {
    arr.sort((b, a) => a.score - b.score || String(a.name).localeCompare(String(b.name)));
  } else {
    /* on_track: closest to ~55% “developing” centre first */
    const target = 0.55;
    arr.sort(
      (a, b) =>
        Math.abs(a.score - target) - Math.abs(b.score - target) || String(a.name).localeCompare(String(b.name)),
    );
  }
  return arr;
}

function StrandTypeChip({ row: s, selected, onToggle }) {
  const pct = Math.round(s.avg * 100);
  const tested = s.testedCount ?? s.count ?? 0;
  const total = s.totalConcepts != null ? s.totalConcepts : tested;
  const coverageLine =
    total > 0
      ? `${tested} of ${total} with class mastery`
      : `${tested} with class mastery`;
  const interactive = typeof onToggle === 'function';
  const baseStyle = strandChipStyle(s);
  const style = {
    ...baseStyle,
    cursor: interactive ? 'pointer' : baseStyle.cursor,
    outline: selected ? '3px solid #2c2418' : 'none',
    outlineOffset: selected ? 1 : 0,
  };
  return (
    <div
      role={interactive ? 'button' : undefined}
      aria-pressed={interactive ? selected : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? () => onToggle(s.depthIndex) : undefined}
      onKeyDown={
        interactive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onToggle(s.depthIndex);
              }
            }
          : undefined
      }
      style={style}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = 'none';
        e.currentTarget.style.filter = 'brightness(0.97) saturate(0.94)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none';
        e.currentTarget.style.filter = 'none';
        e.currentTarget.style.transform = 'none';
      }}
      title={
        interactive
          ? `${s.name}: ${pct}% class average from ${coverageLine} (class mastery in this column) · Click to filter topics below`
          : `${s.name}: ${pct}% class average · ${coverageLine}`
      }
    >
      <span
        style={{
          display: 'block',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          fontWeight: 600,
        }}
      >
        {s.name}
      </span>
      <span style={{ display: 'block', marginTop: 4, fontSize: 10, fontWeight: 400, opacity: 0.95 }}>
        {pct}% class avg
      </span>
      <span
        style={{
          display: 'block',
          marginTop: 3,
          fontSize: 9,
          fontWeight: 500,
          opacity: 0.88,
          lineHeight: 1.3,
        }}
      >
        {coverageLine}
      </span>
    </div>
  );
}

function TopicMasteryTile({ topic: c, selected, onSelect }) {
  const pct = Math.round(c.score * 100);
  const dLab = depthLabel(c.depthIdx ?? 0);
  const { level, label: diffLabel } = difficultyMeta(c.difficulty_level);
  const interactive = typeof onSelect === 'function';
  const isSelected = selected != null && String(selected) === String(c.id);
  const base = masteryGraphTileStyle(c.score);
  const style = {
    ...base,
    cursor: interactive ? 'pointer' : base.cursor,
    outline: isSelected ? '3px solid #0f766e' : 'none',
    outlineOffset: isSelected ? 2 : 0,
  };
  const fireSelect = () => {
    if (!interactive) return;
    onSelect({
      id: c.id,
      name: c.name,
      score: c.score,
      depthIdx: c.depthIdx,
      difficulty_level: c.difficulty_level,
    });
  };
  return (
    <div
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? fireSelect : undefined}
      onKeyDown={
        interactive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fireSelect();
              }
            }
          : undefined
      }
      style={style}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 8px 20px rgba(61, 43, 31, 0.16)';
        e.currentTarget.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(61, 43, 31, 0.12)';
        e.currentTarget.style.transform = 'none';
      }}
      title={
        interactive
          ? `${c.name} · Depth: ${dLab} · Difficulty ${level}/5 (${diffLabel}) · ${pct}% · Click for details below`
          : `${c.name} · Depth: ${dLab} (graph column) · Difficulty ${level}/5 (${diffLabel}) · ${pct}% class mastery`
      }
    >
      <span
        style={{
          display: 'block',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          fontWeight: 600,
        }}
      >
        {c.name}
      </span>
      <span
        style={{
          display: 'flex',
          marginTop: 4,
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 4,
          fontSize: 9,
          fontWeight: 400,
          opacity: 0.95,
        }}
      >
        <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 700 }}>{pct}%</span>
        <span
          style={{
            maxWidth: 88,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            fontWeight: 600,
            opacity: 0.92,
            textAlign: 'right',
          }}
          title={`Graph column: ${dLab}`}
        >
          {dLab}
        </span>
      </span>
      <span
        style={{
          display: 'block',
          marginTop: 5,
          paddingTop: 4,
          borderTop: '1px solid rgba(44,36,24,0.12)',
          fontSize: 8,
          lineHeight: 1.35,
          fontWeight: 500,
          color: '#334155',
          opacity: 0.92,
        }}
        title={`Graph column (map depth): ${dLab}. Skill difficulty: D${level}/5 (${diffLabel}).`}
      >
        <span style={{ opacity: 0.78 }}>Skill</span> · D{level} ({diffLabel})
      </span>
    </div>
  );
}

/**
 * Compact class mastery snapshot: topic-type chips + topic tiles (no graph).
 * maxStrands: depth band chips (Fundamentals … Further). maxTopics / maxPerBand: mastery caps.
 */
export default function ClassMasteryTopicStrip({
  subject,
  masteryMap,
  masteryLoading = false,
  maxStrands = 6,
  maxTopics = 15,
  maxPerBand = 5,
  /** When set, highlights the matching topic tile. */
  selectedConceptId = null,
  /** Called when a topic tile is clicked (dashboard shows details in Class Concept Strengths). */
  onConceptSelect = undefined,
}) {
  const [graph, setGraph] = useState({ concepts: [], prerequisites: [] });
  const [conceptsLoading, setConceptsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [topicSort, setTopicSort] = useState('weakest');
  /** When set, Topics Strong/Developing/Focus only include concepts in this graph depth column. */
  const [selectedDepthIndex, setSelectedDepthIndex] = useState(null);

  const toggleDepthFilter = (depthIndex) => {
    const d = clampDepthIndex(depthIndex);
    setSelectedDepthIndex((prev) => (prev === d ? null : d));
  };

  useEffect(() => {
    let cancelled = false;
    setConceptsLoading(true);
    setLoadError(null);
    getConcepts(subject)
      .then((d) => {
        if (cancelled) return;
        setGraph({
          concepts: Array.isArray(d?.concepts) ? d.concepts : [],
          prerequisites: Array.isArray(d?.prerequisites) ? d.prerequisites : [],
        });
      })
      .catch((e) => {
        if (cancelled) return;
        setLoadError(e?.message || 'Could not load concepts');
        setGraph({ concepts: [], prerequisites: [] });
      })
      .finally(() => {
        if (!cancelled) setConceptsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [subject]);

  const { strands, topicsAll } = useMemo(() => {
    if (!masteryMap || !graph.concepts.length) {
      return { strands: [], topicsAll: [] };
    }

    const depthById = computeDepthIndexByConceptId(graph.concepts, graph.prerequisites);

    const allWithDepth = graph.concepts.map((c) => {
      const id = c.id;
      const raw = masteryMap[id] ?? masteryMap[String(id)];
      const rawD = depthById.get(id) ?? depthById.get(String(id));
      return {
        ...c,
        depthIdx: rawD != null ? clampDepthIndex(rawD) : 0,
        score: raw != null && !Number.isNaN(raw) ? Math.max(0, Math.min(1, raw)) : null,
      };
    });

    const totalByDepth = new Map();
    allWithDepth.forEach((c) => {
      const idx = clampDepthIndex(c.depthIdx);
      totalByDepth.set(idx, (totalByDepth.get(idx) ?? 0) + 1);
    });

    const withScore = allWithDepth.filter((c) => c.score != null);

    const byDepth = new Map();
    withScore.forEach((c) => {
      const idx = clampDepthIndex(c.depthIdx);
      if (!byDepth.has(idx)) byDepth.set(idx, { sum: 0, n: 0 });
      const bucket = byDepth.get(idx);
      bucket.sum += c.score;
      bucket.n += 1;
    });

    const strandList = [...byDepth.entries()]
      .map(([depthIndex, { sum, n }]) => {
        const totalConcepts = totalByDepth.get(depthIndex) ?? n;
        return {
          name: DEPTH_LABELS[depthIndex] ?? `Level ${depthIndex}`,
          depthIndex,
          avg: sum / n,
          /** Topics with class mastery in this graph column (used for averages). */
          testedCount: n,
          /** All concepts in the map for this column (tested plus not yet with class data). */
          totalConcepts,
          count: n,
        };
      })
      .sort((a, b) => a.depthIndex - b.depthIndex)
      .slice(0, maxStrands);

    return { strands: strandList, topicsAll: withScore };
  }, [graph.concepts, graph.prerequisites, masteryMap, maxStrands]);

  const topicsForBands = useMemo(() => {
    if (selectedDepthIndex == null) return topicsAll;
    return topicsAll.filter((t) => clampDepthIndex(t.depthIdx) === selectedDepthIndex);
  }, [topicsAll, selectedDepthIndex]);

  const { topicBands, topicPickMeta } = useMemo(() => {
    const sorted = sortTopicsStable(topicsForBands, topicSort);
    const eligible = partitionByBand(sorted);
    const eligibleTotal = sorted.length;
    const picked = pickBalancedByBand(sorted, maxTopics, maxPerBand);
    const bands = partitionByBand(picked);
    const shown = bands.strong.length + bands.developing.length + bands.focus.length;
    return {
      topicBands: bands,
      topicPickMeta: {
        eligibleTotal,
        eligibleStrong: eligible.strong.length,
        eligibleDeveloping: eligible.developing.length,
        eligibleFocus: eligible.focus.length,
        shown,
        /** True when the cap hides topics that would otherwise appear in this view. */
        isCapped: shown < eligibleTotal,
      },
    };
  }, [topicsForBands, topicSort, maxTopics, maxPerBand]);

  const selectedDepthLabel =
    selectedDepthIndex != null ? DEPTH_LABELS[clampDepthIndex(selectedDepthIndex)] : null;

  const selectedDepthStrand = useMemo(() => {
    if (selectedDepthIndex == null) return null;
    return strands.find((s) => s.depthIndex === selectedDepthIndex) ?? null;
  }, [strands, selectedDepthIndex]);

  const strandBands = useMemo(() => partitionStrandRows(strands), [strands]);

  /** When every topic in the current filter falls in a single mastery band (e.g. only Developing). */
  const singleBandMasteryNote = useMemo(() => {
    if (!topicPickMeta || topicPickMeta.eligibleTotal === 0) return null;
    const e = topicPickMeta;
    const bands = [
      ['Strong', e.eligibleStrong],
      ['Developing', e.eligibleDeveloping],
      ['Focus', e.eligibleFocus],
    ];
    const nonempty = bands.filter(([, n]) => n > 0);
    if (nonempty.length !== 1) return null;
    const [onlyName, onlyCount] = nonempty[0];
    const emptyNames = bands.filter(([, n]) => n === 0).map(([name]) => name);
    const zeroPhrase =
      emptyNames.length === 2 ? `${emptyNames[0]} or ${emptyNames[1]}` : emptyNames.join(', ');
    const depthBit = selectedDepthLabel
      ? `With ${selectedDepthLabel} selected, `
      : 'In this view, ';
    return `${depthBit}there are no ${zeroPhrase} topics. All ${onlyCount} with class mastery here ${onlyCount === 1 ? 'is' : 'are'} ${onlyName}.`;
  }, [topicPickMeta, selectedDepthLabel]);

  if (conceptsLoading || masteryLoading) {
    return (
      <div className="flex min-h-[120px] items-center justify-center py-6">
        <LoadingSpinner message="Loading class mastery snapshot…" />
      </div>
    );
  }

  if (loadError) {
    return <p className="text-sm text-rose-700">{loadError}</p>;
  }

  if (!masteryMap || (!strands.length && !topicsAll.length)) {
    return (
      <p className="text-[12px] leading-relaxed text-slate-600">
        No class mastery for this subject yet. When data is available, depth bands and topics appear here. Open{' '}
        <span className="font-medium text-slate-800">Full View</span> for the interactive map.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-[11px] leading-relaxed text-slate-500">
        Colours match the knowledge graph:{' '}
        <span style={{ color: '#355E4C', fontWeight: 600 }}>Strong (≥70%)</span>,{' '}
        <span style={{ color: '#7F5336', fontWeight: 600 }}>Developing (51–69%)</span>,{' '}
        <span style={{ color: '#7E3E4D', fontWeight: 600 }}>Focus (≤50%)</span>. Difficulty (D1–D5) is shown as
        text. Each tile shows the <span style={{ fontWeight: 600 }}>graph column</span> (Fundamentals … Further) and{' '}
        <span style={{ fontWeight: 600 }}>skill difficulty</span> (D1–D5). At most {maxPerBand} per colour and{' '}
        {maxTopics} in total. You only see rows that have topics in that band.
      </p>

      {strands.length > 0 && (
        <div>
          <p className="axon-label mb-1">Depth (same as graph)</p>
          <p className="mb-2 text-[10px] leading-snug text-slate-500">
            Each chip is a <span style={{ fontWeight: 600 }}>depth column</span> (Fundamentals → Further, same pastels as
            the map legend). The <span style={{ fontWeight: 600 }}>whole chip</span> uses that column colour.{' '}
            <span style={{ fontWeight: 600 }}>X of Y</span> is “concepts with class mastery” vs “all concepts in that
            graph column” (the rest are not in the cohort map yet). <span style={{ fontWeight: 600 }}>Click a chip</span>{' '}
            to filter the Topics section
            to that depth only (click again to clear). <span style={{ fontWeight: 600 }}>Strong / Developing / Focus</span>{' '}
            here is by that
            column’s <em>average</em>; <span style={{ fontWeight: 600 }}>Focus</span> (red section) only if the average
            is at or below 50%.
          </p>
          <div className="flex flex-col gap-3">
            {strandBands.strong.length > 0 && (
              <div>
                <p className="mb-1 text-[9px] font-bold uppercase tracking-wide" style={{ color: '#355E4C' }}>
                  Strong (≥70%), depth bands
                </p>
                <div className="flex flex-wrap gap-2" style={{ alignItems: 'stretch' }}>
                  {strandBands.strong.map((s) => (
                    <StrandTypeChip
                      key={`d-${s.depthIndex}`}
                      row={s}
                      selected={selectedDepthIndex === s.depthIndex}
                      onToggle={toggleDepthFilter}
                    />
                  ))}
                </div>
              </div>
            )}
            {strandBands.developing.length > 0 && (
              <div>
                <p className="mb-1 text-[9px] font-bold uppercase tracking-wide" style={{ color: '#7F5336' }}>
                  Developing (51–69%), depth bands
                </p>
                <div className="flex flex-wrap gap-2" style={{ alignItems: 'stretch' }}>
                  {strandBands.developing.map((s) => (
                    <StrandTypeChip
                      key={`d-${s.depthIndex}`}
                      row={s}
                      selected={selectedDepthIndex === s.depthIndex}
                      onToggle={toggleDepthFilter}
                    />
                  ))}
                </div>
              </div>
            )}
            {strandBands.focus.length > 0 ? (
              <div>
                <p className="mb-1 text-[9px] font-bold uppercase tracking-wide" style={{ color: '#7E3E4D' }}>
                  Focus (≤50%), depth bands
                </p>
                <div className="flex flex-wrap gap-2" style={{ alignItems: 'stretch' }}>
                  {strandBands.focus.map((s) => (
                    <StrandTypeChip
                      key={`d-${s.depthIndex}`}
                      row={s}
                      selected={selectedDepthIndex === s.depthIndex}
                      onToggle={toggleDepthFilter}
                    />
                  ))}
                </div>
              </div>
            ) : (
              strands.length > 0 && (
                <p className="text-[10px] leading-snug text-slate-600">
                  <span style={{ fontWeight: 600 }}>No depth band in Focus:</span> every column average here is above 50%.
                  Individual topics below can still be red when that <em>skill</em> is at or below 50%.
                </p>
              )
            )}
          </div>
        </div>
      )}

      {topicsAll.length > 0 && (
        <div>
          <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="axon-label m-0">
              Topics{' '}
              <span style={{ fontWeight: 400, color: '#64748b' }}>
                · {TOPIC_SORT[topicSort].label}
                {selectedDepthLabel ? (
                  <>
                    {' '}
                    · <span style={{ fontWeight: 600, color: '#334155' }}>{selectedDepthLabel} only</span>
                    {selectedDepthStrand &&
                    selectedDepthStrand.totalConcepts != null &&
                    selectedDepthStrand.testedCount != null ? (
                      <>
                        {' '}
                        ·{' '}
                        <span style={{ color: '#64748b' }}>
                          {selectedDepthStrand.testedCount} of {selectedDepthStrand.totalConcepts} concepts in this column
                          have class mastery
                          {selectedDepthStrand.totalConcepts > selectedDepthStrand.testedCount
                            ? ` (${selectedDepthStrand.totalConcepts - selectedDepthStrand.testedCount} not in cohort data yet)`
                            : ''}
                        </span>
                      </>
                    ) : null}
                  </>
                ) : null}
              </span>
            </p>
            <div className="flex flex-wrap items-center gap-2">
              {selectedDepthIndex != null && (
                <button
                  type="button"
                  onClick={() => setSelectedDepthIndex(null)}
                  className="axon-btn min-h-[2rem] rounded-lg border-2 border-dashed border-[#94a3b8] bg-white/80 px-3 py-1.5 text-[11px] !normal-case text-slate-600 shadow-[2px_2px_0_#cbd5e1] transition hover:-translate-y-px hover:bg-[#fffef4] hover:shadow-[3px_3px_0_#cbd5e1] active:translate-y-px active:shadow-[1px_1px_0_#cbd5e1]"
                >
                  All depths
                </button>
              )}
              {Object.values(TOPIC_SORT).map((opt) => (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => setTopicSort(opt.key)}
                  className={`axon-btn min-h-[2rem] rounded-lg border-2 border-[#2c2418] px-3 py-1.5 text-[11px] !normal-case shadow-[2px_2px_0_#2c2418] transition hover:-translate-y-px hover:shadow-[3px_3px_0_#2c2418] active:translate-y-px active:shadow-[1px_1px_0_#2c2418] ${
                    topicSort === opt.key ? 'axon-btn-primary' : 'bg-[#fffef4] text-[#2c2418] hover:bg-[#efe4be]'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <p className="mb-2 text-[10px] leading-snug text-slate-500">
            <strong>Weakest first</strong>: lowest % first (up to {maxPerBand} tiles per colour).{' '}
            <strong>On track</strong>: closest to ~60% class mastery. <strong>Ahead</strong>: highest % first. The list
            never exceeds {maxPerBand} tiles per colour or {maxTopics} tiles overall, so you may see fewer than{' '}
            {maxTopics} if only one colour has topics in this view (e.g. only Developing).
          </p>
          {topicPickMeta && topicPickMeta.eligibleTotal > 0 && (
            <p className="mb-2 text-[10px] leading-snug text-slate-600">
              <span style={{ fontWeight: 600 }}>This view:</span>{' '}
              showing {topicPickMeta.shown} of {topicPickMeta.eligibleTotal} topic
              {topicPickMeta.eligibleTotal === 1 ? '' : 's'} with class mastery
              {selectedDepthLabel ? ` in ${selectedDepthLabel}` : ''}
              {topicPickMeta.eligibleStrong || topicPickMeta.eligibleDeveloping || topicPickMeta.eligibleFocus ? (
                <>
                  {' '}
                  (
                  {[
                    topicPickMeta.eligibleFocus > 0 ? `${topicPickMeta.eligibleFocus} Focus` : null,
                    topicPickMeta.eligibleDeveloping > 0
                      ? `${topicPickMeta.eligibleDeveloping} Developing`
                      : null,
                    topicPickMeta.eligibleStrong > 0 ? `${topicPickMeta.eligibleStrong} Strong` : null,
                  ]
                    .filter(Boolean)
                    .join(', ')}
                  ).
                </>
              ) : null}
              {topicPickMeta.isCapped
                ? ` Capped at ${maxPerBand} per colour (${maxTopics} max). The rest are omitted here.`
                : null}
            </p>
          )}
          {singleBandMasteryNote && (
            <p className="mb-2 text-[10px] leading-snug text-slate-700">
              <span style={{ fontWeight: 600 }}>Band spread:</span> {singleBandMasteryNote}
            </p>
          )}
          <div className="flex flex-col gap-3">
            {topicsForBands.length === 0 && selectedDepthIndex != null ? (
              <p className="text-[12px] leading-relaxed text-slate-600">
                No topics with class mastery in{' '}
                <span className="font-semibold text-slate-800">{selectedDepthLabel}</span>.{' '}
                <button
                  type="button"
                  onClick={() => setSelectedDepthIndex(null)}
                  className="font-medium text-teal-700 underline decoration-teal-600/40 underline-offset-2 hover:text-teal-800"
                >
                  Show all depths
                </button>
              </p>
            ) : (
              <>
                {topicBands.strong.length > 0 && (
                  <div>
                    <p className="mb-1 text-[9px] font-bold uppercase tracking-wide" style={{ color: '#355E4C' }}>
                      Strong (≥70%)
                    </p>
                    <div className="flex flex-wrap gap-2" style={{ alignItems: 'stretch' }}>
                      {topicBands.strong.map((c) => (
                        <TopicMasteryTile
                          key={c.id}
                          topic={c}
                          selected={selectedConceptId}
                          onSelect={onConceptSelect}
                        />
                      ))}
                    </div>
                  </div>
                )}
                {topicBands.developing.length > 0 && (
                  <div>
                    <p className="mb-1 text-[9px] font-bold uppercase tracking-wide" style={{ color: '#7F5336' }}>
                      Developing (51–69%)
                    </p>
                    <div className="flex flex-wrap gap-2" style={{ alignItems: 'stretch' }}>
                      {topicBands.developing.map((c) => (
                        <TopicMasteryTile
                          key={c.id}
                          topic={c}
                          selected={selectedConceptId}
                          onSelect={onConceptSelect}
                        />
                      ))}
                    </div>
                  </div>
                )}
                {topicBands.focus.length > 0 && (
                  <div>
                    <p className="mb-1 text-[9px] font-bold uppercase tracking-wide" style={{ color: '#7E3E4D' }}>
                      Focus (≤50%)
                    </p>
                    <div className="flex flex-wrap gap-2" style={{ alignItems: 'stretch' }}>
                      {topicBands.focus.map((c) => (
                        <TopicMasteryTile
                          key={c.id}
                          topic={c}
                          selected={selectedConceptId}
                          onSelect={onConceptSelect}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
