import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHealth } from '../api/axonai';

const roles = [
  {
    id: 'teacher',
    label: 'Teacher',
    description: 'Sarah Mitchell — Year 12 Mathematics & Biology',
    icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    path: '/teacher',
    color: '#1E2761',
  },
  {
    id: 'student',
    label: 'Student',
    description: 'Aroha Ngata — Year 12',
    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    path: '/student',
    color: '#0891B2',
  },
  {
    id: 'parent',
    label: 'Parent / Whanau',
    description: "Aroha Ngata's family",
    icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1',
    path: '/parent',
    color: '#10B981',
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHealth()
      .then(d => { setHealth(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#1E2761] flex flex-col">
      {/* Header */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="w-16 h-16 bg-[#0891B2] rounded-2xl flex items-center justify-center mb-6">
          <span className="text-white font-bold text-3xl">A</span>
        </div>
        <h1 className="text-4xl font-bold text-white mb-2">AxonAI</h1>
        <p className="text-[#94A3B8] text-lg mb-2">AI-Native School Intelligence Platform</p>
        <p className="text-[#64748B] text-sm mb-10">NCEA Levels 1-3 — New Zealand Secondary Schools</p>

        {/* Status */}
        {loading ? (
          <div className="flex items-center gap-2 mb-8">
            <div className="w-3 h-3 border-2 border-[#0891B2] border-t-transparent rounded-full animate-spin" />
            <span className="text-[#94A3B8] text-sm">Connecting to API...</span>
          </div>
        ) : health ? (
          <div className="flex items-center gap-2 mb-8">
            <div className="w-2.5 h-2.5 bg-[#10B981] rounded-full" />
            <span className="text-[#94A3B8] text-sm">
              {health.stats.students} students, {health.stats.conversations} conversations, {health.stats.concepts} concepts
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 mb-8">
            <div className="w-2.5 h-2.5 bg-[#EF4444] rounded-full" />
            <span className="text-[#94A3B8] text-sm">API unavailable — data may not load</span>
          </div>
        )}

        {/* Role cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl">
          {roles.map(role => (
            <button
              key={role.id}
              onClick={() => navigate(role.path)}
              className="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl p-6 text-left transition-all group"
            >
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: role.color + '30' }}>
                <svg className="w-6 h-6" style={{ color: role.color === '#1E2761' ? '#94A3B8' : role.color }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={role.icon} />
                </svg>
              </div>
              <h3 className="text-white font-semibold mb-1 group-hover:text-[#0891B2] transition-colors">{role.label}</h3>
              <p className="text-[#64748B] text-sm">{role.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center pb-6">
        <p className="text-[#475569] text-xs">Built with AI for New Zealand schools</p>
      </div>
    </div>
  );
}
