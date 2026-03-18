import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Network,
  Settings,
  ChevronDown,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  Trophy,
  CheckCircle,
  Clock,
} from 'lucide-react';
import DashboardShell from '../../components/DashboardShell';

/* ─────────────────────────────────────────────
   MOCK DATA
   ───────────────────────────────────────────── */

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

const knowledgeNodes = [
  { id: "integers", label: "Integers", x: 80, y: 220, mastery: 91, size: "leaf" },
  { id: "fractions", label: "Fractions", x: 80, y: 320, mastery: 88, size: "leaf" },
  { id: "algebra_1", label: "Linear Equations", x: 200, y: 200, mastery: 84, size: "intermediate" },
  { id: "algebra_2", label: "Quadratic Eq.", x: 200, y: 320, mastery: 78, size: "intermediate" },
  { id: "coord_geom", label: "Coord. Geometry", x: 320, y: 260, mastery: 55, size: "intermediate" },
  { id: "angles", label: "Angle Relationships", x: 440, y: 200, mastery: 38, size: "foundational" },
  { id: "sim_tri", label: "Similar Triangles", x: 440, y: 340, mastery: 42, size: "foundational" },
  { id: "pythagoras", label: "Pythagoras", x: 560, y: 270, mastery: 61, size: "intermediate" },
  { id: "trig_ratios", label: "Trig Ratios", x: 680, y: 200, mastery: 35, size: "foundational" },
  { id: "trig_graphs", label: "Trig Graphs", x: 800, y: 160, mastery: 20, size: "intermediate" },
  { id: "trig_eq", label: "Trig Equations", x: 800, y: 280, mastery: 18, size: "leaf" },
  { id: "unit_circle", label: "Unit Circle", x: 680, y: 340, mastery: 22, size: "intermediate" },
];

const knowledgeEdges = [
  ["integers", "algebra_1"],
  ["fractions", "algebra_1"],
  ["algebra_1", "coord_geom"],
  ["algebra_2", "coord_geom"],
  ["coord_geom", "angles"],
  ["coord_geom", "sim_tri"],
  ["angles", "pythagoras"],
  ["sim_tri", "pythagoras"],
  ["pythagoras", "trig_ratios"],
  ["angles", "trig_ratios"],
  ["sim_tri", "trig_ratios"],
  ["trig_ratios", "trig_graphs"],
  ["trig_ratios", "unit_circle"],
  ["trig_graphs", "trig_eq"],
];

const activityFeed = [
  { time: "2h ago", student: "Priya Sharma", action: "Mastered", concept: "Quadratic Equations", icon: "trophy", colour: "mastered" },
  { time: "3h ago", student: "Aroha Ngata", action: "AI Tutor session:", concept: "Angle Relationships", icon: "sparkle", colour: "primary" },
  { time: "4h ago", student: "Mia Anderson", action: "Mastered", concept: "Trigonometric Ratios", icon: "trophy", colour: "mastered" },
  { time: "5h ago", student: "Noah Williams", action: "Completed quiz:", concept: "Quadratic Factoring", icon: "check", colour: "in-progress" },
  { time: "6h ago", student: "Mason Patel", action: "Needs review:", concept: "Linear Equations", icon: "alert", colour: "needs-attention" },
  { time: "8h ago", student: "Oliver Thompson", action: "Inactive —", concept: "last seen 5 days ago", icon: "clock", colour: "inactive" },
];

/* ─────────────────────────────────────────────
   HELPERS
   ───────────────────────────────────────────── */

function masteryColor(mastery) {
  if (mastery >= 91) return 'var(--mastered)';
  if (mastery >= 76) return 'var(--on-track)';
  if (mastery >= 51) return 'var(--in-progress)';
  if (mastery >= 26) return 'var(--needs-attention)';
  return 'var(--at-risk)';
}

function nodeColor(mastery) {
  if (mastery >= 91) return "#059669";
  if (mastery >= 76) return "#0F766E";
  if (mastery >= 51) return "#2563EB";
  if (mastery >= 26) return "#D97706";
  return "#DC2626";
}

function nodeRadius(size) {
  if (size === 'leaf') return 20;
  if (size === 'intermediate') return 26;
  return 32;
}

function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase();
}

function colourVar(colour) {
  const map = {
    mastered: 'var(--mastered)',
    primary: 'var(--primary-500)',
    'in-progress': 'var(--in-progress)',
    'needs-attention': 'var(--needs-attention)',
    inactive: 'var(--inactive)',
  };
  return map[colour] || 'var(--text-tertiary)';
}

