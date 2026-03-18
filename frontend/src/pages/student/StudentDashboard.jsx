import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getStudentDashboard, getStudentMastery, getStudentPedagogy, getStudentConversations } from '../../api/axonai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import ConversationThread from '../../components/ConversationThread';
import DashboardShell from '../../components/DashboardShell';
import { XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';

const STUDENT_ID = 1; // Demo student: Aroha Ngata

function ProgressBar({ value, max = 100, color = '#0891B2' }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full bg-[#E2E8F0] rounded-full h-3">
      <div className="h-3 rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

export default function StudentDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [pedagogy, setPedagogy] = useState(null);
  const [conversations, setConversations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);
  const [chatSubjectFilter, setChatSubjectFilter] = useState('all');

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getStudentDashboard(STUDENT_ID),
      getStudentMastery(STUDENT_ID),
      getStudentPedagogy(STUDENT_ID),
      getStudentConversations(STUDENT_ID, 44),
    ])
      .then(([d, m, p, c]) => {
        setDashboard(d);
        setMastery(m);
        setPedagogy(p);
        setConversations(c);
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  // Memoize conversation data
  const { convos, lightbulbs, subjects, filteredConvos } = useMemo(() => {
    const allConvos = conversations?.conversations || [];
    const lbs = allConvos.filter(c => c.lightbulb_moment_detected);
    const subjs = [...new Set(allConvos.map(c => c.subject).filter(Boolean))].sort();
    const filtered = chatSubjectFilter === 'all'
      ? allConvos
      : allConvos.filter(c => c.subject === chatSubjectFilter);
    return { convos: allConvos, lightbulbs: lbs, subjects: subjs, filteredConvos: filtered };
  }, [conversations, chatSubjectFilter]);

  // Build engagement trend from conversations (chronological)
  const engagementTrend = useMemo(() => {
    return [...convos].reverse().map((c, i) => ({
      session: i + 1,
      engagement: +(c.session_engagement_score * 100).toFixed(0),
    }));
  }, [convos]);

  // Build mastery improvement projection — shows growth peaking then leveling off
  const masteryProjection = useMemo(() => {
    if (!mastery?.concepts?.length || !convos.length) return [];

    const sorted = [...convos].reverse();
    const windowSize = 5;
    const points = [];

    for (let i = 0; i < sorted.length; i++) {
      const windowStart = Math.max(0, i - windowSize + 1);
      const w = sorted.slice(windowStart, i + 1);
      const avgEngagement = w.reduce((s, c) => s + c.session_engagement_score, 0) / w.length;
      points.push({
        session: i + 1,
        mastery: +(avgEngagement * 100).toFixed(0),
      });
    }

    // Project forward with asymptotic curve: rapid improvement → peak → plateau
    if (points.length >= 3) {
      const lastMastery = points[points.length - 1].mastery;
      const lastSession = points[points.length - 1].session;
      // Bridge: last actual point also gets projected value for line continuity
      points[points.length - 1].projected = lastMastery;
      // Target: aim for ~88-92% ceiling (realistic high performance)
      const ceiling = Math.min(95, Math.max(lastMastery + 20, 85));
      const gap = ceiling - lastMastery;

      for (let i = 1; i <= 12; i++) {
        // Logarithmic growth: fast at first, slows down approaching ceiling
        const progress = 1 - Math.exp(-0.35 * i);
        const projected = Math.min(ceiling, lastMastery + gap * progress);
        points.push({
          session: lastSession + i,
          projected: +projected.toFixed(0),
        });
      }
    }

    return points;
  }, [mastery, convos]);

  if (loading) {
    return (
      <DashboardShell subtitle="Student view">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading your dashboard..." />
        </div>
      </DashboardShell>
    );
  }
  if (error) {
    return (
      <DashboardShell subtitle="Student view">
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={load} />
        </div>
      </DashboardShell>
    );
  }
  if (!dashboard) return null;

  const { student, profile, summary } = dashboard;
  const concepts = mastery?.concepts || [];
  const weakest = concepts.slice(0, 5);
  const strongest = [...concepts].reverse().slice(0, 5);
  const mathAvg = concepts.filter(c => c.subject === 'Mathematics');
  const bioAvg = concepts.filter(c => c.subject === 'Biology');
  const mathMastery = mathAvg.length ? mathAvg.reduce((s, c) => s + c.mastery_score, 0) / mathAvg.length : 0;
  const bioMastery = bioAvg.length ? bioAvg.reduce((s, c) => s + c.mastery_score, 0) / bioAvg.length : 0;

  const bestApproach = pedagogy?.approaches?.[0];

  return (
    <DashboardShell subtitle={`Student · ${student.first_name}'s overview`}>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1.1fr)]">
        {/* Left column: simple mastery & subjects */}
        <div className="axon-card-subtle p-5 sm:p-6 space-y-5">
          <div>
            <p className="axon-label mb-1">Welcome back</p>
            <h1 className="axon-h2 text-lg sm:text-xl text-slate-50">
              Kia ora, {student.first_name}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Year {student.year_level} · {student.ethnicity}
            </p>
          </div>

          {/* Overall mastery */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-100">Overall mastery</p>
              <span className="axon-pill text-[0.7rem]">
                {profile.overall_mastery_trend === 'improving'
                  ? "You're improving"
                  : profile.overall_mastery_trend}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-sky-400 to-emerald-400 transition-all duration-500"
                  style={{ width: `${(summary.mastery.avg_mastery * 100).toFixed(1)}%` }}
                />
              </div>
              <span className="text-xl font-semibold text-sky-300">
                {(summary.mastery.avg_mastery * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Subject snapshot */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="axon-card-ghost p-3.5 space-y-1.5">
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
                {mathAvg.length} concepts tracked
              </p>
            </div>
            <div className="axon-card-ghost p-3.5 space-y-1.5">
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
                {bioAvg.length} concepts tracked
              </p>
            </div>
          </div>
        </div>

        {/* Right column: compact overview panels */}
        <div className="space-y-4">
          <div className="axon-card-subtle p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-slate-100 mb-2">
              Areas to work on
            </h3>
            <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              {weakest.slice(0, 4).map(c => (
                <div
                  key={c.concept_id}
                  className="flex items-center justify-between rounded-lg bg-rose-500/5 border border-rose-500/20 px-3 py-2"
                >
                  <div>
                    <p className="text-xs font-medium text-slate-100">
                      {c.concept_name}
                    </p>
                    <p className="text-[0.7rem] text-slate-500">{c.subject}</p>
                  </div>
                  <span className="text-xs font-semibold text-rose-300">
                    {(c.mastery_score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
              {weakest.length === 0 && (
                <p className="text-[0.72rem] text-slate-500">
                  No flagged concepts right now.
                </p>
              )}
            </div>
          </div>

          <div className="axon-card-subtle p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-slate-100 mb-2">
              AI learning sessions
            </h3>
            <p className="text-[0.72rem] text-slate-400 mb-2">
              Recently with the AxonAI tutor.
            </p>
            <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              {filteredConvos.slice(0, 5).map(c => (
                <div
                  key={c.id}
                  className="flex items-center justify-between rounded-lg bg-slate-900/70 border border-slate-800 px-3 py-2 text-xs text-slate-200 cursor-pointer"
                  onClick={() =>
                    setActiveConversation(
                      activeConversation === c.id ? null : c.id,
                    )
                  }
                >
                  <span className="truncate mr-2">{c.concept_name}</span>
                  <span className="text-slate-500">
                    {(c.session_engagement_score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
              {filteredConvos.length === 0 && (
                <p className="text-[0.72rem] text-slate-500">
                  No sessions yet.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Optional: detailed conversation view below, if one is opened */}
      {activeConversation && (
        <div className="mt-6 axon-card-subtle p-4 sm:p-5">
          <ConversationThread
            conversationId={activeConversation}
            onClose={() => setActiveConversation(null)}
          />
        </div>
      )}
    </DashboardShell>
  );
}
