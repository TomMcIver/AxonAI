import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getConcepts } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';
import ErrorState from './ErrorState';

function DifficultyBadge({ level }) {
  const colors = {
    1: 'bg-green-100 text-green-700',
    2: 'bg-green-100 text-green-700',
    3: 'bg-amber-100 text-amber-700',
    4: 'bg-orange-100 text-orange-700',
    5: 'bg-red-100 text-red-700',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[level] || colors[3]}`}>
      Level {level}
    </span>
  );
}

export default function KnowledgeGraph({ subject }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const canvasRef = useRef(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getConcepts(subject)
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [subject]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const concepts = data.concepts || [];
    const edges = data.prerequisites || [];
    const W = canvas.width = canvas.parentElement.clientWidth;
    const H = canvas.height = 400;

    // Simple grid layout
    const cols = Math.ceil(Math.sqrt(concepts.length));
    const padX = 60, padY = 50;
    const gapX = (W - 2 * padX) / Math.max(cols - 1, 1);
    const gapY = (H - 2 * padY) / Math.max(Math.ceil(concepts.length / cols) - 1, 1);

    const positions = {};
    concepts.forEach((c, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      positions[c.id] = { x: padX + col * gapX, y: padY + row * gapY };
    });

    ctx.clearRect(0, 0, W, H);

    // Draw edges
    ctx.strokeStyle = '#CBD5E1';
    ctx.lineWidth = 1;
    edges.forEach(e => {
      const from = positions[e.prerequisite_concept_id];
      const to = positions[e.concept_id];
      if (from && to) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    concepts.forEach(c => {
      const pos = positions[c.id];
      if (!pos) return;
      const diff = c.difficulty_level || 3;
      const colors = ['#10B981', '#10B981', '#F59E0B', '#F97316', '#EF4444'];
      ctx.fillStyle = colors[diff - 1] || '#0891B2';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [data]);

  if (loading) return <LoadingSpinner message={`Loading ${subject} concepts...`} />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  const concepts = data.concepts || [];
  const edges = data.prerequisites || [];
  const filtered = search
    ? concepts.filter(c => c.name.toLowerCase().includes(search.toLowerCase()))
    : concepts;

  const selectedConcept = selected ? concepts.find(c => c.id === selected) : null;
  const prereqs = selected ? edges.filter(e => e.concept_id === selected).map(e => {
    const pc = concepts.find(c => c.id === e.prerequisite_concept_id);
    return pc ? { ...pc, strength: e.strength } : null;
  }).filter(Boolean) : [];
  const dependents = selected ? edges.filter(e => e.prerequisite_concept_id === selected).map(e => {
    const dc = concepts.find(c => c.id === e.concept_id);
    return dc ? { ...dc, strength: e.strength } : null;
  }).filter(Boolean) : [];

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

      <div className="bg-white rounded-xl border border-[#E2E8F0] p-4 mb-4">
        <canvas ref={canvasRef} className="w-full" />
        <div className="flex items-center gap-4 mt-2 text-xs text-[#6B7280]">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#10B981] inline-block" /> Easy (1-2)</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#F59E0B] inline-block" /> Medium (3)</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#F97316] inline-block" /> Hard (4)</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#EF4444] inline-block" /> Very Hard (5)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
          <div className="p-3 bg-[#F8FAFC] border-b border-[#E2E8F0]">
            <h4 className="text-sm font-semibold text-[#1F2937]">All Concepts</h4>
          </div>
          <div className="max-h-96 overflow-y-auto divide-y divide-[#E2E8F0]">
            {filtered.map(c => (
              <div
                key={c.id}
                className={`px-3 py-2 cursor-pointer transition-colors ${selected === c.id ? 'bg-[#0891B2]/10' : 'hover:bg-[#F1F5F9]'}`}
                onClick={() => setSelected(c.id)}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#1F2937]">{c.name}</span>
                  <DifficultyBadge level={c.difficulty_level} />
                </div>
                <span className="text-xs text-[#6B7280] capitalize">{c.concept_type}</span>
              </div>
            ))}
          </div>
        </div>

        {selectedConcept && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm">
            <div className="p-4 border-b border-[#E2E8F0]">
              <h4 className="font-semibold text-[#1F2937]">{selectedConcept.name}</h4>
              <div className="flex items-center gap-2 mt-1">
                <DifficultyBadge level={selectedConcept.difficulty_level} />
                <span className="text-xs text-[#6B7280] capitalize">{selectedConcept.concept_type}</span>
              </div>
            </div>
            {prereqs.length > 0 && (
              <div className="p-4 border-b border-[#E2E8F0]">
                <h5 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">Prerequisites</h5>
                <div className="space-y-1">
                  {prereqs.map(p => (
                    <div key={p.id} className="flex items-center justify-between text-sm">
                      <span className="text-[#1F2937] cursor-pointer hover:text-[#0891B2]" onClick={() => setSelected(p.id)}>
                        {p.name}
                      </span>
                      <span className="text-xs text-[#6B7280]">strength: {p.strength}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {dependents.length > 0 && (
              <div className="p-4">
                <h5 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">Required By</h5>
                <div className="space-y-1">
                  {dependents.map(d => (
                    <div key={d.id} className="flex items-center justify-between text-sm">
                      <span className="text-[#1F2937] cursor-pointer hover:text-[#0891B2]" onClick={() => setSelected(d.id)}>
                        {d.name}
                      </span>
                      <span className="text-xs text-[#6B7280]">strength: {d.strength}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {prereqs.length === 0 && dependents.length === 0 && (
              <div className="p-4 text-sm text-[#6B7280]">No prerequisite connections found.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
