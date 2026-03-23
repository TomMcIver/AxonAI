import React, { useState, useEffect, useRef, useCallback } from 'react';
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
import { getClassOverview, getConcepts } from '../../api/axonai';
import DashboardShell from '../../components/DashboardShell';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';

/* ─────────────────────────────────────────────
   HELPERS
   ───────────────────────────────────────────── */

function masteryColor(mastery) {
  if (mastery >= 0.91) return 'var(--mastered)';
  if (mastery >= 0.76) return 'var(--on-track)';
  if (mastery >= 0.51) return 'var(--in-progress)';
  if (mastery >= 0.26) return 'var(--needs-attention)';
  return 'var(--at-risk)';
}

function nodeColor(mastery) {
  if (mastery >= 0.91) return "#059669";
  if (mastery >= 0.76) return "#0F766E";
  if (mastery >= 0.51) return "#2563EB";
  if (mastery >= 0.26) return "#D97706";
  return "#DC2626";
}

function nodeRadius(difficulty) {
  if (difficulty <= 1) return 20;
  if (difficulty <= 3) return 26;
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

function getTrendFromScore(score) {
  // Map overall_mastery_trend to trend arrows for visualization
  if (score === 'improving') return 'up';
  if (score === 'declining') return 'down';
  return 'flat';
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
        stroke={masteryColor(mastery / 100)}
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
    const timer = setTimeout(() => {
      setOffset(circumference * (1 - value / 100));
    }, 100);

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

      <div className="flex items-center gap-3">
        {actions.map((action, i) =>
          action.primary ? (
            <button
              key={i}
              onClick={action.onClick}
              className="axon-btn axon-btn-primary"
              style={{ textTransform: 'none', letterSpacing: '0.02em' }}
            >
              {action.label}
            </button>
          ) : (
            <button
              key={i}
              onClick={action.onClick}
              className="axon-btn axon-btn-ghost"
              style={{ textTransform: 'none', letterSpacing: '0.02em' }}
            >
              {action.label}
            </button>
          )
        )}
      </div>
    </div>
  );
}

function NeedsAttentionSection({ students, navigate }) {
  // Find students at risk (overall_risk_score > 0.4 or active_flags > 0)
  const atRiskStudents = (students || [])
    .filter(s => (s.overall_risk_score && s.overall_risk_score > 0.4) || (s.active_flags && s.active_flags > 0))
    .slice(0, 2);

  if (atRiskStudents.length === 0) {
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
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm text-slate-400">All students on track! 🎉</p>
        </div>
      </section>
    );
  }

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
        {atRiskStudents.map(student => {
          const isAtRisk = student.overall_risk_score >= 0.4;
          const severity = isAtRisk ? 'At Risk' : 'Needs Attention';
          const icon = isAtRisk ? AlertCircle : AlertTriangle;
          const borderColor = isAtRisk ? 'var(--at-risk)' : 'var(--needs-attention)';
          const pillBg = isAtRisk ? 'var(--at-risk-bg)' : 'var(--needs-attention-bg)';
          const pillColor = isAtRisk ? 'var(--at-risk)' : 'var(--needs-attention)';

          return (
            <AlertCard
              key={student.student_id}
              name={`${student.first_name} ${student.last_name}`}
              severity={severity}
              icon={icon}
              borderColor={borderColor}
              pillBg={pillBg}
              pillColor={pillColor}
              body={`Risk score: ${(student.overall_risk_score * 100).toFixed(0)}%. ${student.active_flags || 0} active misconception flags.`}
              recommendation="Recommend direct teacher check-in. Review prerequisite concepts and provide targeted support."
              actions={[
                { label: 'View Profile', primary: false, onClick: () => navigate(`/teacher/student/${student.student_id}`) },
                { label: 'Start Intervention', primary: true, onClick: () => navigate(`/teacher/student/${student.student_id}`) },
              ]}
            />
          );
        })}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   TODAY'S ACTIVITY FEED (static for now)
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

const activityFeed = [
  { time: "2h ago", student: "Aroha Ngata", action: "AI Tutor session:", concept: "Trigonometry", icon: "sparkle", colour: "primary" },
  { time: "3h ago", student: "Priya Sharma", action: "Mastered", concept: "Quadratic Equations", icon: "trophy", colour: "mastered" },
  { time: "4h ago", student: "Mia Anderson", action: "Completed quiz:", concept: "Linear Functions", icon: "check", colour: "in-progress" },
  { time: "5h ago", student: "Noah Williams", action: "Flagged:", concept: "Angle Relationships", icon: "alert", colour: "needs-attention" },
  { time: "6h ago", student: "James Tūhoe", action: "Inactive —", concept: "last seen 3 days ago", icon: "clock", colour: "inactive" },
];

const studentIdByName = {};

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
   KNOWLEDGE GRAPH PREVIEW (from real API data)
   ───────────────────────────────────────────── */

