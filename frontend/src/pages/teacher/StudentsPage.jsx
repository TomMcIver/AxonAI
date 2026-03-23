import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  ArrowUpDown,
  ChevronRight,
} from 'lucide-react';
import { getClassOverview } from '../../api/axonai';
import DashboardShell from '../../components/DashboardShell';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';

// Must match SubjectsPage demo class size for Year 11 Mathematics
const DEMO_CLASS_SIZE = 28;

/**
 * Pick a representative sample that gives ~20% at-risk (red),
 * ~50% needs-attention (amber), ~30% on-track (blue/green).
 */
function selectRepresentativeSample(students, size = DEMO_CLASS_SIZE) {
  if (!students || students.length === 0) return [];
  if (students.length <= size) return students;

  const sorted = [...students].sort((a, b) => (a.avg_mastery || 0) - (b.avg_mastery || 0));
  const n = sorted.length;

  const redCount    = Math.round(size * 0.20);
  const yellowCount = Math.round(size * 0.50);
  const greenCount  = size - redCount - yellowCount;

  const bottom = sorted.slice(0, redCount);

  const midStart  = Math.floor(n * 0.30);
  const midSlice  = sorted.slice(midStart, Math.floor(n * 0.70));
  const midOffset = Math.max(0, Math.floor((midSlice.length - yellowCount) / 2));
  const middle    = midSlice.slice(midOffset, midOffset + yellowCount);

  const top = sorted.slice(-greenCount);

  return [...bottom, ...middle, ...top].slice(0, size);
}

function riskPill(riskScore) {
  let risk;
  if (riskScore >= 0.4) risk = 'at-risk';
  else if (riskScore >= 0.2) risk = 'needs-attention';
  else risk = 'on-track';

  const styles = {
    mastered: { bg: 'var(--mastered-bg)', color: 'var(--mastered)', label: 'Mastered' },
    'on-track': { bg: 'var(--on-track-bg)', color: 'var(--on-track)', label: 'On Track' },
    'in-progress': { bg: 'var(--in-progress-bg)', color: 'var(--in-progress)', label: 'In Progress' },
    'needs-attention': { bg: 'var(--needs-attention-bg)', color: 'var(--needs-attention)', label: 'Needs Attention' },
    'at-risk': { bg: 'var(--at-risk-bg)', color: 'var(--at-risk)', label: 'At Risk' },
  };
  const s = styles[risk] || styles['in-progress'];
  return (
    <span
      style={{
        display: 'inline-block',
        fontFamily: "'Lexend', sans-serif",
        fontWeight: 500,
        fontSize: 11,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        background: s.bg,
        color: s.color,
        padding: '2px 10px',
        borderRadius: 'var(--radius-full)',
      }}
    >
      {s.label}
    </span>
  );
}

function trendArrow(trend) {
  if (trend === 'improving') return <span style={{ color: 'var(--mastered)', fontSize: 14 }}>↑</span>;
  if (trend === 'declining') return <span style={{ color: 'var(--at-risk)', fontSize: 14 }}>↓</span>;
  return <span style={{ color: 'var(--text-tertiary)', fontSize: 14 }}>→</span>;
}

function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase();
}

function masteryColor(mastery) {
  if (mastery >= 0.91) return 'var(--mastered)';
  if (mastery >= 0.76) return 'var(--on-track)';
  if (mastery >= 0.51) return 'var(--in-progress)';
  if (mastery >= 0.26) return 'var(--needs-attention)';
  return 'var(--at-risk)';
}

