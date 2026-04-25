import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import {
  getStudentDashboard,
  getStudentMastery,
  getStudentPedagogy,
  getStudentConversations,
  getStudentFlags,
} from '../../api/axonai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import ConversationThread from '../../components/ConversationThread';
import DashboardShell from '../../components/DashboardShell';
import { useTimedProgress } from '../../hooks/useTimedProgress';

const DASH_FILL_MS = 4200;
/** Demo: Aroha Ngata */
const STUDENT_ID = 1;

const SUBJECTS = ['Mathematics', 'Biology'];

const TEAL = '#0F766E';

function normMastery(x) {
  const v = typeof x === 'number' && x > 1 ? x / 100 : x;
  return (typeof v === 'number' && !Number.isNaN(v) ? v : 0) || 0;
}

function masteryPct(raw) {
  return Math.round(normMastery(raw) * 1000) / 10;
}

function barFillForPct(pct) {
  if (pct > 60) return TEAL;
  if (pct >= 40) return '#d97706';
  return '#e11d48';
}

function formatFocusType(flagType) {
  if (!flagType) return '';
  const spaced = String(flagType).replace(/_/g, ' ');
  return spaced.replace(/\b\w/g, (ch) => ch.toUpperCase());
}

function focusCardClass(flagType) {
  switch (flagType) {
    case 'stuck_on_concept':
      return 'border-rose-300/70 bg-rose-50/40';
    case 'low_engagement':
      return 'border-amber-300/70 bg-amber-50/40';
    default:
      return 'border-slate-300/60 bg-slate-50/50';
  }
}

function normalizeTrend(raw) {
  const t = (raw || '').toLowerCase();
  if (t === 'degrading') return 'declining';
  return t;
}

