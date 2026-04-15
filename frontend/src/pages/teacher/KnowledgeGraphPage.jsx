import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DashboardShell from '../../components/DashboardShell';
import KnowledgeGraphNew from '../../components/KnowledgeGraphNew';
import LoadingSpinner from '../../components/LoadingSpinner';
import { useClassMasteryMap } from '../../hooks/useClassMasteryMap';

const SUBJECTS = ['Mathematics', 'Biology'];

export default function KnowledgeGraphPage() {
  const { subject: subjectParam } = useParams();
  const navigate = useNavigate();
  const [subject, setSubject] = useState(
    SUBJECTS.includes(subjectParam) ? subjectParam : 'Mathematics'
  );
  const { masteryMap: classFairMasteryMap, loading: cohortLoading, source: cohortSource, studentCount: cohortN } =
    useClassMasteryMap(1, subject);

  function switchSubject(s) {
    setSubject(s);
    navigate(`/teacher/knowledge-graph/${s}`, { replace: true });
  }

  return (
    <DashboardShell subtitle={`Knowledge graph · prerequisites · ${subject}`}>
      {/* Header card */}
      <div className="axon-card-subtle p-4 sm:p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
          <div className="min-w-0 space-y-2">
            <p className="axon-label">Explore</p>
            <h1 className="axon-h2 text-lg sm:text-xl text-slate-800">
              {subject} Concept Map
            </h1>
            <p className="max-w-xl text-[11px] leading-relaxed text-slate-500">
              Cohort colours use a softened class average (from the class API when available, otherwise averaged from each
              learner&apos;s mastery). Use the toggles for Whole class vs Concepts, and Full map vs Explore path.
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2 sm:pt-1">
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

      {/* Graph panel: inner KnowledgeGraphNew fixes SVG height; avoid huge min-h so toggles don’t stretch the card */}
      <div className="axon-card-subtle relative flex min-h-0 flex-col rounded-lg p-3 sm:p-4">
        {cohortLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-[#fffef4]/85 backdrop-blur-[2px]">
            <LoadingSpinner message="Loading class mastery…" />
          </div>
        )}
        <KnowledgeGraphNew
          subject={subject}
          focusKeyNodes={false}
          masteryMap={classFairMasteryMap || undefined}
          showTeacherViewToggle
          cohortMasteryMeta={
            cohortSource === 'student-aggregate' && cohortN > 0
              ? { source: 'student-aggregate', studentCount: cohortN }
              : cohortSource === 'class-summary'
                ? { source: 'class-summary' }
                : null
          }
        />
      </div>
    </DashboardShell>
  );
}
