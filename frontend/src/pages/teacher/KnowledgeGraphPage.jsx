import React, { useState } from 'react';
import DashboardShell from '../../components/DashboardShell';
import KnowledgeGraph from '../../components/KnowledgeGraph';

const SUBJECTS = ['Mathematics', 'Biology'];

export default function KnowledgeGraphPage() {
  const [subject, setSubject] = useState('Mathematics');

  return (
    <DashboardShell subtitle="Knowledge graph · prerequisites">
      <div className="axon-card-subtle p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="axon-label mb-1">Explore</p>
            <h1 className="axon-h2 text-lg sm:text-xl text-slate-800">
              Knowledge Graph
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Click a concept to jump to prerequisites and dependents.
            </p>
          </div>
          <div className="flex gap-2">
            {SUBJECTS.map(s => (
              <button
                key={s}
                onClick={() => setSubject(s)}
                className={`axon-btn ${
                  subject === s ? 'axon-btn-primary' : 'axon-btn-ghost'
                }`}
                style={{ textTransform: 'none', letterSpacing: '0.02em' }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="axon-card-subtle p-5 sm:p-6">
        <KnowledgeGraph subject={subject} />
      </div>
    </DashboardShell>
  );
}
