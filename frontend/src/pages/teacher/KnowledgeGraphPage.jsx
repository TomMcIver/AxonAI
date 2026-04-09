import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DashboardShell from '../../components/DashboardShell';
import KnowledgeGraphNew from '../../components/KnowledgeGraphNew';

const SUBJECTS = ['Mathematics', 'Biology'];

export default function KnowledgeGraphPage() {
  const { subject: subjectParam } = useParams();
  const navigate = useNavigate();
  const [subject, setSubject] = useState(
    SUBJECTS.includes(subjectParam) ? subjectParam : 'Mathematics'
  );

  function switchSubject(s) {
    setSubject(s);
    navigate(`/teacher/knowledge-graph/${s}`, { replace: true });
  }

  return (
    <DashboardShell subtitle={`Knowledge graph · prerequisites · ${subject}`}>
      {/* Header card */}
      <div className="axon-card-subtle p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="axon-label mb-1">Explore</p>
            <h1 className="axon-h2 text-lg sm:text-xl text-slate-800">
              {subject} Concept Map
            </h1>
          </div>
          <div className="flex gap-2">
            {SUBJECTS.map(s => (
              <button
                key={s}
                onClick={() => switchSubject(s)}
                className={`axon-btn ${subject === s ? 'axon-btn-primary' : 'axon-btn-ghost'}`}
                style={{ textTransform: 'none', letterSpacing: '0.02em' }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Full graph panel — tall fixed height so it doesn't collapse */}
      <div className="axon-card-subtle p-4 sm:p-5" style={{ minHeight: 680 }}>
        <KnowledgeGraphNew subject={subject} mapOnly />
      </div>
    </DashboardShell>
  );
}
