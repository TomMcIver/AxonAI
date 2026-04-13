import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import {
  getStudentDashboard,
  getStudentMastery,
  getClassOverview,
  getStudentSummary,
  getConcepts,
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
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e2e8f0" strokeWidth="8" />
          <circle
            cx={size / 2} cy={size / 2} r={radius} fill="none"
            stroke="#0d9488" strokeWidth="8"
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>
        <div style={{
          position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
        }}>
          <span className="text-2xl font-bold text-slate-700">
            {Math.round(clamp01(percentage) * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
}

/* ── MASTERY NODE COLOUR ── */

function masteryNodeColor(score) {
  if (score === null || score === undefined) return '#94A3B8'; // gray — no data
  if (score < 0.40) return '#DC2626'; // red — struggling
  if (score < 0.70) return '#D97706'; // orange — developing
  return '#059669';                    // green — mastered
}

function masteryLabel(score) {
  if (score === null || score === undefined) return 'Not assessed';
  if (score < 0.40) return 'Struggling';
  if (score < 0.70) return 'Developing';
  return 'Mastered';
}

/* ── TEXT WRAP HELPER ── */

function wrapLabel(name, maxLen = 13) {
  if (name.length <= maxLen) return [name];
  const breakAt = name.lastIndexOf(' ', maxLen);
  if (breakAt > 0) {
    const line1 = name.slice(0, breakAt);
    const rest = name.slice(breakAt + 1);
    return [line1, rest.length > maxLen ? rest.slice(0, maxLen - 1) + '…' : rest];
  }
  return [name.slice(0, maxLen - 1) + '…'];
}

/* ── STUDENT KNOWLEDGE GAP GRAPH ── */

function StudentKnowledgeGraph({ graphData, masteryMap }) {
  const svgRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  if (!graphData) return null;

  const allConcepts = graphData.concepts || [];
  const allEdges = graphData.prerequisites || [];

  if (allConcepts.length === 0) return null;

  // Layout: difficulty level 1–5 mapped to columns left→right
  const COL_X = { 1: 80, 2: 220, 3: 380, 4: 540, 5: 700 };
  const colCount = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  const NODE_SPACING = 76;
  const TOP_OFFSET = 50;

  const positioned = allConcepts.map(c => {
    const lvl = c.difficulty_level || 3;
    const idx = colCount[lvl] || 0;
    colCount[lvl] = idx + 1;
    return { ...c, x: COL_X[lvl] || 380, y: TOP_OFFSET + idx * NODE_SPACING };
  });

  const maxNodes = Math.max(...Object.values(colCount));
  const svgW = 780;
  const svgH = Math.max(360, TOP_OFFSET + maxNodes * NODE_SPACING + 40);

  const posMap = {};
  positioned.forEach(n => { posMap[n.id] = n; });

  const colLabels = [
    { x: 80,  label: 'Foundation' },
    { x: 220, label: 'Basic' },
    { x: 380, label: 'Intermediate' },
    { x: 540, label: 'Advanced' },
    { x: 700, label: 'Complex' },
  ];

  return (
    <div style={{
      background: 'rgba(255,255,255,0.5)',
      backdropFilter: 'blur(16px) saturate(140%)',
      WebkitBackdropFilter: 'blur(16px) saturate(140%)',
      border: '1px solid rgba(255,255,255,0.6)',
      borderRadius: 20,
      boxShadow: '0 4px 16px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.7)',
      overflow: 'hidden',
    }}>
      {/* Scrollable SVG */}
      <div style={{ overflowY: 'auto', maxHeight: 440 }}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${svgW} ${svgH}`}
          width="100%"
          style={{ display: 'block', minHeight: 360 }}
        >
          <defs>
            <marker id="gap-arrow" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
              <polygon points="0 0, 7 2.5, 0 5" fill="#CBD5E1" opacity="0.8" />
            </marker>
            <marker id="gap-arrow-blocked" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
              <polygon points="0 0, 7 2.5, 0 5" fill="#DC2626" opacity="0.7" />
            </marker>
          </defs>

          {/* Column labels */}
          {colLabels.map(col => (
            <text key={col.label} x={col.x} y={22} textAnchor="middle" style={{
              fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 9,
              fill: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em',
            }}>
              {col.label}
            </text>
          ))}

          {/* Edges */}
          {allEdges.map((edge, i) => {
            const src = posMap[edge.prerequisite_concept_id];
            const tgt = posMap[edge.concept_id];
            if (!src || !tgt) return null;

            const srcScore = masteryMap[src.id];
            const tgtScore = masteryMap[tgt.id];
            // Highlight edge red if source is not mastered AND target is also struggling
            const isBlocked = (srcScore !== null && srcScore !== undefined && srcScore < 0.50)
              && (tgtScore !== null && tgtScore !== undefined && tgtScore < 0.50);

            const isSameCol = Math.abs(src.x - tgt.x) < 30;
            const pathD = isSameCol
              ? `M${src.x},${src.y} C${src.x - 70},${src.y} ${tgt.x - 70},${tgt.y} ${tgt.x},${tgt.y}`
              : (() => {
                  const mx = (src.x + tgt.x) / 2;
                  const my = (src.y + tgt.y) / 2 - 18;
                  return `M${src.x},${src.y} Q${mx},${my} ${tgt.x},${tgt.y}`;
                })();
            return (
              <path
                key={i}
                d={pathD}
                fill="none"
                stroke={isBlocked ? '#DC2626' : '#CBD5E1'}
                strokeWidth={isBlocked ? 1.8 : 1.2}
                opacity={isBlocked ? 0.6 : 0.4}
                markerEnd={isBlocked ? 'url(#gap-arrow-blocked)' : 'url(#gap-arrow)'}
              />
            );
          })}

          {/* Nodes */}
          {positioned.map(node => {
            const rawScore = masteryMap[node.id];
            // masteryMap stores 0–1 floats; API may return 0–100 integers
            const score = rawScore !== null && rawScore !== undefined
              ? (rawScore > 1 ? rawScore / 100 : rawScore)
              : null;
            const color = masteryNodeColor(score);
            const r = 18;
            const displayPct = score !== null ? `${Math.round(score * 100)}%` : '—';
            return (
              <g
                key={node.id}
                style={{ cursor: 'default' }}
                onMouseEnter={e => {
                  if (!svgRef.current) return;
                  const rect = svgRef.current.getBoundingClientRect();
                  const sx = rect.width / svgW;
                  const sy = rect.height / svgH;
                  setTooltip({
                    name: node.name,
                    score: displayPct,
                    label: masteryLabel(score),
                    color,
                    x: rect.left + node.x * sx,
                    y: rect.top + (node.y - r - 10) * sy,
                  });
                }}
                onMouseLeave={() => setTooltip(null)}
              >
                <circle
                  cx={node.x} cy={node.y} r={r}
                  fill={color}
                  opacity={score === null ? 0.35 : 0.82}
                  stroke={score !== null && score < 0.50 ? color : 'transparent'}
                  strokeWidth={score !== null && score < 0.50 ? 2.5 : 0}
                  strokeOpacity={0.4}
                />
                <text x={node.x} y={node.y + 4} textAnchor="middle" style={{
                  fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700,
                  fontSize: 8, fill: '#fff', pointerEvents: 'none',
                }}>
                  {displayPct}
                </text>
                {wrapLabel(node.name, 13).map((line, li) => (
                  <text key={li} x={node.x} y={node.y + r + 12 + li * 9} textAnchor="middle" style={{
                    fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 7.5,
                    fill: '#475569', pointerEvents: 'none',
                  }}>
                    {line}
                  </text>
                ))}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div style={{
        display: 'flex', gap: 16, flexWrap: 'wrap', padding: '10px 16px',
        borderTop: '1px solid rgba(148,163,184,0.12)',
      }}>
        {[
          { color: '#94A3B8', label: 'Not assessed' },
          { color: '#DC2626', label: 'Struggling (<40%)' },
          { color: '#D97706', label: 'Developing (40–70%)' },
          { color: '#059669', label: 'Mastered (≥70%)' },
        ].map(item => (
          <span key={item.label} style={{
            display: 'flex', alignItems: 'center', gap: 5,
            fontFamily: "'Inter', sans-serif", fontSize: 10, color: '#64748B',
          }}>
            <span style={{
              width: 9, height: 9, borderRadius: '50%',
              background: item.color, display: 'inline-block', flexShrink: 0,
            }} />
            {item.label}
          </span>
        ))}
        <span style={{
          display: 'flex', alignItems: 'center', gap: 5,
          fontFamily: "'Inter', sans-serif", fontSize: 10, color: '#64748B',
        }}>
          <span style={{
            width: 18, height: 1.5, background: '#DC2626',
            opacity: 0.6, display: 'inline-block', flexShrink: 0,
          }} />
          Blocked path
        </span>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed',
          left: tooltip.x,
          top: tooltip.y - 8,
          transform: 'translateX(-50%)',
          background: 'rgba(255,255,255,0.97)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid rgba(148,163,184,0.2)',
          borderRadius: 10,
          padding: '8px 12px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          zIndex: 100,
          whiteSpace: 'nowrap',
          pointerEvents: 'none',
        }}>
          <div style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600,
            fontSize: 13, color: '#1e293b',
          }}>
            {tooltip.name}
          </div>
          <div style={{
            fontFamily: "'Inter', sans-serif", fontSize: 11,
            color: tooltip.color, marginTop: 2, fontWeight: 600,
          }}>
            {tooltip.score} · {tooltip.label}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── MAIN PAGE ── */

export default function StudentSummary() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [mastery, setMastery] = useState(null);
  const [classOverview, setClassOverview] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [graphData, setGraphData] = useState(null);
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
      getConcepts('Mathematics').catch(() => null),
    ])
      .then(([d, m, co, s, g]) => {
        setDashboard(d);
        setMastery(m);
        setClassOverview(co);
        setSummaryData(s);
        setGraphData(g);
        setLoading(false);
      })
      .catch(e => {
        console.error('Failed to fetch:', e);
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

  const { student, profile, summary } = dashboard;
  const risk = clamp01(profile?.overall_risk_score);
  const tone = riskTone(risk);

  const studentInClass = classOverview?.students?.find(
    s => s.student_id === Number(id) || s.student_id === id
  );
  const engagement = studentInClass?.engagement_percentage ?? profile?.overall_engagement_score ?? 0;

  const masteryBySubject = {};
  (mastery?.concepts || []).forEach(c => {
    if (!masteryBySubject[c.subject]) masteryBySubject[c.subject] = [];
    masteryBySubject[c.subject].push(c.mastery_score || 0);
  });

  const subjectMastery = Object.entries(masteryBySubject).map(([subject, scores]) => {
    const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    return { subject, mastery: avg };
  });

  const overallMastery = summary?.mastery?.avg_mastery ?? 0;

  // Build masteryMap: concept_id → mastery score (0–1)
  const masteryMap = {};
  (mastery?.concepts || []).forEach(c => {
    if (c.concept_id != null) {
      const raw = c.mastery_score ?? null;
      masteryMap[c.concept_id] = raw !== null ? (raw > 1 ? raw / 100 : raw) : null;
    }
  });

  const hasGraph = graphData && (graphData.concepts || []).length > 0;

  return (
    <DashboardShell subtitle="Student · summary">
      {/* Wide container for graph section; inner sections stay narrow */}
      <div className="space-y-6 px-4">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* ── Navigation ── */}
          <div className="flex items-center justify-between gap-3">
            <button className="axon-btn axon-btn-quiet" onClick={() => navigate(-1)}>
              ← Back
            </button>
          </div>

          {/* ── Student Header ── */}
          <div className="axon-card-subtle p-5 sm:p-6 text-center">
            <h1 className="axon-h2 text-2xl sm:text-3xl text-slate-800 mb-1">
              {student.first_name} {student.last_name}
            </h1>
            <p className="text-sm text-slate-400 mb-3">Year {student.year_level}</p>
            <div className={`inline-block px-3 py-1.5 rounded-lg text-sm font-semibold ${tone.color} ${tone.bg}`}>
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
                  <div key={subject} className="rounded-lg border border-slate-200/60 bg-white/40 p-4">
                    <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-2">
                      {subject}
                    </p>
                    <div className="flex items-end gap-3">
                      <p className="text-2xl font-bold text-teal-600">
                        {Math.round(clamp01(m) * 100)}%
                      </p>
                      <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                        <div className="h-full bg-teal-500" style={{ width: `${clamp01(m) * 100}%` }} />
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
              <div className="text-4xl font-bold text-sky-600">{pct(engagement)}</div>
              <p className="text-sm text-slate-600">Active participation in tutoring sessions</p>
            </div>
          </div>

          {/* ── Quick Stats ── */}
          <div className="axon-card-subtle p-5 sm:p-6">
            <p className="text-sm font-semibold text-slate-700 mb-4">Quick stats</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg bg-white/40 border border-slate-200/60 p-3">
                <p className="text-xs text-slate-400 uppercase tracking-wide font-medium">Conversations</p>
                <p className="text-xl font-bold text-slate-700 mt-1">
                  {summary?.conversations?.total_conversations ?? 0}
                </p>
              </div>
              <div className="rounded-lg bg-white/40 border border-slate-200/60 p-3">
                <p className="text-xs text-slate-400 uppercase tracking-wide font-medium">Active flags</p>
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
                {summaryData.classes.map((cls) => (
                  <div key={cls.class_name} className="axon-card-subtle p-5 sm:p-6 rounded-2xl">
                    <div className="mb-4">
                      <h3 className="text-sm font-semibold text-slate-700 mb-3">{cls.class_name}</h3>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-500 font-medium">Overall score</span>
                          <span className="text-sm font-bold text-teal-600">
                            {Math.round(cls.overall_score || 0)}%
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className="h-full bg-teal-500 transition-all duration-500 ease-out"
                            style={{ width: `${Math.min(100, Math.max(0, cls.overall_score || 0))}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {cls.top_3_mastered && cls.top_3_mastered.length > 0 && (
                      <div className="mb-4">
                        <p className="text-xs font-semibold text-slate-600 mb-2">Top 3 Mastered</p>
                        <div className="space-y-2">
                          {cls.top_3_mastered.map((concept) => (
                            <div
                              key={concept.concept_name || concept.name}
                              className="flex items-center gap-2 p-2 rounded-lg border border-green-500/40 bg-white/40"
                            >
                              <CheckCircle2 size={16} className="text-green-600 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-green-700 truncate">
                                  {concept.concept_name || concept.name}
                                </p>
                              </div>
                              <span className="text-xs font-bold text-green-600 flex-shrink-0">
                                {Math.round(concept.mastery_score || 0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {cls.bottom_3_struggling && cls.bottom_3_struggling.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-slate-600 mb-2">Bottom 3 Struggling</p>
                        <div className="space-y-2">
                          {cls.bottom_3_struggling.map((concept) => (
                            <div
                              key={concept.concept_name || concept.name}
                              className="flex items-center gap-2 p-2 rounded-lg border border-red-500/40 bg-white/40"
                            >
                              <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-red-700 truncate">
                                  {concept.concept_name || concept.name}
                                </p>
                              </div>
                              <span className="text-xs font-bold text-red-600 flex-shrink-0">
                                {Math.round(concept.mastery_score || 0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Learning Path Analysis (full-width) ── */}
        {hasGraph && (
          <div className="max-w-4xl mx-auto">
            <div className="mb-3">
              <p className="text-sm font-semibold text-slate-700">Learning path analysis</p>
              <p className="text-xs text-slate-400 mt-0.5">
                Each node shows this student's mastery. Red edges indicate a foundational gap
                blocking a higher concept — hover any node for details.
              </p>
            </div>
            <StudentKnowledgeGraph graphData={graphData} masteryMap={masteryMap} />
          </div>
        )}

        {/* ── Action Buttons ── */}
        <div className="max-w-2xl mx-auto">
          <div className="flex gap-3">
            <button
              className="flex-1 axon-btn axon-btn-primary"
              onClick={() => navigate(`/teacher/student/${id}`)}
            >
              Deep dive
            </button>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
