import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Network,
  Settings,
  Menu,
  X,
  ChevronDown,
} from 'lucide-react';

const NAVS = {
  teacher: [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/teacher' },
    { icon: Users, label: 'Students', path: '/teacher/students' },
    { icon: BookOpen, label: 'Subjects', path: '/teacher/subjects' },
    { icon: Network, label: 'Knowledge Graph', path: '/teacher/knowledge-graph' },
    { icon: Settings, label: 'Settings', path: '/teacher/settings' },
  ],
  student: [{ icon: LayoutDashboard, label: 'Overview', path: '/student' }],
  parent: [{ icon: LayoutDashboard, label: 'Overview', path: '/parent' }],
};

export default function DashboardShell({ children, subtitle, mode: modeProp }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [qaOpen, setQaOpen] = useState(false);
  const qaRef = useRef(null);

  const mode = useMemo(() => {
    if (modeProp) return modeProp;
    if (location.pathname.startsWith('/student')) return 'student';
    if (location.pathname.startsWith('/parent')) return 'parent';
    return 'teacher';
  }, [location.pathname, modeProp]);

  const navItems = NAVS[mode] || NAVS.teacher;

  useEffect(() => {
    function onDown(e) {
      if (!qaRef.current) return;
      if (!qaRef.current.contains(e.target)) setQaOpen(false);
    }
    if (!qaOpen) return undefined;
    window.addEventListener('mousedown', onDown, true);
    return () => window.removeEventListener('mousedown', onDown, true);
  }, [qaOpen]);

  useEffect(() => {
    setQaOpen(false);
    setMobileNavOpen(false);
  }, [location.pathname]);

  return (
    <div className="app-shell min-h-screen text-slate-100">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="app-shell-blur hidden lg:flex lg:flex-col w-64 xl:w-72 border-r border-slate-800/80 bg-slate-900/60">
          <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-slate-800/70">
            <button
              onClick={() => navigate('/')}
              className="group flex items-center gap-2"
            >
              <div className="relative">
                <div className="h-8 w-8 rounded-2xl bg-sky-400/90 group-hover:bg-sky-300 text-slate-950 font-semibold flex items-center justify-center text-lg transition-colors">
                  A
                </div>
                <div className="absolute -right-1 -bottom-1 h-4 w-4 rounded-full bg-slate-900 ring-2 ring-slate-950 flex items-center justify-center">
                  <div className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.9)]" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="axon-h2 text-base leading-tight text-slate-100">
                  AxonAI
                </span>
                <span className="text-[0.62rem] tracking-[0.19em] uppercase text-slate-500">
                  School Intelligence
                </span>
              </div>
            </button>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1">
            <p className="axon-label px-3 pb-1 pt-0">
              {mode === 'teacher' ? 'Teacher view' : mode === 'student' ? 'Student view' : 'Parent view'}
            </p>
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive =
                location.pathname === item.path ||
                (item.path !== '/teacher' &&
                  location.pathname.startsWith(item.path));

              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-slate-900/80 text-slate-50 shadow-[0_0_0_1px_rgba(148,163,184,0.5),0_14px_35px_rgba(15,23,42,0.9)]'
                      : 'text-slate-400 hover:bg-slate-900/40 hover:text-slate-100'
                  }`}
                >
                  <span
                    className={`inline-flex h-7 w-7 items-center justify-center rounded-full border ${
                      isActive
                        ? 'border-sky-400/80 bg-sky-400/10 text-sky-300'
                        : 'border-slate-700/80 bg-slate-900/40 text-slate-400 group-hover:border-slate-500/80 group-hover:text-slate-100'
                    }`}
                  >
                    <Icon size={16} />
                  </span>
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="border-t border-slate-800/70 px-4 py-4">
            <button className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 hover:bg-slate-900/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="h-8 w-8 rounded-full bg-sky-500/20 text-sky-300 flex items-center justify-center text-xs font-semibold">
                    MW
                  </div>
                  <span className="absolute -right-0.5 -bottom-0.5 h-2.5 w-2.5 rounded-full bg-emerald-400 ring-2 ring-slate-950" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-slate-100">
                    {mode === 'teacher' ? 'Ms. Williams' : mode === 'student' ? 'Aroha Ngata' : 'Whānau view'}
                  </p>
                  <p className="text-[0.7rem] tracking-[0.18em] uppercase text-slate-500">
                    {mode === 'teacher' ? 'Year 11 Mathematics' : mode === 'student' ? 'Year 12' : 'Caregiver'}
                  </p>
                </div>
              </div>
              <ChevronDown size={16} className="text-slate-500" />
            </button>
          </div>
        </aside>

        {/* Main region */}
        <div className="flex-1 flex flex-col">
          {/* Top bar */}
          <header className="app-shell-blur sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/60">
            <div className="mx-auto w-full max-w-7xl flex items-center justify-between px-4 sm:px-6 lg:px-8 py-3">
              <div className="flex items-center gap-3">
                <button
                  className="lg:hidden inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-800 bg-slate-900/80 text-slate-200 hover:bg-slate-900"
                  onClick={() => setMobileNavOpen(true)}
                  aria-label="Open navigation"
                >
                  <Menu size={18} />
                </button>
                <div>
                  <p className="axon-label mb-0.5">
                    {mode === 'teacher' ? 'Teacher' : mode === 'student' ? 'Student' : 'Parent'} · AxonAI
                  </p>
                  <p className="axon-h2 text-base sm:text-lg text-slate-50">
                    {subtitle || 'Class mastery overview'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="hidden sm:flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.7)]" />
                  <p className="text-xs text-slate-400">
                    <span className="font-medium text-slate-200">Live</span>{' '}
                    NCEA feed
                  </p>
                </div>
                <div className="relative hidden sm:block" ref={qaRef}>
                  <button
                    className="axon-btn axon-btn-ghost inline-flex"
                    onClick={() => setQaOpen(v => !v)}
                    aria-haspopup="menu"
                    aria-expanded={qaOpen}
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
                    Quick actions
                  </button>
                  {qaOpen && (
                    <div
                      role="menu"
                      className="absolute right-0 mt-2 w-56 axon-card-ghost overflow-hidden shadow-[0_0_0_1px_rgba(148,163,184,0.18),0_18px_45px_rgba(15,23,42,0.85)]"
                    >
                      <button
                        role="menuitem"
                        className="w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-900/70 transition-colors"
                        onClick={() => navigate('/login')}
                      >
                        Switch role
                      </button>
                      {mode === 'teacher' && (
                        <>
                          <button
                            role="menuitem"
                            className="w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-900/70 transition-colors"
                            onClick={() => navigate('/teacher/students')}
                          >
                            Open student roster
                          </button>
                          <button
                            role="menuitem"
                            className="w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-900/70 transition-colors"
                            onClick={() => navigate('/teacher/subjects')}
                          >
                            Upload class content
                          </button>
                        </>
                      )}
                      {mode !== 'teacher' && (
                        <button
                          role="menuitem"
                          className="w-full text-left px-3 py-2 text-sm text-slate-200 hover:bg-slate-900/70 transition-colors"
                          onClick={() => navigate(`/${mode}`)}
                        >
                          Go to overview
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </header>

          {/* Content */}
          <main className="flex-1 px-3 sm:px-5 lg:px-8 py-5 lg:py-7">
            <div className="mx-auto w-full max-w-7xl space-y-6 sm:space-y-8">
              {children}
            </div>
          </main>
        </div>

        {/* Mobile drawer */}
        {mobileNavOpen && (
          <div className="fixed inset-0 z-40 flex lg:hidden">
            <div
              className="flex-1 bg-black/50 backdrop-blur-sm"
              onClick={() => setMobileNavOpen(false)}
            />
            <div className="relative w-72 max-w-full app-shell-blur bg-slate-950/90 border-l border-slate-800/80">
              <button
                className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-700/70 bg-slate-900/80 text-slate-200 hover:bg-slate-900"
                onClick={() => setMobileNavOpen(false)}
                aria-label="Close navigation"
              >
                <X size={16} />
              </button>
              <div className="px-4 pt-6 pb-4 border-b border-slate-800/70">
                <button
                  onClick={() => {
                    navigate('/');
                    setMobileNavOpen(false);
                  }}
                  className="group flex items-center gap-2"
                >
                  <div className="h-8 w-8 rounded-2xl bg-sky-400/90 text-slate-950 font-semibold flex items-center justify-center text-lg">
                    A
                  </div>
                  <div className="flex flex-col">
                    <span className="axon-h2 text-base leading-tight text-slate-100">
                      AxonAI
                    </span>
                    <span className="text-[0.62rem] tracking-[0.19em] uppercase text-slate-500">
                      School Intelligence
                    </span>
                  </div>
                </button>
              </div>
              <nav className="px-3 py-4 space-y-1">
                <p className="axon-label px-2 pb-1">
                  {mode === 'teacher' ? 'Teacher view' : mode === 'student' ? 'Student view' : 'Parent view'}
                </p>
                {navItems.map(item => {
                  const Icon = item.icon;
                  const isActive =
                    location.pathname === item.path ||
                    (item.path !== '/teacher' &&
                      location.pathname.startsWith(item.path));
                  return (
                    <button
                      key={item.path}
                      onClick={() => {
                        navigate(item.path);
                        setMobileNavOpen(false);
                      }}
                      className={`group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                        isActive
                          ? 'bg-slate-900 text-slate-50'
                          : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-100'
                      }`}
                    >
                      <span
                        className={`inline-flex h-7 w-7 items-center justify-center rounded-full border ${
                          isActive
                            ? 'border-sky-400/80 bg-sky-400/10 text-sky-300'
                            : 'border-slate-700/80 bg-slate-900/60 text-slate-400 group-hover:border-slate-500/80 group-hover:text-slate-100'
                        }`}
                      >
                        <Icon size={16} />
                      </span>
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

