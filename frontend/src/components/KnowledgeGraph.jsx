import React, { useRef, useState, useEffect, useCallback } from 'react';
import { getConcepts } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';
import ErrorState from './ErrorState';

const DIFFICULTY_CONFIG = {
  5: { label: 'Very Hard', color: '#EF4444', bg: 'bg-red-100', text: 'text-red-700', ring: 'ring-red-300' },
  4: { label: 'Hard', color: '#F97316', bg: 'bg-orange-100', text: 'text-orange-700', ring: 'ring-orange-300' },
  3: { label: 'Medium', color: '#F59E0B', bg: 'bg-amber-100', text: 'text-amber-700', ring: 'ring-amber-300' },
  2: { label: 'Easy', color: '#10B981', bg: 'bg-green-100', text: 'text-green-700', ring: 'ring-green-300' },
  1: { label: 'Foundational', color: '#10B981', bg: 'bg-emerald-100', text: 'text-emerald-700', ring: 'ring-emerald-300' },
};

function DifficultyBadge({ level }) {
  const cfg = DIFFICULTY_CONFIG[level] || DIFFICULTY_CONFIG[3];
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      Level {level} — {cfg.label}
    </span>
  );
}

function ConceptNode({ concept, isSelected, isHovered, onSelect, onHover, onLeave }) {
  const diff = concept.difficulty_level || 3;
  const cfg = DIFFICULTY_CONFIG[diff] || DIFFICULTY_CONFIG[3];
  return (
    <div
      className={`relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-all border-2 ${
        isSelected
          ? `${cfg.bg} ${cfg.text} border-current shadow-md scale-105`
          : isHovered
            ? `bg-white ${cfg.text} border-current shadow-sm`
            : 'bg-white text-[#1F2937] border-[#E2E8F0] hover:shadow-sm'
      }`}
      onClick={() => onSelect(concept.id)}
      onMouseEnter={() => onHover(concept.id)}
      onMouseLeave={onLeave}
    >
      <span
        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: cfg.color }}
      />
      <span className="truncate max-w-[160px]">{concept.name}</span>
    </div>
  );
}

