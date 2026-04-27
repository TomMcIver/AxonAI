import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { loadParentDashboardBundle } from '../../api/primedRequests';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import DashboardShell from '../../components/DashboardShell';
import { useTimedProgress } from '../../hooks/useTimedProgress';

const DASH_FILL_MS = 4200;

function StatusIndicator({ score }) {
  if (!score?.label && !score?.narrative) return null;
  return (
    <div className="flex items-center gap-2 px-4 py-3 rounded-xl" style={{ color: 'var(--text-primary)', background: 'var(--surface-muted)', border: '1px solid var(--border-soft)' }}>
      {score.label ? <span className="font-medium">{score.label}</span> : null}
      {score.narrative ? <span className="text-sm text-slate-600">{score.narrative}</span> : null}
    </div>
  );
}

export default function ParentDashboard() {
  const { id } = useParams();
  const studentId = id || 1;

  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [flags, setFlags] = useState(null);
  const [pedagogy, setPedagogy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [barEpoch, setBarEpoch] = useState(0);
  const progress = useTimedProgress(DASH_FILL_MS, barEpoch);
  const studentIdFirst = useRef(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    loadParentDashboardBundle(studentId)
      .then(({ dashboard: d, mastery: m, flags: f, pedagogy: p }) => {
        setDashboard(d);
        setMastery(m);
        setFlags(f);
        setPedagogy(p);
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [studentId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (studentIdFirst.current) {
      studentIdFirst.current = false;
      return;
    }
    setBarEpoch((e) => e + 1);
  }, [studentId]);

  const dataReady = Boolean(dashboard) && !loading;
  const barComplete = progress >= 99.9;
  const showMain = dataReady && barComplete;
  const waitingOnApi = progress >= 99.9 && !dataReady && !error;

  if (error) {
    return (
      <DashboardShell subtitle="Parent / Whanau view">
        <div className="flex items-center justify-center py-16">
          <ErrorState
            message={error}
            onRetry={() => {
              setBarEpoch((e) => e + 1);
              load();
            }}
          />
        </div>
      </DashboardShell>
    );
  }

  if (!showMain) {
    return (
      <DashboardShell subtitle="Parent / Whanau view">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner
            message={
              waitingOnApi
                ? 'Still loading…'
                : dataReady
                  ? 'Preparing your dashboard…'
                  : "Loading your child's progress..."
            }
            progress={progress}
          />
        </div>
      </DashboardShell>
    );
  }
  if (!dashboard) {
    return (
      <DashboardShell subtitle="Parent / Whanau view">
        <div className="flex items-center justify-center py-16">
          <ErrorState message="No dashboard data was returned. Check the API or student id." onRetry={load} />
        </div>
      </DashboardShell>
    );
  }

  const {
    student,
    profile = {},
    wellbeing = {},
    summary = {},
  } = dashboard;
  const riskStatus = {
    label: profile?.risk_label ?? null,
    narrative: profile?.risk_narrative ?? null,
  };
  const concepts = mastery?.concepts || [];
  const mathConcepts = concepts.filter(c => c.subject === 'Mathematics');
  const bioConcepts = concepts.filter(c => c.subject === 'Biology');
  const n = (x) => (typeof x === 'number' && x > 1 ? x / 100 : x) || 0;
  const mathMastery = mathConcepts.length ? mathConcepts.reduce((s, c) => s + n(c.mastery_score), 0) / mathConcepts.length : 0;
  const bioMastery = bioConcepts.length ? bioConcepts.reduce((s, c) => s + n(c.mastery_score), 0) / bioConcepts.length : 0;
  const bestApproach = pedagogy?.approaches?.[0];

  const trendNarrative = summary?.trend_narrative ?? null;
  const engagementNarrative = summary?.engagement_narrative ?? null;

  const attendanceColor =
    (wellbeing?.attendance_percentage ?? 0) >= 90
      ? 'var(--mastered)'
      : (wellbeing?.attendance_percentage ?? 0) >= 80
        ? 'var(--needs-attention)'
        : 'var(--at-risk)';

  return (
    <DashboardShell subtitle={`Parent · ${student.first_name}'s overview`}>
      <div className="mx-auto w-full max-w-3xl space-y-5">
        <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="axon-label mb-1">You're viewing</p>
              <h2 className="axon-h2 text-lg text-slate-800">{student.first_name} {student.last_name}</h2>
              <p className="text-xs text-slate-500 mt-1">Year {student.year_level} · {student.ethnicity}</p>
            </div>
            <div className="text-right">
              <p className="text-[0.7rem] text-slate-400 mb-1">Attendance</p>
              <p className="text-xl font-semibold" style={{ color: attendanceColor }}>
                {wellbeing?.attendance_percentage ?? '-'}%
              </p>
            </div>
          </div>
          <StatusIndicator score={riskStatus} />
        </div>

        <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-1">Overall progress</h3>
            {trendNarrative ? <p className="text-xs text-slate-500">{trendNarrative}</p> : null}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 w-16">Overall</span>
            <div className="flex-1 h-2.5 rounded-full bg-slate-200 overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${((summary?.mastery?.avg_mastery ?? 0) * 100).toFixed(1)}%`, background: 'var(--mastered)' }} />
            </div>
            <span className="text-sm font-semibold text-slate-800 w-14 text-right">
              {((summary?.mastery?.avg_mastery ?? 0) * 100).toFixed(1)}%
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div className="axon-card-ghost p-3 space-y-1.5">
              <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-400">Mathematics</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${(mathMastery * 100).toFixed(1)}%`, background: 'var(--needs-attention)' }} />
                </div>
                <span className="text-sm font-medium text-slate-700">{(mathMastery * 100).toFixed(0)}%</span>
              </div>
              <p className="text-[0.7rem] text-slate-400">{mathConcepts.length} concepts assessed</p>
            </div>
            <div className="axon-card-ghost p-3 space-y-1.5">
              <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-400">Biology</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${(bioMastery * 100).toFixed(1)}%`, background: 'var(--mastered)' }} />
                </div>
                <span className="text-sm font-medium text-slate-700">{(bioMastery * 100).toFixed(0)}%</span>
              </div>
              <p className="text-[0.7rem] text-slate-400">{bioConcepts.length} concepts assessed</p>
            </div>
          </div>
        </div>

        <div className="axon-card-subtle p-5 sm:p-6 space-y-3">
          <h3 className="text-sm font-semibold text-slate-700">Engagement at a glance</h3>
          {engagementNarrative ? <p className="text-xs text-slate-500">{engagementNarrative}</p> : null}
          <div className="grid grid-cols-3 gap-3 text-center text-[0.75rem]">
            <div>
              <p className="text-base font-semibold" style={{ color: 'var(--mastered)' }}>{summary?.conversations?.total_conversations ?? '-'}</p>
              <p className="text-slate-400">Learning sessions</p>
            </div>
            <div>
              <p className="text-base font-semibold" style={{ color: 'var(--needs-attention)' }}>{summary?.conversations?.lightbulb_count ?? '-'}</p>
              <p className="text-slate-400">Lightbulb moments</p>
            </div>
            <div>
              <p className="text-base font-semibold" style={{ color: 'var(--mastered)' }}>{(summary?.quizzes?.avg_score ?? 0).toFixed(0)}%</p>
              <p className="text-slate-400">Quiz average</p>
            </div>
          </div>
        </div>

        {bestApproach && (
          <div className="axon-card-subtle p-5 sm:p-6 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">How they learn best</h3>
            <p className="text-xs text-slate-500">
              {student.first_name} responds well to{' '}
              <span className="text-slate-700 font-medium capitalize">{bestApproach.teaching_approach.replace(/_/g, ' ')}</span>{' '}
              with a {(bestApproach.success_rate * 100).toFixed(0)}% success rate.
            </p>
          </div>
        )}

        {flags?.flags?.length > 0 && (
          <div className="axon-card-subtle p-5 sm:p-6 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Ideas to support at home</h3>
            <p className="text-xs text-slate-500">A few concepts {student.first_name} is finding harder right now.</p>
            <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {flags.flags.map(f => (
                <div key={f.id} className="flex items-start gap-3 rounded-lg px-3 py-2" style={{ background: 'var(--needs-attention-bg)', border: '1px solid color-mix(in srgb, var(--needs-attention) 30%, white)' }}>
                  <div className="mt-1 h-1.5 w-1.5 rounded-full flex-shrink-0" style={{ background: 'var(--needs-attention)' }} />
                  <div>
                    <p className="text-xs font-medium text-slate-700">{f.concept_name}</p>
                    <p className="text-[0.7rem] text-slate-400">{f.subject}: {f.flag_detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
