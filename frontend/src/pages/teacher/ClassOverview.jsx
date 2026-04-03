import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getClassOverview } from '../../api/axonai';
import StudentTable from '../../components/StudentTable';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import DashboardShell from '../../components/DashboardShell';

// The 26 specific students in class_id=1 with full ML data
const DEMO_CLASS_STUDENT_IDS = [
  1, 547, 548, 549, 550, 551, 552, 553, 554, 555,
  556, 557, 558, 559, 560, 561, 562, 563, 564, 565,
  566, 567, 568, 569, 570, 571,
];

export default function ClassOverview() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getClassOverview(id)
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <DashboardShell subtitle="Class overview">
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner message="Loading class data..." />
        </div>
      </DashboardShell>
    );
  }
  if (error) {
    return (
      <DashboardShell subtitle="Class overview">
        <div className="flex items-center justify-center py-16">
          <ErrorState message={error} onRetry={load} />
        </div>
      </DashboardShell>
    );
  }
  if (!data) return null;

  const roster = (data.students || []).filter(
    s => DEMO_CLASS_STUDENT_IDS.includes(s.student_id || s.id)
  );

  const counts = roster.reduce(
    (acc, s) => {
      const trend = s.overall_mastery_trend || 'stable';
      if (trend === 'improving') acc.improving += 1;
      else if (trend === 'declining') acc.declining += 1;
      else acc.stable += 1;

      const riskScore = s.overall_risk_score ?? 0;
      if (riskScore >= 0.4) acc.atRisk += 1;
      else acc.onTrack += 1;

      return acc;
    },
    { improving: 0, declining: 0, stable: 0, atRisk: 0, onTrack: 0 },
  );

  const trendData = [
    { name: 'Improving', value: counts.improving, color: '#10B981' },
    { name: 'Declining', value: counts.declining, color: '#EF4444' },
    { name: 'Stable', value: counts.stable, color: '#6B7280' },
  ].filter(d => d.value > 0);

  const riskData = [
    { name: 'At Risk', value: counts.atRisk, color: '#EF4444' },
    { name: 'On Track', value: counts.onTrack, color: '#10B981' },
  ].filter(d => d.value > 0);

  return (
    <DashboardShell subtitle={`${data.class?.name || 'Class'} · overview`}>
      <div className="space-y-5">
        <div className="axon-card-subtle p-5 sm:p-6">
          <p className="axon-label mb-1">Class</p>
          <h1 className="axon-h2 text-lg sm:text-xl text-slate-50">
            {data.class?.name}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {data.class?.subject} · Year {data.class?.year_level} · {data.class?.academic_year}
          </p>
          <p className="text-[0.72rem] text-slate-500 mt-3">
            Showing {roster.length} students in this class.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="axon-card-ghost p-4">
            <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-500">Students</p>
            <p className="text-2xl font-semibold text-slate-50">
              {roster.length}
            </p>
          </div>
          <div className="axon-card-ghost p-4" style={{ borderLeft: '3px solid #ef4444' }}>
            <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-500">At risk</p>
            <p className="text-2xl font-semibold text-rose-300">
              {counts.atRisk}
            </p>
          </div>
          <div className="axon-card-ghost p-4" style={{ borderLeft: '3px solid #3b82f6' }}>
            <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-500">Avg engagement</p>
            <p className="text-2xl font-semibold text-sky-300">
              {(data.class_stats?.avg_engagement * 100).toFixed(0)}%
            </p>
          </div>
          <div className="axon-card-ghost p-4" style={{ borderLeft: '3px solid #10b981' }}>
            <p className="text-[0.72rem] tracking-[0.16em] uppercase text-slate-500">Resolve rate</p>
            <p className="text-2xl font-semibold text-emerald-300">
              {(data.class_stats?.resolve_rate * 100).toFixed(0)}%
            </p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="axon-card-subtle p-5">
            <p className="text-sm font-semibold text-slate-100 mb-3">Trends</p>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={trendData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={72}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {trendData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15,23,42,0.95)',
                    border: '1px solid rgba(148,163,184,0.15)',
                    borderRadius: 8,
                    boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                    fontFamily: "'Lexend', sans-serif",
                    fontSize: 13,
                    color: '#e2e8f0',
                  }}
                  itemStyle={{ color: '#94a3b8' }}
                />
                <Legend
                  wrapperStyle={{
                    fontFamily: "'Lexend', sans-serif",
                    fontSize: 12,
                    color: '#64748b',
                  }}
                  formatter={(value) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="axon-card-subtle p-5">
            <p className="text-sm font-semibold text-slate-100 mb-3">Risk</p>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={72}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {riskData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15,23,42,0.95)',
                    border: '1px solid rgba(148,163,184,0.15)',
                    borderRadius: 8,
                    boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                    fontFamily: "'Lexend', sans-serif",
                    fontSize: 13,
                    color: '#e2e8f0',
                  }}
                  itemStyle={{ color: '#94a3b8' }}
                />
                <Legend
                  wrapperStyle={{
                    fontFamily: "'Lexend', sans-serif",
                    fontSize: 12,
                    color: '#64748b',
                  }}
                  formatter={(value) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="axon-card-subtle p-5">
          <div className="flex items-end justify-between gap-3 mb-3">
            <div>
              <p className="text-sm font-semibold text-slate-100">Students</p>
              <p className="text-xs text-slate-500">
                Showing {roster.length} students.
              </p>
            </div>
          </div>
          <StudentTable students={roster} />
        </div>
      </div>
    </DashboardShell>
  );
}
