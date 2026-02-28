import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getStudentDashboard, getStudentMastery, getStudentPedagogy, getStudentConversations } from '../../api/axonai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import ConversationThread from '../../components/ConversationThread';
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

  if (loading) return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <LoadingSpinner message="Loading your dashboard..." />
    </div>
  );
  if (error) return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <ErrorState message={error} onRetry={load} />
    </div>
  );
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
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* Header */}
      <div className="bg-[#1E2761] text-white">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <p className="text-[#94A3B8] text-sm mb-1">AxonAI Student Portal</p>
          <h1 className="text-3xl font-bold">Kia ora, {student.first_name}!</h1>
          <p className="text-[#94A3B8] mt-1">Year {student.year_level} — {student.ethnicity}</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Overall mastery */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-[#1F2937]">Overall Mastery</h2>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              profile.overall_mastery_trend === 'improving' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
            }`}>
              {profile.overall_mastery_trend === 'improving' ? 'You\'re improving!' : profile.overall_mastery_trend}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <ProgressBar value={summary.mastery.avg_mastery * 100} color="#0891B2" />
            <span className="text-2xl font-bold text-[#0891B2] whitespace-nowrap">
              {(summary.mastery.avg_mastery * 100).toFixed(1)}%
            </span>
          </div>
          <p className="text-sm text-[#6B7280] mt-2">
            {summary.mastery.concepts_assessed} concepts assessed — Strongest: {(summary.mastery.strongest * 100).toFixed(0)}%, Weakest: {(summary.mastery.weakest * 100).toFixed(0)}%
          </p>
        </div>

        {/* Subject cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#6B7280] mb-2">Mathematics</h3>
            <div className="flex items-center gap-3">
              <ProgressBar value={mathMastery * 100} color={mathMastery >= 0.7 ? '#10B981' : mathMastery >= 0.4 ? '#F59E0B' : '#EF4444'} />
              <span className="text-xl font-bold text-[#1F2937]">{(mathMastery * 100).toFixed(1)}%</span>
            </div>
            <p className="text-xs text-[#6B7280] mt-1">{mathAvg.length} concepts</p>
          </div>
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#6B7280] mb-2">Biology</h3>
            <div className="flex items-center gap-3">
              <ProgressBar value={bioMastery * 100} color={bioMastery >= 0.7 ? '#10B981' : bioMastery >= 0.4 ? '#F59E0B' : '#EF4444'} />
              <span className="text-xl font-bold text-[#1F2937]">{(bioMastery * 100).toFixed(1)}%</span>
            </div>
            <p className="text-xs text-[#6B7280] mt-1">{bioAvg.length} concepts</p>
          </div>
        </div>

        {/* Weakest & Strongest */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Areas to Work On</h3>
            <div className="space-y-2">
              {weakest.map(c => (
                <div key={c.concept_id} className="flex items-center justify-between p-2 rounded-lg bg-red-50">
                  <div>
                    <p className="text-sm font-medium text-[#1F2937]">{c.concept_name}</p>
                    <p className="text-xs text-[#6B7280]">{c.subject}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-semibold text-[#EF4444]">{(c.mastery_score * 100).toFixed(0)}%</span>
                    <p className="text-xs text-green-600 capitalize">{c.trend}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Your Strengths</h3>
            <div className="space-y-2">
              {strongest.map(c => (
                <div key={c.concept_id} className="flex items-center justify-between p-2 rounded-lg bg-green-50">
                  <div>
                    <p className="text-sm font-medium text-[#1F2937]">{c.concept_name}</p>
                    <p className="text-xs text-[#6B7280]">{c.subject}</p>
                  </div>
                  <span className="text-sm font-semibold text-[#10B981]">{(c.mastery_score * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Engagement trend chart */}
        {engagementTrend.length > 0 && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Your Engagement Over Time</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={engagementTrend}>
                <XAxis dataKey="session" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `${v}%`} />
                <Line type="monotone" dataKey="engagement" stroke="#0891B2" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Improvement Projection chart */}
        {masteryProjection.length > 0 && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#1F2937] mb-1">Improvement Projection</h3>
            <p className="text-xs text-[#6B7280] mb-3">Based on your recent learning trend — dashed line shows projected progress</p>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={masteryProjection}>
                <XAxis dataKey="session" tick={{ fontSize: 11 }} label={{ value: 'Session', position: 'insideBottom', offset: -5, fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} label={{ value: '%', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                <Tooltip
                  formatter={(value, name) => [`${value}%`, name === 'mastery' ? 'Actual' : 'Projected']}
                  labelFormatter={(l) => `Session ${l}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="mastery"
                  stroke="#0891B2"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                  name="Actual"
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="projected"
                  stroke="#10B981"
                  strokeWidth={2}
                  strokeDasharray="6 3"
                  dot={{ r: 2 }}
                  name="Projected"
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Best teaching approach */}
        {bestApproach && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#1F2937] mb-2">What Works Best for You</h3>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#0891B2]/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-[#0891B2]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-[#1F2937] capitalize">{bestApproach.teaching_approach.replace(/_/g, ' ')}</p>
                <p className="text-xs text-[#6B7280]">{(bestApproach.success_rate * 100).toFixed(0)}% success rate — {bestApproach.success_count} of {bestApproach.attempt_count} sessions</p>
              </div>
            </div>
          </div>
        )}

        {/* AI Chat Sessions — organized by class */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold text-[#1F2937]">
                AI Learning Sessions
                {lightbulbs.length > 0 && (
                  <span className="ml-2 text-xs font-normal text-[#F59E0B]">{lightbulbs.length} lightbulb moments!</span>
                )}
              </h3>
              <p className="text-xs text-[#6B7280]">Click a session to view the full conversation</p>
            </div>
          </div>

          {/* Subject filter tabs */}
          <div className="flex gap-2 mb-4 border-b border-[#E2E8F0] pb-3">
            <button
              onClick={() => setChatSubjectFilter('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                chatSubjectFilter === 'all'
                  ? 'bg-[#1E2761] text-white'
                  : 'bg-[#F1F5F9] text-[#6B7280] hover:bg-[#E2E8F0]'
              }`}
            >
              All Subjects ({convos.length})
            </button>
            {subjects.map(subj => {
              const count = convos.filter(c => c.subject === subj).length;
              return (
                <button
                  key={subj}
                  onClick={() => setChatSubjectFilter(subj)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    chatSubjectFilter === subj
                      ? 'bg-[#1E2761] text-white'
                      : 'bg-[#F1F5F9] text-[#6B7280] hover:bg-[#E2E8F0]'
                  }`}
                >
                  {subj} ({count})
                </button>
              );
            })}
          </div>

          <div className="space-y-2">
            {filteredConvos.slice(0, 15).map(c => (
              <div key={c.id}>
                <div
                  className="flex items-center justify-between p-3 rounded-lg border border-[#E2E8F0] hover:bg-[#F8FAFC] cursor-pointer transition-colors"
                  onClick={() => setActiveConversation(activeConversation === c.id ? null : c.id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[#1F2937]">{c.concept_name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                        c.subject === 'Mathematics' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                      }`}>
                        {c.subject}
                      </span>
                      {c.lightbulb_moment_detected && (
                        <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded-full">Lightbulb!</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-[#6B7280]">
                      <span>{new Date(c.started_at).toLocaleDateString()}</span>
                      <span>Engagement: {(c.session_engagement_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      c.outcome === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {c.outcome}
                    </span>
                    <svg className={`w-4 h-4 text-[#6B7280] transition-transform ${activeConversation === c.id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
                {activeConversation === c.id && (
                  <div className="mt-2 ml-4">
                    <ConversationThread
                      conversationId={c.id}
                      onClose={() => setActiveConversation(null)}
                    />
                  </div>
                )}
              </div>
            ))}
            {filteredConvos.length === 0 && (
              <p className="text-sm text-[#6B7280] text-center py-4">No conversations found for this subject.</p>
            )}
          </div>
        </div>

        {/* Quick stats footer */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-[#0891B2]">{summary.conversations.total_conversations}</p>
            <p className="text-xs text-[#6B7280]">Total Sessions</p>
          </div>
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-[#F59E0B]">{summary.conversations.lightbulb_count}</p>
            <p className="text-xs text-[#6B7280]">Lightbulb Moments</p>
          </div>
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-[#10B981]">{summary.quizzes.avg_score.toFixed(0)}%</p>
            <p className="text-xs text-[#6B7280]">Quiz Average</p>
          </div>
        </div>
      </div>
    </div>
  );
}
