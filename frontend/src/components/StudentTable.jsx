import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

const PAGE_SIZE = 25;

function getRiskLevel(score) {
  if (score >= 0.4) return { label: 'High', color: '#dc2626' };
  if (score >= 0.2) return { label: 'Medium', color: '#d97706' };
  return { label: 'Low', color: '#16a34a' };
}

function riskColor(score) {
  if (score >= 0.4) return '#dc2626';
  if (score >= 0.2) return '#d97706';
  return '#16a34a';
}

function masteryColor(m) {
  if (m >= 0.91) return '#059669';
  if (m >= 0.76) return '#0d9488';
  if (m >= 0.51) return '#2563eb';
  if (m >= 0.26) return '#d97706';
  return '#dc2626';
}

function TrendBadge({ trend }) {
  const config = {
    improving: { label: 'Improving', color: '#16a34a', bg: 'rgba(22,163,74,0.08)' },
    declining: { label: 'Declining', color: '#dc2626', bg: 'rgba(220,38,38,0.08)' },
    stable: { label: 'Stable', color: '#64748b', bg: 'rgba(100,116,139,0.08)' },
  };
  const c = config[trend] || config.stable;
  return (
    <span style={{
      padding: '2px 10px', borderRadius: 9999, fontSize: 11,
      fontFamily: "'Inter', sans-serif", fontWeight: 500,
      color: c.color, background: c.bg,
    }}>
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

  const filtered = useMemo(() => {
    let list = [...students];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(s => `${s.first_name} ${s.last_name}`.toLowerCase().includes(q));
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
    return list;
  }, [students, search, sortKey, sortDir]);

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
        padding: '10px 16px', textAlign: 'left', fontSize: 11,
        fontFamily: "'Inter', sans-serif", fontWeight: 500,
        textTransform: 'uppercase', letterSpacing: '0.06em',
        color: '#94a3b8', cursor: 'pointer', userSelect: 'none',
        transition: 'color 150ms', whiteSpace: 'nowrap',
      }}
      onMouseEnter={e => (e.currentTarget.style.color = '#1e293b')}
      onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}
    >
      {label} {sortKey === field && (sortDir === 'desc' ? '\u2193' : '\u2191')}
    </th>
  );

  function renderRow(s) {
    const risk = getRiskLevel(s.overall_risk_score);
    const signalColor = riskColor(s.overall_risk_score);
    return (
      <tr
        key={s.student_id}
        onClick={() => navigate(`/teacher/student/${s.student_id}/summary`)}
        style={{
          cursor: 'pointer', transition: 'background 150ms ease-out',
          borderBottom: '1px solid rgba(148,163,184,0.08)',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(148,163,184,0.06)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        <td style={{ padding: '10px 16px', fontSize: 14, fontFamily: "'Inter', sans-serif", fontWeight: 500, color: '#1e293b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 3, height: 28, borderRadius: 2, background: signalColor, flexShrink: 0 }} />
            <span>{s.first_name} {s.last_name}</span>
          </div>
        </td>
        <td style={{ padding: '10px 16px', fontSize: 14, fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, color: masteryColor(s.avg_mastery) }}>
          {(s.avg_mastery * 100).toFixed(1)}%
        </td>
        <td style={{ padding: '10px 16px' }}>
          <span style={{
            padding: '2px 10px', borderRadius: 9999, fontSize: 11,
            fontFamily: "'Inter', sans-serif", fontWeight: 500,
            color: risk.color,
            background: s.overall_risk_score >= 0.4 ? 'rgba(220,38,38,0.08)' : s.overall_risk_score >= 0.2 ? 'rgba(217,119,6,0.08)' : 'rgba(22,163,74,0.08)',
          }}>
            {risk.label}
          </span>
        </td>
        <td style={{ padding: '10px 16px', fontSize: 13, fontFamily: "'Inter', sans-serif", color: '#475569' }}>
          {(s.overall_engagement_score * 100).toFixed(0)}%
        </td>
        <td style={{ padding: '10px 16px', fontSize: 13, fontFamily: "'Inter', sans-serif", color: '#475569' }}>
          {s.avg_quiz_score?.toFixed(1) ?? '\u2014'}%
        </td>
        <td style={{ padding: '10px 16px', fontSize: 13, fontFamily: "'Inter', sans-serif", color: '#475569' }}>
          {s.attendance_percentage?.toFixed(1)}%
        </td>
        <td style={{ padding: '10px 16px' }}>
          <TrendBadge trend={s.overall_mastery_trend} />
        </td>
        <td style={{ padding: '10px 16px' }}>
          {s.active_flags > 0 && (
            <span style={{
              background: 'rgba(220,38,38,0.08)', color: '#dc2626',
              padding: '2px 8px', borderRadius: 9999, fontSize: 11,
              fontWeight: 600, fontFamily: "'Inter', sans-serif",
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
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'rgba(255,255,255,0.6)', borderRadius: 8,
          border: '1px solid rgba(148,163,184,0.2)', padding: '8px 12px', width: 280,
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input
            type="text" placeholder="Search students..." value={search}
            onChange={e => { setSearch(e.target.value); setPage(0); }}
            style={{
              border: 'none', outline: 'none', background: 'transparent',
              fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 14,
              color: '#1e293b', width: '100%',
            }}
          />
        </div>
        <span style={{ fontSize: 13, fontFamily: "'Inter', sans-serif", color: '#94a3b8' }}>
          {filtered.length} students
        </span>
      </div>

      <div style={{
        borderRadius: 20, border: '1px solid rgba(255,255,255,0.6)', overflow: 'hidden',
        background: 'rgba(255,255,255,0.5)',
        backdropFilter: 'blur(16px) saturate(140%)',
        WebkitBackdropFilter: 'blur(16px) saturate(140%)',
        boxShadow: '0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.7)',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(148,163,184,0.1)', background: 'rgba(255,255,255,0.3)' }}>
              <SortHeader label="Name" field="last_name" />
              <SortHeader label="Mastery" field="avg_mastery" />
              <SortHeader label="Risk" field="overall_risk_score" />
              <SortHeader label="Engagement" field="overall_engagement_score" />
              <SortHeader label="Quiz Avg" field="avg_quiz_score" />
              <SortHeader label="Attendance" field="attendance_percentage" />
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontFamily: "'Inter', sans-serif", fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8' }}>Trend</th>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontFamily: "'Inter', sans-serif", fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8' }}>Flags</th>
            </tr>
          </thead>
          <tbody>
            {pageStudents.map(s => renderRow(s))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="axon-btn axon-btn-ghost"
            style={{ opacity: page === 0 ? 0.4 : 1 }}
          >
            Previous
          </button>
          <span style={{ fontSize: 13, fontFamily: "'Inter', sans-serif", color: '#94a3b8' }}>
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="axon-btn axon-btn-ghost"
            style={{ opacity: page >= totalPages - 1 ? 0.4 : 1 }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
