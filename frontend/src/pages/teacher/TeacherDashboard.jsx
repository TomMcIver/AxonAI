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

// Canonical class sizes matching SubjectsPage demo data
const DEMO_CLASS_SIZE = 28;

/**
 * Pick `size` evenly-spaced students across the full mastery range so every
 * student has a different mastery score.  The result naturally produces a
 * spread of red / amber / blue / green rings.
 */
function selectRepresentativeSample(students, size = DEMO_CLASS_SIZE) {
  if (!students || students.length === 0) return [];
  if (students.length <= size) return students;

  const sorted = [...students].sort((a, b) => (a.avg_mastery || 0) - (b.avg_mastery || 0));
  const n = sorted.length;
  const step = n / size;
  const picked = [];
  for (let i = 0; i < size; i++) {
    picked.push(sorted[Math.floor(i * step)]);
  }
  return picked;
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

// Per-card AI recommendations — rotate so cards never look identical
const RECOMMENDATIONS = [
  'Focused review of prerequisite concepts before continuing the current unit. Consider a 1:1 check-in.',
  'Engagement has been declining. Recommend pastoral care referral and a change of learning approach.',
  'Multiple misconception flags suggest foundational gaps. Try scaffolded practice on earlier topics.',
  'Consider pairing with a peer mentor and adjusting task difficulty to rebuild confidence.',
];

function NeedsAttentionSection({ students, navigate }) {
  // Sort by risk descending, deduplicate by student_id, take top 2
  const seen = new Set();
  const atRiskStudents = (students || [])
    .filter(s => s.overall_risk_score > 0.4 || (s.active_flags && s.active_flags > 0))
    .sort((a, b) => (b.overall_risk_score || 0) - (a.overall_risk_score || 0))
    .filter(s => {
      if (seen.has(s.student_id)) return false;
      seen.add(s.student_id);
      return true;
    })
    .slice(0, 1);

  const sectionHeading = (
    <h2
      style={{
        fontFamily: "'Plus Jakarta Sans', sans-serif",
        fontWeight: 600,
        fontSize: 20,
        letterSpacing: '-0.01em',
        color: '#F1F5F9',
        margin: '0 0 16px 0',
      }}
    >
      Needs Attention
    </h2>
  );

  if (atRiskStudents.length === 0) {
    return (
      <section>
        {sectionHeading}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm text-slate-400">All students on track!</p>
        </div>
      </section>
    );
  }

  return (
    <section>
      {sectionHeading}
      <div className="flex flex-col gap-4">
        {atRiskStudents.map((student, idx) => {
          const risk = student.overall_risk_score || 0;
          const mastery = student.avg_mastery || 0;
          const flags = student.active_flags || 0;
          const trend = student.overall_mastery_trend || 'stable';
          const isAtRisk = risk >= 0.6;
          const severity = isAtRisk ? 'At Risk' : 'Needs Attention';
          const icon = isAtRisk ? AlertCircle : AlertTriangle;
          const borderColor = isAtRisk ? 'var(--at-risk)' : 'var(--needs-attention)';
          const pillBg = isAtRisk ? 'var(--at-risk-bg)' : 'var(--needs-attention-bg)';
          const pillColor = isAtRisk ? 'var(--at-risk)' : 'var(--needs-attention)';

          // Build a unique body description per student
          const parts = [];
          parts.push(`Overall mastery at ${(mastery * 100).toFixed(0)}%`);
          if (trend === 'declining') parts.push('trend declining');
          if (flags > 0) parts.push(`${flags} active misconception flag${flags > 1 ? 's' : ''}`);
          parts.push(`engagement ${((student.overall_engagement_score || 0) * 100).toFixed(0)}%`);
          const body = parts.join('. ') + '.';

          return (
            <AlertCard
              key={student.student_id}
              name={`${student.first_name} ${student.last_name}`}
              severity={severity}
              icon={icon}
              borderColor={borderColor}
              pillBg={pillBg}
              pillColor={pillColor}
              body={body}
              recommendation={RECOMMENDATIONS[idx % RECOMMENDATIONS.length]}
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
          color: '#F1F5F9',
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
   KNOWLEDGE GRAPH PREVIEW
   Shows a curated subset of concepts in a clean
   left-to-right prerequisite chain layout.
   ───────────────────────────────────────────── */

/**
 * From the full 97-concept DAG, pick ~12 concepts that form a readable
 * prerequisite chain across difficulty levels 1 → 5.
 */
function selectPreviewConcepts(allConcepts, allEdges) {
  if (!allConcepts?.length) return { nodes: [], edges: [] };

  // Pick 2-3 concepts per difficulty level, favouring ones with edges
  const byLevel = {};
  allConcepts.forEach(c => {
    const lvl = c.difficulty_level || 3;
    if (!byLevel[lvl]) byLevel[lvl] = [];
    byLevel[lvl].push(c);
  });

  // Build edge counts so we pick "hub" concepts
  const edgeCount = {};
  (allEdges || []).forEach(e => {
    edgeCount[e.concept_id] = (edgeCount[e.concept_id] || 0) + 1;
    edgeCount[e.prerequisite_concept_id] = (edgeCount[e.prerequisite_concept_id] || 0) + 1;
  });

  const picked = new Set();
  const pickedNodes = [];

  [1, 2, 3, 4, 5].forEach(lvl => {
    const pool = (byLevel[lvl] || [])
      .sort((a, b) => (edgeCount[b.id] || 0) - (edgeCount[a.id] || 0));
    // Take top 2-3 most-connected concepts at this level
    const take = lvl <= 2 || lvl >= 5 ? 2 : 3;
    pool.slice(0, take).forEach(c => {
      picked.add(c.id);
      pickedNodes.push(c);
    });
  });

  // Edges between picked concepts only
  const pickedEdges = (allEdges || []).filter(
    e => picked.has(e.concept_id) && picked.has(e.prerequisite_concept_id)
  );

  return { nodes: pickedNodes, edges: pickedEdges };
}

function KnowledgeGraphPreview({ nodes: allNodes, edges: allEdges, navigate }) {
  const [tooltip, setTooltip] = useState(null);
  const svgRef = useRef(null);

  if (!allNodes || allNodes.length === 0) {
    return <p className="text-sm text-slate-400">No concepts available.</p>;
  }

  const { nodes, edges } = selectPreviewConcepts(allNodes, allEdges);

  // Layout: position by difficulty level (columns) with staggered rows
  const svgWidth = 900;
  const svgHeight = 400;
  const colX = { 1: 90, 2: 250, 3: 450, 4: 650, 5: 810 };
  const colCount = {};

  const positionedNodes = nodes.map(n => {
    const lvl = n.difficulty_level || 3;
    const col = colCount[lvl] || 0;
    colCount[lvl] = col + 1;
    const x = colX[lvl] || 450;
    const y = 80 + col * 110;
    return { ...n, x, y };
  });

  const posMap = {};
  positionedNodes.forEach(n => { posMap[n.id] = n; });

  // Difficulty level colors for node fill
  function difficultyColor(level) {
    if (level <= 1) return '#10B981'; // green — foundational
    if (level <= 2) return '#0891B2'; // teal
    if (level <= 3) return '#3B82F6'; // blue
    if (level <= 4) return '#F59E0B'; // amber
    return '#EF4444';                 // red — hardest
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontWeight: 600,
            fontSize: 20,
            letterSpacing: '-0.01em',
            color: '#F1F5F9',
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
                opacity="0.4"
              />
            </marker>
          </defs>

          {/* Column labels */}
          {[
            { x: 90, label: 'Foundational' },
            { x: 250, label: 'Basic' },
            { x: 450, label: 'Intermediate' },
            { x: 650, label: 'Advanced' },
            { x: 810, label: 'Complex' },
          ].map(col => (
            <text
              key={col.label}
              x={col.x}
              y={30}
              textAnchor="middle"
              style={{
                fontFamily: "'Lexend', sans-serif",
                fontWeight: 500,
                fontSize: 10,
                fill: 'var(--text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              {col.label}
            </text>
          ))}

          {/* Edges — curved paths for clarity */}
          {edges.map((edge, i) => {
            const src = posMap[edge.prerequisite_concept_id];
            const tgt = posMap[edge.concept_id];
            if (!src || !tgt) return null;
            const mx = (src.x + tgt.x) / 2;
            const my = (src.y + tgt.y) / 2 - 20;
            return (
              <path
                key={i}
                d={`M${src.x},${src.y} Q${mx},${my} ${tgt.x},${tgt.y}`}
                fill="none"
                stroke="var(--text-tertiary)"
                strokeWidth={1.5}
                opacity={Math.max(0.2, edge.strength || 0.4)}
                markerEnd="url(#arrowhead)"
              />
            );
          })}

          {/* Nodes */}
          {positionedNodes.map(node => {
            const r = 22;
            const fill = difficultyColor(node.difficulty_level);
            return (
              <g
                key={node.id}
                onMouseEnter={e => {
                  const svgRect = svgRef.current.getBoundingClientRect();
                  const sx = svgRect.width / svgWidth;
                  const sy = svgRect.height / svgHeight;
                  setTooltip({
                    label: node.name,
                    level: node.difficulty_level,
                    type: node.concept_type,
                    x: svgRect.left + node.x * sx,
                    y: svgRect.top + (node.y - r - 12) * sy,
                  });
                }}
                onMouseLeave={() => setTooltip(null)}
                style={{ cursor: 'pointer' }}
              >
                <circle cx={node.x} cy={node.y} r={r} fill={fill} opacity={0.85} />
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  style={{
                    fontFamily: "'Plus Jakarta Sans', sans-serif",
                    fontWeight: 700,
                    fontSize: 9,
                    fill: '#FFFFFF',
                  }}
                >
                  L{node.difficulty_level}
                </text>
                <text
                  x={node.x}
                  y={node.y + r + 14}
                  textAnchor="middle"
                  style={{
                    fontFamily: "'Lexend', sans-serif",
                    fontWeight: 400,
                    fontSize: 10,
                    fill: 'var(--text-secondary)',
                  }}
                >
                  {node.name.length > 18 ? node.name.substring(0, 16) + '…' : node.name}
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
              Level {tooltip.level} · {tooltip.type}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-3 pt-3" style={{ borderTop: '1px solid var(--surface-muted)' }}>
          {[
            { label: 'Foundational', color: '#10B981' },
            { label: 'Basic', color: '#0891B2' },
            { label: 'Intermediate', color: '#3B82F6' },
            { label: 'Advanced', color: '#F59E0B' },
            { label: 'Complex', color: '#EF4444' },
          ].map(item => (
            <span key={item.label} className="flex items-center gap-1.5" style={{ fontFamily: "'Lexend', sans-serif", fontSize: 11, color: 'var(--text-tertiary)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: item.color, display: 'inline-block' }} />
              {item.label}
            </span>
          ))}
        </div>
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

  // Cap to demo class size with representative mastery distribution
  const students = selectRepresentativeSample(classData?.students || [], DEMO_CLASS_SIZE);
  const classAvg = students.length > 0
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