function colourBgVar(colour) {
  const map = {
    mastered: 'var(--mastered-bg)',
    primary: 'var(--primary-50)',
    'in-progress': 'var(--in-progress-bg)',
    'needs-attention': 'var(--needs-attention-bg)',
    inactive: 'var(--inactive-bg)',
  };
  return map[colour] || 'var(--surface-muted)';
}

/* ─────────────────────────────────────────────
   CSS STYLES (injected via <style>)
   ───────────────────────────────────────────── */

const cssStyles = `
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700&family=Lexend:wght@400;500&display=swap');

:root {
  /* Brand */
  --primary-900: #134E48;
  --primary-700: #0F766E;
  --primary-500: #14B8A6;
  --primary-300: #5EEAD4;
  --primary-100: #CCFBF1;
  --primary-50:  #F0FDFA;

  /* Surfaces */
  --surface-base:    #F8FAFB;
  --surface-card:    #FFFFFF;
  --surface-sidebar: #F1F5F4;
  --surface-muted:   #F1F5F9;

  /* Text */
  --text-primary:   #0F172A;
  --text-secondary: #475569;
  --text-tertiary:  #94A3B8;
  --text-inverse:   #FFFFFF;

  /* Semantic */
  --mastered:         #059669;
  --mastered-bg:      #ECFDF5;
  --on-track:         #0F766E;
  --on-track-bg:      #F0FDFA;
  --in-progress:      #2563EB;
  --in-progress-bg:   #EFF6FF;
  --needs-attention:  #D97706;
  --needs-attention-bg: #FFFBEB;
  --at-risk:          #DC2626;
  --at-risk-bg:       #FEF2F2;
  --inactive:         #94A3B8;
  --inactive-bg:      #F1F5F9;

  /* Shadows */
  --shadow-1: 0 1px 3px rgba(15,23,42,0.04), 0 1px 2px rgba(15,23,42,0.06);
  --shadow-2: 0 4px 6px rgba(15,23,42,0.04), 0 2px 4px rgba(15,23,42,0.06);
  --shadow-3: 0 12px 24px rgba(15,23,42,0.08), 0 4px 8px rgba(15,23,42,0.04);

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-full: 9999px;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1.0; }
}

.pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}

.kg-tooltip {
  pointer-events: none;
  position: absolute;
  background: var(--surface-card);
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  box-shadow: var(--shadow-2);
  z-index: 50;
  white-space: nowrap;
}
`;

/* ─────────────────────────────────────────────
   SMALL MASTERY RING (24px)
   ───────────────────────────────────────────── */

function SmallMasteryRing({ mastery, index }) {
  const size = 24;
  const strokeWidth = 3;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOffset(circumference * (1 - mastery / 100));
    }, index * 30);
    return () => clearTimeout(timer);
  }, [mastery, index, circumference]);

  return (
    <svg width={size} height={size} style={{ display: 'block' }}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="var(--surface-muted)"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={masteryColor(mastery)}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dashoffset 800ms ease-out' }}
      />
    </svg>
  );
}

/* ─────────────────────────────────────────────
   LARGE MASTERY RING (80px) — Class Average
   ───────────────────────────────────────────── */

function ClassAverageRing({ value }) {
  const size = 80;
  const strokeWidth = 8;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const [offset, setOffset] = useState(circumference);
  const [displayVal, setDisplayVal] = useState(0);

  useEffect(() => {
    // Animate arc
    const timer = setTimeout(() => {
      setOffset(circumference * (1 - value / 100));
    }, 100);

    // Animate number count-up
    const duration = 800;
    const startTime = Date.now() + 100;
    let raf;
    function tick() {
      const elapsed = Date.now() - startTime;
      if (elapsed < 0) {
        raf = requestAnimationFrame(tick);
        return;
      }
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayVal(Math.round(eased * value));
      if (progress < 1) {
        raf = requestAnimationFrame(tick);
      }
    }
    raf = requestAnimationFrame(tick);
    return () => {
      clearTimeout(timer);
      cancelAnimationFrame(raf);
    };
  }, [value, circumference]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="var(--surface-muted)"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="var(--on-track)"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 800ms ease-out' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontWeight: 700,
            fontSize: 22,
            color: 'var(--text-primary)',
          }}
        >
          {displayVal}%
        </div>
      </div>
      <span
        style={{
          fontFamily: "'Lexend', sans-serif",
          fontWeight: 400,
          fontSize: 14,
          color: 'var(--text-tertiary)',
        }}
      >
        Class Average
      </span>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SIDEBAR
   ───────────────────────────────────────────── */

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', active: true, path: '/teacher' },
  { icon: Users, label: 'Students', active: false, path: '/teacher/students' },
  { icon: BookOpen, label: 'Subjects', active: false, path: '/teacher/subjects' },
  { icon: Network, label: 'Knowledge Graph', active: false, path: '/teacher/knowledge-graph' },
  { icon: Settings, label: 'Settings', active: false, path: '/teacher/settings' },
];

