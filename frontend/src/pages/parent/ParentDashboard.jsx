import React, { useState, useEffect, useCallback } from 'react';
import { getStudentDashboard, getStudentMastery, getStudentFlags, getStudentPedagogy } from '../../api/axonai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import DashboardShell from '../../components/DashboardShell';

const STUDENT_ID = 1;

function StatusIndicator({ score }) {
  if (score < 0.2) return (
    <div className="flex items-center gap-2 text-green-700 bg-green-50 px-4 py-3 rounded-xl">
      <span className="text-2xl">&#10003;</span>
      <span className="font-medium">Your child is on track</span>
    </div>
  );
  if (score < 0.4) return (
    <div className="flex items-center gap-2 text-amber-700 bg-amber-50 px-4 py-3 rounded-xl">
      <span className="text-2xl">&#9888;</span>
      <span className="font-medium">Some areas need attention</span>
    </div>
  );
  return (
    <div className="flex items-center gap-2 text-red-700 bg-red-50 px-4 py-3 rounded-xl">
      <span className="text-2xl">&#9888;</span>
      <span className="font-medium">Your child may need additional support</span>
    </div>
  );
}

function ProgressBar({ value, max = 100, color = '#0891B2' }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full bg-[#E2E8F0] rounded-full h-2.5">
      <div className="h-2.5 rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

export default function ParentDashboard() {
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
      getStudentDashboard(STUDENT_ID),
      getStudentMastery(STUDENT_ID),
      getStudentFlags(STUDENT_ID),
      getStudentPedagogy(STUDENT_ID),
    ])
      .then(([d, m, f, p]) => {
        setDashboard(d);
        setMastery(m);
        setFlags(f);
        setPedagogy(p);
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <DashboardShell subtitle="Parent / Whānau view">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading your child's progress..." />
        </div>
      </DashboardShell>
    );
  }
  if (error) {
    return (
      <DashboardShell subtitle="Parent / Whānau view">
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={load} />
        </div>
      </DashboardShell>
    );
  }
  if (!dashboard) return null;

  const { student, profile, wellbeing, summary } = dashboard;
  const riskScore = profile.overall_risk_score;
  const concepts = mastery?.concepts || [];
  const mathConcepts = concepts.filter(c => c.subject === 'Mathematics');
  const bioConcepts = concepts.filter(c => c.subject === 'Biology');
  const mathMastery = mathConcepts.length ? mathConcepts.reduce((s, c) => s + c.mastery_score, 0) / mathConcepts.length : 0;
  const bioMastery = bioConcepts.length ? bioConcepts.reduce((s, c) => s + c.mastery_score, 0) / bioConcepts.length : 0;
  const bestApproach = pedagogy?.approaches?.[0];

  const trendMessage = profile.overall_mastery_trend === 'improving'
    ? `${student.first_name} is improving across their subjects`
    : profile.overall_mastery_trend === 'declining'
    ? `${student.first_name} may need some extra support right now`
    : `${student.first_name} is maintaining steady progress`;

  const engagementMessage = profile.overall_engagement_score >= 0.7
    ? `${student.first_name} is highly engaged with their learning`
    : profile.overall_engagement_score >= 0.4
    ? `${student.first_name} is moderately engaged with their learning`
    : `${student.first_name} could benefit from more encouragement to engage`;

  return (
    <DashboardShell subtitle={`Parent · ${student.first_name}'s overview`}>
      <div className="max-w-3xl space-y-5">
        {/* Child overview + risk in one calm card */}
        <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="axon-label mb-1">You’re viewing</p>
              <h2 className="axon-h2 text-lg text-slate-50">
                {student.first_name} {student.last_name}
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Year {student.year_level} · {student.ethnicity}
              </p>
            </div>
            <div className="text-right">
              <p className="text-[0.7rem] text-slate-500 mb-1">Attendance</p>
              <p
                className={`text-xl font-semibold ${
                  wellbeing.attendance_percentage >= 90
                    ? 'text-emerald-300'
                    : wellbeing.attendance_percentage >= 80
                    ? 'text-amber-300'
                    : 'text-rose-300'
                }`}
              >
                {wellbeing.attendance_percentage}%
              </p>
            </div>
          </div>
          <StatusIndicator score={riskScore} />
        </div>

        {/* Progress + simple subjects */}
        <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-100 mb-1">
              Overall progress
            </h3>
            <p className="text-xs text-slate-400">{trendMessage}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-16">Overall</span>
            <div className="flex-1 h-2.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-sky-400"
                style={{ width: `${(summary.mastery.avg_mastery * 100).toFixed(1)}%` }}
              />
            </div>
            <span className="text-sm font-semibold text-slate-50 w-14 text-right">
              {(summary.mastery.avg_mastery * 100).toFixed(1)}%
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div className="axon-card-ghost p-3 space-y-1.5">
              <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-500">
                Mathematics
              </p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-slate-900 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-sky-400"
                    style={{ width: `${(mathMastery * 100).toFixed(1)}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-slate-100">
                  {(mathMastery * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-[0.7rem] text-slate-500">
                {mathConcepts.length} concepts assessed
              </p>
            </div>
            <div className="axon-card-ghost p-3 space-y-1.5">
              <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-500">
                Biology
              </p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-slate-900 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-400"
                    style={{ width: `${(bioMastery * 100).toFixed(1)}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-slate-100">
                  {(bioMastery * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-[0.7rem] text-slate-500">
                {bioConcepts.length} concepts assessed
              </p>
            </div>
          </div>
        </div>

        {/* Engagement small strip */}
        <div className="axon-card-subtle p-5 sm:p-6 space-y-3">
          <h3 className="text-sm font-semibold text-slate-100">
            Engagement at a glance
          </h3>
          <p className="text-xs text-slate-400">{engagementMessage}</p>
          <div className="grid grid-cols-3 gap-3 text-center text-[0.75rem]">
            <div>
              <p className="text-base font-semibold text-sky-300">
                {summary.conversations.total_conversations}
              </p>
              <p className="text-slate-500">Learning sessions</p>
            </div>
            <div>
              <p className="text-base font-semibold text-amber-300">
                {summary.conversations.lightbulb_count}
              </p>
              <p className="text-slate-500">Lightbulb moments</p>
            </div>
            <div>
              <p className="text-base font-semibold text-emerald-300">
                {summary.quizzes.avg_score.toFixed(0)}%
              </p>
              <p className="text-slate-500">Quiz average</p>
            </div>
          </div>
        </div>

        {/* Key insight and flags condensed */}
        {bestApproach && (
          <div className="axon-card-subtle p-5 sm:p-6 space-y-3">
            <h3 className="text-sm font-semibold text-slate-100">
              How they learn best
            </h3>
            <p className="text-xs text-slate-400">
              {student.first_name} responds well to{' '}
              <span className="text-slate-100 font-medium capitalize">
                {bestApproach.teaching_approach.replace(/_/g, ' ')}
              </span>{' '}
              with a {(bestApproach.success_rate * 100).toFixed(0)}% success rate.
            </p>
          </div>
        )}

        {flags?.flags?.length > 0 && (
          <div className="axon-card-subtle p-5 sm:p-6 space-y-3">
            <h3 className="text-sm font-semibold text-slate-100">
              Ideas to support at home
            </h3>
            <p className="text-xs text-slate-400">
              A few concepts {student.first_name} is finding harder right now.
            </p>
            <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {flags.flags.map(f => (
                <div
                  key={f.id}
                  className="flex items-start gap-3 rounded-lg bg-amber-500/5 border border-amber-500/20 px-3 py-2"
                >
                  <div className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-medium text-slate-100">
                      {f.concept_name}
                    </p>
                    <p className="text-[0.7rem] text-slate-500">
                      {f.subject} — {f.flag_detail}
                    </p>
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
