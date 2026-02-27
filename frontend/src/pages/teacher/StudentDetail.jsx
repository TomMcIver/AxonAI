import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getStudentDashboard, getStudentMastery, getStudentFlags, getStudentPedagogy, getStudentConversations } from '../../api/axonai';
import Layout from '../../components/Layout';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import MasteryChart from '../../components/MasteryChart';
import RiskGauge, { getRiskLevel } from '../../components/RiskGauge';
import ConversationThread from '../../components/ConversationThread';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

function Badge({ children, color }) {
  const colors = {
    green: 'bg-green-100 text-green-700',
    amber: 'bg-amber-100 text-amber-700',
    red: 'bg-red-100 text-red-700',
    blue: 'bg-blue-100 text-blue-700',
    gray: 'bg-gray-100 text-gray-700',
  };
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${colors[color] || colors.gray}`}>
      {children}
    </span>
  );
}

function interventionLabel(intervention) {
  const map = {
    monitor_continue: 'Monitor & Continue',
    targeted_support: 'Targeted Support',
    intensive_intervention: 'Intensive Intervention',
    peer_tutoring: 'Peer Tutoring',
  };
  return map[intervention] || intervention?.replace(/_/g, ' ');
}

export default function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [flags, setFlags] = useState(null);
  const [pedagogy, setPedagogy] = useState(null);
  const [conversations, setConversations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getStudentDashboard(id),
      getStudentMastery(id),
      getStudentFlags(id),
      getStudentPedagogy(id),
      getStudentConversations(id),
    ])
      .then(([d, m, f, p, c]) => {
        setDashboard(d);
        setMastery(m);
        setFlags(f);
        setPedagogy(p);
        setConversations(c);
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <Layout><LoadingSpinner message="Loading student profile..." /></Layout>;
  if (error) return <Layout><ErrorState message={error} onRetry={load} /></Layout>;
  if (!dashboard) return null;

  const { student, profile, wellbeing, predictions, summary } = dashboard;
  const riskPred = predictions?.find(p => p.model_name === 'risk_prediction');
  const engagementPred = predictions?.find(p => p.model_name === 'engagement');
  const interventionPred = predictions?.find(p => p.model_name === 'intervention');
  const riskScore = riskPred?.prediction_value?.probability ?? profile.overall_risk_score;

  // Split mastery by subject
  const mathConcepts = mastery?.concepts?.filter(c => c.subject === 'Mathematics') || [];
  const bioConcepts = mastery?.concepts?.filter(c => c.subject === 'Biology') || [];

  return (
    <Layout>
      {/* Back button */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-[#6B7280] hover:text-[#1F2937] mb-4">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 mb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#1F2937]">{student.first_name} {student.last_name}</h1>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <Badge color="blue">Year {student.year_level}</Badge>
              <Badge color="gray">{student.ethnicity}</Badge>
              <Badge color="gray">{student.gender}</Badge>
              <Badge color={wellbeing.attendance_percentage >= 90 ? 'green' : wellbeing.attendance_percentage >= 80 ? 'amber' : 'red'}>
                {wellbeing.attendance_percentage}% Attendance
              </Badge>
              {wellbeing.has_learning_support_plan && <Badge color="amber">Learning Support Plan</Badge>}
              {wellbeing.is_esol && <Badge color="blue">ESOL</Badge>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge color={profile.overall_mastery_trend === 'improving' ? 'green' : profile.overall_mastery_trend === 'declining' ? 'red' : 'gray'}>
              {profile.overall_mastery_trend}
            </Badge>
            <span className="text-sm text-[#6B7280]">{profile.total_interactions} interactions</span>
          </div>
        </div>
      </div>

      {/* ML Predictions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5 flex flex-col items-center">
          <h3 className="text-sm font-semibold text-[#6B7280] mb-2">Risk Level</h3>
          <RiskGauge score={riskScore} size={140} />
          <p className="text-xs text-[#6B7280] mt-1">Confidence: {((riskPred?.confidence || 0) * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5 flex flex-col items-center">
          <h3 className="text-sm font-semibold text-[#6B7280] mb-2">Engagement</h3>
          <div className="text-4xl font-bold text-[#0891B2] my-4">
            {((engagementPred?.prediction_value?.predicted_engagement || profile.overall_engagement_score) * 100).toFixed(0)}%
          </div>
          <p className="text-xs text-[#6B7280]">Average: {(summary.conversations.avg_engagement * 100).toFixed(0)}%</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5 flex flex-col items-center">
          <h3 className="text-sm font-semibold text-[#6B7280] mb-2">Recommended Action</h3>
          <div className="my-4">
            <Badge color={
              interventionPred?.prediction_value?.intervention === 'monitor_continue' ? 'green'
              : interventionPred?.prediction_value?.intervention === 'targeted_support' ? 'amber'
              : 'blue'
            }>
              {interventionLabel(interventionPred?.prediction_value?.intervention)}
            </Badge>
          </div>
          <p className="text-xs text-[#6B7280]">Confidence: {((interventionPred?.confidence || 0) * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4">
          <p className="text-xs text-[#6B7280]">Avg Mastery</p>
          <p className="text-xl font-bold text-[#1F2937]">{(summary.mastery.avg_mastery * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4">
          <p className="text-xs text-[#6B7280]">Conversations</p>
          <p className="text-xl font-bold text-[#1F2937]">{summary.conversations.total_conversations}</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4">
          <p className="text-xs text-[#6B7280]">Lightbulb Moments</p>
          <p className="text-xl font-bold text-[#F59E0B]">{summary.conversations.lightbulb_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4">
          <p className="text-xs text-[#6B7280]">Quiz Average</p>
          <p className="text-xl font-bold text-[#1F2937]">{summary.quizzes.avg_score.toFixed(1)}%</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4">
          <p className="text-xs text-[#6B7280]">Active Flags</p>
          <p className="text-xl font-bold text-[#EF4444]">{summary.active_flags}</p>
        </div>
      </div>

      {/* Mastery charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {mathConcepts.length > 0 && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Mathematics Mastery (weakest first)</h3>
            <MasteryChart concepts={mathConcepts} height={Math.max(250, mathConcepts.length * 22)} maxItems={mathConcepts.length} />
          </div>
        )}
        {bioConcepts.length > 0 && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
            <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Biology Mastery (weakest first)</h3>
            <MasteryChart concepts={bioConcepts} height={Math.max(250, bioConcepts.length * 22)} maxItems={bioConcepts.length} />
          </div>
        )}
      </div>

      {/* Flags */}
      {flags?.flags?.length > 0 && (
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5 mb-6">
          <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Active Flags ({flags.total_flags})</h3>
          <div className="space-y-3">
            {flags.flags.map(f => (
              <div key={f.id} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                <div className="w-2 h-2 rounded-full bg-[#EF4444] mt-1.5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[#1F2937]">{f.concept_name}</span>
                    <Badge color="red">{f.flag_type.replace(/_/g, ' ')}</Badge>
                  </div>
                  <p className="text-sm text-[#6B7280] mt-0.5">{f.flag_detail}</p>
                  <p className="text-xs text-[#0891B2] mt-1">{f.recommended_intervention}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Teaching approaches */}
      {pedagogy?.approaches?.length > 0 && (
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5 mb-6">
          <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Teaching Approaches (by success rate)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={pedagogy.approaches.map(a => ({
              name: a.teaching_approach.replace(/_/g, ' '),
              rate: +(a.success_rate * 100).toFixed(1),
              attempts: a.attempt_count,
            }))}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="rate" radius={[4, 4, 0, 0]} barSize={30}>
                {pedagogy.approaches.map((a, i) => (
                  <Cell key={i} fill={a.success_rate >= 0.5 ? '#10B981' : a.success_rate >= 0.3 ? '#F59E0B' : '#EF4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Conversations */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5 mb-6">
        <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Recent Conversations</h3>
        <div className="space-y-2">
          {(conversations?.conversations || []).map(c => (
            <div
              key={c.id}
              className="flex items-center justify-between p-3 rounded-lg border border-[#E2E8F0] hover:bg-[#F8FAFC] cursor-pointer transition-colors"
              onClick={() => setActiveConversation(activeConversation === c.id ? null : c.id)}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-[#1F2937]">{c.concept_name}</span>
                  <span className="text-xs text-[#6B7280]">{c.subject}</span>
                  {c.lightbulb_moment_detected && (
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded-full">Lightbulb</span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-0.5 text-xs text-[#6B7280]">
                  <span>{new Date(c.started_at).toLocaleDateString()}</span>
                  <span>Engagement: {(c.session_engagement_score * 100).toFixed(0)}%</span>
                  <span className="capitalize">{c.outcome}</span>
                  <span className="capitalize">{c.primary_teaching_approach?.replace(/_/g, ' ')}</span>
                </div>
              </div>
              <svg className={`w-5 h-5 text-[#6B7280] transition-transform ${activeConversation === c.id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          ))}
        </div>
      </div>

      {/* Conversation thread */}
      {activeConversation && (
        <div className="mb-6">
          <ConversationThread
            conversationId={activeConversation}
            onClose={() => setActiveConversation(null)}
          />
        </div>
      )}
    </Layout>
  );
}
