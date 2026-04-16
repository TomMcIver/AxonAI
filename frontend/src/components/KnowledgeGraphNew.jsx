import React, {
  useCallback, useEffect, useMemo, useState,
} from 'react';
import { createPortal } from 'react-dom';
import { getConcepts } from '../api/axonai';
import { buildPrerequisiteTreeDatum } from '../utils/prerequisiteTree';
import { chainRootToSelected, layoutTidyTree, normId } from '../utils/tidyTreeLayout';
import { forwardUnlockIds, getRootConceptIds } from '../utils/graphExploration';
import KnowledgeTreeDiagram from './KnowledgeTreeDiagram';
import LoadingSpinner from './LoadingSpinner';
import ErrorState from './ErrorState';
import { masteryBandKey } from '../constants/masteryBands';

/** Teacher + student graph: green strong, orange developing, red focus, gray not assessed. */
function masteryFillTeacher(score) {
  if (score == null || score === undefined) return '#9ca3af';
  const band = masteryBandKey(score);
  if (band === 'none') return '#9ca3af';
  if (band === 'strong') return '#16a34a';
  if (band === 'developing') return '#f97316';
  return '#dc2626';
}

function buildEasyChain(selectedId, edges, direction) {
  if (!selectedId) return [];
  const chain = [selectedId];
  const visited = new Set([selectedId]);
  let current = selectedId;

  while (true) {
    const candidates = direction === 'prereq'
      ? edges.filter((e) => e.concept_id === current)
      : edges.filter((e) => e.prerequisite_concept_id === current);

    if (candidates.length === 0) break;

    const strongest = [...candidates].sort(
      (a, b) => (b.strength ?? 0) - (a.strength ?? 0),
    )[0];

    const nextId = direction === 'prereq'
      ? strongest.prerequisite_concept_id
      : strongest.concept_id;

    if (visited.has(nextId)) break;
    visited.add(nextId);
    chain.push(nextId);
    current = nextId;
  }

  return direction === 'prereq' ? chain.reverse() : chain;
}

