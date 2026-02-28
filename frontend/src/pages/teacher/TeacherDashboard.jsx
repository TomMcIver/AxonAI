import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getClassOverview } from '../../api/axonai';
import Layout from '../../components/Layout';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import { getRiskLevel } from '../../components/RiskGauge';

const CLASSES = [
  { id: 1, name: 'Year 12 Mathematics', subject: 'Mathematics' },
  { id: 2, name: 'Year 12 Biology', subject: 'Biology' },
];

function StatCard({ label, value, sub, color }) {
  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
      <p className="text-sm text-[#6B7280] mb-1">{label}</p>
      <p className="text-2xl font-bold" style={{ color: color || '#1F2937' }}>{value}</p>
      {sub && <p className="text-xs text-[#6B7280] mt-1">{sub}</p>}
    </div>
  );
}

function TrendBadge({ trend }) {
  const config = {
    improving: { label: 'Improving', cls: 'bg-green-100 text-green-700' },
    declining: { label: 'Declining', cls: 'bg-red-100 text-red-700' },
    stable: { label: 'Stable', cls: 'bg-gray-100 text-gray-700' },
  };
  const c = config[trend] || config.stable;
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.cls}`}>{c.label}</span>;
}

function StudentRow({ student, navigate, highlight }) {
  const risk = getRiskLevel(student.overall_risk_score);
  const bgMap = {
    red: 'bg-red-50 hover:bg-red-100',
    amber: 'bg-amber-50 hover:bg-amber-100',
    green: 'bg-green-50 hover:bg-green-100',
    blue: 'bg-blue-50 hover:bg-blue-100',
    default: 'hover:bg-gray-50',
  };
  const bg = bgMap[highlight] || bgMap.default;

  return (
    <tr
      className={`${bg} cursor-pointer transition-colors`}
      onClick={() => navigate(`/teacher/student/${student.student_id}`)}
    >
      <td className="px-3 py-2.5 text-sm font-medium text-[#1F2937]">
        <div className="flex items-center gap-2">
          {student.first_name} {student.last_name}
          {student.student_id === 1 && (
            <span className="bg-[#0891B2] text-white px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase">Demo</span>
          )}
        </div>
      </td>
      <td className="px-3 py-2.5 text-sm">
        <span className={student.avg_mastery >= 0.7 ? 'text-green-600' : student.avg_mastery >= 0.4 ? 'text-amber-600' : 'text-red-600'}>
          {(student.avg_mastery * 100).toFixed(1)}%
        </span>
      </td>
      <td className="px-3 py-2.5">
        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${risk.bg}`} style={{ color: risk.color }}>
          {risk.label}
        </span>
      </td>
      <td className="px-3 py-2.5 text-sm text-[#1F2937]">{(student.overall_engagement_score * 100).toFixed(0)}%</td>
      <td className="px-3 py-2.5">
        <TrendBadge trend={student.overall_mastery_trend} />
      </td>
      <td className="px-3 py-2.5 text-sm">
        {student.active_flags > 0 && (
          <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs font-medium">{student.active_flags}</span>
        )}
      </td>
    </tr>
  );
}

