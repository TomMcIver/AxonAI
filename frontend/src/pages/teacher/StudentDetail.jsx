import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  getStudentConversations,
  getStudentDashboard,
  getStudentFlags,
  getStudentInsights,
  getStudentMastery,
  getStudentPedagogy,
  getStudentPredictions,
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

function trendTone(trend) {
  if (!trend) return { pill: 'axon-pill', label: null };
  const t = trend.toLowerCase();
  if (t === 'improving') return { pill: 'axon-pill-success', label: '↑ Improving' };
  if (t === 'declining') return { pill: 'axon-pill-danger', label: '↓ Declining' };
  return { pill: 'axon-pill', label: '→ Stable' };
}

function pct(v) {
  return `${Math.round(clamp01(v) * 100)}%`;
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-3 text-sm">
      <span className="text-slate-400 shrink-0">{label}</span>
      <span className={`text-right ${value ? 'text-slate-100' : 'text-slate-600'}`}>
        {value || '—'}
      </span>
    </div>
  );
}

export default function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [flags, setFlags] = useState(null);
  const [conversations, setConversations] = useState(null);
  const [pedagogy, setPedagogy] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [insights, setInsights] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
      getStudentPedagogy(id).catch(() => null),
      getStudentPredictions(id).catch(() => null),
      getStudentInsights(id).catch(() => null),
    ])
      .then(([d, m, f, c, p, pr, ins]) => {
        setDashboard(d);
        setMastery(m);
        setFlags(f);
        setConversations(c);
        setPedagogy(p);
        setPredictions(pr);
        setInsights(ins);
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
  const trend = trendTone(profile?.overall_mastery_trend);

  // Flatten arrays from student profile
  const interestsList = Array.isArray(student?.interests)
    ? student.interests.join(', ')
    : student?.interests || null;
  const activitiesList = Array.isArray(student?.extracurricular_activities)
    ? student.extracurricular_activities.join(', ')
    : student?.extracurricular_activities || null;

  // Pedagogy data
  const strategies = pedagogy?.recommended_strategies || pedagogy?.strategies || [];
  const pedagogyNotes = pedagogy?.notes || pedagogy?.summary || null;

  // Predictions data
  const predRisk = predictions?.risk_score ?? predictions?.predicted_risk ?? null;
  const predGrade = predictions?.predicted_grade ?? predictions?.predicted_final_grade ?? null;
  const predConfidence = predictions?.confidence ?? predictions?.confidence_level ?? null;
  const riskFactors = predictions?.risk_factors || [];
  const improvementAreas = predictions?.improvement_areas || [];

  // AI Insights data — from TeacherAIInsight via /student/:id/insights
  const aiSummary = insights?.summary || insights?.ai_summary || insights?.narrative || null;
  const insightType = insights?.insight_type || null;
  const suggestedInterventions = insights?.suggested_interventions || [];
  const successfulStrategies = insights?.successful_strategies || [];
  const failedStrategies = insights?.failed_strategies || [];
  const generatedAt = insights?.generated_at || null;

  return (
    <DashboardShell subtitle="Student · detail">
      <div className="space-y-5">
        {/* ── Navigation ── */}
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

        {/* ── Student Header ── */}
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
                {trend.label && (
                  <span className={`axon-pill ${trend.pill}`}>{trend.label}</span>
                )}
                <span className="axon-pill">
                  Attendance {wellbeing?.attendance_percentage?.toFixed?.(0) ?? wellbeing?.attendance_percentage ?? '—'}%
                </span>
                <span className="axon-pill">
                  {summary?.active_flags ?? 0} flags
                </span>
                {student?.learning_style && (
                  <span className="axon-pill">{student.learning_style} learner</span>
                )}
                {student?.learning_difficulty && (
                  <span className="axon-pill axon-pill-soft">{student.learning_difficulty}</span>
                )}
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
                {predGrade != null && (
                  <div className="flex items-center justify-between text-sm border-t border-slate-700 pt-2 mt-2">
                    <span className="text-slate-400">Predicted grade</span>
                    <span className="text-sky-300 font-medium">
                      {typeof predGrade === 'number' ? `${Math.round(predGrade)}%` : predGrade}
                      {predConfidence != null && (
                        <span className="text-slate-500 text-xs ml-1">
                          ({Math.round(clamp01(predConfidence) * 100)}% conf.)
                        </span>
                      )}
                    </span>
                  </div>
                )}
                {predRisk != null && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Predicted risk</span>
                    <span className={`font-medium text-sm ${clamp01(predRisk) >= 0.4 ? 'text-rose-400' : clamp01(predRisk) >= 0.2 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {pct(predRisk)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Student Profile Info ── */}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm font-semibold text-slate-100 mb-3">Student profile</p>
          <div className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
            <InfoRow label="Learning style" value={student?.learning_style} />
            <InfoRow label="Preferred difficulty" value={student?.preferred_difficulty} />
            <InfoRow label="Learning difficulty" value={student?.learning_difficulty} />
            <InfoRow label="Primary language" value={student?.primary_language} />
            <InfoRow label="Secondary language" value={student?.secondary_language} />
            <InfoRow label="Academic goals" value={student?.academic_goals} />
            <InfoRow label="Interests" value={interestsList} />
            <InfoRow label="Activities" value={activitiesList} />
          </div>
          {student?.major_life_event && (
            <div className="flex items-start gap-3 text-sm rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 mt-3">
              <span className="text-amber-400 shrink-0">⚠ Life event</span>
              <span className="text-slate-200">{student.major_life_event}</span>
            </div>
          )}
        </div>

        {/* ── AI Summary ── */}
        <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
          {(aiSummary || suggestedInterventions.length > 0 || successfulStrategies.length > 0 || failedStrategies.length > 0) ? (<>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-100">AI summary</p>
                {insightType && (
                  <span className={`axon-pill text-[0.7rem] mt-1 inline-block ${
                    insightType === 'at_risk' ? 'axon-pill-danger'
                    : insightType === 'improving' ? 'axon-pill-success'
                    : 'axon-pill-soft'
                  }`}>
                    {insightType.replace(/_/g, ' ')}
                  </span>
                )}
              </div>
              {generatedAt && (
                <p className="text-[0.65rem] text-slate-600 shrink-0 mt-0.5">
                  Generated {new Date(generatedAt).toLocaleDateString()}
                </p>
              )}
            </div>

            {aiSummary && (
              <p className="text-sm text-slate-300 leading-relaxed">{aiSummary}</p>
            )}

            {suggestedInterventions.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
                  Suggested interventions
                </p>
                <ul className="space-y-1.5">
                  {suggestedInterventions.map((item, i) => {
                    const text = typeof item === 'string' ? item : (item.action || item.description || JSON.stringify(item));
                    return (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                        <span className="text-sky-400 mt-0.5 shrink-0">→</span>
                        {text}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {(successfulStrategies.length > 0 || failedStrategies.length > 0) && (
              <div className="grid gap-3 sm:grid-cols-2 pt-1 border-t border-slate-800">
                {successfulStrategies.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-emerald-500 mb-1.5">What's working</p>
                    <ul className="space-y-1">
                      {successfulStrategies.map((s, i) => {
                        const text = typeof s === 'string' ? s : (s.strategy || s.name || JSON.stringify(s));
                        return (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                            <span className="text-emerald-400 mt-0.5 shrink-0">✓</span>
                            {text}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
                {failedStrategies.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-rose-500 mb-1.5">What hasn't worked</p>
                    <ul className="space-y-1">
                      {failedStrategies.map((s, i) => {
                        const text = typeof s === 'string' ? s : (s.strategy || s.name || JSON.stringify(s));
                        return (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                            <span className="text-rose-400 mt-0.5 shrink-0">✗</span>
                            {text}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
          </>) : (
            <div className="text-center py-4">
              <p className="text-sm font-semibold text-slate-100 mb-1">AI summary</p>
              <p className="text-xs text-slate-500">No AI insights generated for this student yet.</p>
            </div>
          )}
        </div>

        {/* ── Main Grid: Focus Concepts + Flags + Sessions ── */}
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

        {/* ── Pedagogy Recommendations ── */}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm font-semibold text-slate-100 mb-3">Teaching recommendations</p>
          {(strategies.length > 0 || pedagogyNotes) ? (
            <>
              {pedagogyNotes && (
                <p className="text-xs text-slate-400 mb-3">{pedagogyNotes}</p>
              )}
              {strategies.length > 0 && (
                <div className="grid gap-2 sm:grid-cols-2">
                  {strategies.map((s, i) => {
                    const name = typeof s === 'string' ? s : (s.name || s.strategy || JSON.stringify(s));
                    const desc = typeof s === 'object' ? (s.description || s.detail || null) : null;
                    return (
                      <div
                        key={i}
                        className="rounded-lg border border-sky-500/20 bg-sky-500/5 px-3 py-2"
                      >
                        <p className="text-xs font-medium text-sky-200">{name}</p>
                        {desc && <p className="text-[0.7rem] text-slate-400 mt-0.5">{desc}</p>}
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <p className="text-xs text-slate-500">No teaching recommendations available yet.</p>
          )}
        </div>

        {/* ── Predictions: Risk Factors & Improvement Areas ── */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="axon-card-subtle p-5 sm:p-6">
            <p className="text-sm font-semibold text-slate-100 mb-2">Risk factors</p>
            {riskFactors.length > 0 ? (
              <ul className="space-y-1">
                {riskFactors.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="text-rose-400 mt-0.5 shrink-0">•</span>
                    {typeof f === 'string' ? f : JSON.stringify(f)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">No risk factors identified.</p>
            )}
          </div>
          <div className="axon-card-subtle p-5 sm:p-6">
            <p className="text-sm font-semibold text-slate-100 mb-2">Improvement areas</p>
            {improvementAreas.length > 0 ? (
              <ul className="space-y-1">
                {improvementAreas.map((a, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="text-emerald-400 mt-0.5 shrink-0">•</span>
                    {typeof a === 'string' ? a : JSON.stringify(a)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">No improvement areas identified.</p>
            )}
          </div>
        </div>

        {/* ── Conversation Thread ── */}
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
