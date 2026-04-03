import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getRiskLevel } from './RiskGauge';

const PAGE_SIZE = 25;
const DEMO_STUDENT_ID = 1;

function riskColor(score) {
  if (score >= 0.4) return '#ef4444';
  if (score >= 0.2) return '#f59e0b';
  return '#10b981';
}

function masteryColor(m) {
  if (m >= 0.91) return '#059669';
  if (m >= 0.76) return '#0d9488';
  if (m >= 0.51) return '#3b82f6';
  if (m >= 0.26) return '#f59e0b';
  return '#ef4444';
}

function TrendBadge({ trend }) {
  const config = {
    improving: { label: 'Improving', color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
    declining: { label: 'Declining', color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
    stable: { label: 'Stable', color: '#64748b', bg: 'rgba(100,116,139,0.1)' },
  };
  const c = config[trend] || config.stable;
  return (
    <span
      style={{
        padding: '2px 10px',
        borderRadius: 9999,
        fontSize: 11,
        fontFamily: "'Lexend', sans-serif",
        fontWeight: 500,
        color: c.color,
        background: c.bg,
      }}
    >
      {c.label}
    </span>
  );
}

export default function StudentTable({ students = [] }) {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState('overall_risk_score');
  const [sortDir, setSortDir] = useState('desc');
  const [search, setSearch] = useState('');

  const { demoStudent, filtered } = useMemo(() => {
    const demo = students.find(s => s.student_id === DEMO_STUDENT_ID);
    let list = students.filter(s => s.student_id !== DEMO_STUDENT_ID);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(s =>
        `${s.first_name} ${s.last_name}`.toLowerCase().includes(q)
      );
    }
    list.sort((a, b) => {
      let av = a[sortKey] ?? 0;
      let bv = b[sortKey] ?? 0;
      if (sortKey === 'last_name') {
        av = (a.last_name || '').toLowerCase();
        bv = (b.last_name || '').toLowerCase();
        return sortDir === 'desc' ? bv.localeCompare(av) : av.localeCompare(bv);
      }
      return sortDir === 'desc' ? bv - av : av - bv;
    });
    const demoVisible = demo && (!search || `${demo.first_name} ${demo.last_name}`.toLowerCase().includes(search.toLowerCase()));
    return { demoStudent: demoVisible ? demo : null, filtered: list };
  }, [students, search, sortKey, sortDir]);

  const totalCount = (demoStudent ? 1 : 0) + filtered.length;
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pageStudents = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDir('desc'); }
    setPage(0);
  }

  const SortHeader = ({ label, field }) => (
    <th
      onClick={() => handleSort(field)}
      style={{
        padding: '10px 16px',
        textAlign: 'left',
        fontSize: 11,
        fontFamily: "'Lexend', sans-serif",
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        color: '#64748b',
        cursor: 'pointer',
        userSelect: 'none',
        transition: 'color 150ms',
        whiteSpace: 'nowrap',
      }}
      onMouseEnter={e => (e.currentTarget.style.color = '#e2e8f0')}
      onMouseLeave={e => (e.currentTarget.style.color = '#64748b')}
    >
      {label} {sortKey === field && (sortDir === 'desc' ? '↓' : '↑')}
    </th>
  );

  function renderRow(s, isDemo = false) {
    const risk = getRiskLevel(s.overall_risk_score);
    const signalColor = riskColor(s.overall_risk_score);
    return (
      <tr
        key={s.student_id}
        onClick={() => navigate(`/teacher/student/${s.student_id}`)}
        style={{
          cursor: 'pointer',
          transition: 'background 150ms ease-out',
          borderBottom: '1px solid rgba(148,163,184,0.06)',
          position: 'relative',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(148,163,184,0.05)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        {/* Signal bar in first cell */}
        <td style={{ padding: '10px 16px', fontSize: 14, fontFamily: "'Lexend', sans-serif", fontWeight: 500, color: '#f1f5f9' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 3, height: 28, borderRadius: 2, background: signalColor, flexShrink: 0 }} />
            <span>{s.first_name} {s.last_name}</span>
            {isDemo && (
              <span style={{
                background: 'rgba(14,165,233,0.15)',
                color: '#38bdf8',
                padding: '1px 7px',
                borderRadius: 6,
                fontSize: 10,
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                Demo
              </span>
            )}
          </div>
        </td>
        <td style={{ padding: '10px 16px', fontSize: 14, fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, color: masteryColor(s.avg_mastery) }}>
          {(s.avg_mastery * 100).toFixed(1)}%
        </td>
        <td style={{ padding: '10px 16px' }}>
          <span style={{
            padding: '2px 10px',
            borderRadius: 9999,
            fontSize: 11,
            fontFamily: "'Lexend', sans-serif",
            fontWeight: 500,
            color: risk.color,
            background: s.overall_risk_score >= 0.4 ? 'rgba(239,68,68,0.1)' : s.overall_risk_score >= 0.2 ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)',
          }}>
            {risk.label}
          </span>
        </td>
        <td style={{ padding: '10px 16px', fontSize: 13, fontFamily: "'Lexend', sans-serif", color: '#94a3b8' }}>
          {(s.overall_engagement_score * 100).toFixed(0)}%
        </td>
        <td style={{ padding: '10px 16px', fontSize: 13, fontFamily: "'Lexend', sans-serif", color: '#94a3b8' }}>
          {s.avg_quiz_score?.toFixed(1) ?? '—'}%
        </td>
        <td style={{ padding: '10px 16px', fontSize: 13, fontFamily: "'Lexend', sans-serif", color: '#94a3b8' }}>
          {s.attendance_percentage?.toFixed(1)}%
        </td>
        <td style={{ padding: '10px 16px' }}>
          <TrendBadge trend={s.overall_mastery_trend} />
        </td>
        <td style={{ padding: '10px 16px' }}>
          {s.active_flags > 0 && (
            <span style={{
              background: 'rgba(239,68,68,0.12)',
              color: '#f87171',
              padding: '2px 8px',
              borderRadius: 9999,
              fontSize: 11,
              fontWeight: 600,
              fontFamily: "'Lexend', sans-serif",
            }}>
              {s.active_flags}
            </span>
          )}
        </td>
      </tr>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'rgba(30,41,59,0.7)',
          borderRadius: 8,
          border: '1px solid rgba(148,163,184,0.12)',
          padding: '8px 12px',
          width: 280,
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input
            type="text"
            placeholder="Search students..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0); }}
            style={{
              border: 'none',
              outline: 'none',
              background: 'transparent',
              fontFamily: "'Lexend', sans-serif",
              fontWeight: 400,
              fontSize: 14,
              color: '#f1f5f9',
              width: '100%',
            }}
          />
        </div>
        <span style={{ fontSize: 13, fontFamily: "'Lexend', sans-serif", color: '#64748b' }}>
          {totalCount} students
        </span>
      </div>

      <div style={{
        borderRadius: 12,
        border: '1px solid rgba(148,163,184,0.08)',
        overflow: 'hidden',
        background: 'rgba(15,23,42,0.5)',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(148,163,184,0.1)', background: 'rgba(30,41,59,0.5)' }}>
              <SortHeader label="Name" field="last_name" />
              <SortHeader label="Mastery" field="avg_mastery" />
              <SortHeader label="Risk" field="overall_risk_score" />
              <SortHeader label="Engagement" field="overall_engagement_score" />
              <SortHeader label="Quiz Avg" field="avg_quiz_score" />
              <SortHeader label="Attendance" field="attendance_percentage" />
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontFamily: "'Lexend', sans-serif", fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b' }}>Trend</th>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontFamily: "'Lexend', sans-serif", fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b' }}>Flags</th>
            </tr>
          </thead>
          <tbody>
            {page === 0 && demoStudent && renderRow(demoStudent, true)}
            {pageStudents.map(s => renderRow(s))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            style={{
              padding: '6px 14px',
              fontSize: 13,
              fontFamily: "'Lexend', sans-serif",
              borderRadius: 8,
              border: '1px solid rgba(148,163,184,0.12)',
              background: 'rgba(30,41,59,0.5)',
              color: page === 0 ? '#475569' : '#94a3b8',
              cursor: page === 0 ? 'not-allowed' : 'pointer',
              transition: 'all 150ms',
            }}
          >
            Previous
          </button>
          <span style={{ fontSize: 13, fontFamily: "'Lexend', sans-serif", color: '#64748b' }}>
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            style={{
              padding: '6px 14px',
              fontSize: 13,
              fontFamily: "'Lexend', sans-serif",
              borderRadius: 8,
              border: '1px solid rgba(148,163,184,0.12)',
              background: 'rgba(30,41,59,0.5)',
              color: page >= totalPages - 1 ? '#475569' : '#94a3b8',
              cursor: page >= totalPages - 1 ? 'not-allowed' : 'pointer',
              transition: 'all 150ms',
            }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