function Sidebar({ navigate }) {
  return (
    <aside
      style={{
        width: 260,
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        background: 'var(--surface-sidebar)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 40,
      }}
    >
      {/* Wordmark */}
      <div className="px-6 pt-6 pb-8">
        <span
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontWeight: 700,
            fontSize: 20,
          }}
        >
          <span style={{ color: 'var(--text-primary)' }}>axon</span>
          <span style={{ color: 'var(--primary-700)' }}>AI</span>
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1 px-3">
        {navItems.map(item => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              onClick={() => !item.active && navigate(item.path)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                height: 44,
                paddingLeft: 16,
                paddingRight: 12,
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                cursor: 'pointer',
                width: '100%',
                fontFamily: "'Lexend', sans-serif",
                fontWeight: 500,
                fontSize: 14,
                background: item.active ? 'var(--primary-50)' : 'transparent',
                color: item.active ? 'var(--primary-700)' : 'var(--text-secondary)',
                borderLeft: item.active ? '3px solid var(--primary-700)' : '3px solid transparent',
                transition: 'background 150ms, color 150ms',
              }}
              onMouseEnter={e => {
                if (!item.active) e.currentTarget.style.background = 'rgba(0,0,0,0.03)';
              }}
              onMouseLeave={e => {
                if (!item.active) e.currentTarget.style.background = 'transparent';
              }}
            >
              <Icon size={20} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* User area */}
      <div
        className="px-4 py-4 mx-3 mb-3"
        style={{
          borderTop: '1px solid rgba(0,0,0,0.08)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: 'var(--primary-100)',
            color: 'var(--primary-700)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontWeight: 600,
            fontSize: 13,
            flexShrink: 0,
          }}
        >
          MW
        </div>
        <div className="flex-1" style={{ minWidth: 0 }}>
          <div
            style={{
              fontFamily: "'Lexend', sans-serif",
              fontWeight: 500,
              fontSize: 14,
              color: 'var(--text-primary)',
            }}
          >
            Ms. Williams
          </div>
          <span
            style={{
              display: 'inline-block',
              fontFamily: "'Lexend', sans-serif",
              fontWeight: 500,
              fontSize: 11,
              textTransform: 'uppercase',
              background: 'var(--primary-100)',
              color: 'var(--primary-700)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-full)',
              marginTop: 2,
            }}
          >
            Teacher
          </span>
        </div>
        <ChevronDown size={16} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
      </div>
    </aside>
  );
}

/* ─────────────────────────────────────────────
   NEEDS ATTENTION CARDS
   ───────────────────────────────────────────── */

