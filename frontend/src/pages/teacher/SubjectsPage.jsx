import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, ChevronRight, Users, TrendingUp, AlertTriangle } from 'lucide-react';
import DashboardShell from '../../components/DashboardShell';

const subjects = [
  {
    id: 'math-y11',
    name: 'Year 11 Mathematics',
    code: 'MATH11',
    students: 28,
    avgMastery: 71,
    atRisk: 2,
    needsAttention: 6,
    recentActivity: '2h ago',
    topics: ['Algebra', 'Geometry', 'Trigonometry', 'Statistics'],
    trend: 'up',
  },
  {
    id: 'bio-y11',
    name: 'Year 11 Biology',
    code: 'BIO11',
    students: 24,
    avgMastery: 68,
    atRisk: 1,
    needsAttention: 4,
    recentActivity: '4h ago',
    topics: ['Cell Biology', 'Genetics', 'Ecology', 'Evolution'],
    trend: 'up',
  },
  {
    id: 'math-y12',
    name: 'Year 12 Mathematics',
    code: 'MATH12',
    students: 22,
    avgMastery: 74,
    atRisk: 1,
    needsAttention: 3,
    recentActivity: '1d ago',
    topics: ['Calculus', 'Probability', 'Complex Numbers'],
    trend: 'flat',
  },
];

function masteryColor(mastery) {
  if (mastery >= 91) return 'var(--mastered)';
  if (mastery >= 76) return 'var(--on-track)';
  if (mastery >= 51) return 'var(--in-progress)';
  if (mastery >= 26) return 'var(--needs-attention)';
  return 'var(--at-risk)';
}

export default function SubjectsPage() {
  const navigate = useNavigate();

  return (
    <DashboardShell>
      <div style={{ maxWidth: 960, margin: '0 auto', padding: '32px 40px' }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div>
            <span
              style={{
                fontFamily: "'Lexend', sans-serif",
                fontWeight: 500,
                fontSize: 12,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: 'var(--text-tertiary)',
              }}
            >
              CURRICULUM
            </span>
            <h1
              style={{
                fontFamily: "'Plus Jakarta Sans', sans-serif",
                fontWeight: 700,
                fontSize: 28,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
                margin: '4px 0 4px 0',
              }}
            >
              Subjects
            </h1>
            <p style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--text-tertiary)', margin: 0 }}>
              {subjects.length} active subjects this term
            </p>
          </div>
        </div>

        {/* Subject cards */}
        <div className="flex flex-col gap-4 mt-6">
          {subjects.map(subject => (
            <div
              key={subject.id}
              onClick={() => navigate('/teacher/class/1')}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                backdropFilter: 'blur(16px) saturate(140%)',
                WebkitBackdropFilter: 'blur(16px) saturate(140%)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: 20,
                boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 8px 32px rgba(0, 0, 0, 0.3)',
                padding: '24px 28px',
                cursor: 'pointer',
                transition: 'all 300ms cubic-bezier(0.16, 1, 0.3, 1)',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.12)';
                e.currentTarget.style.boxShadow = 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 12px 40px rgba(0, 0, 0, 0.4)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                e.currentTarget.style.boxShadow = 'inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 8px 32px rgba(0, 0, 0, 0.3)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--primary-50)',
                      color: 'var(--primary-700)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <BookOpen size={24} />
                  </div>
                  <div>
                    <h2
                      style={{
                        fontFamily: "'Plus Jakarta Sans', sans-serif",
                        fontWeight: 600,
                        fontSize: 18,
                        color: 'var(--text-primary)',
                        margin: '0 0 4px 0',
                      }}
                    >
                      {subject.name}
                    </h2>
                    <p style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 13, color: 'var(--text-tertiary)', margin: 0 }}>
                      {subject.code} · Last activity {subject.recentActivity}
                    </p>
                  </div>
                </div>
                <ChevronRight size={20} style={{ color: 'var(--text-tertiary)', marginTop: 4 }} />
              </div>

              {/* Stats row */}
              <div className="flex items-center gap-8 mt-5 pt-4" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.04)' }}>
                <div className="flex items-center gap-2">
                  <Users size={15} style={{ color: 'var(--text-tertiary)' }} />
                  <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--text-secondary)' }}>
                    {subject.students} students
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp size={15} style={{ color: masteryColor(subject.avgMastery) }} />
                  <span style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 14, color: masteryColor(subject.avgMastery) }}>
                    {subject.avgMastery}% avg mastery
                  </span>
                </div>
                {(subject.atRisk > 0 || subject.needsAttention > 0) && (
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={15} style={{ color: 'var(--needs-attention)' }} />
                    <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--needs-attention)' }}>
                      {subject.atRisk + subject.needsAttention} need support
                    </span>
                  </div>
                )}
              </div>

              {/* Topic pills */}
              <div className="flex flex-wrap gap-2 mt-3">
                {subject.topics.map(topic => (
                  <span
                    key={topic}
                    style={{
                      fontFamily: "'Lexend', sans-serif",
                      fontWeight: 400,
                      fontSize: 12,
                      background: 'rgba(255, 255, 255, 0.04)',
                      color: 'var(--text-secondary)',
                      padding: '3px 10px',
                      borderRadius: 'var(--radius-full)',
                    }}
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