function KnowledgeGraphPreview({ nodes, edges, navigate, loading, error }) {
  const [tooltip, setTooltip] = useState(null);
  const svgRef = useRef(null);

  if (loading) return <p className="text-sm text-slate-400">Loading knowledge graph...</p>;
  if (error) return <p className="text-sm text-red-500">{error}</p>;
  if (!nodes || nodes.length === 0) return <p className="text-sm text-slate-400">No concepts available.</p>;

  const nodeMap = {};
  nodes.forEach(n => { nodeMap[n.id] = n; });

  // Simple layout: position nodes in 3 columns by difficulty
  const grouped = { easy: [], medium: [], hard: [] };
  nodes.forEach(n => {
    const diff = n.difficulty_level || 3;
    if (diff <= 2) grouped.easy.push(n);
    else if (diff <= 4) grouped.medium.push(n);
    else grouped.hard.push(n);
  });

  const positionedNodes = [];
  let x = 100, y = 60;
  [grouped.easy, grouped.medium, grouped.hard].forEach((group, colIdx) => {
    x = 100 + colIdx * 300;
    y = 60;
    group.forEach(n => {
      positionedNodes.push({ ...n, x, y });
      y += 80;
    });
  });

  const svgWidth = 900;
  const svgHeight = 420;

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
          {(edges || []).map((edge, i) => {
            const src = positionedNodes.find(n => n.id === edge.prerequisite_concept_id);
            const tgt = positionedNodes.find(n => n.id === edge.concept_id);
            if (!src || !tgt) return null;
            const tgtR = nodeRadius(tgt.difficulty_level);
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
          {positionedNodes.map(node => {
            const r = nodeRadius(node.difficulty_level);
            return (
              <g
                key={node.id}
                onMouseEnter={e => {
                  const svgRect = svgRef.current.getBoundingClientRect();
                  const svgScaleX = svgRect.width / svgWidth;
                  const svgScaleY = svgRect.height / svgHeight;
                  setTooltip({
                    label: node.name,
                    mastery: (node.mastery_score * 100).toFixed(0),
                    x: svgRect.left + node.x * svgScaleX,
                    y: svgRect.top + (node.y - r - 12) * svgScaleY,
                  });
                }}
                onMouseLeave={() => setTooltip(null)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={r}
                  fill={nodeColor(node.mastery_score || 0.5)}
                  opacity={0.9}
                />
                <text
                  x={node.x}
                  y={node.y + r + 12}
                  textAnchor="middle"
                  style={{
                    fontFamily: "'Lexend', sans-serif",
                    fontWeight: 400,
                    fontSize: 10,
                    fill: 'var(--text-secondary)',
                  }}
                >
                  {node.name.substring(0, 12)}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip */}
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
              {tooltip.mastery}%
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────
   CLASS PULSE SECTION (from real API data)
   ───────────────────────────────────────────── */

function ClassPulseSection({ students, classAvg, navigate }) {
  const sortedStudents = [...(students || [])].sort((a, b) => (a.avg_mastery || 0) - (b.avg_mastery || 0));

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
            {sortedStudents.length} students
          </p>

          <div className="flex flex-wrap gap-2">
            {sortedStudents.map((st, i) => (
              <div
                key={st.student_id}
                title={`${st.first_name} ${st.last_name}: ${(st.avg_mastery * 100).toFixed(0)}%`}
                onClick={() => navigate(`/teacher/student/${st.student_id}`)}
                style={{ cursor: 'pointer' }}
              >
                <SmallMasteryRing mastery={(st.avg_mastery * 100).toFixed(0)} index={i} />
              </div>
            ))}
          </div>
        </div>

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
  const [classData, setClassData] = useState(null);
  const [conceptsData, setConceptsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getClassOverview(1),
      getConcepts('Mathematics'),
    ])
      .then(([classRes, conceptsRes]) => {
        console.log('[TeacherDashboard] Class data:', classRes);
        console.log('[TeacherDashboard] Concepts data:', conceptsRes);
        setClassData(classRes);
        setConceptsData(conceptsRes);
        setLoading(false);
      })
      .catch(e => {
        console.error('[TeacherDashboard] Error:', e);
        setError(e.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <DashboardShell subtitle="Year 11 Mathematics · Mastery signal">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading class data..." />
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell subtitle="Year 11 Mathematics · Mastery signal">
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={load} />
        </div>
      </DashboardShell>
    );
  }

  const students = classData?.students || [];
  const classAvg = classData?.class_stats?.avg_engagement
    ? Math.round((classData.class_stats.avg_engagement) * 100)
    : students.length > 0
    ? Math.round(students.reduce((s, st) => s + (st.avg_mastery || 0), 0) / students.length * 100)
    : 0;

  const conceptNodes = conceptsData?.concepts || [];
  const conceptEdges = conceptsData?.prerequisites || [];

  return (
    <DashboardShell subtitle="Year 11 Mathematics · Mastery signal">
      <style>{cssStyles}</style>
      <div className="grid gap-6 lg:gap-7">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1.1fr)]">
          <ClassPulseSection students={students} classAvg={classAvg} navigate={navigate} />
          <NeedsAttentionSection students={students} navigate={navigate} />
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1.6fr)]">
          <ActivityFeedSection navigate={navigate} />
          <KnowledgeGraphPreview
            nodes={conceptNodes}
            edges={conceptEdges}
            navigate={navigate}
            loading={false}
            error={null}
          />
        </div>
      </div>
    </DashboardShell>
  );
}