export default function KnowledgeGraphNew({
  subject = 'Mathematics',
  mapOnly = false,
  dataOverride = null,
  masteryMap = null,
  focusKeyNodes = null,
  /** 'canvas' = show full / key-node map; 'path' = reveal prerequisites + next 1–2 steps as you click. */
  defaultExploration = 'path',
  showExplorationToggle = true,
  forwardRevealCount = 2,
  /** Teacher pages: toggle cohort colouring vs structure-only (yellow) nodes. */
  showTeacherViewToggle = false,
  showColorLegend = true,
  /** Where cohort scores came from (for teacher copy). */
  cohortMasteryMeta = null,
}) {
  const [graphExpanded, setGraphExpanded] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [showAllNodes, setShowAllNodes] = useState(!mapOnly);
  const [exploration, setExploration] = useState(defaultExploration);
  const [revealedList, setRevealedList] = useState([]);
  /** 'class' = cohort / class fair colours; 'structure' = concept map only (no mastery fill). */
  const [teacherMasteryMode, setTeacherMasteryMode] = useState('class');

  /** When true, canvas mode can show the high-degree subset unless user clicks Show all. Pass `focusKeyNodes={false}` to always show the full graph (e.g. teacher class overview). */
  const shouldFocusKeyNodes = focusKeyNodes ?? mapOnly;

  const effectiveMasteryMap = useMemo(() => {
    if (!showTeacherViewToggle) return masteryMap;
    return teacherMasteryMode === 'structure' ? null : masteryMap;
  }, [showTeacherViewToggle, teacherMasteryMode, masteryMap]);

  const load = useCallback(() => {
    if (dataOverride) {
      setData(dataOverride);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    getConcepts(subject)
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [dataOverride, subject]);

  useEffect(() => {
    setExploration(defaultExploration);
  }, [defaultExploration]);

  useEffect(() => {
    setSelectedId(null);
    setShowAllNodes(!mapOnly);
    load();
  }, [load, mapOnly]);

  useEffect(() => {
    if (!graphExpanded) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = e => {
      if (e.key === 'Escape') setGraphExpanded(false);
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener('keydown', onKey);
    };
  }, [graphExpanded]);

  const concepts = data?.concepts || [];
  const edges = data?.prerequisites || [];

  useEffect(() => {
    if (exploration !== 'path') {
      setRevealedList([]);
      return;
    }
    if (!concepts.length) return;
    const roots = getRootConceptIds(concepts, edges, 12);
    setRevealedList(
      roots.length ? roots : concepts.slice(0, 8).map((c) => c.id),
    );
  }, [exploration, concepts, edges, dataOverride, subject]);

  const filteredConcepts = useMemo(() => {
    if (!search.trim()) return concepts;
    const q = search.toLowerCase();
    return concepts.filter((c) => c.name.toLowerCase().includes(q));
  }, [concepts, search]);

  const keyNodeIds = useMemo(() => {
    if (!mapOnly || search.trim()) return null;
    const degree = {};
    edges.forEach((e) => {
      degree[e.concept_id] = (degree[e.concept_id] || 0) + 1;
      degree[e.prerequisite_concept_id] = (degree[e.prerequisite_concept_id] || 0) + 1;
    });

    const ranked = [...filteredConcepts]
      .sort((a, b) => (degree[b.id] || 0) - (degree[a.id] || 0))
      .slice(0, 24)
      .map((c) => c.id);

    return new Set(ranked);
  }, [edges, filteredConcepts, mapOnly, search]);

  const spineParentOf = useMemo(() => {
    if (!filteredConcepts.length) return null;
    try {
      const datum = buildPrerequisiteTreeDatum(filteredConcepts, edges);
      return layoutTidyTree(datum, { nodeW: 132, nodeH: 58 }).parentOf;
    } catch {
      return null;
    }
  }, [filteredConcepts, edges]);

  const displayConcepts = useMemo(() => {
    if (exploration === 'path') {
      const revealed = new Set(revealedList.map(normId));
      return filteredConcepts.filter((c) => revealed.has(normId(c.id)));
    }
    if (!shouldFocusKeyNodes || showAllNodes || !keyNodeIds) return filteredConcepts;
    const required = new Set(keyNodeIds);

    if (selectedId != null) {
      required.add(selectedId);
      edges.forEach((e) => {
        if (e.concept_id === selectedId) required.add(e.prerequisite_concept_id);
        if (e.prerequisite_concept_id === selectedId) required.add(e.concept_id);
      });
    }

    return filteredConcepts.filter((c) => required.has(c.id));
  }, [
    exploration,
    revealedList,
    edges,
    filteredConcepts,
    shouldFocusKeyNodes,
    keyNodeIds,
    selectedId,
    showAllNodes,
  ]);

  const visibleIds = new Set(displayConcepts.map((c) => c.id));
  const visibleEdges = edges.filter(
    (e) => visibleIds.has(e.concept_id) && visibleIds.has(e.prerequisite_concept_id),
  );

  /** Stable while selection expands a key-node view (avoids resetting zoom/pan on every node click). */
  const treeViewportKey = useMemo(() => {
    if (exploration === 'path') {
      return `path:${subject}`;
    }
    const keyView = shouldFocusKeyNodes && !showAllNodes && !search.trim() && keyNodeIds?.size;
    if (keyView) {
      const ids = [...keyNodeIds].sort((a, b) => Number(a) - Number(b)).join(',');
      return `keynodes:${subject}:${ids}`;
    }
    const cPart = filteredConcepts
      .map((c) => c.id)
      .sort((a, b) => Number(a) - Number(b))
      .join(',');
    const ePart = visibleEdges
      .map((e) => `${e.prerequisite_concept_id}->${e.concept_id}`)
      .sort()
      .join('|');
    return `full:${subject}:${cPart}:${ePart}`;
  }, [exploration, shouldFocusKeyNodes, showAllNodes, search, keyNodeIds, subject, filteredConcepts, visibleEdges]);

  const selected = concepts.find((c) => c.id === selectedId) || null;

  const prereqChain = useMemo(() => (
    selectedId != null && spineParentOf
      ? chainRootToSelected(selectedId, spineParentOf)
      : []
  ), [selectedId, spineParentOf]);

  const forwardChain = selectedId ? buildEasyChain(selectedId, edges, 'forward') : [];

  const nodeById = useMemo(() => {
    const map = {};
    concepts.forEach((c) => { map[c.id] = c; });
    return map;
  }, [concepts]);

  /** Raw cohort map from parent; empty means “whole class” has nothing to paint yet. */
  const cohortScoresMissing = useMemo(
    () => showTeacherViewToggle
      && teacherMasteryMode === 'class'
      && (!masteryMap || Object.keys(masteryMap).length === 0),
    [showTeacherViewToggle, teacherMasteryMode, masteryMap],
  );

  const getNodeBasePresentation = useCallback(
    (id) => {
      const c = concepts.find((x) => x.id === id);
      const name = c?.name ?? String(id);
      const label = name;

      if (cohortScoresMissing) {
        return {
          label,
          fill: '#94a3b8',
          tooltip: `${name} · no cohort mastery (class summary empty and per-student data missing)`,
        };
      }

      const score = effectiveMasteryMap?.[id] ?? effectiveMasteryMap?.[String(id)] ?? null;
      const fill = effectiveMasteryMap
        ? masteryFillTeacher(score)
        : '#f6c445';

      let tooltip = name;
      if (effectiveMasteryMap) {
        if (score != null && score !== undefined) {
          const pct = Math.round((typeof score === 'number' && score > 1 ? score / 100 : score) * 100);
          tooltip = `${name}: ${pct}%`;
          if (showTeacherViewToggle && teacherMasteryMode === 'class') {
            tooltip += ' (class average)';
          } else if (!showTeacherViewToggle) {
            tooltip += ' (this student)';
          }
        } else {
          tooltip = `${name} · not assessed`;
        }
      }
      return { label, fill, tooltip };
    },
    [
      concepts,
      cohortScoresMissing,
      effectiveMasteryMap,
      showTeacherViewToggle,
      teacherMasteryMode,
    ],
  );

  const onTreeNodeClick = useCallback((rawId) => {
    const nid = normId(rawId);
    setSelectedId(nid);
    if (exploration !== 'path') return;
    setRevealedList((prev) => {
      const acc = new Set(prev.map(normId));
      acc.add(nid);
      if (spineParentOf) {
        chainRootToSelected(nid, spineParentOf).forEach((x) => acc.add(normId(x)));
      }
      forwardUnlockIds(nid, edges, forwardRevealCount).forEach((x) => acc.add(x));
      return [...acc];
    });
  }, [exploration, spineParentOf, edges, forwardRevealCount]);

  if (loading) {
    return (
      <div
        className="flex w-full items-center justify-center"
        style={{ minHeight: 'min(70vh, 1200px)' }}
      >
        <LoadingSpinner message="Loading graph..." />
      </div>
    );
  }
  if (error) {
    return (
      <div
        className="flex w-full items-center justify-center"
        style={{ minHeight: 'min(70vh, 1200px)' }}
      >
        <ErrorState message={error} onRetry={load} />
      </div>
    );
  }

  /** Overlay shell lives inside a portal wrapper (no second `fixed`; avoids broken layout / zero-size graph). */
  const graphViewportShellClass = graphExpanded
    ? 'shadow-[6px_6px_0_#2c2418] z-[240] flex w-full max-w-[min(100vw,3200px)] flex-col overflow-hidden rounded-lg border-2 border-[#2c2418] bg-[#fffef4] p-2 sm:p-3'
    : 'axon-card-subtle relative flex w-full shrink-0 flex-col overflow-hidden p-2 sm:p-3';

  /**
   * Pixel / vh sizing via inline style so the diagram always gets height even when Tailwind arbitrary
   * classes (h-[min(92dvh,…)]) are missing from compiled.css; otherwise the flex column collapses,
   * ResizeObserver sees ~0×0, and the tree/SVG disappears or shows as a thin text strip.
   */
  const graphViewportStyle = graphExpanded
    ? {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        minHeight: '50dvh',
        height: 'calc(100dvh - 1.5rem)',
        maxHeight: '100dvh',
      }
    : {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        minHeight: 'min(480px, 70vh)',
        height: 'min(92vh, 1400px)',
        maxHeight: 'min(98vh, 3200px)',
      };

  const diagramBlock = (
    <div className={graphViewportShellClass} style={graphViewportStyle}>
      {graphExpanded ? (
        <div className="flex shrink-0 items-center justify-between gap-2 border-b-2 border-[#2c2418]/20 pb-2">
          <span className="text-[11px] font-semibold text-[#2c2418]">Full screen graph</span>
          <button
            type="button"
            className="axon-btn axon-btn-ghost text-[11px] !normal-case"
            onClick={() => setGraphExpanded(false)}
          >
            Close
          </button>
        </div>
      ) : null}
      <div
        className="relative flex-1 basis-0 overflow-hidden"
        style={{
          flex: '1 1 auto',
          minHeight: 'min(320px, 45vh)',
          position: 'relative',
        }}
      >
        <KnowledgeTreeDiagram
          concepts={displayConcepts}
          edges={visibleEdges}
          masteryMap={effectiveMasteryMap}
          getNodeBasePresentation={getNodeBasePresentation}
          selectedId={selectedId}
          onNodeClick={onTreeNodeClick}
          mapOnly={mapOnly}
          showAllNodes={showAllNodes}
          search={search}
          onZoomOutExpand={undefined}
          viewportLayoutKey={`${treeViewportKey}-${graphExpanded ? 'x' : 'n'}`}
          showLegend={showColorLegend}
          showMasteryInLegend={Boolean(effectiveMasteryMap)}
        />
      </div>
    </div>
  );

  return (
    <div className="flex min-h-0 flex-col gap-4">
      {showTeacherViewToggle && (
        <div
          className="flex min-w-0 shrink-0 flex-col gap-3 rounded-lg border-2 border-[#2c2418] bg-[#efe4be] px-3 py-3 shadow-[3px_3px_0_#2c2418]"
          role="region"
          aria-label="Class mastery map mode"
        >
          <div className="min-w-0 max-w-full space-y-2 text-[11px] font-semibold leading-relaxed text-[#2c2418]">
            <p className="break-words">
              Whole class: mastery colours and % on hover. Concept map only: gold nodes, no scores.
            </p>
            {cohortMasteryMeta?.source === 'student-aggregate' && Number(cohortMasteryMeta.studentCount) > 0 && (
              <p className="rounded border border-emerald-700/25 bg-emerald-50/95 px-2 py-1.5 text-[10px] font-medium leading-snug text-emerald-950">
                Class summary empty. Cohort map built locally (median per concept across{' '}
                {cohortMasteryMeta.studentCount} learners, GET /student/…/mastery), filtered to {subject}.
              </p>
            )}
            {cohortScoresMissing && (
              <p className="rounded border border-amber-600/40 bg-amber-50/90 px-2 py-1.5 text-[10px] font-medium leading-snug text-amber-950">
                No cohort data: class concept-summary is empty and per-student mastery did not yield scores for this
                graph.
              </p>
            )}
          </div>
          {/* Two-column grid keeps both toggles visible; avoid w-full + flex-row (second button was shoved off-screen). */}
          <div
            className="grid w-full min-w-0 grid-cols-1 gap-2 min-[420px]:grid-cols-2"
            role="group"
            aria-label="Teacher graph view"
          >
            <button
              type="button"
              aria-pressed={teacherMasteryMode === 'class'}
              className={`axon-btn min-h-[2.5rem] w-full justify-start px-3 py-2 text-[11px] !normal-case ${
                teacherMasteryMode === 'class' ? 'axon-btn-primary' : 'axon-btn-ghost'
              }`}
              onClick={() => setTeacherMasteryMode('class')}
            >
              Whole class
            </button>
            <button
              type="button"
              aria-pressed={teacherMasteryMode === 'structure'}
              className={`axon-btn min-h-[2.5rem] w-full justify-start px-3 py-2 text-[11px] !normal-case ${
                teacherMasteryMode === 'structure' ? 'axon-btn-primary' : 'axon-btn-ghost'
              }`}
              onClick={() => setTeacherMasteryMode('structure')}
            >
              Concept map only
            </button>
          </div>
        </div>
      )}
      <div className="flex shrink-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <div className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-700">
            {displayConcepts.length}{!showAllNodes && shouldFocusKeyNodes && exploration !== 'path' ? ` / ${filteredConcepts.length}` : ''} nodes · {visibleEdges.length} links
          </div>
          <button
            type="button"
            className="axon-btn axon-btn-primary px-3 py-1.5 text-[11px] !normal-case"
            aria-expanded={graphExpanded}
            aria-controls="knowledge-graph-viewport"
            onClick={() => setGraphExpanded(v => !v)}
          >
            {graphExpanded ? 'Exit expanded' : 'Expand graph'}
          </button>
        </div>
        <div className="flex w-full min-w-0 flex-col gap-3 sm:max-w-full sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
          {showExplorationToggle && (
            <div
              className="flex w-full shrink-0 flex-col gap-1 sm:w-auto"
              role="group"
              aria-label="Map view mode"
            >
              <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500 sm:sr-only">
                View mode
              </span>
              <div className="inline-flex w-full max-w-md flex-wrap items-center gap-2 sm:w-auto sm:min-w-0">
                <button
                  type="button"
                  aria-pressed={exploration === 'canvas'}
                  className={`axon-btn min-h-[2.25rem] flex-1 px-3 py-2 text-[11px] !normal-case sm:min-w-[6.5rem] ${
                    exploration === 'canvas' ? 'axon-btn-primary' : 'axon-btn-ghost'
                  }`}
                  onClick={() => {
                    setExploration('canvas');
                    setSelectedId(null);
                  }}
                >
                  Full map
                </button>
                <button
                  type="button"
                  aria-pressed={exploration === 'path'}
                  className={`axon-btn min-h-[2.25rem] flex-1 px-3 py-2 text-[11px] !normal-case sm:min-w-[6.5rem] ${
                    exploration === 'path' ? 'axon-btn-primary' : 'axon-btn-ghost'
                  }`}
                  onClick={() => {
                    setExploration('path');
                    setSelectedId(null);
                    const roots = getRootConceptIds(concepts, edges, 12);
                    setRevealedList(
                      roots.length ? roots : concepts.slice(0, 8).map((c) => c.id),
                    );
                  }}
                >
                  Explore path
                </button>
              </div>
            </div>
          )}
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search concept..."
            className="min-h-[2.5rem] w-full min-w-0 flex-1 px-3 py-2 text-sm bg-[#fffef4] border-2 border-[#2c2418] rounded-[8px] sm:max-w-xs"
          />
        </div>
      </div>

      {exploration === 'path' && (
        <div className="shrink-0 rounded-md border border-sky-300/50 bg-sky-50/80 px-3 py-2 text-[11px] text-slate-700">
          <span className="font-medium text-sky-900">Explore path:</span>{' '}
          Start from entry concepts (no prerequisites). Each click adds the prerequisite spine plus the next{' '}
          {forwardRevealCount} strongest “unlocks” so you can see where learning leads.
        </div>
      )}

      {shouldFocusKeyNodes && exploration !== 'path' && !showAllNodes && !search.trim() && keyNodeIds?.size ? (
        <div className="flex shrink-0 flex-col gap-1.5 rounded-md border-2 border-[#2c2418] bg-[#efe4be] px-3 py-2 text-[11px] text-slate-700 sm:flex-row sm:items-center sm:justify-between">
          <span>
            Focused view: high-connectivity concepts only. Use Show all to load every node (zoom no longer auto-expands
            the set).
          </span>
          <button type="button" className="axon-btn axon-btn-ghost shrink-0 self-start !py-1 !px-2 sm:self-auto" onClick={() => setShowAllNodes(true)}>
            Show all
          </button>
        </div>
      ) : null}

      <div
        className={`grid shrink-0 grid-cols-1 items-start gap-4 ${mapOnly ? '' : 'xl:grid-cols-[minmax(0,1fr)_320px]'}`}
      >
        <div id="knowledge-graph-viewport" className="min-w-0">
          {graphExpanded ? (
            <>
              {createPortal(
                <>
                  <button
                    type="button"
                    className="fixed inset-0 z-[230] cursor-default bg-[#2c2418]/45"
                    aria-label="Close expanded graph"
                    onClick={() => setGraphExpanded(false)}
                  />
                  <div className="pointer-events-none fixed inset-0 z-[235] flex items-start justify-center overflow-y-auto p-2 pt-[max(0.5rem,env(safe-area-inset-top))] pb-[max(0.5rem,env(safe-area-inset-bottom))] sm:p-4">
                    <div className="pointer-events-auto my-auto w-full max-w-[100vw] sm:my-2">{diagramBlock}</div>
                  </div>
                </>,
                document.body
              )}
              <div
                className="flex min-h-[100px] items-center justify-center rounded-lg border border-dashed border-[#2c2418]/30 bg-[#efe4be]/50 px-3 py-4 text-center text-[11px] leading-snug text-[#2c2418]/80"
                aria-hidden
              >
                Full screen map is open. Use Close, Esc, or the dimmed backdrop to return.
              </div>
            </>
          ) : (
            diagramBlock
          )}
        </div>

        {!mapOnly && (
          <div className="axon-card-subtle max-h-[min(94dvh,1800px)] space-y-4 overflow-y-auto p-4 bg-[#fff8dc]">
            <div>
              <p className="axon-label mb-2">Selected Node</p>
              <p className="text-sm font-semibold text-slate-800 leading-6">
                {selected ? selected.name : 'Click any node'}
              </p>
            </div>

            {selected && (
              <>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-blue-600">Prerequisite path</p>
                  <ol className="mt-2 space-y-1 text-xs text-slate-700">
                    {prereqChain.map((id, idx) => (
                      <li key={`p-${id}`}>{idx + 1}. {nodeById[id]?.name || id}</li>
                    ))}
                  </ol>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-violet-600">Leads to</p>
                  <ol className="mt-2 space-y-1 text-xs text-slate-700">
                    {forwardChain.map((id, idx) => (
                      <li key={`f-${id}`}>{idx + 1}. {nodeById[id]?.name || id}</li>
                    ))}
                  </ol>
                </div>
                <p className="text-[11px] text-slate-500">
                  Blue highlights follow the prerequisite spine in the tree. Orange links below show what this concept unlocks next (full graph).
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
