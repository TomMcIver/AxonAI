import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import {
  getStudentDashboard,
  getStudentMastery,
  getClassOverview,
  getStudentSummary,
} from '../../api/axonai';
import DashboardShell from '../../components/DashboardShell';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';

function clamp01(n) {
  if (typeof n !== 'number' || Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function pct(v) {
  return `${Math.round(clamp01(v) * 100)}%`;
}

function riskTone(score) {
  if (score >= 0.4) return { label: 'At risk', color: 'text-rose-600', bg: 'bg-rose-50' };
  if (score >= 0.2) return { label: 'Needs attention', color: 'text-amber-600', bg: 'bg-amber-50' };
  return { label: 'On track', color: 'text-emerald-600', bg: 'bg-emerald-50' };
}

function MasteryRing({ percentage, size = 120 }) {
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamp01(percentage) * circumference);

  return (
    <div className="flex flex-col items-center gap-2">
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#0d9488"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
          }}
        >
          <span className="text-2xl font-bold text-slate-700">
            {Math.round(clamp01(percentage) * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
}

export default function StudentSummary() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [classOverview, setClassOverview] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getStudentDashboard(id),
      getStudentMastery(id),
      getClassOverview(1).catch(() => null),
      getStudentSummary(id),
    ])
      .then(([d, m, co, s]) => {
        setDashboard(d);
        setMastery(m);
        setClassOverview(co);
        setSummaryData(s);
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

  // Calculate engagement from classOverview if available
  const studentInClass = classOverview?.students?.find(s => s.student_id === Number(id) || s.student_id === id);
  const engagement = studentInClass?.engagement_percentage ?? profile?.overall_engagement_score ?? 0;

  // Get mastery by subject
  const masteryBySubject = {};
  (mastery?.concepts || []).forEach(c => {
    if (!masteryBySubject[c.subject]) {
      masteryBySubject[c.subject] = [];
    }
    masteryBySubject[c.subject].push(c.mastery_score || 0);
  });

  const subjectMastery = Object.entries(masteryBySubject).map(([subject, scores]) => {
    const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    return { subject, mastery: avg };
  });

  const overallMastery = summary?.mastery?.avg_mastery ?? 0;

  return (
    <DashboardShell subtitle="Student · summary">
      <div className="space-y-6 max-w-2xl mx-auto px-4">
        {/* ── Navigation ── */}
        <div className="flex items-center justify-between gap-3">
          <button
            className="axon-btn axon-btn-quiet"
            onClick={() => navigate(-1)}
          >
            ← Back
          </button>
        </div>

        {/* ── Student Header ── */}
        <div className="axon-card-subtle p-5 sm:p-6 text-center">
          <h1 className="axon-h2 text-2xl sm:text-3xl text-slate-800 mb-1">
            {student.first_name} {student.last_name}
          </h1>
          <p className="text-sm text-slate-400 mb-3">
            Year {student.year_level}
          </p>

          {/* Risk Status */}
          <div
            className={`inline-block px-3 py-1.5 rounded-lg text-sm font-semibold ${tone.color} ${tone.bg}`}
          >
            {tone.label}
          </div>
        </div>

        {/* ── Overall Mastery ── */}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm font-semibold text-slate-700 mb-4">Overall mastery</p>
          <div className="flex items-center justify-center">
            <MasteryRing percentage={overallMastery} />
          </div>
        </div>

        {/* ── Subject Mastery Grid ── */}
        {subjectMastery.length > 0 && (
          <div className="axon-card-subtle p-5 sm:p-6">
            <p className="text-sm font-semibold text-slate-700 mb-4">Mastery by subject</p>
            <div className="grid gap-4 sm:grid-cols-2">
              {subjectMastery.map(({ subject, mastery: m }) => (
                <div
                  key={subject}
                  className="rounded-lg border border-slate-200/60 bg-white/40 p-4"
                >
                  <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-2">
                    {subject}
                  </p>
                  <div className="flex items-end gap-3">
                    <p className="text-2xl font-bold text-teal-600">
                      {Math.round(clamp01(m) * 100)}%
                    </p>
                    <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        className="h-full bg-teal-500"
                        style={{ width: `${clamp01(m) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Engagement Score ── */}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm font-semibold text-slate-700 mb-3">Engagement</p>
          <div className="flex items-center gap-4">
            <div className="text-4xl font-bold text-sky-600">
              {pct(engagement)}
            </div>
            <p className="text-sm text-slate-600">
              Active participation in tutoring sessions
            </p>
          </div>
        </div>

        {/* ── Quick Stats ── */}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm font-semibold text-slate-700 mb-4">Quick stats</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg bg-white/40 border border-slate-200/60 p-3">
              <p className="text-xs text-slate-400 uppercase tracking-wide font-medium">
                Conversations
              </p>
              <p className="text-xl font-bold text-slate-700 mt-1">
                {summary?.conversations?.total_conversations ?? 0}
              </p>
            </div>
            <div className="rounded-lg bg-white/40 border border-slate-200/60 p-3">
              <p className="text-xs text-slate-400 uppercase tracking-wide font-medium">
                Active flags
              </p>
              <p className="text-xl font-bold text-slate-700 mt-1">
                {summary?.active_flags ?? 0}
              </p>
            </div>
          </div>
        </div>

        {/* ── Concept Mastery by Class ── */}
        {summaryData?.classes && summaryData.classes.length > 0 && (
          <div>
            <p className="text-sm font-semibold text-slate-700 mb-4">Concept mastery by class</p>
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
              {summaryData.classes.map((classData) => {
                // Filter and sort mastered concepts (≥85%)
                const mastered = (classData.concepts || [])
                  .filter(c => (c.score || 0) >= 85)
                  .sort((a, b) => (b.score || 0) - (a.score || 0))
                  .slice(0, 3);

                // Filter and sort struggling concepts (<50%)
                const struggling = (classData.concepts || [])
                  .filter(c => (c.score || 0) < 50)
                  .sort((a, b) => (a.score || 0) - (b.score || 0))
                  .slice(0, 3);

                // Use overall score from API or calculate from concepts
                const overallScore = classData.overallScore || (
                  classData.concepts?.length > 0
                    ? classData.concepts.reduce((sum, c) => sum + (c.score || 0), 0) / classData.concepts.length
                    : 0
                );

                return (
                  <div
                    key={classData.classId || classData.className}
                    className="axon-card-subtle p-5 sm:p-6 rounded-2xl"
                  >
                    {/* Class header */}
                    <div className="mb-4">
                      <h3 className="text-sm font-semibold text-slate-700 mb-3">
                        {classData.className}
                      </h3>

                      {/* Overall score bar */}
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-500 font-medium">Overall score</span>
                          <span className="text-sm font-bold text-teal-600">
                            {Math.round(clamp01(overallScore / 100) * 100)}%
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className="h-full bg-teal-500 transition-all duration-500 ease-out"
                            style={{ width: `${clamp01(overallScore / 100) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Mastered concepts */}
                    {mastered.length > 0 && (
                      <div className="mb-4">
                        <p className="text-xs font-semibold text-slate-600 mb-2">Top 3 Mastered</p>
                        <div className="space-y-2">
                          {mastered.map((concept) => (
                            <div
                              key={concept.name}
                              className="flex items-center gap-2 p-2 rounded-lg border border-green-500/40 bg-white/40"
                            >
                              <CheckCircle2 size={16} className="text-green-600 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-green-700 truncate">
                                  {concept.name}
                                </p>
                              </div>
                              <span className="text-xs font-bold text-green-600 flex-shrink-0">
                                {Math.round(concept.score || 0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Struggling concepts */}
                    {struggling.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-slate-600 mb-2">Bottom 3 Struggling</p>
                        <div className="space-y-2">
                          {struggling.map((concept) => (
                            <div
                              key={concept.name}
                              className="flex items-center gap-2 p-2 rounded-lg border border-red-500/40 bg-white/40"
                            >
                              <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-red-700 truncate">
                                  {concept.name}
                                </p>
                              </div>
                              <span className="text-xs font-bold text-red-600 flex-shrink-0">
                                {Math.round(concept.score || 0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Action Buttons ── */}
        <div className="flex gap-3">
          <button
            className="flex-1 axon-btn axon-btn-primary"
            onClick={() => navigate(`/teacher/student/${id}`)}
          >
            Deep dive
          </button>
        </div>
      </div>
    </DashboardShell>
  );
}
