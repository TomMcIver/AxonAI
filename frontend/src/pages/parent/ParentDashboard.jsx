import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getStudentDashboard, getStudentMastery, getStudentFlags, getStudentPedagogy } from '../../api/axonai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import DashboardShell from '../../components/DashboardShell';

function StatusIndicator({ score }) {
  if (score < 0.2) return (
    <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50/80 border border-emerald-200/50 px-4 py-3 rounded-xl">
      <span className="text-2xl">&#10003;</span>
      <span className="font-medium">Your child is on track</span>
    </div>
  );
  if (score < 0.4) return (
    <div className="flex items-center gap-2 text-amber-700 bg-amber-50/80 border border-amber-200/50 px-4 py-3 rounded-xl">
      <span className="text-2xl">&#9888;</span>
      <span className="font-medium">Some areas need attention</span>
    </div>
  );
  return (
    <div className="flex items-center gap-2 text-red-700 bg-red-50/80 border border-red-200/50 px-4 py-3 rounded-xl">
      <span className="text-2xl">&#9888;</span>
      <span className="font-medium">Your child may need additional support</span>
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

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getStudentDashboard(studentId),
      getStudentMastery(studentId),
      getStudentFlags(studentId),
      getStudentPedagogy(studentId),
    ])
      .then(([d, m, f, p]) => {
        setDashboard(d);
        setMastery(m);
        setFlags(f);
        setPedagogy(p);
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [studentId]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <DashboardShell subtitle="Parent / Whanau view">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading your child's progress..." />
        </div>
      </DashboardShell>
    );
  }
  if (error) {
    return (
      <DashboardShell subtitle="Parent / Whanau view">
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={load} />
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
  const riskScore = profile?.overall_risk_score ?? 0.5;
  const concepts = mastery?.concepts || [];
  const mathConcepts = concepts.filter(c => c.subject === 'Mathematics');
  const bioConcepts = concepts.filter(c => c.subject === 'Biology');
  const n = (x) => (typeof x === 'number' && x > 1 ? x / 100 : x) || 0;
  const mathMastery = mathConcepts.length ? mathConcepts.reduce((s, c) => s + n(c.mastery_score), 0) / mathConcepts.length : 0;
  const bioMastery = bioConcepts.length ? bioConcepts.reduce((s, c) => s + n(c.mastery_score), 0) / bioConcepts.length : 0;
  const bestApproach = pedagogy?.approaches?.[0];

  const trendMessage = profile?.overall_mastery_trend === 'improving'
    ? `${student.first_name} is improving across their subjects`
    : profile?.overall_mastery_trend === 'declining'
    ? `${student.first_name} may need some extra support right now`
    : `${student.first_name} is maintaining steady progress`;

  const engagementMessage = (profile?.overall_engagement_score ?? 0) >= 0.7
    ? `${student.first_name} is highly engaged with their learning`
    : (profile?.overall_engagement_score ?? 0) >= 0.4
    ? `${student.first_name} is moderately engaged with their learning`
    : `${student.first_name} could benefit from more encouragement to engage`;

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
              <p className={`text-xl font-semibold ${
                (wellbeing?.attendance_percentage ?? 0) >= 90 ? 'text-emerald-600' :
                (wellbeing?.attendance_percentage ?? 0) >= 80 ? 'text-amber-600' : 'text-rose-600'
              }`}>
                {wellbeing?.attendance_percentage ?? '—'}%
              </p>
            </div>
          </div>
          <StatusIndicator score={riskScore} />
        </div>

        <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-1">Overall progress</h3>
            <p className="text-xs text-slate-500">{trendMessage}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 w-16">Overall</span>
            <div className="flex-1 h-2.5 rounded-full bg-slate-200 overflow-hidden">
              <div className="h-full rounded-full bg-teal-500" style={{ width: `${((summary?.mastery?.avg_mastery ?? 0) * 100).toFixed(1)}%` }} />
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
                  <div className="h-full rounded-full bg-sky-500" style={{ width: `${(mathMastery * 100).toFixed(1)}%` }} />
                </div>
                <span className="text-sm font-medium text-slate-700">{(mathMastery * 100).toFixed(0)}%</span>
              </div>
              <p className="text-[0.7rem] text-slate-400">{mathConcepts.length} concepts assessed</p>
            </div>
            <div className="axon-card-ghost p-3 space-y-1.5">
              <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-400">Biology</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                  <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(bioMastery * 100).toFixed(1)}%` }} />
                </div>
                <span className="text-sm font-medium text-slate-700">{(bioMastery * 100).toFixed(0)}%</span>
              </div>
              <p className="text-[0.7rem] text-slate-400">{bioConcepts.length} concepts assessed</p>
            </div>
          </div>
        </div>

        <div className="axon-card-subtle p-5 sm:p-6 space-y-3">
          <h3 className="text-sm font-semibold text-slate-700">Engagement at a glance</h3>
          <p className="text-xs text-slate-500">{engagementMessage}</p>
          <div className="grid grid-cols-3 gap-3 text-center text-[0.75rem]">
            <div>
              <p className="text-base font-semibold text-teal-600">{summary?.conversations?.total_conversations ?? '—'}</p>
              <p className="text-slate-400">Learning sessions</p>
            </div>
            <div>
              <p className="text-base font-semibold text-amber-600">{summary?.conversations?.lightbulb_count ?? '—'}</p>
              <p className="text-slate-400">Lightbulb moments</p>
            </div>
            <div>
              <p className="text-base font-semibold text-emerald-600">{(summary?.quizzes?.avg_score ?? 0).toFixed(0)}%</p>
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
                <div key={f.id} className="flex items-start gap-3 rounded-lg bg-amber-50/60 border border-amber-300/30 px-3 py-2">
                  <div className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-medium text-slate-700">{f.concept_name}</p>
                    <p className="text-[0.7rem] text-slate-400">{f.subject} — {f.flag_detail}</p>
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
