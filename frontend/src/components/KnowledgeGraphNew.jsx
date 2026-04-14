import React, { useCallback, useEffect, useMemo, useState } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { getConcepts } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';
import ErrorState from './ErrorState';

cytoscape.use(dagre);

function masteryTone(score) {
  if (score == null) return '#94a3b8';
  if (score < 0.4) return '#dc2626';
  if (score < 0.7) return '#d97706';
  return '#16a34a';
}

function getPathSets(selectedId, edges) {
  if (!selectedId) {
    return {
      ancestors: new Set(),
      descendants: new Set(),
      prereqEdges: new Set(),
      forwardEdges: new Set(),
    };
  }

  const ancestors = new Set();
  const descendants = new Set();
  const prereqEdges = new Set();
  const forwardEdges = new Set();

  let queue = [selectedId];
  while (queue.length > 0) {
    const next = [];
    queue.forEach((id) => {
      edges.forEach((e, i) => {
        if (e.concept_id === id && !ancestors.has(e.prerequisite_concept_id)) {
          ancestors.add(e.prerequisite_concept_id);
          prereqEdges.add(i);
          next.push(e.prerequisite_concept_id);
        }
      });
    });
    queue = next;
  }

  queue = [selectedId];
  while (queue.length > 0) {
    const next = [];
    queue.forEach((id) => {
      edges.forEach((e, i) => {
        if (e.prerequisite_concept_id === id && !descendants.has(e.concept_id)) {
          descendants.add(e.concept_id);
          forwardEdges.add(i);
          next.push(e.concept_id);
        }
      });
    });
    queue = next;
  }

  return { ancestors, descendants, prereqEdges, forwardEdges };
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
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState(null);

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
    setSelectedId(null);
    load();
  }, [load]);

  const concepts = data?.concepts || [];
  const edges = data?.prerequisites || [];

  const filteredConcepts = useMemo(() => {
    if (!search.trim()) return concepts;
    const q = search.toLowerCase();
    return concepts.filter((c) => c.name.toLowerCase().includes(q));
  }, [concepts, search]);

  const visibleIds = new Set(filteredConcepts.map((c) => c.id));
  const visibleEdges = edges.filter(
    (e) => visibleIds.has(e.concept_id) && visibleIds.has(e.prerequisite_concept_id),
  );

  const selected = concepts.find((c) => c.id === selectedId) || null;
  const pathSets = getPathSets(selectedId, visibleEdges);

  const prereqChain = selectedId ? buildEasyChain(selectedId, visibleEdges, 'prereq') : [];
  const forwardChain = selectedId ? buildEasyChain(selectedId, visibleEdges, 'forward') : [];

  const nodeById = useMemo(() => {
    const map = {};
    concepts.forEach((c) => { map[c.id] = c; });
    return map;
  }, [concepts]);

  const elements = useMemo(() => {
    const nodes = filteredConcepts.map((c) => {
      const score = masteryMap?.[c.id] ?? masteryMap?.[String(c.id)] ?? null;
      const color = masteryMap ? masteryTone(score) : '#f6c445';
      const label = masteryMap && score != null
        ? `${c.name}\n${Math.round((score > 1 ? score / 100 : score) * 100)}%`
        : c.name;

      let klass = 'node-default';
      if (selectedId) {
        if (c.id === selectedId) klass = 'node-selected';
        else if (pathSets.ancestors.has(c.id)) klass = 'node-ancestor';
        else if (pathSets.descendants.has(c.id)) klass = 'node-descendant';
        else klass = 'node-muted';
      }

      return {
        data: {
          id: String(c.id),
          label,
          baseColor: color,
          level: c.difficulty_level || 3,
        },
        classes: klass,
      };
    });

    const edgeEls = visibleEdges.map((e, i) => {
      let klass = 'edge-default';
      if (selectedId) {
        if (pathSets.prereqEdges.has(i)) klass = 'edge-prereq';
        else if (pathSets.forwardEdges.has(i)) klass = 'edge-forward';
        else klass = 'edge-muted';
      }
      return {
        data: {
          id: `e-${i}`,
          source: String(e.prerequisite_concept_id),
          target: String(e.concept_id),
          strength: e.strength ?? 0.5,
        },
        classes: klass,
      };
    });

    return [...nodes, ...edgeEls];
  }, [filteredConcepts, masteryMap, pathSets, selectedId, visibleEdges]);

  if (loading) return <LoadingSpinner message="Loading graph..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs text-slate-700 font-semibold tracking-[0.08em] uppercase">
          {filteredConcepts.length} nodes · {visibleEdges.length} links
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search concept..."
          className="w-full max-w-xs px-3 py-2 text-sm bg-[#fffef4] border-2 border-[#2c2418] rounded-[8px]"
        />
      </div>

      <div className={`grid min-h-0 flex-1 gap-3 ${mapOnly ? 'grid-cols-1' : 'grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px]'}`}>
        <div className="axon-card-subtle min-h-[520px] p-2 sm:p-3">
          <CytoscapeComponent
            elements={elements}
            style={{ width: '100%', height: '100%' }}
            layout={{
              name: 'dagre',
              rankDir: 'LR',
              fit: true,
              padding: 30,
              nodeSep: 50,
              rankSep: 110,
            }}
            cy={(cy) => {
              cy.on('tap', 'node', (evt) => {
                setSelectedId(Number(evt.target.id()));
              });
              cy.on('tap', (evt) => {
                if (evt.target === cy) setSelectedId(null);
              });
            }}
            stylesheet={[
              {
                selector: 'node',
                style: {
                  shape: 'rectangle',
                  width: 132,
                  height: 58,
                  'background-color': 'data(baseColor)',
                  label: 'data(label)',
                  color: '#2c2418',
                  'font-size': 8,
                  'font-family': 'Press Start 2P, Inter, sans-serif',
                  'text-wrap': 'wrap',
                  'text-max-width': 118,
                  'text-valign': 'center',
                  'text-halign': 'center',
                  'border-width': 3,
                  'border-color': '#2c2418',
                },
              },
              { selector: '.node-default', style: { opacity: 1 } },
              { selector: '.node-muted', style: { opacity: 0.2 } },
              {
                selector: '.node-selected',
                style: {
                  opacity: 1,
                  'border-color': '#2563eb',
                  'border-width': 4,
                },
              },
              { selector: '.node-ancestor', style: { opacity: 1, 'border-color': '#3b82f6' } },
              { selector: '.node-descendant', style: { opacity: 1, 'border-color': '#8b5cf6' } },
              {
                selector: 'edge',
                style: {
                  width: 2,
                  'line-color': '#6b5a42',
                  'target-arrow-color': '#6b5a42',
                  'target-arrow-shape': 'vee',
                  'curve-style': 'bezier',
                  opacity: 0.45,
                },
              },
              { selector: '.edge-muted', style: { opacity: 0.08 } },
              { selector: '.edge-prereq', style: { 'line-color': '#3b82f6', 'target-arrow-color': '#3b82f6', width: 3, opacity: 0.9 } },
              { selector: '.edge-forward', style: { 'line-color': '#8b5cf6', 'target-arrow-color': '#8b5cf6', width: 3, opacity: 0.9 } },
            ]}
          />
        </div>

        {!mapOnly && (
          <div className="axon-card-subtle space-y-4 p-4 bg-[#fff8dc]">
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
                  Blue links are prerequisites needed beforehand. Purple links show where this concept unlocks next.
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
