import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  ArrowUpDown,
  ChevronRight,
} from 'lucide-react';
import DashboardShell from '../../components/DashboardShell';

const students = [
  { id: 1, name: "Aroha Ngata", mastery: 64, risk: "needs-attention", lastActive: "2h ago", engagement: 72, trend: "down" },
  { id: 2, name: "James Tūhoe", mastery: 23, risk: "at-risk", lastActive: "3d ago", engagement: 41, trend: "down" },
  { id: 3, name: "Priya Sharma", mastery: 88, risk: "on-track", lastActive: "1h ago", engagement: 91, trend: "up" },
  { id: 4, name: "Liam Chen", mastery: 76, risk: "on-track", lastActive: "4h ago", engagement: 83, trend: "up" },
  { id: 5, name: "Sofia Ramirez", mastery: 45, risk: "needs-attention", lastActive: "1d ago", engagement: 58, trend: "flat" },
  { id: 6, name: "Noah Williams", mastery: 92, risk: "mastered", lastActive: "30m ago", engagement: 95, trend: "up" },
  { id: 7, name: "Ella Parata", mastery: 67, risk: "in-progress", lastActive: "5h ago", engagement: 74, trend: "up" },
  { id: 8, name: "Mason Patel", mastery: 31, risk: "needs-attention", lastActive: "2d ago", engagement: 49, trend: "down" },
  { id: 9, name: "Isla Mackenzie", mastery: 79, risk: "on-track", lastActive: "3h ago", engagement: 86, trend: "up" },
  { id: 10, name: "Ethan Brown", mastery: 55, risk: "in-progress", lastActive: "6h ago", engagement: 67, trend: "flat" },
  { id: 11, name: "Chloe Davis", mastery: 84, risk: "on-track", lastActive: "2h ago", engagement: 88, trend: "up" },
  { id: 12, name: "Oliver Thompson", mastery: 18, risk: "at-risk", lastActive: "5d ago", engagement: 32, trend: "down" },
  { id: 13, name: "Ava Wilson", mastery: 71, risk: "in-progress", lastActive: "1h ago", engagement: 79, trend: "up" },
  { id: 14, name: "Lucas Taylor", mastery: 60, risk: "in-progress", lastActive: "8h ago", engagement: 70, trend: "flat" },
  { id: 15, name: "Mia Anderson", mastery: 95, risk: "mastered", lastActive: "45m ago", engagement: 97, trend: "up" },
  { id: 16, name: "Henry Moore", mastery: 48, risk: "needs-attention", lastActive: "1d ago", engagement: 55, trend: "flat" },
  { id: 17, name: "Zara Jackson", mastery: 82, risk: "on-track", lastActive: "3h ago", engagement: 87, trend: "up" },
  { id: 18, name: "Jack Martin", mastery: 37, risk: "needs-attention", lastActive: "2d ago", engagement: 44, trend: "down" },
  { id: 19, name: "Lily White", mastery: 74, risk: "on-track", lastActive: "4h ago", engagement: 80, trend: "up" },
  { id: 20, name: "Samuel Harris", mastery: 63, risk: "in-progress", lastActive: "7h ago", engagement: 72, trend: "flat" },
  { id: 21, name: "Grace Clark", mastery: 89, risk: "on-track", lastActive: "1h ago", engagement: 92, trend: "up" },
  { id: 22, name: "Benjamin Lewis", mastery: 52, risk: "in-progress", lastActive: "6h ago", engagement: 61, trend: "flat" },
  { id: 23, name: "Amelia Hall", mastery: 77, risk: "on-track", lastActive: "2h ago", engagement: 83, trend: "up" },
  { id: 24, name: "William Young", mastery: 41, risk: "needs-attention", lastActive: "3d ago", engagement: 50, trend: "down" },
  { id: 25, name: "Charlotte Allen", mastery: 68, risk: "in-progress", lastActive: "5h ago", engagement: 75, trend: "up" },
  { id: 26, name: "James King", mastery: 85, risk: "on-track", lastActive: "2h ago", engagement: 89, trend: "up" },
  { id: 27, name: "Poppy Wright", mastery: 73, risk: "in-progress", lastActive: "4h ago", engagement: 78, trend: "up" },
  { id: 28, name: "Thomas Scott", mastery: 56, risk: "in-progress", lastActive: "9h ago", engagement: 65, trend: "flat" },
];

function riskPill(risk) {
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
  if (trend === 'up') return <span style={{ color: 'var(--mastered)', fontSize: 14 }}>↑</span>;
  if (trend === 'down') return <span style={{ color: 'var(--at-risk)', fontSize: 14 }}>↓</span>;
  return <span style={{ color: 'var(--text-tertiary)', fontSize: 14 }}>→</span>;
}

function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase();
}

function masteryColor(mastery) {
  if (mastery >= 91) return 'var(--mastered)';
  if (mastery >= 76) return 'var(--on-track)';
  if (mastery >= 51) return 'var(--in-progress)';
  if (mastery >= 26) return 'var(--needs-attention)';
  return 'var(--at-risk)';
}

export default function StudentsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = React.useState('');
  const [sortBy, setSortBy] = React.useState('name');
  const [sortDir, setSortDir] = React.useState('asc');

  const filtered = students
    .filter(s => s.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'name') cmp = a.name.localeCompare(b.name);
      else if (sortBy === 'mastery') cmp = a.mastery - b.mastery;
      else if (sortBy === 'engagement') cmp = a.engagement - b.engagement;
      return sortDir === 'asc' ? cmp : -cmp;
    });

  function toggleSort(field) {
    if (sortBy === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortBy(field); setSortDir('asc'); }
  }

  const atRisk = students.filter(s => s.risk === 'at-risk').length;
  const needsAtt = students.filter(s => s.risk === 'needs-attention').length;
  const onTrack = students.filter(s => s.risk === 'on-track' || s.risk === 'mastered').length;

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
              Year 11 Mathematics · {students.length} students
            </p>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-4 my-6">
          {[
            { label: 'At Risk', value: atRisk, color: 'var(--at-risk)', bg: 'var(--at-risk-bg)' },
            { label: 'Needs Attention', value: needsAtt, color: 'var(--needs-attention)', bg: 'var(--needs-attention-bg)' },
            { label: 'On Track / Mastered', value: onTrack, color: 'var(--mastered)', bg: 'var(--mastered-bg)' },
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
              { label: 'Student', field: 'name' },
              { label: 'Mastery', field: 'mastery' },
              { label: 'Engagement', field: 'engagement' },
              { label: 'Status', field: null },
              { label: 'Last Active', field: null },
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
          {filtered.map(student => (
            <div
              key={student.id}
              onClick={() => navigate(`/teacher/student/${student.id}`)}
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
                  {getInitials(student.name)}
                </div>
                <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                  {student.name}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 16, color: masteryColor(student.mastery) }}>
                  {student.mastery}%
                </span>
                {trendArrow(student.trend)}
              </div>
              <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--text-secondary)' }}>
                {student.engagement}%
              </span>
              {riskPill(student.risk)}
              <span style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 13, color: 'var(--text-tertiary)' }}>
                {student.lastActive}
              </span>
              <ChevronRight size={16} style={{ color: 'var(--text-tertiary)' }} />
            </div>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
