import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { getClassOverview, getClassConceptSummary } from '../../api/axonai';
import DashboardShell from '../../components/DashboardShell';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import KnowledgeGraphNew from '../../components/KnowledgeGraphNew';
import { useClassMasteryMap } from '../../hooks/useClassMasteryMap';
import { DEMO_STUDENT_IDS, filterDemoStudents, sortWithArohaFirst } from '../../constants/demoStudents';

/* ── HELPERS ── */

function masteryColor(mastery) {
  if (mastery >= 0.91) return 'var(--mastered)';
  if (mastery >= 0.76) return 'var(--on-track)';
  if (mastery >= 0.51) return 'var(--in-progress)';
  if (mastery >= 0.26) return 'var(--needs-attention)';
  return 'var(--at-risk)';
}

/* ── MASTERY RING (configurable size) ── */

function MasteryRing({ value, label, size = 72, strokeWidth = 7 }) {
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const [offset, setOffset] = useState(circumference);
  const [displayVal, setDisplayVal] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setOffset(circumference * (1 - value / 100)), 120);
    const duration = 700;
    const start = Date.now() + 120;
    let raf;
    function tick() {
      const el = Date.now() - start;
      if (el < 0) { raf = requestAnimationFrame(tick); return; }
      const p = Math.min(el / duration, 1);
      const e = 1 - Math.pow(1 - p, 3);
      setDisplayVal(Math.round(e * value));
      if (p < 1) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => { clearTimeout(t); cancelAnimationFrame(raf); };
  }, [value, circumference]);

  const stroke = masteryColor(value / 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--surface-muted)" strokeWidth={strokeWidth} />
          <circle
            cx={size/2} cy={size/2} r={r} fill="none"
            stroke={stroke} strokeWidth={strokeWidth}
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size/2} ${size/2})`}
            style={{ transition: 'stroke-dashoffset 700ms ease-out' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          fontWeight: 700, fontSize: size > 60 ? 18 : 13,
          color: 'var(--text-primary)',
        }}>
          {displayVal}%
        </div>
      </div>
      <span style={{
        fontFamily: "'Lexend', sans-serif", fontWeight: 400,
        fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center',
      }}>
        {label}
      </span>
    </div>
  );
}

/* ── NEEDS ATTENTION CARDS ── */

function AlertCard({ name, severity, icon: IconComponent, borderColor, pillBg, pillColor, body, recommendation, actions }) {
  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.5)',
      backdropFilter: 'blur(16px) saturate(140%)',
      WebkitBackdropFilter: 'blur(16px) saturate(140%)',
      border: '1px solid rgba(255, 255, 255, 0.6)',
      borderRadius: 20,
      borderLeft: `4px solid ${borderColor}`,
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.7)',
      padding: '20px 24px',
    }}>
      <div className="flex items-center gap-3 mb-3">
        <IconComponent size={18} style={{ color: borderColor, flexShrink: 0 }} />
        <span style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>
          {name}
        </span>
        <span style={{
          fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 11, textTransform: 'uppercase',
          background: pillBg, color: pillColor, padding: '2px 10px', borderRadius: 'var(--radius-full)',
        }}>
          {severity}
        </span>
      </div>
      <p style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 15, lineHeight: 1.6, color: 'var(--text-secondary)', margin: '0 0 12px 0' }}>
        {body}
      </p>
      <div className="flex items-start gap-2 mb-4" style={{
        padding: '10px 12px', background: 'rgba(20, 184, 166, 0.06)', backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)', border: '1px solid rgba(20, 184, 166, 0.12)', borderRadius: 10,
      }}>
        <Sparkles size={14} style={{ color: 'var(--primary-500)', flexShrink: 0, marginTop: 3 }} />
        <p style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 14, lineHeight: 1.5, color: 'var(--text-secondary)', margin: 0 }}>
          {recommendation}
        </p>
      </div>
      <div className="flex items-center gap-3">
        {actions.map((action, i) => (
          <button
            key={i}
            onClick={action.onClick}
            className={`axon-btn ${action.primary ? 'axon-btn-primary' : 'axon-btn-ghost'}`}
            style={{ textTransform: 'none', letterSpacing: '0.02em' }}
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}

const RECOMMENDATIONS = [
  'Focused review of prerequisite concepts before continuing the current unit. Consider a 1:1 check-in.',
  'Engagement has been declining. Recommend pastoral care referral and a change of learning approach.',
  'Multiple misconception flags suggest foundational gaps. Try scaffolded practice on earlier topics.',
  'Consider pairing with a peer mentor and adjusting task difficulty to rebuild confidence.',
];

function NeedsAttentionSection({ students, navigate }) {
  const eligible = (students || [])
    .filter(s => s.overall_risk_score > 0.2 || (s.active_flags && s.active_flags > 0))
    .sort((a, b) => (b.overall_risk_score || 0) - (a.overall_risk_score || 0));

  const atRiskStudents = eligible.slice(0, 1);

  const sectionHeading = (
    <h2 style={{
      fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 20,
      letterSpacing: '-0.01em', color: 'var(--text-primary)', margin: '0 0 16px 0',
    }}>
      Needs Attention
    </h2>
  );

  if (atRiskStudents.length === 0) {
    return (
      <section>
        {sectionHeading}
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="text-sm text-slate-500">All students on track!</p>
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

/* ── CLASS PULSE SECTION ── */

function ClassPulseSection({ students, navigate }) {
  // Compute groups from live demo data — nothing hardcoded
  const low  = students.filter(s => (s.avg_mastery || 0) < 0.50);
  const mid  = students.filter(s => (s.avg_mastery || 0) >= 0.50 && (s.avg_mastery || 0) <= 0.75);
  const high = students.filter(s => (s.avg_mastery || 0) > 0.75);
  const total = students.length;

  const avg = arr => arr.length
    ? Math.round(arr.reduce((s, st) => s + (st.avg_mastery || 0), 0) / arr.length * 100)
    : 0;

  const lowAvg  = avg(low);
  const midAvg  = avg(mid);
  const highAvg = avg(high);

  // Overall = unweighted mean of the three band averages (matches what the rings show)
  const nonEmptyBands = [
    { avg: lowAvg, count: low.length },
    { avg: midAvg, count: mid.length },
    { avg: highAvg, count: high.length },
  ].filter(b => b.count > 0);
  const overallAvg = nonEmptyBands.length
    ? Math.round(nonEmptyBands.reduce((s, b) => s + b.avg, 0) / nonEmptyBands.length)
    : 0;

  const lowPct  = total ? Math.round((low.length  / total) * 100) : 0;
  const midPct  = total ? Math.round((mid.length  / total) * 100) : 0;
  const highPct = total ? 100 - lowPct - midPct : 0; // avoids rounding gap

  const segments = [
    { pct: lowPct,  color: '#DC2626', label: 'At Risk',   count: low.length },
    { pct: midPct,  color: '#D97706', label: 'On Track',  count: mid.length },
    { pct: highPct, color: '#059669', label: 'Excelling', count: high.length },
  ].filter(s => s.pct > 0);

  return (
    <section style={{
      background: 'var(--surface-card)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-2)',
      padding: '32px 36px',
    }}>
      {/* Header */}
      <span style={{
        fontFamily: "'Lexend', sans-serif", fontWeight: 500,
        fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.04em',
        color: 'var(--text-tertiary)',
      }}>
        CLASS PULSE
      </span>
      <h1 style={{
        fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700,
        fontSize: 28, letterSpacing: '-0.02em', color: 'var(--text-primary)',
        margin: '4px 0 2px 0',
      }}>
        Year 11 Mathematics
      </h1>
      <p style={{
        fontFamily: "'Lexend', sans-serif", fontSize: 14,
        color: 'var(--text-tertiary)', margin: '0 0 28px 0',
      }}>
        {total} students
      </p>

      {/* Main layout: bar left, rings right */}
      <div style={{ display: 'flex', gap: 32, alignItems: 'flex-start', flexWrap: 'wrap' }}>

        {/* Segmented bar */}
        <div style={{ flex: '1 1 260px', minWidth: 200 }}>
          {/* Bar */}
          <div style={{
            display: 'flex', width: '100%', height: 28,
            borderRadius: 'var(--radius-full)', overflow: 'hidden', gap: 2,
          }}>
            {segments.map((seg, i) => (
              <div
                key={seg.label}
                style={{
                  width: `${seg.pct}%`, background: seg.color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'width 700ms ease-out',
                  borderRadius: i === 0 ? '999px 0 0 999px' : i === segments.length - 1 ? '0 999px 999px 0' : 0,
                }}
              >
                {seg.pct > 10 && (
                  <span style={{
                    fontFamily: "'Plus Jakarta Sans', sans-serif",
                    fontWeight: 700, fontSize: 11, color: '#fff',
                  }}>
                    {seg.pct}%
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Labels below bar */}
          <div style={{ display: 'flex', gap: 2, marginTop: 10 }}>
            {segments.map(seg => (
              <div
                key={seg.label}
                style={{
                  width: `${seg.pct}%`,
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                }}
              >
                <span style={{
                  fontFamily: "'Lexend', sans-serif", fontWeight: 500,
                  fontSize: 12, color: seg.color, whiteSpace: 'nowrap',
                }}>
                  {seg.label}
                </span>
                <span style={{
                  fontFamily: "'Lexend', sans-serif", fontWeight: 400,
                  fontSize: 11, color: 'var(--text-tertiary)', whiteSpace: 'nowrap',
                }}>
                  {seg.count} student{seg.count !== 1 ? 's' : ''}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 4 mastery rings */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, auto)',
          gap: '16px 20px', flexShrink: 0,
        }}>
          <MasteryRing value={lowAvg}     label="Low"     size={72} strokeWidth={7} />
          <MasteryRing value={midAvg}     label="Mid"     size={72} strokeWidth={7} />
          <MasteryRing value={highAvg}    label="High"    size={72} strokeWidth={7} />
          <MasteryRing value={overallAvg} label="Overall" size={72} strokeWidth={7} />
        </div>
      </div>
    </section>
  );
}

/* ── CONCEPT STRENGTHS SECTION ── */

const SORT_OPTIONS = [
  { key: 'mastery', label: 'By Mastery' },
  { key: 'alpha', label: 'A–Z' },
  { key: 'questions', label: 'By Questions' },
];

function masteryBarColor(pct) {
  if (pct >= 0.7) return '#059669';
  if (pct >= 0.4) return '#D97706';
  return '#DC2626';
}

function SkeletonBar() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '8px 0', borderBottom: '1px solid rgba(148,163,184,0.07)',
    }}>
      <div style={{
        width: 160, height: 11, borderRadius: 6,
        background: 'rgba(148,163,184,0.15)', flexShrink: 0,
      }} />
      <div style={{ flex: 1, height: 10, borderRadius: 6, background: 'rgba(148,163,184,0.1)' }} />
      <div style={{ width: 36, height: 11, borderRadius: 6, background: 'rgba(148,163,184,0.12)' }} />
    </div>
  );
}

function ConceptStrengthsSection({ navigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState('mastery');
  const [hoveredRow, setHoveredRow] = useState(null);

  useEffect(() => {
    getClassConceptSummary(1)
      .then(d => { setData(d); setLoading(false); })
      .catch(() => { setData(null); setLoading(false); });
  }, []);

  const concepts = data?.concepts || [];

  const sorted = [...concepts].sort((a, b) => {
    if (sort === 'mastery') return (b.avg_mastery ?? 0) - (a.avg_mastery ?? 0);
    if (sort === 'alpha') return a.name.localeCompare(b.name);
    if (sort === 'questions') return (b.question_count ?? 0) - (a.question_count ?? 0);
    return 0;
  }).slice(0, 10);

  return (
    <section>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{
          fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 20,
          letterSpacing: '-0.01em', color: 'var(--text-primary)', margin: 0,
        }}>
          Class Concept Strengths
        </h2>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {SORT_OPTIONS.map(opt => (
            <button
              key={opt.key}
              onClick={() => setSort(opt.key)}
              style={{
                padding: '4px 10px', borderRadius: 20, border: 'none', cursor: 'pointer',
                fontFamily: "'Lexend', sans-serif", fontSize: 11, fontWeight: 500,
                background: sort === opt.key ? '#0F766E' : 'rgba(148,163,184,0.12)',
                color: sort === opt.key ? '#fff' : '#64748B',
                transition: 'all 140ms',
              }}
            >
              {opt.label}
            </button>
          ))}
          <button
            onClick={() => navigate('/teacher/knowledge-graph')}
            style={{
              fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 12, color: '#0f766e',
              textTransform: 'uppercase', letterSpacing: '0.06em', cursor: 'pointer',
              background: 'none', border: 'none', marginLeft: 8,
            }}
          >
            Full Graph &#8594;
          </button>
        </div>
      </div>

      <div style={{
        background: 'rgba(255,255,255,0.5)',
        backdropFilter: 'blur(16px) saturate(140%)',
        WebkitBackdropFilter: 'blur(16px) saturate(140%)',
        border: '1px solid rgba(255,255,255,0.6)',
        borderRadius: 20,
        boxShadow: '0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.7)',
        padding: '16px 20px',
      }}>
        {loading ? (
          <div>
            {[...Array(5)].map((_, i) => <SkeletonBar key={i} />)}
          </div>
        ) : sorted.length === 0 ? (
          <p style={{
            textAlign: 'center', color: '#94A3B8', fontSize: 13,
            fontFamily: "'Inter', sans-serif", padding: '20px 0',
          }}>
            Concept mastery data unavailable — deploy the <code>/class/&#123;id&#125;/concept-summary</code> endpoint to enable this widget.
          </p>
        ) : (
          <div>
            {/* Column headers */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
              paddingBottom: 8, borderBottom: '1px solid rgba(148,163,184,0.15)',
            }}>
              <span style={{ width: 180, flexShrink: 0, fontSize: 10, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94A3B8',
                fontFamily: "'Lexend', sans-serif" }}>
                Concept
              </span>
              <span style={{ flex: 1, fontSize: 10, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94A3B8',
                fontFamily: "'Lexend', sans-serif" }}>
                Class Mastery
              </span>
              <span style={{ width: 48, textAlign: 'right', fontSize: 10, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94A3B8',
                fontFamily: "'Lexend', sans-serif" }}>
                %
              </span>
            </div>

            {sorted.map((concept, i) => {
              const pct = concept.avg_mastery ?? 0;
              const barColor = masteryBarColor(pct);
              const isHov = hoveredRow === i;
              return (
                <div
                  key={concept.concept_id || i}
                  onClick={() => navigate('/teacher/knowledge-graph')}
                  onMouseEnter={() => setHoveredRow(i)}
                  onMouseLeave={() => setHoveredRow(null)}
                  title={`${concept.students_mastered ?? '?'} mastered · ${concept.students_struggling ?? '?'} struggling · ${concept.question_count ?? 0} Q`}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 8px', borderRadius: 8, cursor: 'pointer',
                    background: isHov ? 'rgba(15,118,110,0.05)' : 'transparent',
                    borderBottom: i < sorted.length - 1 ? '1px solid rgba(148,163,184,0.07)' : 'none',
                    transition: 'background 120ms',
                  }}
                >
                  {/* Name */}
                  <span style={{
                    width: 180, flexShrink: 0, fontSize: 12, color: '#334155',
                    fontFamily: "'Inter', sans-serif",
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {concept.name}
                  </span>

                  {/* Bar track */}
                  <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'rgba(148,163,184,0.15)' }}>
                    <div style={{
                      width: `${Math.round(pct * 100)}%`, height: '100%',
                      borderRadius: 4, background: barColor,
                      transition: 'width 600ms cubic-bezier(0.16,1,0.3,1)',
                    }} />
                  </div>

                  {/* Pct label */}
                  <span style={{
                    width: 36, textAlign: 'right', fontSize: 12, fontWeight: 600,
                    color: barColor, fontFamily: "'Lexend', sans-serif", flexShrink: 0,
                  }}>
                    {Math.round(pct * 100)}%
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

/* ── MAIN DASHBOARD ── */

export default function TeacherDashboard() {
  const navigate = useNavigate();
  const [classData, setClassData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([getClassOverview(1)])
      .then(([classRes]) => {
        setClassData(classRes);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  useEffect(() => { load(); }, [load]);

  const students = useMemo(
    () => sortWithArohaFirst(filterDemoStudents(classData?.students)),
    [classData],
  );

  const graphStudentIds = useMemo(
    () => students.map((s) => s.student_id ?? s.id).filter((id) => DEMO_STUDENT_IDS.includes(id)),
    [students],
  );

  const {
    masteryMap: classFairMasteryMap,
    source: cohortSource,
    studentCount: cohortN,
  } = useClassMasteryMap(1, 'Mathematics', { studentIds: graphStudentIds });

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

  return (
    <DashboardShell subtitle="Year 11 Mathematics · Mastery signal">
      <div className="grid gap-6 lg:gap-7">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1.1fr)]">
          <ClassPulseSection students={students} navigate={navigate} />
          <NeedsAttentionSection students={students} navigate={navigate} />
        </div>
        <section className="space-y-3 sm:space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
            <h2 className="axon-h2 text-base text-slate-800">Knowledge Graph</h2>
            <button
              type="button"
              onClick={() => navigate('/teacher/knowledge-graph')}
              className="axon-btn axon-btn-ghost shrink-0 self-start sm:self-auto"
            >
              Full View
            </button>
          </div>
          <p className="text-[11px] text-slate-500 max-w-3xl leading-relaxed">
            Class overview shows the full concept map. Cohort colours use a median across learners when built from
            individual mastery (and a softened display scale) so outliers don’t dominate; class-summary uses the API
            average with the same scaling. Shaded boxes group nodes by prerequisite depth (fundamentals on the left).
            Use Whole class vs Concepts to switch cohort colouring off.
          </p>
          <div className="axon-card-subtle flex min-h-0 flex-col rounded-lg p-3 sm:p-4">
            <KnowledgeGraphNew
              subject="Mathematics"
              mapOnly
              focusKeyNodes={false}
              defaultExploration="canvas"
              masteryMap={classFairMasteryMap || undefined}
              showTeacherViewToggle
              cohortMasteryMeta={
                cohortSource === 'student-aggregate' && cohortN > 0
                  ? { source: 'student-aggregate', studentCount: cohortN }
                  : cohortSource === 'class-summary'
                    ? { source: 'class-summary' }
                    : null
              }
            />
          </div>
        </section>
        <ConceptStrengthsSection navigate={navigate} />
      </div>
    </DashboardShell>
  );
}
