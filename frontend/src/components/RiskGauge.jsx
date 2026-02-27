import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

function getRiskLevel(score) {
  if (score >= 0.4) return { label: 'High', color: '#EF4444', bg: 'bg-red-100' };
  if (score >= 0.2) return { label: 'Medium', color: '#F59E0B', bg: 'bg-amber-100' };
  return { label: 'Low', color: '#10B981', bg: 'bg-green-100' };
}

export default function RiskGauge({ score, size = 120, showLabel = true }) {
  const risk = getRiskLevel(score);
  const pct = Math.round(score * 100);
  const data = [
    { value: pct },
    { value: 100 - pct },
  ];

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size / 2 + 10 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={size * 0.3}
              outerRadius={size * 0.45}
              paddingAngle={0}
              dataKey="value"
            >
              <Cell fill={risk.color} />
              <Cell fill="#E2E8F0" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      {showLabel && (
        <div className="text-center -mt-2">
          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${risk.bg}`} style={{ color: risk.color }}>
            {risk.label} Risk
          </span>
          <p className="text-xs text-[#6B7280] mt-1">{pct}%</p>
        </div>
      )}
    </div>
  );
}

export { getRiskLevel };