function StudentSection({ title, subtitle, students, navigate, highlightColor, icon, accentColor }) {
  if (!students.length) return null;
  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-[#E2E8F0] flex items-center gap-3" style={{ borderLeftWidth: 4, borderLeftColor: accentColor }}>
        <span className="text-lg">{icon}</span>
        <div>
          <h3 className="text-sm font-semibold text-[#1F2937]">{title}</h3>
          <p className="text-xs text-[#6B7280]">{subtitle}</p>
        </div>
        <span className="ml-auto text-xs font-medium text-[#6B7280]">{students.length} students</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[#F8FAFC]">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Name</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Mastery</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Risk</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Engagement</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Trend</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Flags</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0]">
            {students.map(s => (
              <StudentRow key={s.student_id} student={s} navigate={navigate} highlight={highlightColor} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function TeacherDashboard() {
  const navigate = useNavigate();
  const [classId, setClassId] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getClassOverview(classId)
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [classId]);

  useEffect(() => { load(); }, [load]);

  const cls = CLASSES.find(c => c.id === classId);

  // Smart grouping: 5 needing help, 5 improving, 20 average/stalled (30 total per class)
  const { needsHelp, improving, average } = useMemo(() => {
    if (!data?.students) return { needsHelp: [], improving: [], average: [] };
    const students = [...data.students];

    // 5 Needing Help — highest risk score
    const byRisk = [...students].sort((a, b) => b.overall_risk_score - a.overall_risk_score);
    const needsHelpGroup = byRisk.slice(0, 5);
    const helpIds = new Set(needsHelpGroup.map(s => s.student_id));

    // 5 Improving — trend = 'improving', sorted by mastery (best first)
    const improvingCandidates = students
      .filter(s => !helpIds.has(s.student_id) && s.overall_mastery_trend === 'improving')
      .sort((a, b) => b.avg_mastery - a.avg_mastery);
    const improvingGroup = improvingCandidates.slice(0, 5);
    const improvingIds = new Set(improvingGroup.map(s => s.student_id));

    // 20 Average/Stalled — everyone else, alphabetical
    const averageGroup = students
      .filter(s => !helpIds.has(s.student_id) && !improvingIds.has(s.student_id))
      .sort((a, b) => a.last_name.localeCompare(b.last_name))
      .slice(0, 20);

    return { needsHelp: needsHelpGroup, improving: improvingGroup, average: averageGroup };
  }, [data]);

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#1F2937]">Kia ora, Sarah</h1>
        <p className="text-[#6B7280]">Teacher Dashboard — {cls?.name}</p>
      </div>

      {/* Class selector */}
      <div className="flex gap-2 mb-6">
        {CLASSES.map(c => (
          <button
            key={c.id}
            onClick={() => setClassId(c.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              classId === c.id
                ? 'bg-[#1E2761] text-white'
                : 'bg-white text-[#6B7280] border border-[#E2E8F0] hover:bg-[#F1F5F9]'
            }`}
          >
            {c.subject}
          </button>
        ))}
      </div>

      {loading && <LoadingSpinner message={`Loading ${cls?.subject} class data...`} />}
      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && data && (() => {
        const students = data.students || [];
        const avgMastery = students.length
          ? students.reduce((sum, s) => sum + (s.avg_mastery || 0), 0) / students.length
          : 0;
        const avgQuiz = students.filter(s => s.avg_quiz_score != null);
        const avgQuizScore = avgQuiz.length
          ? avgQuiz.reduce((sum, s) => sum + s.avg_quiz_score, 0) / avgQuiz.length
          : 0;
        const flaggedStudents = students.filter(s => s.active_flags > 0).length;

        return (
          <>
            {/* Stats row */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
              <StatCard
                label="Total Students"
                value={data.student_count}
                sub={`${data.class_stats?.active_students || data.student_count} active`}
              />
              <StatCard
                label="At-Risk Students"
                value={data.at_risk_count}
                sub={`${((data.at_risk_count / data.student_count) * 100).toFixed(0)}% of class`}
                color="#EF4444"
              />
              <StatCard
                label="Avg Class Mastery"
                value={`${(avgMastery * 100).toFixed(1)}%`}
                sub={`Quiz avg: ${avgQuizScore.toFixed(1)}%`}
                color="#0891B2"
              />
              <StatCard
                label="Average Engagement"
                value={`${(data.class_stats?.avg_engagement * 100).toFixed(1)}%`}
                sub={`${data.class_stats?.total_conversations} conversations`}
              />
              <StatCard
                label="Improving"
                value={data.improving_count}
                sub={`${data.declining_count} declining, ${flaggedStudents} flagged`}
                color="#10B981"
              />
            </div>

            {/* ML Model Note */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-[#0891B2] mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-[#1F2937]">ML Model Insights Available</p>
                  <p className="text-xs text-[#6B7280] mt-0.5">
                    Click any student to view their individual ML predictions (risk, engagement, intervention) with model confidence scores.
                  </p>
                </div>
              </div>
            </div>

            {/* Categorized student sections */}
            <div className="space-y-4">
              <StudentSection
                title="Needs Help"
                subtitle="Highest risk — may need intervention"
                students={needsHelp}
                navigate={navigate}
                highlightColor="red"
                icon="!!!"
                accentColor="#EF4444"
              />
              <StudentSection
                title="Improving"
                subtitle="On an upward trend — keep it up"
                students={improving}
                navigate={navigate}
                highlightColor="green"
                icon="***"
                accentColor="#10B981"
              />
              <StudentSection
                title="Average / Stalled"
                subtitle="Steady performers — alphabetical"
                students={average}
                navigate={navigate}
                highlightColor="default"
                icon="---"
                accentColor="#0891B2"
              />
            </div>

            <p className="text-xs text-[#6B7280] mt-4 text-center">
              Showing {needsHelp.length + improving.length + average.length} of {students.length} students
            </p>
          </>
        );
      })()}
    </Layout>
  );
}
