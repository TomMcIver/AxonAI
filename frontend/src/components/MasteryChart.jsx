import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

function getMasteryColor(score) {
  if (score >= 0.7) return '#10B981';
  if (score >= 0.4) return '#F59E0B';
  return '#EF4444';
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-lg p-3 text-sm">
      <p className="font-medium text-[#1F2937]">{d.concept_name}</p>
      <p className="text-[#6B7280]">{d.subject}</p>
      <p className="font-semibold mt-1" style={{ color: getMasteryColor(d.mastery_score) }}>
        {(d.mastery_score * 100).toFixed(1)}% mastery
      </p>
      {d.trend && <p className="text-xs text-[#6B7280] capitalize">Trend: {d.trend}</p>}
    </div>
  );
}

export default function MasteryChart({ concepts, height = 300, maxItems = 20 }) {
  const data = (concepts || []).slice(0, maxItems).map(c => ({
    ...c,
    display_name: c.concept_name.length > 25 ? c.concept_name.slice(0, 22) + '...' : c.concept_name,
    mastery_pct: +(c.mastery_score * 100).toFixed(1),
  }));

  if (!data.length) return <p className="text-[#6B7280] text-sm">No mastery data available</p>;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
        <YAxis type="category" dataKey="display_name" width={160} tick={{ fontSize: 11 }} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="mastery_pct" radius={[0, 4, 4, 0]} barSize={16}>
          {data.map((entry, i) => (
            <Cell key={i} fill={getMasteryColor(entry.mastery_score)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
