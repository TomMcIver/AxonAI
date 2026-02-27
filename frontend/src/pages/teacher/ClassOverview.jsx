import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getClassOverview } from '../../api/axonai';
import Layout from '../../components/Layout';
import StudentTable from '../../components/StudentTable';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorState from '../../components/ErrorState';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

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

  if (loading) return <Layout><LoadingSpinner message="Loading class data..." /></Layout>;
  if (error) return <Layout><ErrorState message={error} onRetry={load} /></Layout>;
  if (!data) return null;

  const trendData = [
    { name: 'Improving', value: data.improving_count, color: '#10B981' },
    { name: 'Declining', value: data.declining_count, color: '#EF4444' },
    { name: 'Stable', value: data.student_count - data.improving_count - data.declining_count, color: '#6B7280' },
  ].filter(d => d.value > 0);

  const riskData = [
    { name: 'At Risk', value: data.at_risk_count, color: '#EF4444' },
    { name: 'On Track', value: data.student_count - data.at_risk_count, color: '#10B981' },
  ];

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#1F2937]">{data.class?.name}</h1>
        <p className="text-[#6B7280]">{data.class?.subject} — Year {data.class?.year_level} — {data.class?.academic_year}</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
          <p className="text-sm text-[#6B7280]">Students</p>
          <p className="text-2xl font-bold text-[#1F2937]">{data.student_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
          <p className="text-sm text-[#6B7280]">At-Risk</p>
          <p className="text-2xl font-bold text-[#EF4444]">{data.at_risk_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
          <p className="text-sm text-[#6B7280]">Avg Engagement</p>
          <p className="text-2xl font-bold text-[#0891B2]">{(data.class_stats?.avg_engagement * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
          <p className="text-sm text-[#6B7280]">Resolve Rate</p>
          <p className="text-2xl font-bold text-[#10B981]">{(data.class_stats?.resolve_rate * 100).toFixed(1)}%</p>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
          <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Mastery Trends</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={trendData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                {trendData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
          <h3 className="text-sm font-semibold text-[#1F2937] mb-3">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={riskData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                {riskData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Student table */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5">
        <h2 className="text-lg font-semibold text-[#1F2937] mb-4">All Students</h2>
        <StudentTable students={data.students} />
      </div>
    </Layout>
  );
}