function AlertCard({ name, severity, icon: IconComponent, borderColor, pillBg, pillColor, body, recommendation, actions }) {
  return (
    <div
      style={{
        background: 'var(--surface-card)',
        borderRadius: 'var(--radius-lg)',
        borderLeft: `4px solid ${borderColor}`,
        boxShadow: 'var(--shadow-1)',
        padding: '20px 24px',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <IconComponent size={18} style={{ color: borderColor, flexShrink: 0 }} />
        <span
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontWeight: 600,
            fontSize: 15,
            color: 'var(--text-primary)',
          }}
        >
          {name}
        </span>
        <span
          style={{
            fontFamily: "'Lexend', sans-serif",
            fontWeight: 500,
            fontSize: 11,
            textTransform: 'uppercase',
            background: pillBg,
            color: pillColor,
            padding: '2px 10px',
            borderRadius: 'var(--radius-full)',
          }}
        >
          {severity}
        </span>
      </div>

      {/* Body */}
      <p
        style={{
          fontFamily: "'Lexend', sans-serif",
          fontWeight: 400,
          fontSize: 15,
          lineHeight: 1.6,
          color: 'var(--text-secondary)',
          margin: '0 0 12px 0',
        }}
      >
        {body}
      </p>

      {/* AI Recommendation */}
      <div className="flex items-start gap-2 mb-4" style={{ padding: '10px 12px', background: 'var(--primary-50)', borderRadius: 'var(--radius-sm)' }}>
        <Sparkles size={14} style={{ color: 'var(--primary-500)', flexShrink: 0, marginTop: 3 }} />
        <p
          style={{
            fontFamily: "'Lexend', sans-serif",
            fontWeight: 400,
            fontSize: 14,
            lineHeight: 1.5,
            color: 'var(--text-secondary)',
            margin: 0,
          }}
        >
          {recommendation}
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {actions.map((action, i) =>
          action.primary ? (
            <button
              key={i}
              onClick={action.onClick}
              style={{
                fontFamily: "'Lexend', sans-serif",
                fontWeight: 500,
                fontSize: 14,
                background: 'var(--primary-700)',
                color: 'var(--text-inverse)',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 16px',
                cursor: 'pointer',
                transition: 'opacity 150ms',
              }}
              onMouseEnter={e => (e.currentTarget.style.opacity = '0.9')}
              onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
            >
              {action.label}
            </button>
          ) : (
            <button
              key={i}
              onClick={action.onClick}
              style={{
                fontFamily: "'Lexend', sans-serif",
                fontWeight: 500,
                fontSize: 14,
                background: 'transparent',
                color: 'var(--primary-700)',
                border: 'none',
                cursor: 'pointer',
                padding: '8px 4px',
              }}
            >
              {action.label}
            </button>
          )
        )}
      </div>
    </div>
  );
}