export default function StudentDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [flagsPayload, setFlagsPayload] = useState(null);
  const [conversations, setConversations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [barEpoch, setBarEpoch] = useState(0);
  const progress = useTimedProgress(DASH_FILL_MS, barEpoch);
  const [activeConversation, setActiveConversation] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getStudentDashboard(STUDENT_ID),
      getStudentMastery(STUDENT_ID),
      getStudentPedagogy(STUDENT_ID),
      getStudentFlags(STUDENT_ID),
      getStudentConversations(STUDENT_ID, 500),
    ])
      .then(([d, m, _pedagogy, fl, c]) => {
        setDashboard(d);
        setMastery(m);
        setFlagsPayload(fl);
        setConversations(c);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const subjectAverages = useMemo(() => {
    const concepts = mastery?.concepts || [];
    return SUBJECTS.map((subject) => {
      const rows = concepts.filter((c) => c.subject === subject);
      const pct = rows.length
        ? rows.reduce((s, c) => s + normMastery(c.mastery_score), 0) / rows.length
        : 0;
      return { subject, pct: pct * 100, count: rows.length };
    });
  }, [mastery]);

  const weakestFive = useMemo(() => {
    const concepts = mastery?.concepts || [];
    return concepts.slice(0, 5);
  }, [mastery]);

  const engagementChartData = useMemo(() => {
    const list = conversations?.conversations || [];
    const last10 = list.slice(0, 10);
    const chronological = [...last10].reverse();
    return chronological.map((c, i) => ({
      i,
      engagement: (c.session_engagement_score ?? 0) * 100,
    }));
  }, [conversations]);

  const recentFive = useMemo(() => {
    const list = conversations?.conversations || [];
    return list.slice(0, 5);
  }, [conversations]);

  const dataReady = Boolean(dashboard) && !loading;
  const barComplete = progress >= 99.9;
  const showMain = dataReady && barComplete;
  const waitingOnApi = progress >= 99.9 && !dataReady && !error;

  if (error) {
    return (
      <DashboardShell subtitle="Student view">
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
      <DashboardShell subtitle="Student view">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner
            message={
              waitingOnApi
                ? 'Still loading…'
                : dataReady
                  ? 'Preparing your dashboard…'
                  : 'Loading your dashboard...'
            }
            progress={progress}
          />
        </div>
      </DashboardShell>
    );
  }

  if (!dashboard) {
    return (
      <DashboardShell subtitle="Student view">
        <div className="flex items-center justify-center py-16">
          <ErrorState message="No dashboard data was returned. Check the API or student id." onRetry={load} />
        </div>
      </DashboardShell>
    );
  }

  const { student, profile = {}, summary = {} } = dashboard;
  const trendKey = normalizeTrend(profile?.overall_mastery_trend);
  /** Prefer server-reported AI conversation totals; otherwise use conversations payload (capped by fetch limit). */
  const aiChatCount =
    summary?.conversations?.total_conversations ??
    conversations?.total ??
    conversations?.total_count ??
    conversations?.count ??
    (conversations?.conversations?.length ?? 0);
  const lightbulbMoments =
    summary.lightbulb_moments ??
    summary?.conversations?.lightbulb_count ??
    summary?.lightbulb_count ??
    0;

  const focusRows = (flagsPayload?.flags || []).slice(0, 6);

  return (
    <DashboardShell subtitle={`Student · ${student.first_name}'s overview`}>
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Section 1: Mastery and Progress */}
        <section className="axon-card-subtle p-5 sm:p-6 space-y-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <h2 className="axon-h2 text-base sm:text-lg text-slate-800">Your progress</h2>
            <div className="flex flex-wrap gap-2">
              {SUBJECTS.map((s) => (
                <span
                  key={s}
                  className="axon-pill text-[0.65rem] tracking-wide text-slate-600 border border-slate-200/80 bg-white/70"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
          <p className="text-sm text-slate-600">
            Kia ora, <span className="font-medium text-slate-800">{student.first_name}</span>
          </p>

          <div className="space-y-5">
            {subjectAverages.map(({ subject, pct, count }) => (
              <div key={subject} className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-slate-700">{subject}</span>
                  <span className="text-lg font-semibold tabular-nums" style={{ color: TEAL }}>
                    {pct.toFixed(0)}%
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, Math.max(0, pct))}%`,
                      backgroundColor: barFillForPct(pct),
                    }}
                  />
                </div>
                <p className="text-[0.7rem] text-slate-400">{count} concepts tracked</p>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-200/60 pt-4 space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Weakest areas</p>
            <div className="space-y-3">
              {weakestFive.map((c) => {
                const pct = masteryPct(c.mastery_score);
                return (
                  <div key={c.concept_id ?? c.concept_name} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm text-slate-800">{c.concept_name}</span>
                      <span className="text-xs font-medium tabular-nums text-slate-600">{pct.toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.min(100, Math.max(0, pct))}%`,
                          backgroundColor: barFillForPct(pct),
                        }}
                      />
                    </div>
                  </div>
                );
              })}
              {weakestFive.length === 0 && (
                <p className="text-sm text-slate-500">No mastery data yet, your journey starts here.</p>
              )}
            </div>
          </div>
        </section>

        {/* Section 2: Learning Trend */}
        <section className="axon-card-subtle p-5 sm:p-6 space-y-4">
          <h2 className="axon-h2 text-base sm:text-lg text-slate-800">Your momentum</h2>

          {trendKey === 'improving' && (
            <div className="flex items-center gap-2 text-emerald-700">
              <TrendingUp className="h-5 w-5 shrink-0" aria-hidden />
              <span className="text-sm font-medium">On a roll 🔥</span>
            </div>
          )}
          {trendKey === 'declining' && (
            <div className="flex items-center gap-2 text-amber-700">
              <TrendingDown className="h-5 w-5 shrink-0" aria-hidden />
              <span className="text-sm font-medium">Needs focus</span>
            </div>
          )}
          {trendKey !== 'improving' && trendKey !== 'declining' && (
            <div className="flex items-center gap-2 text-slate-600">
              <Minus className="h-5 w-5 shrink-0" aria-hidden />
              <span className="text-sm font-medium">Holding steady</span>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-xs font-medium text-slate-700">
              {aiChatCount} AI chats
            </span>
            <span className="inline-flex items-center rounded-full border border-amber-200/80 bg-amber-50/80 px-3 py-1 text-xs font-medium text-amber-900/90">
              {lightbulbMoments} lightbulb moments 💡
            </span>
          </div>

          <div className="h-44 w-full min-w-0 pt-2">
            {engagementChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={engagementChartData} margin={{ top: 4, right: 8, left: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="i" hide />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 10, fill: '#64748b' }}
                    tickLine={false}
                    axisLine={{ stroke: '#cbd5e1' }}
                    label={{
                      value: 'Engagement %',
                      angle: -90,
                      position: 'insideLeft',
                      offset: 4,
                      style: { fontSize: 11, fill: '#64748b' },
                    }}
                  />
                  <Tooltip
                    formatter={(v) => [`${Number(v).toFixed(0)}%`, 'Engagement']}
                    labelFormatter={() => ''}
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="engagement"
                    stroke={TEAL}
                    strokeWidth={2}
                    dot={{ r: 3, fill: TEAL, strokeWidth: 0 }}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-500">Not enough sessions yet for a trend line.</p>
            )}
          </div>
        </section>

        {/* Section 3: Focus Areas */}
        <section className="axon-card-subtle p-5 sm:p-6 space-y-4">
          <h2 className="axon-h2 text-base sm:text-lg text-slate-800">Where to focus</h2>
          <p className="text-xs text-slate-500">Areas that need attention from your recent work.</p>
          <div className="space-y-2">
            {focusRows.map((f) => (
              <div
                key={f.id ?? `${f.concept_name}-${f.flag_type}`}
                className={`rounded-lg border px-3 py-2.5 ${focusCardClass(f.flag_type)}`}
              >
                <p className="text-sm font-medium text-slate-800">{f.concept_name}</p>
                <p className="text-[0.72rem] text-slate-600 mt-0.5">{formatFocusType(f.flag_type)}</p>
              </div>
            ))}
            {focusRows.length === 0 && (
              <p className="rounded-lg border border-emerald-200/60 bg-emerald-50/40 px-3 py-3 text-sm text-slate-700">
                All clear, keep it up! ✅
              </p>
            )}
          </div>
        </section>

        {/* Section 4: Recent Sessions */}
        <section className="axon-card-subtle p-5 sm:p-6 space-y-3">
          <h2 className="axon-h2 text-base sm:text-lg text-slate-800">Recent AI sessions</h2>
          <p className="text-xs text-slate-500">Tap a row to read the full conversation.</p>
          <div className="space-y-2">
            {recentFive.map((c) => {
              const open = activeConversation === c.id;
              const engPct = ((c.session_engagement_score ?? 0) * 100).toFixed(0);
              return (
                <div key={c.id} className="space-y-0">
                  <button
                    type="button"
                    className={`flex w-full items-center justify-between gap-2 rounded-lg border px-3 py-2.5 text-left text-sm transition-colors ${
                      open
                        ? 'border-teal-400/80 bg-teal-50/70 ring-1 ring-teal-200/60'
                        : 'border-slate-200 bg-white/50 hover:bg-white/80'
                    }`}
                    onClick={() => setActiveConversation(open ? null : c.id)}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block font-medium text-slate-800 truncate">{c.concept_name}</span>
                      <span className="block text-[0.7rem] text-slate-500">{c.subject}</span>
                    </span>
                    <span className="flex shrink-0 items-center gap-2">
                      {c.lightbulb_moment_detected || c.lightbulb_moment ? (
                        <span className="text-base" aria-label="Lightbulb moment">
                          💡
                        </span>
                      ) : null}
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                        {engPct}%
                      </span>
                    </span>
                  </button>
                  {open && (
                    <div className="mt-2 overflow-hidden rounded-lg border border-[#2c2418]/25 bg-[#fffef4]/90">
                      <ConversationThread
                        conversationId={c.id}
                        studentId={STUDENT_ID}
                        variant="inline"
                        onClose={() => setActiveConversation(null)}
                      />
                    </div>
                  )}
                </div>
              );
            })}
            {recentFive.length === 0 && (
              <p className="text-sm text-slate-500">No sessions yet, chat with the tutor to get started.</p>
            )}
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
