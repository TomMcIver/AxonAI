import React, { useState, useEffect, useCallback } from 'react';
import { getStudentDashboard, getStudentMastery, getStudentFlags, getStudentPedagogy } from '../../api/axonai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';

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

  if (loading) return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <LoadingSpinner message="Loading your child's progress..." />
    </div>
  );
  if (error) return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <ErrorState message={error} onRetry={load} />
    </div>
  );
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
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* Header */}
      <div className="bg-[#1E2761] text-white">
        <div className="max-w-3xl mx-auto px-6 py-8">
          <p className="text-[#94A3B8] text-sm mb-1">AxonAI Parent Portal</p>
          <h1 className="text-3xl font-bold">Kia ora, Whanau</h1>
          <p className="text-[#94A3B8] mt-1">Viewing progress for {student.first_name} {student.last_name}</p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        {/* Child overview */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-[#1F2937]">{student.first_name} {student.last_name}</h2>
              <p className="text-[#6B7280] mt-1">Year {student.year_level} — {student.ethnicity}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-[#6B7280]">Attendance</p>
              <p className={`text-2xl font-bold ${wellbeing.attendance_percentage >= 90 ? 'text-[#10B981]' : wellbeing.attendance_percentage >= 80 ? 'text-[#F59E0B]' : 'text-[#EF4444]'}`}>
                {wellbeing.attendance_percentage}%
              </p>
            </div>
          </div>
        </div>

        {/* Risk status */}
        <StatusIndicator score={riskScore} />

        {/* Overall progress */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6">
          <h3 className="text-lg font-semibold text-[#1F2937] mb-2">Overall Progress</h3>
          <p className="text-[#6B7280] mb-4">{trendMessage}</p>
          <div className="flex items-center gap-4 mb-2">
            <span className="text-sm text-[#6B7280] w-20">Overall</span>
            <div className="flex-1">
              <ProgressBar value={summary.mastery.avg_mastery * 100} color="#0891B2" />
            </div>
            <span className="text-sm font-semibold text-[#1F2937] w-16 text-right">
              {(summary.mastery.avg_mastery * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Subject breakdown */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6">
          <h3 className="text-lg font-semibold text-[#1F2937] mb-4">Subject Breakdown</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-[#1F2937]">Mathematics</span>
                <span className="text-sm font-semibold" style={{ color: mathMastery >= 0.7 ? '#10B981' : mathMastery >= 0.4 ? '#F59E0B' : '#EF4444' }}>
                  {(mathMastery * 100).toFixed(1)}%
                </span>
              </div>
              <ProgressBar value={mathMastery * 100} color={mathMastery >= 0.7 ? '#10B981' : mathMastery >= 0.4 ? '#F59E0B' : '#EF4444'} />
              <p className="text-xs text-[#6B7280] mt-1">{mathConcepts.length} concepts assessed</p>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-[#1F2937]">Biology</span>
                <span className="text-sm font-semibold" style={{ color: bioMastery >= 0.7 ? '#10B981' : bioMastery >= 0.4 ? '#F59E0B' : '#EF4444' }}>
                  {(bioMastery * 100).toFixed(1)}%
                </span>
              </div>
              <ProgressBar value={bioMastery * 100} color={bioMastery >= 0.7 ? '#10B981' : bioMastery >= 0.4 ? '#F59E0B' : '#EF4444'} />
              <p className="text-xs text-[#6B7280] mt-1">{bioConcepts.length} concepts assessed</p>
            </div>
          </div>
        </div>

        {/* Engagement */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6">
          <h3 className="text-lg font-semibold text-[#1F2937] mb-2">Engagement</h3>
          <p className="text-[#6B7280]">{engagementMessage}</p>
          <div className="mt-3 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xl font-bold text-[#0891B2]">{summary.conversations.total_conversations}</p>
              <p className="text-xs text-[#6B7280]">Learning Sessions</p>
            </div>
            <div>
              <p className="text-xl font-bold text-[#F59E0B]">{summary.conversations.lightbulb_count}</p>
              <p className="text-xs text-[#6B7280]">Lightbulb Moments</p>
            </div>
            <div>
              <p className="text-xl font-bold text-[#10B981]">{summary.quizzes.avg_score.toFixed(0)}%</p>
              <p className="text-xs text-[#6B7280]">Quiz Average</p>
            </div>
          </div>
        </div>

        {/* Key insight */}
        {bestApproach && (
          <div className="bg-[#0891B2]/5 rounded-xl border border-[#0891B2]/20 p-6">
            <h3 className="text-lg font-semibold text-[#1F2937] mb-2">Key Insight</h3>
            <p className="text-[#6B7280]">
              {student.first_name} learns best with <strong className="text-[#1F2937] capitalize">{bestApproach.teaching_approach.replace(/_/g, ' ')}</strong> and has a {(bestApproach.success_rate * 100).toFixed(0)}% success rate with this approach.
            </p>
            <p className="text-sm text-[#6B7280] mt-2">
              Their preferred learning style is <strong className="text-[#1F2937] capitalize">{profile.dominant_learning_style}</strong> and they learn best in the <strong className="text-[#1F2937]">{profile.best_time_of_day}</strong>.
            </p>
          </div>
        )}

        {/* Areas to support at home */}
        {flags?.flags?.length > 0 && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6">
            <h3 className="text-lg font-semibold text-[#1F2937] mb-2">Areas to Support at Home</h3>
            <p className="text-sm text-[#6B7280] mb-4">
              These are concepts {student.first_name} is finding challenging. Encouragement and practice at home can help.
            </p>
            <div className="space-y-2">
              {flags.flags.map(f => (
                <div key={f.id} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
                  <div className="w-2 h-2 rounded-full bg-[#F59E0B] mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-[#1F2937]">{f.concept_name}</p>
                    <p className="text-xs text-[#6B7280]">{f.subject} — {f.flag_detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Talk to teacher suggestion */}
        {flags?.total_flags >= 3 && (
          <div className="bg-[#1E2761] text-white rounded-xl p-6 text-center">
            <h3 className="text-lg font-semibold mb-2">Consider Connecting with {student.first_name}'s Teacher</h3>
            <p className="text-[#94A3B8] text-sm">
              With {flags.total_flags} active learning flags, a conversation with {student.first_name}'s teacher could help identify the best support strategy.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