function NeedsAttentionSection({ navigate }) {
  return (
    <section>
      <h2
        style={{
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          fontWeight: 600,
          fontSize: 20,
          letterSpacing: '-0.01em',
          color: 'var(--text-primary)',
          margin: '0 0 16px 0',
        }}
      >
        Needs Attention
      </h2>
      <div className="flex flex-col gap-4">
        <AlertCard
          name="Aroha Ngata"
          severity="Needs Attention"
          icon={AlertTriangle}
          borderColor="var(--needs-attention)"
          pillBg="var(--needs-attention-bg)"
          pillColor="var(--needs-attention)"
          body="3 prerequisite concepts for Trigonometry are below mastery threshold: Similar Triangles (42%), Angle Relationships (38%), Coordinate Geometry (55%)."
          recommendation="Focused review of angle properties and triangle similarity before continuing the Trigonometry unit."
          actions={[
            { label: 'View Profile', primary: false, onClick: () => navigate('/teacher/student/1') },
            { label: 'Start Intervention', primary: true, onClick: () => navigate('/teacher/student/1') },
          ]}
        />
        <AlertCard
          name="James Tūhoe"
          severity="At Risk"
          icon={AlertCircle}
          borderColor="var(--at-risk)"
          pillBg="var(--at-risk-bg)"
          pillColor="var(--at-risk)"
          body="Engagement has declined 38% over the past 14 days. Last active 5 days ago. Overall mastery has dropped from 31% to 23% this week."
          recommendation="Recommend direct teacher check-in. Disengagement pattern may indicate external factors. Consider pastoral care referral."
          actions={[
            { label: 'View Profile', primary: false, onClick: () => navigate('/teacher/student/2') },
            { label: 'Contact Student', primary: true, onClick: () => navigate('/teacher/student/2') },
          ]}
        />
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   TODAY'S ACTIVITY FEED
   ───────────────────────────────────────────── */

function ActivityIcon({ type, colour }) {
  const c = colourVar(colour);
  const props = { size: 14, style: { color: c } };
  switch (type) {
    case 'trophy': return <Trophy {...props} />;
    case 'sparkle': return <Sparkles {...props} />;
    case 'check': return <CheckCircle {...props} />;
    case 'alert': return <AlertTriangle {...props} />;
    case 'clock': return <Clock {...props} />;
    default: return null;
  }
}

const studentIdByName = {};
students.forEach(s => { studentIdByName[s.name] = s.id; });

function ActivityFeedSection({ navigate }) {
  return (
    <section>
      <h2
        style={{
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          fontWeight: 600,
          fontSize: 20,
          letterSpacing: '-0.01em',
          color: 'var(--text-primary)',
          margin: '0 0 16px 0',
        }}
      >
        Today's Activity
      </h2>
      <div
        style={{
          background: 'var(--surface-card)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-1)',
          overflow: 'hidden',
        }}
      >
        {activityFeed.map((item, i) => (
          <div
            key={i}
            onClick={() => {
              const sid = studentIdByName[item.student];
              if (sid) navigate(`/teacher/student/${sid}`);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 20px',
              borderLeft: `2px solid ${colourVar(item.colour)}`,
              borderBottom: i < activityFeed.length - 1 ? '1px solid var(--surface-muted)' : 'none',
              cursor: 'pointer',
              transition: 'background 150ms',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--primary-50)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            {/* Avatar */}
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                background: colourBgVar(item.colour),
                color: colourVar(item.colour),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 9,
                fontFamily: "'Plus Jakarta Sans', sans-serif",
                fontWeight: 600,
                flexShrink: 0,
              }}
            >
              {getInitials(item.student)}
            </div>
            {/* Content */}
            <div className="flex-1" style={{ minWidth: 0 }}>
              <div className="flex items-center gap-2">
                <span
                  style={{
                    fontFamily: "'Lexend', sans-serif",
                    fontWeight: 500,
                    fontSize: 14,
                    color: 'var(--text-primary)',
                  }}
                >
                  {item.student}
                </span>
                <ActivityIcon type={item.icon} colour={item.colour} />
                <span
                  style={{
                    fontFamily: "'Lexend', sans-serif",
                    fontWeight: 400,
                    fontSize: 14,
                    color: 'var(--text-secondary)',
                  }}
                >
                  {item.action} {item.concept}
                </span>
              </div>
            </div>
            {/* Timestamp */}
            <span
              style={{
                fontFamily: "'Lexend', sans-serif",
                fontWeight: 400,
                fontSize: 12,
                color: 'var(--text-tertiary)',
                flexShrink: 0,
              }}
            >
              {item.time}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   KNOWLEDGE GRAPH PREVIEW
   ───────────────────────────────────────────── */

const trigNodeIds = new Set(['trig_ratios', 'trig_graphs', 'trig_eq', 'unit_circle']);

function hasTrigOutgoing(nodeId) {
  return knowledgeEdges.some(([src, tgt]) => src === nodeId && trigNodeIds.has(tgt));
}

function KnowledgeGraphPreview({ navigate }) {
  const [tooltip, setTooltip] = useState(null);
  const svgRef = useRef(null);
  const nodeMap = {};
  knowledgeNodes.forEach(n => { nodeMap[n.id] = n; });

  const svgWidth = 900;
  const svgHeight = 420;
  const pad = 50;

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontWeight: 600,
            fontSize: 20,
            letterSpacing: '-0.01em',
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          Knowledge Graph
        </h2>
        <button
          onClick={() => navigate('/teacher/knowledge-graph')}
          style={{
            fontFamily: "'Lexend', sans-serif",
            fontWeight: 500,
            fontSize: 12,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            color: 'var(--primary-700)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          View Full Graph →
        </button>
      </div>
      <div
        style={{
          background: 'var(--surface-card)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-1)',
          padding: 16,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <svg
          ref={svgRef}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          width="100%"
          style={{ display: 'block' }}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="6"
              refX="8"
              refY="3"
              orient="auto"
            >
              <polygon
                points="0 0, 8 3, 0 6"
                fill="var(--text-tertiary)"
                opacity="0.3"
              />
            </marker>
          </defs>

          {/* Edges */}
          {knowledgeEdges.map(([srcId, tgtId], i) => {
            const src = nodeMap[srcId];
            const tgt = nodeMap[tgtId];
            if (!src || !tgt) return null;
            const tgtR = nodeRadius(tgt.size);
            const dx = tgt.x - src.x;
            const dy = tgt.y - src.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const endX = tgt.x - (dx / dist) * tgtR;
            const endY = tgt.y - (dy / dist) * tgtR;
            return (
              <line
                key={i}
                x1={src.x}
                y1={src.y}
                x2={endX}
                y2={endY}
                stroke="var(--text-tertiary)"
                strokeWidth={1.5}
                opacity={0.3}
                markerEnd="url(#arrowhead)"
              />
            );
          })}

          {/* Nodes */}
          {knowledgeNodes.map(node => {
            const r = nodeRadius(node.size);
            const shouldPulse = node.mastery < 50 && knowledgeEdges.some(
              ([src]) => src === node.id && trigNodeIds.has(knowledgeEdges.find(([s]) => s === node.id)?.[1])
            );
            const pulseNode = node.mastery < 50 && (
              hasTrigOutgoing(node.id) || trigNodeIds.has(node.id)
            );
            return (
              <g
                key={node.id}
                onMouseEnter={e => {
                  const svgRect = svgRef.current.getBoundingClientRect();
                  const svgScaleX = svgRect.width / svgWidth;
                  const svgScaleY = svgRect.height / svgHeight;
                  setTooltip({
                    label: node.label,
                    mastery: node.mastery,
                    x: svgRect.left + node.x * svgScaleX,
                    y: svgRect.top + (node.y - r - 12) * svgScaleY,
                  });
                }}
                onMouseLeave={() => setTooltip(null)}
                style={{ cursor: 'pointer' }}
              >
                {pulseNode && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={r + 6}
                    fill="none"
                    stroke="#D97706"
                    strokeWidth={2}
                    className="pulse-glow"
                  />
                )}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={r}
                  fill={nodeColor(node.mastery)}
                  opacity={0.9}
                />
                <text
                  x={node.x}
                  y={node.y + r + 16}
                  textAnchor="middle"
                  style={{
                    fontFamily: "'Lexend', sans-serif",
                    fontWeight: 400,
                    fontSize: 11,
                    fill: 'var(--text-secondary)',
                  }}
                >
                  {node.label}
                </text>
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  style={{
                    fontFamily: "'Plus Jakarta Sans', sans-serif",
                    fontWeight: 700,
                    fontSize: r >= 26 ? 12 : 10,
                    fill: '#FFFFFF',
                  }}
                >
                  {node.mastery}%
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip (portal-style, positioned absolutely) */}
        {tooltip && (
          <div
            style={{
              position: 'fixed',
              left: tooltip.x,
              top: tooltip.y - 8,
              transform: 'translateX(-50%)',
              background: 'var(--surface-card)',
              border: '1px solid #E2E8F0',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 10px',
              boxShadow: 'var(--shadow-2)',
              zIndex: 50,
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
            }}
          >
            <div style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
              {tooltip.label}
            </div>
            <div style={{ fontFamily: "'Lexend', sans-serif", fontWeight: 400, fontSize: 12, color: 'var(--text-tertiary)' }}>
              Class average: {tooltip.mastery}%
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   CLASS PULSE SECTION
   ───────────────────────────────────────────── */

function ClassPulseSection({ navigate }) {
  const sortedStudents = [...students].sort((a, b) => a.mastery - b.mastery);
  const classAvg = Math.round(students.reduce((s, st) => s + st.mastery, 0) / students.length);

  return (
    <section
      style={{
        background: 'var(--surface-card)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-2)',
        padding: '32px 36px',
      }}
    >
      <div className="flex items-start justify-between gap-8">
        {/* Left — Distribution */}
        <div className="flex-1">
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
            CLASS PULSE
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
            Year 11 Mathematics
          </h1>
          <p
            style={{
              fontFamily: "'Lexend', sans-serif",
              fontWeight: 400,
              fontSize: 14,
              color: 'var(--text-tertiary)',
              margin: '0 0 24px 0',
            }}
          >
            28 students · Term 1, Week 8
          </p>

          {/* Mini mastery rings */}
          <div className="flex flex-wrap gap-2">
            {sortedStudents.map((st, i) => (
              <div
                key={st.id}
                title={`${st.name}: ${st.mastery}%`}
                onClick={() => navigate(`/teacher/student/${st.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <SmallMasteryRing mastery={st.mastery} index={i} />
              </div>
            ))}
          </div>
        </div>

        {/* Right — Class Average */}
        <div className="flex items-center justify-center" style={{ paddingTop: 32 }}>
          <ClassAverageRing value={classAvg} />
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   MAIN DASHBOARD
   ───────────────────────────────────────────── */

export default function TeacherDashboard() {
  const navigate = useNavigate();

  return (
    <DashboardShell subtitle="Year 11 Mathematics · Mastery signal">
      <div className="grid gap-6 lg:gap-7">
        {/* Top: class pulse + at-risk */}
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1.1fr)]">
          <ClassPulseSection navigate={navigate} />
          <NeedsAttentionSection navigate={navigate} />
        </div>

        {/* Bottom: activity + knowledge graph */}
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1.6fr)]">
          <ActivityFeedSection navigate={navigate} />
          <KnowledgeGraphPreview navigate={navigate} />
        </div>
      </div>
    </DashboardShell>
  );
}
