import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

function getRiskLevel(score) {
  if (score >= 0.4) return { label: 'High', color: '#ef4444', bg: 'bg-rose-500/10 text-rose-400' };
  if (score >= 0.2) return { label: 'Medium', color: '#f59e0b', bg: 'bg-amber-500/10 text-amber-400' };
  return { label: 'Low', color: '#10b981', bg: 'bg-emerald-500/10 text-emerald-400' };
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
              <Cell fill="rgba(51,65,85,0.5)" />
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
