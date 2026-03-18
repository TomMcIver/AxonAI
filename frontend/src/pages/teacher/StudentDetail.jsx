import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  getStudentConversations,
  getStudentDashboard,
  getStudentFlags,
  getStudentMastery,
} from '../../api/axonai';
import DashboardShell from '../../components/DashboardShell';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import ConversationThread from '../../components/ConversationThread';

function clamp01(n) {
  if (typeof n !== 'number' || Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function riskTone(score) {
  if (score >= 0.4) return { pill: 'axon-pill-danger', label: 'At risk' };
  if (score >= 0.2) return { pill: 'axon-pill-soft', label: 'Needs attention' };
  return { pill: 'axon-pill-success', label: 'On track' };
}

function pct(v) {
  return `${Math.round(clamp01(v) * 100)}%`;
}

export default function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [flags, setFlags] = useState(null);
  const [conversations, setConversations] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Hooks must be called unconditionally (even while loading).
  const focusConcepts = useMemo(() => {
    const cs = mastery?.concepts || [];
    return [...cs]
      .sort((a, b) => (a.mastery_score ?? 0) - (b.mastery_score ?? 0))
      .slice(0, 5);
  }, [mastery]);

  const recentConvos = useMemo(() => {
    return (conversations?.conversations || []).slice(0, 6);
  }, [conversations]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getStudentDashboard(id),
      getStudentMastery(id),
      getStudentFlags(id),
      getStudentConversations(id, 20, 0),
    ])
      .then(([d, m, f, c]) => {
        setDashboard(d);
        setMastery(m);
        setFlags(f);
        setConversations(c);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <DashboardShell subtitle="Student profile">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading student profile..." />
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell subtitle="Student profile">
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={load} />
        </div>
      </DashboardShell>
    );
  }

  if (!dashboard) return null;

  const { student, profile, wellbeing, summary } = dashboard;
  const risk = clamp01(profile?.overall_risk_score);
  const tone = riskTone(risk);

  return (
    <DashboardShell subtitle="Student · detail">
      <div className="space-y-5">
        <div className="flex items-center justify-between gap-3">
          <button
            className="axon-btn axon-btn-quiet"
            onClick={() => navigate(-1)}
          >
            ← Back
          </button>
          <button
            className="axon-btn axon-btn-ghost"
            onClick={() => navigate('/teacher/students')}
          >
            All students
          </button>
        </div>

        <div className="axon-card-subtle p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="axon-label mb-1">Student</p>
              <h1 className="axon-h2 text-lg sm:text-xl text-slate-50">
                {student.first_name} {student.last_name}
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Year {student.year_level} · {student.ethnicity} · {student.gender}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className={`axon-pill ${tone.pill}`}>{tone.label}</span>
                <span className="axon-pill">
                  Attendance {wellbeing?.attendance_percentage?.toFixed?.(0) ?? wellbeing?.attendance_percentage ?? '—'}%
                </span>
                <span className="axon-pill">
                  {summary?.active_flags ?? 0} flags
                </span>
              </div>
            </div>

            <div className="axon-card-ghost p-4 min-w-[240px]">
              <p className="axon-label mb-2">At a glance</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Avg mastery</span>
                  <span className="text-slate-100 font-medium">
                    {pct(summary?.mastery?.avg_mastery)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Engagement</span>
                  <span className="text-slate-100 font-medium">
                    {pct(profile?.overall_engagement_score)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Conversations</span>
                  <span className="text-slate-100 font-medium">
                    {summary?.conversations?.total_conversations ?? 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
          <div className="axon-card-subtle p-5 sm:p-6">
            <div className="flex items-end justify-between gap-3 mb-3">
              <div>
                <p className="text-sm font-semibold text-slate-100">Focus concepts</p>
                <p className="text-xs text-slate-500">
                  Lowest mastery first — keep the list short and actionable.
                </p>
              </div>
            </div>
            <div className="space-y-2">
              {focusConcepts.map(c => (
                <div
                  key={c.concept_id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-100 truncate">
                      {c.concept_name}
                    </p>
                    <p className="text-[0.7rem] text-slate-500 truncate">
                      {c.subject}
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-sky-200">
                    {pct(c.mastery_score)}
                  </span>
                </div>
              ))}
              {focusConcepts.length === 0 && (
                <p className="text-xs text-slate-500">No mastery data yet.</p>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="axon-card-subtle p-5 sm:p-6">
              <p className="text-sm font-semibold text-slate-100 mb-2">Active flags</p>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {(flags?.flags || []).slice(0, 6).map(f => (
                  <div
                    key={f.id}
                    className="rounded-lg border border-rose-500/20 bg-rose-500/5 px-3 py-2"
                  >
                    <p className="text-xs font-medium text-slate-100">
                      {f.concept_name}
                    </p>
                    <p className="text-[0.7rem] text-slate-500">
                      {f.flag_detail}
                    </p>
                  </div>
                ))}
                {(flags?.flags || []).length === 0 && (
                  <p className="text-xs text-slate-500">No active flags.</p>
                )}
              </div>
            </div>

            <div className="axon-card-subtle p-5 sm:p-6">
              <p className="text-sm font-semibold text-slate-100 mb-2">Recent sessions</p>
              <div className="space-y-2">
                {recentConvos.map(c => (
                  <button
                    key={c.id}
                    className="w-full text-left rounded-lg border border-slate-800 bg-slate-950/40 hover:bg-slate-950/70 transition-colors px-3 py-2"
                    onClick={() =>
                      setActiveConversation(activeConversation === c.id ? null : c.id)
                    }
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs font-medium text-slate-100 truncate">
                        {c.concept_name}
                      </p>
                      <span className="text-[0.7rem] text-slate-500">
                        {pct(c.session_engagement_score)}
                      </span>
                    </div>
                    <p className="text-[0.7rem] text-slate-500 mt-0.5 truncate">
                      {c.subject} · {new Date(c.started_at).toLocaleDateString()}
                    </p>
                  </button>
                ))}
                {recentConvos.length === 0 && (
                  <p className="text-xs text-slate-500">No sessions yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {activeConversation && (
          <div className="axon-card-subtle p-5 sm:p-6">
            <ConversationThread
              conversationId={activeConversation}
              onClose={() => setActiveConversation(null)}
            />
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

