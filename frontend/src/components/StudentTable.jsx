import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getRiskLevel } from './RiskGauge';

const PAGE_SIZE = 25;

function TrendBadge({ trend }) {
  const config = {
    improving: { label: 'Improving', cls: 'bg-green-100 text-green-700' },
    declining: { label: 'Declining', cls: 'bg-red-100 text-red-700' },
    stable: { label: 'Stable', cls: 'bg-gray-100 text-gray-700' },
  };
  const c = config[trend] || config.stable;
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.cls}`}>{c.label}</span>;
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
      list = list.filter(s =>
        `${s.first_name} ${s.last_name}`.toLowerCase().includes(q)
      );
    }
    list.sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      return sortDir === 'desc' ? bv - av : av - bv;
    });
    return list;
  }, [students, search, sortKey, sortDir]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pageStudents = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
    setPage(0);
  }

  function getRowBg(risk) {
    if (risk >= 0.4) return 'bg-red-50 hover:bg-red-100';
    if (risk >= 0.2) return 'bg-amber-50 hover:bg-amber-100';
    return 'hover:bg-gray-50';
  }

  const SortHeader = ({ label, field }) => (
    <th
      className="px-3 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider cursor-pointer select-none hover:text-[#1F2937]"
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field && (sortDir === 'desc' ? '↓' : '↑')}
    </th>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <input
          type="text"
          placeholder="Search students..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0); }}
          className="px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-[#0891B2] focus:border-transparent"
        />
        <span className="text-sm text-[#6B7280]">{filtered.length} students</span>
      </div>
      <div className="overflow-x-auto rounded-xl border border-[#E2E8F0]">
        <table className="w-full">
          <thead className="bg-[#F8FAFC]">
            <tr>
              <SortHeader label="Name" field="last_name" />
              <SortHeader label="Mastery" field="avg_mastery" />
              <SortHeader label="Risk" field="overall_risk_score" />
              <SortHeader label="Engagement" field="overall_engagement_score" />
              <SortHeader label="Quiz Avg" field="avg_quiz_score" />
              <SortHeader label="Attendance" field="attendance_percentage" />
              <th className="px-3 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Trend</th>
              <th className="px-3 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Flags</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0]">
            {pageStudents.map(s => {
              const risk = getRiskLevel(s.overall_risk_score);
              return (
                <tr
                  key={s.student_id}
                  className={`${getRowBg(s.overall_risk_score)} cursor-pointer transition-colors`}
                  onClick={() => navigate(`/teacher/student/${s.student_id}`)}
                >
                  <td className="px-3 py-2.5 text-sm font-medium text-[#1F2937]">
                    {s.first_name} {s.last_name}
                  </td>
                  <td className="px-3 py-2.5 text-sm">
                    <span className={s.avg_mastery >= 0.7 ? 'text-green-600' : s.avg_mastery >= 0.4 ? 'text-amber-600' : 'text-red-600'}>
                      {(s.avg_mastery * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${risk.bg}`} style={{ color: risk.color }}>
                      {risk.label}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-sm text-[#1F2937]">
                    {(s.overall_engagement_score * 100).toFixed(0)}%
                  </td>
                  <td className="px-3 py-2.5 text-sm text-[#1F2937]">
                    {s.avg_quiz_score?.toFixed(1) ?? 'N/A'}%
                  </td>
                  <td className="px-3 py-2.5 text-sm text-[#1F2937]">
                    {s.attendance_percentage?.toFixed(1)}%
                  </td>
                  <td className="px-3 py-2.5">
                    <TrendBadge trend={s.overall_mastery_trend} />
                  </td>
                  <td className="px-3 py-2.5 text-sm">
                    {s.active_flags > 0 && (
                      <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs font-medium">
                        {s.active_flags}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 text-sm border border-[#E2E8F0] rounded-lg disabled:opacity-40 hover:bg-[#F1F5F9]"
          >
            Previous
          </button>
          <span className="text-sm text-[#6B7280]">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 text-sm border border-[#E2E8F0] rounded-lg disabled:opacity-40 hover:bg-[#F1F5F9]"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
