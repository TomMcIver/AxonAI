import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHealth } from '../api/axonai';
import { Button, Card } from 'pixel-retroui';

const roles = [
  {
    id: 'teacher',
    label: 'Teacher',
    description: 'See mastery, risk and AI interventions for every class.',
    badge: 'Most used',
    icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    path: '/teacher',
    color: '#0d9488',
  },
  {
    id: 'student',
    label: 'Student',
    description: 'Personalised mastery map, tutor chat and next best step.',
    badge: 'Learner',
    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    path: '/student',
    color: '#16a34a',
  },
  {
    id: 'parent',
    label: 'Parent / Whanau',
    description: 'Calm, narrative view of progress across each subject.',
    badge: 'Whanau',
    icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1',
    path: '/parent',
    color: '#ea580c',
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHealth()
      .then(d => {
        setHealth(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const statusNode = (() => {
    if (loading) {
      return (
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/60 px-3 py-1.5">
          <span className="h-2 w-2 rounded-full border border-teal-500 border-t-transparent animate-spin" />
          <span className="text-xs text-slate-600">Connecting to AxonAI...</span>
        </div>
      );
    }
    if (health) {
      return (
        <div className="inline-flex items-center gap-3 rounded-full border border-emerald-300/50 bg-emerald-50/60 px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
          <span className="text-xs text-slate-700">
            <span className="font-medium text-emerald-700">Live</span>{' '}
            <span className="text-slate-400">·</span>{' '}
            {health.stats.students} students · {health.stats.conversations} conversations ·{' '}
            {health.stats.concepts} concepts
          </span>
        </div>
      );
    }
    return (
      <div className="inline-flex items-center gap-3 rounded-full border border-rose-300/50 bg-rose-50/60 px-3 py-1.5">
        <span className="h-2 w-2 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(220,38,38,0.6)]" />
        <span className="text-xs text-slate-700">
          <span className="font-medium text-rose-700">Offline demo</span>{' '}
          <span className="text-slate-400">·</span> API unavailable
        </span>
      </div>
    );
  })();

  return (
    <div className="app-shell ux-auth-surface flex min-h-screen flex-col px-[max(var(--ux-space-3),env(safe-area-inset-left))] pr-[max(var(--ux-space-3),env(safe-area-inset-right))] pb-[max(var(--ux-space-3),env(safe-area-inset-bottom))] pt-[max(var(--ux-space-2),env(safe-area-inset-top))]">
      <header
        className="app-shell-blur border-b border-slate-200/60"
        style={{ background: 'rgba(255, 255, 255, 0.6)' }}
      >
        <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-3">
          <button
            onClick={() => navigate('/')}
            className="group flex items-center gap-2"
          >
            <div className="relative">
              <div className="h-9 w-9 rounded-2xl bg-teal-500 group-hover:bg-teal-400 text-white font-semibold flex items-center justify-center text-lg transition-colors">
                A
              </div>
              <div className="absolute -right-1 -bottom-1 h-4 w-4 rounded-full bg-white ring-2 ring-white flex items-center justify-center">
                <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="axon-h2 text-base leading-tight text-slate-800">
                AxonAI
              </span>
              <span className="text-[0.62rem] tracking-[0.19em] uppercase text-slate-400">
                School Intelligence · NCEA
              </span>
            </div>
          </button>

          <div className="hidden sm:flex items-center gap-2 text-[0.7rem] text-slate-500">
            <span className="axon-mono text-slate-400">Demo</span>
            <span className="text-slate-300">·</span>
            <span>Aotearoa secondary schools</span>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-10 xl:px-12 py-10 lg:py-16 grid gap-10 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1.1fr)] xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1.1fr)] items-stretch lg:items-center">
          {/* Left: hero copy */}
          <section className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-teal-300/40 bg-teal-50/60 px-3 py-1.5">
              <span className="h-1.5 w-4 rounded-full bg-gradient-to-r from-teal-500 via-emerald-400 to-sky-500" />
              <span className="text-[0.7rem] font-medium tracking-[0.16em] uppercase text-teal-800">
                AI-Native School Intelligence
              </span>
            </div>

            <div className="space-y-3">
              <h1 className="axon-h1 text-3xl sm:text-4xl lg:text-[2.6rem] text-slate-800">
                Every learner&apos;s mastery,{' '}
                <span className="bg-gradient-to-r from-teal-600 via-emerald-500 to-sky-500 bg-clip-text text-transparent">
                  in one live view.
                </span>
              </h1>
              <p className="max-w-xl text-sm sm:text-base text-slate-600">
                AxonAI reads the noise of assessments, engagement and tutor chats —
                then surfaces a calm, structured signal of who&apos;s thriving, who&apos;s
                drifting, and exactly what to do next.
              </p>
            </div>

            <div className="space-y-4">
              {statusNode}
              <p className="text-[0.78rem] text-slate-400">
                Fully simulated demo — no sign-in required. Choose the view that matches
                how you arrive at school.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                onClick={() => navigate('/teacher')}
                className="axon-btn axon-btn-primary"
              >
                Enter as teacher
              </Button>
              <button
                onClick={() => navigate('/student')}
                className="axon-btn axon-btn-ghost"
              >
                Explore student view
              </button>
            </div>
          </section>

          {/* Right: role selector panel */}
          <Card className="axon-card px-5 py-5 sm:px-6 sm:py-6 lg:px-7 lg:py-7">
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="axon-label mb-1">Choose a lens</p>
                <p className="axon-h2 text-sm sm:text-base text-slate-800">
                  How are you looking at school today?
                </p>
              </div>
              <div className="hidden sm:flex items-center gap-1 rounded-full border border-slate-200 bg-white/60 px-2 py-1">
                <span className="h-5 w-5 rounded-full bg-gradient-to-tr from-teal-500 to-emerald-400 opacity-80" />
                <span className="text-[0.7rem] text-slate-500">Multi-agent demo</span>
              </div>
            </div>

            <div className="space-y-3">
              {roles.map(role => (
                <button
                  key={role.id}
                  onClick={() => navigate(role.path)}
                  className="group w-full text-left rounded-xl border border-slate-200/80 bg-white/40 hover:border-teal-400/60 hover:bg-white/70 transition-colors px-3.5 py-3.5 flex items-center gap-3"
                >
                  <div
                    className="h-9 w-9 rounded-xl flex items-center justify-center"
                    style={{ background: `${role.color}15` }}
                  >
                    <svg
                      className="h-5 w-5"
                      style={{ color: role.color }}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={1.5}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d={role.icon} />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-sm font-medium text-slate-700 group-hover:text-teal-700">
                        {role.label}
                      </span>
                      {role.badge && (
                        <span className="axon-pill-soft text-[0.62rem] leading-none px-2 py-0.5">
                          {role.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">
                      {role.description}
                    </p>
                  </div>
                  <span className="text-slate-400 text-xs group-hover:text-teal-600">
                    &#8594;
                  </span>
                </button>
              ))}
            </div>
          </Card>
        </div>
      </main>

      <footer
        className="border-t border-slate-200/60"
        style={{ background: 'rgba(255, 255, 255, 0.4)' }}
      >
        <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-[0.7rem] text-slate-400">
            Built as an AI-first demo for{' '}
            <span className="text-slate-600">Aotearoa New Zealand secondary schools</span>.
          </p>
          <p className="text-[0.7rem] text-slate-400">
            Mastery, risk and interventions shown here are{' '}
            <span className="text-slate-600">simulated for illustration only</span>.
          </p>
        </div>
      </footer>
    </div>
  );
}
