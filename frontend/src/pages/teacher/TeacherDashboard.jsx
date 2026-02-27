import React, { useState, useEffect, useCallback } from 'react';
import { getClassOverview } from '../../api/axonai';
import Layout from '../../components/Layout';
import StudentTable from '../../components/StudentTable';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';

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

export default function TeacherDashboard() {
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
                    Click any student to view their individual ML predictions (risk, engagement, intervention) with model confidence scores. Risk scores shown in the table are from our <span className="font-mono text-[10px] bg-white px-1 py-0.5 rounded">risk_prediction</span> model.
                  </p>
                </div>
              </div>
            </div>

            {/* Student table */}
            <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
              <h2 className="text-lg font-semibold text-[#1F2937] mb-4">Students</h2>
              <StudentTable students={students} />
            </div>
          </>
        );
      })()}
    </Layout>
  );
}