export default function StudentsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = React.useState('');
  const [sortBy, setSortBy] = React.useState('overall_risk_score');
  const [sortDir, setSortDir] = React.useState('desc');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getClassOverview(1)
      .then(d => {
        console.log('[StudentsPage] Class overview data:', d);
        setData(d);
        setLoading(false);
      })
      .catch(e => {
        console.error('[StudentsPage] Error:', e);
        setError(e.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => { load(); }, [load]);

  const students = useMemo(() => {
    // Cap to demo class size first, then filter/sort
    const sample = selectRepresentativeSample(data?.students || [], DEMO_CLASS_SIZE);
    const list = sample
      .filter(s => `${s.first_name} ${s.last_name}`.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => {
        let av = a[sortBy] ?? 0;
        let bv = b[sortBy] ?? 0;
        // Handle string sort for last_name
        if (sortBy === 'last_name') {
          av = (a.last_name || '').toLowerCase();
          bv = (b.last_name || '').toLowerCase();
          return sortDir === 'desc' ? bv.localeCompare(av) : av.localeCompare(bv);
        }
        return sortDir === 'desc' ? bv - av : av - bv;
      });
    return list;
  }, [data, search, sortBy, sortDir]);

  function toggleSort(field) {
    if (sortBy === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortBy(field); setSortDir('desc'); }
  }

  if (loading) {
    return (
      <DashboardShell>
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading student roster..." />
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell>
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={load} />
        </div>
      </DashboardShell>
    );
  }

  const atRisk = students.filter(s => s.overall_risk_score >= 0.4).length;
  const needsAtt = students.filter(s => s.overall_risk_score >= 0.2 && s.overall_risk_score < 0.4).length;
  const onTrack = students.filter(s => s.overall_risk_score < 0.2).length;

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
              STUDENT ROSTER
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
              Students
            </h1>
            <p style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--text-tertiary)', margin: 0 }}>
              {data?.class?.subject || 'Mathematics'} · {DEMO_CLASS_SIZE} students
            </p>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-4 my-6">
          {[
            { label: 'At Risk', value: atRisk, color: 'var(--at-risk)', bg: 'var(--at-risk-bg)' },
            { label: 'Needs Attention', value: needsAtt, color: 'var(--needs-attention)', bg: 'var(--needs-attention-bg)' },
            { label: 'On Track', value: onTrack, color: 'var(--mastered)', bg: 'var(--mastered-bg)' },
          ].map(card => (
            <div
              key={card.label}
              style={{
                background: card.bg,
                borderRadius: 'var(--radius-md)',
                padding: '16px 20px',
              }}
            >
              <div style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700, fontSize: 32, color: card.color }}>
                {card.value}
              </div>
              <div style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 14, color: card.color }}>
                {card.label}
              </div>
            </div>
          ))}
        </div>

        {/* Search */}
        <div className="flex items-center gap-3 mb-4">
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: 'var(--surface-card)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid #E2E8F0',
              padding: '8px 12px',
            }}
          >
            <Search size={16} style={{ color: 'var(--text-tertiary)' }} />
            <input
              type="text"
              placeholder="Search students..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                border: 'none',
                outline: 'none',
                background: 'transparent',
                fontFamily: "'Lexend', sans-serif",
                fontWeight: 400,
                fontSize: 14,
                color: 'var(--text-primary)',
                width: '100%',
              }}
            />
          </div>
        </div>

        {/* Table */}
        <div
          style={{
            background: 'var(--surface-card)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-1)',
            overflow: 'hidden',
          }}
        >
          {/* Table header */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 40px',
              padding: '12px 20px',
              borderBottom: '1px solid var(--surface-muted)',
              background: 'var(--surface-muted)',
            }}
          >
            {[
              { label: 'Student', field: 'last_name' },
              { label: 'Mastery', field: 'avg_mastery' },
              { label: 'Engagement', field: 'overall_engagement_score' },
              { label: 'Status', field: null },
              { label: 'Trend', field: null },
            ].map(col => (
              <button
                key={col.label}
                onClick={() => col.field && toggleSort(col.field)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  fontFamily: "'Lexend', sans-serif",
                  fontWeight: 500,
                  fontSize: 12,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  color: 'var(--text-tertiary)',
                  background: 'none',
                  border: 'none',
                  cursor: col.field ? 'pointer' : 'default',
                  padding: 0,
                }}
              >
                {col.label}
                {col.field && <ArrowUpDown size={12} />}
              </button>
            ))}
            <span />
          </div>

          {/* Rows */}
          {students.map(student => (
            <div
              key={student.student_id}
              onClick={() => navigate(`/teacher/student/${student.student_id}`)}
              style={{
                display: 'grid',
                gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 40px',
                padding: '14px 20px',
                borderBottom: '1px solid var(--surface-muted)',
                cursor: 'pointer',
                transition: 'background 150ms',
                alignItems: 'center',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--primary-50)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <div className="flex items-center gap-3">
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: 'var(--primary-100)',
                    color: 'var(--primary-700)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: "'Plus Jakarta Sans', sans-serif",
                    fontWeight: 600,
                    fontSize: 11,
                    flexShrink: 0,
                  }}
                >
                  {getInitials(`${student.first_name} ${student.last_name}`)}
                </div>
                <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                  {student.first_name} {student.last_name}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 16, color: masteryColor(student.avg_mastery) }}>
                  {(student.avg_mastery * 100).toFixed(0)}%
                </span>
                {trendArrow(student.overall_mastery_trend)}
              </div>
              <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--text-secondary)' }}>
                {(student.overall_engagement_score * 100).toFixed(0)}%
              </span>
              {riskPill(student.overall_risk_score)}
              <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 12, color: 'var(--text-tertiary)' }}>
                {student.active_flags > 0 ? `${student.active_flags} flags` : '—'}
              </span>
              <ChevronRight size={16} style={{ color: 'var(--text-tertiary)' }} />
            </div>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
