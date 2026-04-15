import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {
  getStudentDashboard,
  getStudentMastery,
  getStudentPedagogy,
  getStudentConversations,
  getConcepts,
} from '../../api/axonai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import ConversationThread from '../../components/ConversationThread';
import DashboardShell from '../../components/DashboardShell';
import KnowledgeGraphNew from '../../components/KnowledgeGraphNew';

export default function StudentDashboard() {
  const { id } = useParams();
  const studentId = id || 1;

  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [pedagogy, setPedagogy] = useState(null);
  const [conversations, setConversations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);
  const [chatSubjectFilter, setChatSubjectFilter] = useState('all');
  const [graphData, setGraphData] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getStudentDashboard(studentId),
      getStudentMastery(studentId),
      getStudentPedagogy(studentId),
      getStudentConversations(studentId, 44),
      getConcepts('Mathematics').catch(() => null),
    ])
      .then(([d, m, p, c, g]) => {
        setDashboard(d);
        setMastery(m);
        setPedagogy(p);
        setConversations(c);
        setGraphData(g);
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [studentId]);

  useEffect(() => { load(); }, [load]);

  const { convos, filteredConvos } = useMemo(() => {
    const allConvos = conversations?.conversations || [];
    const filtered = chatSubjectFilter === 'all'
      ? allConvos
      : allConvos.filter(c => c.subject === chatSubjectFilter);
    return { convos: allConvos, filteredConvos: filtered };
  }, [conversations, chatSubjectFilter]);

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
  if (!dashboard) {
    return (
      <DashboardShell subtitle="Student view">
        <div className="flex items-center justify-center py-16">
          <ErrorState message="No dashboard data was returned. Check the API or student id." onRetry={load} />
        </div>
      </DashboardShell>
    );
  }

  const { student, profile = {}, summary = { mastery: { avg_mastery: 0 } } } = dashboard;
  const concepts = mastery?.concepts || [];
  const weakest = concepts.slice(0, 5);
  const mathAvg = concepts.filter(c => c.subject === 'Mathematics');
  const bioAvg = concepts.filter(c => c.subject === 'Biology');
  const n = (x) => (typeof x === 'number' && x > 1 ? x / 100 : x) || 0;
  const mathMastery = mathAvg.length ? mathAvg.reduce((s, c) => s + n(c.mastery_score), 0) / mathAvg.length : 0;
  const bioMastery = bioAvg.length ? bioAvg.reduce((s, c) => s + n(c.mastery_score), 0) / bioAvg.length : 0;

  const masteryMapForGraph = useMemo(() => {
    const map = {};
    concepts.forEach((c) => {
      if (c.concept_id != null) {
        const raw = c.mastery_score ?? null;
        map[c.concept_id] = raw !== null ? n(raw) : null;
      }
    });
    return map;
  }, [concepts]);

  const hasLearningGraph = graphData && (graphData.concepts || []).length > 0;

  return (
    <DashboardShell subtitle={`Student · ${student.first_name}'s overview`}>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1.1fr)]">
        {/* Left column */}
        <div className="axon-card-subtle p-5 sm:p-6 space-y-5">
          <div>
            <p className="axon-label mb-1">Welcome back</p>
            <h1 className="axon-h2 text-lg sm:text-xl text-slate-800">
              Kia ora, {student.first_name}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Year {student.year_level} · {student.ethnicity}
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-700">Overall mastery</p>
              <span className="axon-pill text-[0.7rem]">
                {profile?.overall_mastery_trend === 'improving' ? "You're improving" : (profile?.overall_mastery_trend || '—')}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2.5 rounded-full bg-slate-200 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${((summary?.mastery?.avg_mastery ?? 0) * 100).toFixed(1)}%` }}
                />
              </div>
              <span className="text-xl font-semibold text-teal-600">
                {((summary?.mastery?.avg_mastery ?? 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="axon-card-ghost p-3.5 space-y-1.5">
              <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-400">Mathematics</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                  <div className="h-full rounded-full bg-sky-500" style={{ width: `${(mathMastery * 100).toFixed(1)}%` }} />
                </div>
                <span className="text-sm font-medium text-slate-700">{(mathMastery * 100).toFixed(0)}%</span>
              </div>
              <p className="text-[0.7rem] text-slate-400">{mathAvg.length} concepts tracked</p>
            </div>
            <div className="axon-card-ghost p-3.5 space-y-1.5">
              <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-400">Biology</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                  <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(bioMastery * 100).toFixed(1)}%` }} />
                </div>
                <span className="text-sm font-medium text-slate-700">{(bioMastery * 100).toFixed(0)}%</span>
              </div>
              <p className="text-[0.7rem] text-slate-400">{bioAvg.length} concepts tracked</p>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          <div className="axon-card-subtle p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Areas to work on</h3>
            <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              {weakest.slice(0, 4).map(c => (
                <div key={c.concept_id} className="flex items-center justify-between rounded-lg bg-rose-50/60 border border-rose-300/30 px-3 py-2">
                  <div>
                    <p className="text-xs font-medium text-slate-700">{c.concept_name}</p>
                    <p className="text-[0.7rem] text-slate-400">{c.subject}</p>
                  </div>
                  <span className="text-xs font-semibold text-rose-600">{(c.mastery_score * 100).toFixed(0)}%</span>
                </div>
              ))}
              {weakest.length === 0 && <p className="text-[0.72rem] text-slate-400">No flagged concepts right now.</p>}
            </div>
          </div>

          <div className="axon-card-subtle p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">AI learning sessions</h3>
            <p className="text-[0.72rem] text-slate-500 mb-2">Recently with the AxonAI tutor.</p>
            <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              {filteredConvos.slice(0, 5).map(c => (
                <div
                  key={c.id}
                  className="flex items-center justify-between rounded-lg bg-white/50 border border-slate-200 px-3 py-2 text-xs text-slate-700 cursor-pointer hover:bg-white/70 transition-colors"
                  onClick={() => setActiveConversation(activeConversation === c.id ? null : c.id)}
                >
                  <span className="truncate mr-2">{c.concept_name}</span>
                  <span className="text-slate-400">{(c.session_engagement_score * 100).toFixed(0)}%</span>
                </div>
              ))}
              {filteredConvos.length === 0 && <p className="text-[0.72rem] text-slate-400">No sessions yet.</p>}
            </div>
          </div>
        </div>
      </div>

      {hasLearningGraph && (
        <div className="mt-6 space-y-4 axon-card-subtle p-4 sm:p-5 sm:space-y-5">
          <div className="space-y-2">
            <p className="text-sm font-semibold text-slate-700">Your learning map (Mathematics)</p>
            <p className="text-xs leading-relaxed text-slate-500">
              Switch between the full prerequisite tree and explore mode — click to open the path and see what comes next.
              Shaded columns show level (left = fundamentals).
            </p>
          </div>
          <div className="min-h-[min(52vh,520px)] overflow-hidden rounded-lg border border-[#2c2418]/10 p-1 sm:p-2">
            <KnowledgeGraphNew
              dataOverride={graphData}
              masteryMap={masteryMapForGraph}
              mapOnly
              focusKeyNodes
              defaultExploration="path"
            />
          </div>
        </div>
      )}

      {activeConversation && (
        <div className="mt-6 axon-card-subtle p-4 sm:p-5">
          <ConversationThread conversationId={activeConversation} onClose={() => setActiveConversation(null)} />
        </div>
      )}
    </DashboardShell>
  );
}
