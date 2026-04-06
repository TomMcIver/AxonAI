import React, { useRef, useState, useEffect, useCallback } from 'react';
import { getConcepts } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';
import ErrorState from './ErrorState';

const DIFFICULTY_CONFIG = {
  5: { label: 'Very Hard', color: '#dc2626', bg: 'bg-red-50', text: 'text-red-700', ring: 'ring-red-200' },
  4: { label: 'Hard', color: '#ea580c', bg: 'bg-orange-50', text: 'text-orange-700', ring: 'ring-orange-200' },
  3: { label: 'Medium', color: '#d97706', bg: 'bg-amber-50', text: 'text-amber-700', ring: 'ring-amber-200' },
  2: { label: 'Easy', color: '#16a34a', bg: 'bg-green-50', text: 'text-green-700', ring: 'ring-green-200' },
  1: { label: 'Foundational', color: '#059669', bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200' },
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
            : 'bg-white/70 text-slate-700 border-slate-200/60 hover:shadow-sm'
      }`}
      onClick={() => onSelect(concept.id)}
      onMouseEnter={() => onHover(concept.id)}
      onMouseLeave={onLeave}
    >
      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: cfg.color }} />
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

  const ranks = [5, 4, 3, 2, 1];
  const grouped = {};
  ranks.forEach(r => { grouped[r] = []; });
  concepts.forEach(c => {
    const lvl = c.difficulty_level || 3;
    if (!grouped[lvl]) grouped[lvl] = [];
    grouped[lvl].push(c);
  });
  ranks.forEach(r => { grouped[r].sort((a, b) => a.name.localeCompare(b.name)); });

  const matchesSearch = (c) => !search || c.name.toLowerCase().includes(search.toLowerCase());

  const selectedConcept = selected ? concepts.find(c => c.id === selected) : null;

  function handleSelect(conceptId) {
    setSelected(conceptId);
    requestAnimationFrame(() => {
      detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-4">
        <div className="text-sm text-slate-500">
          {concepts.length} concepts, {edges.length} prerequisite links
        </div>
        <input
          type="text"
          placeholder="Search concepts..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            padding: '6px 12px',
            border: '1px solid rgba(148, 163, 184, 0.25)',
            borderRadius: 8,
            fontSize: 14,
            width: 256,
            background: 'rgba(255, 255, 255, 0.6)',
            backdropFilter: 'blur(8px)',
            color: '#1e293b',
            outline: 'none',
          }}
        />
      </div>

      {/* Ranked concept map */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.5)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.6)',
        borderRadius: 16,
        padding: 16,
        marginBottom: 16,
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
      }}>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-slate-700">Concept Hierarchy</h4>
          <span className="text-xs text-slate-400">Hardest at top, easiest at bottom</span>
        </div>

        <div className="space-y-1">
          {ranks.map(rank => {
            const cfg = DIFFICULTY_CONFIG[rank] || DIFFICULTY_CONFIG[3];
            const items = grouped[rank]?.filter(matchesSearch) || [];
            if (items.length === 0 && search) return null;
            return (
              <div key={rank} className="flex items-start gap-3 py-3" style={{ borderBottom: '1px solid rgba(148, 163, 184, 0.1)' }}>
                <div className="w-24 flex-shrink-0 pt-1">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${cfg.bg} ${cfg.text} uppercase tracking-wider`}>
                    Lvl {rank}
                  </span>
                  <p className="text-[10px] text-slate-400 mt-0.5">{cfg.label}</p>
                </div>
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
                    <span className="text-xs text-slate-300 italic py-1">No concepts at this level</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex items-center gap-4 mt-3 pt-3 text-xs text-slate-400" style={{ borderTop: '1px solid rgba(148, 163, 184, 0.1)' }}>
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
            <div className="lg:col-span-2" style={{
              background: 'rgba(255, 255, 255, 0.6)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.7)',
              borderRadius: 16,
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
            }}>
              <div className="p-4" style={{ borderBottom: '1px solid rgba(148, 163, 184, 0.15)' }}>
                <h4 className="font-semibold text-slate-700">{showConcept.name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <DifficultyBadge level={showConcept.difficulty_level} />
                  <span className="text-xs text-slate-400 capitalize">{showConcept.concept_type}</span>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2">
                <div className="p-4" style={{ borderRight: '1px solid rgba(148, 163, 184, 0.1)' }}>
                  <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Prerequisites ({showPrereqs.length})
                  </h5>
                  {showPrereqs.length > 0 ? (
                    <div className="space-y-1.5">
                      {showPrereqs.map(p => (
                        <div key={p.id} className="flex items-center justify-between text-sm">
                          <span className="text-slate-700 cursor-pointer hover:text-teal-600" onClick={() => handleSelect(p.id)}>
                            {p.name}
                          </span>
                          <div className="flex items-center gap-2">
                            <DifficultyBadge level={p.difficulty_level} />
                            <span className="text-xs text-slate-400">{p.strength}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-300">No prerequisites — foundational concept</p>
                  )}
                </div>
                <div className="p-4">
                  <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Required By ({showDeps.length})
                  </h5>
                  {showDeps.length > 0 ? (
                    <div className="space-y-1.5">
                      {showDeps.map(d => (
                        <div key={d.id} className="flex items-center justify-between text-sm">
                          <span className="text-slate-700 cursor-pointer hover:text-teal-600" onClick={() => handleSelect(d.id)}>
                            {d.name}
                          </span>
                          <div className="flex items-center gap-2">
                            <DifficultyBadge level={d.difficulty_level} />
                            <span className="text-xs text-slate-400">{d.strength}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-300">No dependent concepts</p>
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
