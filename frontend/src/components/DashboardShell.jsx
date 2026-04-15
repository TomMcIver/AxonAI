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
  PanelLeftClose,
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
  /** Desktop: start with nav hidden so content isn’t squeezed; hamburger expands it. */
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
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

  function handleToggleNavigation() {
    if (window.innerWidth >= 1024) {
      setSidebarCollapsed(v => !v);
    } else {
      setMobileNavOpen(true);
    }
  }

  return (
    <div className="app-shell min-h-screen px-[max(var(--ux-space-2),env(safe-area-inset-left))] pr-[max(var(--ux-space-2),env(safe-area-inset-right))] pb-[max(var(--ux-space-3),env(safe-area-inset-bottom))] pt-[env(safe-area-inset-top)]">
      {/* Rebuilt top-left menu trigger with isolated click layer */}
      {/* Mobile: always show. Desktop (lg+): only when sidebar is collapsed — avoids overlapping the open sidebar. */}
      <div className="fixed left-[max(0.5rem,env(safe-area-inset-left))] top-[max(0.25rem,env(safe-area-inset-top))] z-[1000] pointer-events-none">
        <button
          type="button"
          className={`pointer-events-auto inline-flex h-10 w-10 items-center justify-center rounded-md border-2 border-[#2c2418] bg-[#fff8dc] text-slate-700 shadow-[3px_3px_0_#2c2418] hover:bg-[#fffef4] active:translate-x-[1px] active:translate-y-[1px] active:shadow-[2px_2px_0_#2c2418] ${
            sidebarCollapsed ? 'flex' : 'max-lg:flex lg:hidden'
          }`}
          onClick={handleToggleNavigation}
          aria-label="Toggle navigation"
        >
          <Menu size={18} />
        </button>
      </div>

      <div className="flex min-h-screen">
        {/* Sidebar — frosted white glass */}
        <aside
          className="hidden min-h-0 lg:sticky lg:top-0 lg:flex lg:h-screen lg:max-h-screen lg:flex-col lg:overflow-hidden w-64 min-w-[16rem] xl:w-72 xl:min-w-[18rem] shrink-0"
          style={{
            background: '#efe4be',
            borderRight: '2px solid #2c2418',
            ...(sidebarCollapsed ? { display: 'none' } : {}),
          }}
        >
          <div className="flex shrink-0 items-center justify-between gap-1.5 border-b border-slate-200/60 px-2 pb-2.5 pt-1">
            <button
              type="button"
              className="hidden lg:inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-300/80 bg-white/50 text-slate-600 hover:bg-white/80"
              onClick={() => setSidebarCollapsed(true)}
              aria-label="Collapse navigation"
            >
              <PanelLeftClose size={18} />
            </button>
            <button
              onClick={() => navigate('/')}
              className="group flex min-w-0 flex-1 items-center gap-2"
            >
              <div className="relative">
                <div className="h-8 w-8 rounded-2xl bg-teal-500 group-hover:bg-teal-400 text-white font-semibold flex items-center justify-center text-lg transition-colors">
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
                  School Intelligence
                </span>
              </div>
            </button>
          </div>

          <nav className="min-h-0 flex-1 space-y-[var(--ux-space-2)] overflow-y-auto overscroll-y-contain px-2 py-3">
            <div className="flex items-start gap-2 px-2 pb-2 pt-0">
              <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-slate-200/80 bg-white/50 text-[10px] font-bold text-slate-400" aria-hidden>
                {mode === 'teacher' ? 'T' : mode === 'student' ? 'S' : 'P'}
              </span>
              <p className="axon-label !m-0 !p-0 leading-tight">
                {mode === 'teacher' ? 'Teacher view' : mode === 'student' ? 'Student view' : 'Parent view'}
              </p>
            </div>
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
                  className={`group flex w-full items-start gap-2 rounded-lg px-2 py-2 text-sm font-medium transition-all duration-200 ease-out ${
                    isActive
                      ? 'bg-teal-500/10 text-teal-700 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]'
                      : 'text-slate-500 hover:bg-white/50 hover:text-slate-700'
                  }`}
                >
                  <span
                    className={`mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border ${
                      isActive
                        ? 'border-teal-400/60 bg-teal-500/10 text-teal-600'
                        : 'border-slate-200 bg-white/60 text-slate-400 group-hover:border-slate-300 group-hover:text-slate-600'
                    }`}
                  >
                    <Icon size={16} />
                  </span>
                  <span className="min-w-0 flex-1 text-left text-sm leading-snug break-words [overflow-wrap:anywhere]">
                    {item.label}
                  </span>
                </button>
              );
            })}
          </nav>

          <div className="shrink-0 border-t border-slate-200/60 px-2 py-3">
            <button className="flex w-full items-center justify-between rounded-lg px-1.5 py-2 hover:bg-white/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="h-8 w-8 rounded-full bg-teal-500/15 text-teal-700 flex items-center justify-center text-xs font-semibold">
                    MW
                  </div>
                  <span className="absolute -right-0.5 -bottom-0.5 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-slate-700">
                    {mode === 'teacher' ? 'Ms. Williams' : mode === 'student' ? 'Aroha Ngata' : 'Whanau view'}
                  </p>
                  <p className="text-[0.7rem] tracking-[0.18em] uppercase text-slate-400">
                    {mode === 'teacher' ? 'Year 11 Mathematics' : mode === 'student' ? 'Year 12' : 'Caregiver'}
                  </p>
                </div>
              </div>
              <ChevronDown size={16} className="text-slate-400" />
            </button>
          </div>
        </aside>

        {/* Main region */}
        <div className="flex-1 flex flex-col">
          {/* Top bar — frosted glass */}
          <header
            className="sticky top-0 z-[220]"
            style={{
              background: '#fff8dc',
              borderBottom: '2px solid #2c2418',
            }}
          >
            <div
              className="mx-auto w-full max-w-7xl flex flex-col gap-[var(--ux-space-3)] sm:flex-row sm:items-center sm:justify-between px-2 sm:px-3 lg:px-4 pb-2.5 pt-0 sm:pb-3"
            >
              <div className="flex min-w-0 items-start gap-[var(--ux-space-3)]">
                <div className="h-9 w-9 shrink-0" aria-hidden="true" />
                <div className="min-w-0">
                  <p className="axon-label mb-[var(--ux-space-2)]">
                    {mode === 'teacher' ? 'Teacher' : mode === 'student' ? 'Student' : 'Parent'} · AxonAI
                  </p>
                  <p className="axon-h2 text-base sm:text-lg text-slate-800 leading-snug">
                    {subtitle || 'Class mastery overview'}
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 flex-wrap items-center gap-[var(--ux-space-3)] sm:justify-end">
                <div className="hidden sm:flex items-center gap-[var(--ux-space-2)] rounded-full border border-slate-200 bg-white/60 px-[var(--ux-space-3)] py-[var(--ux-space-2)]">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                  <p className="text-xs text-slate-500">
                    <span className="font-medium text-slate-700">Live</span>{' '}
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
                    <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
                    Quick actions
                  </button>
                  {qaOpen && (
                    <div
                      role="menu"
                      className="absolute right-0 mt-2 w-56 overflow-hidden"
                      style={{
                        background: 'rgba(255, 255, 255, 0.85)',
                        backdropFilter: 'blur(20px)',
                        WebkitBackdropFilter: 'blur(20px)',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                        borderRadius: 12,
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                      }}
                    >
                      <button
                        role="menuitem"
                        className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-100/60 transition-colors"
                        onClick={() => navigate('/login')}
                      >
                        Switch role
                      </button>
                      {mode === 'teacher' && (
                        <>
                          <button
                            role="menuitem"
                            className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-100/60 transition-colors"
                            onClick={() => navigate('/teacher/students')}
                          >
                            Open student roster
                          </button>
                          <button
                            role="menuitem"
                            className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-100/60 transition-colors"
                            onClick={() => navigate('/teacher/subjects')}
                          >
                            Upload class content
                          </button>
                        </>
                      )}
                      {mode !== 'teacher' && (
                        <button
                          role="menuitem"
                          className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-100/60 transition-colors"
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
          <main
            className="app-shell-main flex-1 px-2 sm:px-3 lg:px-4 py-[var(--ux-space-4)] lg:py-[var(--ux-space-5)]"
            style={{ position: 'relative', zIndex: 0, isolation: 'isolate' }}
          >
            <div className="mx-auto w-full max-w-7xl space-y-[var(--ux-space-4)] sm:space-y-[var(--ux-space-5)]">
              {children}
            </div>
          </main>
        </div>

        {/* Mobile drawer — frosted glass */}
        {mobileNavOpen && (
          <div className="fixed inset-0 z-[60] flex lg:hidden">
            <div
              className="relative w-72 max-w-full"
              style={{
                background: '#efe4be',
                borderRight: '2px solid #2c2418',
              }}
            >
              <button
                className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white/60 text-slate-600 hover:bg-white"
                onClick={() => setMobileNavOpen(false)}
                aria-label="Close navigation"
              >
                <X size={16} />
              </button>
              <div className="border-b border-slate-200/60 px-3 pb-3 pt-2">
                <button
                  onClick={() => {
                    navigate('/');
                    setMobileNavOpen(false);
                  }}
                  className="group flex items-center gap-2"
                >
                  <div className="h-8 w-8 rounded-2xl bg-teal-500 text-white font-semibold flex items-center justify-center text-lg">
                    A
                  </div>
                  <div className="flex flex-col">
                    <span className="axon-h2 text-base leading-tight text-slate-800">
                      AxonAI
                    </span>
                    <span className="text-[0.62rem] tracking-[0.19em] uppercase text-slate-400">
                      School Intelligence
                    </span>
                  </div>
                </button>
              </div>
              <nav className="space-y-[var(--ux-space-2)] px-2 py-3">
                <div className="flex items-start gap-2 px-2 pb-2">
                  <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-slate-200/80 bg-white/50 text-[10px] font-bold text-slate-400" aria-hidden>
                    {mode === 'teacher' ? 'T' : mode === 'student' ? 'S' : 'P'}
                  </span>
                  <p className="axon-label !m-0 !p-0 leading-tight">
                    {mode === 'teacher' ? 'Teacher view' : mode === 'student' ? 'Student view' : 'Parent view'}
                  </p>
                </div>
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
                      className={`group flex w-full items-start gap-2 rounded-lg px-2 py-2 text-sm font-medium transition-all duration-200 ease-out ${
                        isActive
                          ? 'bg-teal-500/10 text-teal-700'
                          : 'text-slate-500 hover:bg-white/50 hover:text-slate-700'
                      }`}
                    >
                      <span
                        className={`mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border ${
                          isActive
                            ? 'border-teal-400/60 bg-teal-500/10 text-teal-600'
                            : 'border-slate-200 bg-white/60 text-slate-400 group-hover:border-slate-300 group-hover:text-slate-600'
                        }`}
                      >
                        <Icon size={16} />
                      </span>
                      <span className="min-w-0 flex-1 text-left text-sm leading-snug break-words [overflow-wrap:anywhere]">
                        {item.label}
                      </span>
                    </button>
                  );
                })}
              </nav>
            </div>
            <div
              className="flex-1 bg-black/20 backdrop-blur-sm"
              onClick={() => setMobileNavOpen(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
