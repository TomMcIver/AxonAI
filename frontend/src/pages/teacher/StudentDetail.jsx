import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  getStudentConversations,
  getStudentDashboard,
  getStudentFlags,
  getStudentMastery,
  getStudentPedagogy,
  getStudentPredictions,
  getTeacherAIInsights,
  getStudentWellbeing,
  getPedagogicalMemory,
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

function formatApproachName(s) {
  if (!s) return '';
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function flagBorderStyle(flagType) {
  switch (flagType) {
    case 'at_risk': return 'border-rose-300/40 bg-rose-50/60';
    case 'stuck': return 'border-amber-300/40 bg-amber-50/60';
    case 'prerequisite_gap': return 'border-amber-300/40 bg-amber-50/60';
    case 'needs_quiz': return 'border-sky-300/40 bg-sky-50/60';
    case 'mastered': return 'border-emerald-300/40 bg-emerald-50/60';
    default: return 'border-rose-300/40 bg-rose-50/60';
  }
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-3 text-sm">
      <span className="text-slate-400 shrink-0">{label}</span>
      <span className={`text-right ${value ? 'text-slate-700' : 'text-slate-600'}`}>
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
  const [aiInsights, setAiInsights] = useState(null);
  const [wellbeingCtx, setWellbeingCtx] = useState(null);
  const [pedagogicalMemory, setPedagogicalMemory] = useState(null);
  const [expandedConversations, setExpandedConversations] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Toggle expanded state for a conversation
  const toggleConversation = (conversationId) => {
    setExpandedConversations(prev => {
      const next = new Set(prev);
      if (next.has(conversationId)) {
        next.delete(conversationId);
      } else {
        next.add(conversationId);
      }
      return next;
    });
  };

  const focusConcepts = useMemo(() => {
    const cs = mastery?.concepts || [];
    return [...cs]
      .sort((a, b) => (a.mastery_score ?? 0) - (b.mastery_score ?? 0))
      .slice(0, 5);
  }, [mastery]);

  const recentConvos = useMemo(() => {
    return (conversations?.conversations || []).slice(0, 6);
  }, [conversations]);

  // Predicted concept mastery map from model_predictions (prediction_type = 'concept_mastery')
  const conceptMasteryPredMap = useMemo(() => {
    if (!predictions) return {};
    const extract = (val) => {
      if (!val) return {};
      if (typeof val === 'string') { try { return JSON.parse(val); } catch { return {}; } }
      return typeof val === 'object' && !Array.isArray(val) ? val : {};
    };
    // Array of prediction objects
    if (Array.isArray(predictions)) {
      const cm = predictions.find(p => p.prediction_type === 'concept_mastery');
      return extract(cm?.prediction_value);
    }
    // predictions.predictions array
    if (Array.isArray(predictions.predictions)) {
      const cm = predictions.predictions.find(p => p.prediction_type === 'concept_mastery');
      return extract(cm?.prediction_value);
    }
    // Flat object with concept_mastery key
    if (predictions.concept_mastery) return extract(predictions.concept_mastery);
    return {};
  }, [predictions]);

  // Sorted pedagogical memory approaches
  const sortedApproaches = useMemo(() => {
    const list = Array.isArray(pedagogicalMemory)
      ? pedagogicalMemory
      : (pedagogicalMemory?.approaches || pedagogicalMemory?.records || []);
    return [...list].sort((a, b) => (b.success_rate ?? 0) - (a.success_rate ?? 0));
  }, [pedagogicalMemory]);

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
      getTeacherAIInsights(id).catch(() => null),
      getStudentWellbeing(id).catch(() => null),
      getPedagogicalMemory(id).catch(() => null),
    ])
      .then(([d, m, f, c, p, pr, ai, wb, pm]) => {
        setDashboard(d);
        setMastery(m);
        setFlags(f);
        setConversations(c);
        setPedagogy(p);
        setPredictions(pr);
        setAiInsights(ai);
        setWellbeingCtx(wb);
        setPedagogicalMemory(pm);
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

  // Profile-mapped fields — new schema stores these in profile/wellbeing, not student
  const learningStyle = profile?.dominant_learning_style || student?.learning_style || null;
  const learningDifficulty = wellbeing?.has_learning_support_plan
    ? (wellbeing?.learning_support_details || 'Learning support plan active')
    : (student?.learning_difficulty || null);
  const primaryLanguage = student?.primary_language || 'English';
  const academicGoals = student?.academic_goals || 'NCEA Level 2';
  // Interests/activities not present in new schema — use legacy field if available
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

  // AI Insights data — from TeacherAIInsight via /student/:id/ai-insights
  const aiSummary = aiInsights?.insights?.student_summary || null;
  const insightType = null;
  const suggestedInterventions = [];
  const successfulStrategies = [];
  const failedStrategies = [];
  const generatedAt = aiInsights?.insights?.generated_at || null;

  // Wellbeing context pills — prefer new endpoint, fall back to dashboard wellbeing
  const wbData = wellbeingCtx || wellbeing;
  const showIEP = !!(wbData?.has_learning_support_plan);
  const showPastoral = !!(wbData?.home_situation_flag);
  const showESOL = !!(wbData?.is_esol);

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
              <h1 className="axon-h2 text-lg sm:text-xl text-slate-800">
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
                {learningStyle && (
                  <span className="axon-pill">{learningStyle} learner</span>
                )}
                {learningDifficulty && (
                  <span className="axon-pill axon-pill-soft">{learningDifficulty}</span>
                )}
                {showIEP && (
                  <span className="axon-pill axon-pill-soft">IEP</span>
                )}
                {showPastoral && (
                  <span className="axon-pill axon-pill-soft">Pastoral</span>
                )}
                {showESOL && (
                  <span className="axon-pill" style={{ color: '#0369a1', borderColor: 'rgba(14,165,233,0.3)' }}>ESOL</span>
                )}
              </div>
            </div>

            <div className="axon-card-ghost p-4 min-w-[240px]">
              <p className="axon-label mb-2">At a glance</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Avg mastery</span>
                  <span className="text-slate-700 font-medium">
                    {pct(summary?.mastery?.avg_mastery)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Engagement</span>
                  <span className="text-slate-700 font-medium">
                    {pct(profile?.overall_engagement_score)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Conversations</span>
                  <span className="text-slate-700 font-medium">
                    {summary?.conversations?.total_conversations ?? 0}
                  </span>
                </div>
                {predGrade != null && (
                  <div className="flex items-center justify-between text-sm border-t border-slate-200 pt-2 mt-2">
                    <span className="text-slate-400">Predicted grade</span>
                    <span className="text-sky-600 font-medium">
                      {typeof predGrade === 'number' ? `${Math.round(predGrade)}%` : predGrade}
                      {predConfidence != null && (
                        <span className="text-slate-8000 text-xs ml-1">
                          ({Math.round(clamp01(predConfidence) * 100)}% conf.)
                        </span>
                      )}
                    </span>
                  </div>
                )}
                {predRisk != null && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Predicted risk</span>
                    <span className={`font-medium text-sm ${clamp01(predRisk) >= 0.4 ? 'text-rose-600' : clamp01(predRisk) >= 0.2 ? 'text-amber-600' : 'text-emerald-600'}`}>
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
          <p className="text-sm font-semibold text-slate-700 mb-3">Student profile</p>
          <div className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
            <InfoRow label="Learning style" value={learningStyle} />
            <InfoRow label="Primary language" value={primaryLanguage} />
            <InfoRow label="Learning difficulty" value={learningDifficulty} />
            <InfoRow label="Academic goals" value={academicGoals} />
            {interestsList && <InfoRow label="Interests" value={interestsList} />}
            {activitiesList && <InfoRow label="Activities" value={activitiesList} />}
          </div>
          {student?.major_life_event && (
            <div className="flex items-start gap-3 text-sm rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 mt-3">
              <span className="text-amber-600 shrink-0">⚠ Life event</span>
              <span className="text-slate-700">{student.major_life_event}</span>
            </div>
          )}
        </div>

        {/* ── AI Summary ── */}
        <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
          {(aiSummary || suggestedInterventions.length > 0 || successfulStrategies.length > 0 || failedStrategies.length > 0) ? (<>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-700">AI summary</p>
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
              <p className="text-sm text-slate-600 leading-relaxed">{aiSummary}</p>
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
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                        <span className="text-teal-600 mt-0.5 shrink-0">→</span>
                        {text}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {(successfulStrategies.length > 0 || failedStrategies.length > 0) && (
              <div className="grid gap-3 sm:grid-cols-2 pt-1 border-t border-slate-200">
                {successfulStrategies.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-emerald-600 mb-1.5">What's working</p>
                    <ul className="space-y-1">
                      {successfulStrategies.map((s, i) => {
                        const text = typeof s === 'string' ? s : (s.strategy || s.name || JSON.stringify(s));
                        return (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                            <span className="text-emerald-600 mt-0.5 shrink-0">✓</span>
                            {text}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
                {failedStrategies.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-rose-600 mb-1.5">What hasn't worked</p>
                    <ul className="space-y-1">
                      {failedStrategies.map((s, i) => {
                        const text = typeof s === 'string' ? s : (s.strategy || s.name || JSON.stringify(s));
                        return (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                            <span className="text-rose-600 mt-0.5 shrink-0">✗</span>
                            {text}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </>) : (
            <div className="text-center py-4">
              <p className="text-sm font-semibold text-slate-700 mb-1">AI summary</p>
              <p className="text-xs text-slate-8000">No AI insights generated for this student yet.</p>
            </div>
          )}
        </div>

        {/* ── Main Grid: Focus Concepts + Flags + Sessions ── */}
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
          <div className="axon-card-subtle p-5 sm:p-6">
            <div className="flex items-end justify-between gap-3 mb-3">
              <div>
                <p className="text-sm font-semibold text-slate-700">Focus concepts</p>
                <p className="text-xs text-slate-8000">
                  Lowest mastery first — keep the list short and actionable.
                </p>
              </div>
            </div>
            <div className="space-y-2">
              {focusConcepts.map(c => {
                const predicted = conceptMasteryPredMap[c.concept_id] ?? conceptMasteryPredMap[String(c.concept_id)] ?? null;
                return (
                  <div
                    key={c.concept_id}
                    className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white/40 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-slate-700 truncate">
                        {c.concept_name}
                      </p>
                      <p className="text-[0.7rem] text-slate-8000 truncate">
                        {c.subject}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs font-semibold text-sky-600">
                        {pct(c.mastery_score)}
                      </span>
                      {predicted !== null && (
                        <span className="text-[0.7rem] text-slate-8000" title="Predicted mastery">
                          → {pct(predicted)}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
              {focusConcepts.length === 0 && (
                <p className="text-xs text-slate-8000">No mastery data yet.</p>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="axon-card-subtle p-5 sm:p-6">
              <p className="text-sm font-semibold text-slate-700 mb-2">Active flags</p>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {(flags?.flags || []).slice(0, 6).map(f => (
                  <div
                    key={f.id}
                    className={`rounded-lg border px-3 py-2 ${flagBorderStyle(f.flag_type)}`}
                  >
                    <p className="text-xs font-medium text-slate-700">
                      {f.concept_name}
                    </p>
                    <p className="text-[0.7rem] text-slate-8000">
                      {f.flag_type ? f.flag_type.replace(/_/g, ' ') : ''}{f.flag_detail ? ` · ${f.flag_detail}` : ''}
                    </p>
                  </div>
                ))}
                {(flags?.flags || []).length === 0 && (
                  <p className="text-xs text-slate-8000">No active flags.</p>
                )}
              </div>
            </div>

            <div className="axon-card-subtle p-5 sm:p-6">
              <p className="text-sm font-semibold text-slate-700 mb-2">Recent sessions</p>
              <div className="space-y-2">
                {recentConvos.map(c => {
                  const isExpanded = expandedConversations.has(c.id);
                  return (
                    <div key={c.id}>
                      <button
                        className={`w-full text-left rounded-lg border transition-colors px-3 py-2 ${
                          isExpanded
                            ? 'border-teal-300 bg-teal-50/60'
                            : 'border-slate-200 bg-white/40 hover:bg-white/60'
                        }`}
                        onClick={() => toggleConversation(c.id)}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-xs font-medium text-slate-700 truncate">
                            {c.concept_name}
                          </p>
                          <span className="text-[0.7rem] text-slate-8000">
                            {pct(c.session_engagement_score)}
                          </span>
                        </div>
                        <p className="text-[0.7rem] text-slate-8000 mt-0.5 truncate">
                          {c.subject} · {new Date(c.started_at).toLocaleDateString()}
                        </p>
                      </button>

                      {/* Conversation thread dropdown */}
                      {isExpanded && (
                        <div
                          className="overflow-hidden transition-all duration-200"
                          style={{
                            maxHeight: '600px',
                            marginTop: '8px',
                          }}
                        >
                          <div className="rounded-lg border border-slate-200 overflow-hidden">
                            <ConversationThread
                              conversationId={c.id}
                              onClose={() => toggleConversation(c.id)}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
                {recentConvos.length === 0 && (
                  <p className="text-xs text-slate-8000">No sessions yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Pedagogy Recommendations ── */}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm font-semibold text-slate-700 mb-3">Teaching recommendations</p>
          {aiInsights?.insights?.teaching_approach_advice ? (
            <p className="text-sm text-slate-600 leading-relaxed">{aiInsights.insights.teaching_approach_advice}</p>
          ) : (
            <p className="text-xs text-slate-8000">No teaching recommendations available yet.</p>
          )}
        </div>

        {/* ── Predictions: Risk Factors & Improvement Areas ── */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="axon-card-subtle p-5 sm:p-6">
            <p className="text-sm font-semibold text-slate-700 mb-2">Risk factors</p>
            {aiInsights?.insights?.risk_narrative ? (
              <p className="text-sm text-slate-600 leading-relaxed">{aiInsights.insights.risk_narrative}</p>
            ) : (
              <p className="text-xs text-slate-8000">No risk factors identified.</p>
            )}
          </div>
          <div className="axon-card-subtle p-5 sm:p-6">
            <p className="text-sm font-semibold text-slate-700 mb-2">Improvement areas</p>
            {aiInsights?.insights?.recommended_interventions ? (
              Array.isArray(aiInsights.insights.recommended_interventions) ? (
                <ul className="space-y-1">
                  {aiInsights.insights.recommended_interventions.map((a, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                      <span className="text-emerald-600 mt-0.5 shrink-0">•</span>
                      {typeof a === 'string' ? a : JSON.stringify(a)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-600 leading-relaxed">{aiInsights.insights.recommended_interventions}</p>
              )
            ) : (
              <p className="text-xs text-slate-8000">No improvement areas identified.</p>
            )}
          </div>
        </div>

        {/* ── AI Insight (teacher_ai_insights) ── */}
        {aiInsights?.insights && (
          <div className="axon-card-subtle p-5 sm:p-6 space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <span style={{ color: '#0f766e' }}>✦</span>
                <p
                  className="font-semibold tracking-widest uppercase"
                  style={{ color: '#0f766e', fontSize: '11px' }}
                >
                  Axon Intelligence
                </p>
              </div>
              {(aiInsights.insights.generated_at || aiInsights.insights.model_used) && (
                <p className="text-[0.65rem] text-slate-600 shrink-0 mt-0.5">
                  {aiInsights.insights.model_used ? `Generated by ${aiInsights.insights.model_used}` : 'Generated'}
                  {aiInsights.insights.generated_at ? ` · ${new Date(aiInsights.insights.generated_at).toLocaleDateString()}` : ''}
                </p>
              )}
            </div>

            {aiInsights.insights.student_summary && (
              <p className="text-sm text-slate-600 leading-relaxed">{aiInsights.insights.student_summary}</p>
            )}

            {aiInsights.insights.risk_narrative && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                  Risk assessment
                </p>
                <p className="text-sm text-slate-600 leading-relaxed">{aiInsights.insights.risk_narrative}</p>
              </div>
            )}

            {aiInsights.insights.recommended_interventions && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                  Recommended actions
                </p>
                {Array.isArray(aiInsights.insights.recommended_interventions) ? (
                  <ul className="space-y-1.5">
                    {aiInsights.insights.recommended_interventions.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                        <span style={{ color: '#0f766e' }} className="mt-0.5 shrink-0">→</span>
                        {typeof item === 'string' ? item : JSON.stringify(item)}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-600 leading-relaxed">{aiInsights.insights.recommended_interventions}</p>
                )}
              </div>
            )}

            {aiInsights.insights.teaching_approach_advice && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                  How to teach this student
                </p>
                <p className="text-sm text-slate-600 leading-relaxed">{aiInsights.insights.teaching_approach_advice}</p>
              </div>
            )}
          </div>
        )}

        {/* ── Teach This Student (pedagogical_memory) ── */}
        {sortedApproaches.length > 0 && (
          <div className="axon-card-subtle p-5 sm:p-6">
            <p className="text-sm font-semibold text-slate-700 mb-4">Teach this student</p>
            <div className="space-y-3">
              {sortedApproaches.slice(0, 4).map((approach, i) => {
                const rate = clamp01(approach.success_rate ?? 0);
                const barColor =
                  rate > 0.6
                    ? 'bg-emerald-500'
                    : rate >= 0.3
                    ? 'bg-amber-500'
                    : 'bg-rose-500';
                const name = formatApproachName(approach.teaching_approach);
                return (
                  <div key={i}>
                    <div className="flex items-center justify-between gap-3 mb-1">
                      <span className="text-xs text-slate-700">{name}</span>
                      <span className="text-xs text-slate-400 shrink-0">
                        {pct(rate)} ({approach.attempt_count ?? 0} sessions)
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-200">
                      <div
                        className={`h-1.5 rounded-full ${barColor}`}
                        style={{ width: pct(rate) }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
            {sortedApproaches[0] && (
              <p className="text-[0.7rem] text-slate-8000 mt-4">
                Best approach: {formatApproachName(sortedApproaches[0].teaching_approach)}
                {sortedApproaches[0].avg_messages_to_lightbulb != null && (
                  ` · Avg ${Math.round(sortedApproaches[0].avg_messages_to_lightbulb)} messages to breakthrough`
                )}
              </p>
            )}
          </div>
        )}

      </div>
    </DashboardShell>
  );
}