export default function KnowledgeGraph({ subject }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [search, setSearch] = useState('');
  const detailRef = useRef(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getConcepts(subject)
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [subject]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner message={`Loading ${subject} concepts...`} />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  const concepts = data.concepts || [];
  const edges = data.prerequisites || [];

  // Group by difficulty level, ranked from hardest (top) to easiest (bottom)
  const ranks = [5, 4, 3, 2, 1];
  const grouped = {};
  ranks.forEach(r => { grouped[r] = []; });
  concepts.forEach(c => {
    const lvl = c.difficulty_level || 3;
    if (!grouped[lvl]) grouped[lvl] = [];
    grouped[lvl].push(c);
  });
  // Sort each group alphabetically
  ranks.forEach(r => {
    grouped[r].sort((a, b) => a.name.localeCompare(b.name));
  });

  // Filter for search
  const matchesSearch = (c) => !search || c.name.toLowerCase().includes(search.toLowerCase());

  const selectedConcept = selected ? concepts.find(c => c.id === selected) : null;
  const prereqs = selected ? edges.filter(e => e.concept_id === selected).map(e => {
    const pc = concepts.find(c => c.id === e.prerequisite_concept_id);
    return pc ? { ...pc, strength: e.strength } : null;
  }).filter(Boolean) : [];
  const dependents = selected ? edges.filter(e => e.prerequisite_concept_id === selected).map(e => {
    const dc = concepts.find(c => c.id === e.concept_id);
    return dc ? { ...dc, strength: e.strength } : null;
  }).filter(Boolean) : [];

  function handleSelect(conceptId) {
    setSelected(conceptId);
    // Jump down to the detail panel for a more "drill-in" feel.
    requestAnimationFrame(() => {
      detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-4">
        <div className="text-sm text-[#6B7280]">
          {concepts.length} concepts, {edges.length} prerequisite links
        </div>
        <input
          type="text"
          placeholder="Search concepts..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="px-3 py-1.5 border border-[#E2E8F0] rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-[#0891B2]"
        />
      </div>

      {/* Ranked concept map — top = hardest, bottom = easiest */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-[#1F2937]">Concept Hierarchy</h4>
          <span className="text-xs text-[#6B7280]">Hardest at top, easiest at bottom</span>
        </div>

        <div className="space-y-1">
          {ranks.map(rank => {
            const cfg = DIFFICULTY_CONFIG[rank] || DIFFICULTY_CONFIG[3];
            const items = grouped[rank]?.filter(matchesSearch) || [];
            if (items.length === 0 && search) return null;
            return (
              <div key={rank} className="flex items-start gap-3 py-3 border-b border-[#E2E8F0] last:border-0">
                {/* Rank label */}
                <div className="w-24 flex-shrink-0 pt-1">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${cfg.bg} ${cfg.text} uppercase tracking-wider`}>
                    Lvl {rank}
                  </span>
                  <p className="text-[10px] text-[#6B7280] mt-0.5">{cfg.label}</p>
                </div>
                {/* Concept nodes */}
                <div className="flex flex-wrap gap-2 flex-1 min-h-[32px]">
                  {items.length > 0 ? items.map(c => (
                    <ConceptNode
                      key={c.id}
                      concept={c}
                      isSelected={selected === c.id}
                      isHovered={hovered === c.id}
                      onSelect={handleSelect}
                      onHover={setHovered}
                      onLeave={() => setHovered(null)}
                    />
                  )) : (
                    <span className="text-xs text-[#CBD5E1] italic py-1">No concepts at this level</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-[#E2E8F0] text-xs text-[#6B7280]">
          {ranks.map(r => {
            const cfg = DIFFICULTY_CONFIG[r];
            return (
              <span key={r} className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: cfg.color }} />
                {cfg.label} ({r})
              </span>
            );
          })}
        </div>
      </div>

      {/* Detail panel */}
      <div ref={detailRef} className="grid grid-cols-1 lg:grid-cols-2 gap-4 scroll-mt-24">
        {/* Hover / selected tooltip */}
        {(selectedConcept || hovered) && (() => {
          const showConcept = selectedConcept || concepts.find(c => c.id === hovered);
          if (!showConcept) return null;
          const showPrereqs = edges.filter(e => e.concept_id === showConcept.id).map(e => {
            const pc = concepts.find(c => c.id === e.prerequisite_concept_id);
            return pc ? { ...pc, strength: e.strength } : null;
          }).filter(Boolean);
          const showDeps = edges.filter(e => e.prerequisite_concept_id === showConcept.id).map(e => {
            const dc = concepts.find(c => c.id === e.concept_id);
            return dc ? { ...dc, strength: e.strength } : null;
          }).filter(Boolean);

          return (
            <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm lg:col-span-2">
              <div className="p-4 border-b border-[#E2E8F0]">
                <h4 className="font-semibold text-[#1F2937]">{showConcept.name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <DifficultyBadge level={showConcept.difficulty_level} />
                  <span className="text-xs text-[#6B7280] capitalize">{showConcept.concept_type}</span>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#E2E8F0]">
                <div className="p-4">
                  <h5 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">
                    Prerequisites ({showPrereqs.length})
                  </h5>
                  {showPrereqs.length > 0 ? (
                    <div className="space-y-1.5">
                      {showPrereqs.map(p => (
                        <div key={p.id} className="flex items-center justify-between text-sm">
                          <span className="text-[#1F2937] cursor-pointer hover:text-[#0891B2]" onClick={() => handleSelect(p.id)}>
                            {p.name}
                          </span>
                          <div className="flex items-center gap-2">
                            <DifficultyBadge level={p.difficulty_level} />
                            <span className="text-xs text-[#6B7280]">{p.strength}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#CBD5E1]">No prerequisites — this is a foundational concept</p>
                  )}
                </div>
                <div className="p-4">
                  <h5 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">
                    Required By ({showDeps.length})
                  </h5>
                  {showDeps.length > 0 ? (
                    <div className="space-y-1.5">
                      {showDeps.map(d => (
                        <div key={d.id} className="flex items-center justify-between text-sm">
                          <span className="text-[#1F2937] cursor-pointer hover:text-[#0891B2]" onClick={() => handleSelect(d.id)}>
                            {d.name}
                          </span>
                          <div className="flex items-center gap-2">
                            <DifficultyBadge level={d.difficulty_level} />
                            <span className="text-xs text-[#6B7280]">{d.strength}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[#CBD5E1]">No dependent concepts</p>
                  )}
                </div>
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
