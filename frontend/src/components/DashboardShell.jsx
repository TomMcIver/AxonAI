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
  const previousPathRef = useRef(location.pathname);
  const logNav = (event, details = {}) => {
    const viewport = typeof window !== 'undefined' ? window.innerWidth : null;
    console.debug('[DashboardShell nav]', event, {
      pathname: location.pathname,
      viewport,
      ...details,
    });
  };

  const mode = useMemo(() => {
    if (modeProp) return modeProp;
    if (location.pathname.startsWith('/student')) return 'student';
    if (location.pathname.startsWith('/parent')) return 'parent';
    return 'teacher';
  }, [location.pathname, modeProp]);

  const navItems = NAVS[mode] || NAVS.teacher;

  useEffect(() => {
    const previousPath = previousPathRef.current;
    if (previousPath !== location.pathname && mobileNavOpen) {
      logNav('auto-close mobile on route change', { reason: 'pathname change' });
      setMobileNavOpen(false);
    }
    previousPathRef.current = location.pathname;
  }, [location.pathname, mobileNavOpen]);

  const navLocksScroll = !sidebarCollapsed || mobileNavOpen;
  useEffect(() => {
    if (!navLocksScroll) return undefined;
    logNav('body scroll locked', { reason: 'nav open' });
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
      logNav('body scroll restored', { reason: 'all nav closed' });
    };
  }, [navLocksScroll]);

  useEffect(() => {
    if (sidebarCollapsed) return undefined;
    function onEsc(e) {
      if (e.key === 'Escape') {
        logNav('desktop close', { source: 'escape key' });
        setSidebarCollapsed(true);
      }
    }
    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, [sidebarCollapsed]);

  useEffect(() => {
    logNav('desktop state changed', { open: !sidebarCollapsed });
  }, [sidebarCollapsed]);

  useEffect(() => {
    logNav('mobile state changed', { open: mobileNavOpen });
  }, [mobileNavOpen]);

  function handleToggleNavigation() {
    logNav('menu button clicked');
    if (window.innerWidth >= 1024) {
      setSidebarCollapsed(v => {
        const next = !v;
        logNav('desktop toggle requested', { fromCollapsed: v, toCollapsed: next });
        return next;
      });
    } else {
      setMobileNavOpen(v => {
        const next = !v;
        logNav('mobile toggle requested', { fromOpen: v, toOpen: next });
        return next;
      });
    }
  }

  return (
    <div className="app-shell flex min-h-screen flex-col pb-[max(var(--ux-space-3),env(safe-area-inset-bottom))] pt-[env(safe-area-inset-top)]">
      {/* Full-bleed header — scrolls with the page (not fixed/sticky). Overlay z-500 still covers it when nav is open. */}
      <header className="relative z-20 w-full shrink-0 border-b-2 border-[#2c2418] bg-[#fff8dc]">
        <div
          className="mx-auto flex w-full max-w-7xl flex-col gap-[var(--ux-space-3)] px-2 pb-2.5 pt-0 sm:flex-row sm:items-center sm:justify-between sm:px-3 sm:pb-3 lg:px-4 pl-[max(var(--ux-space-2),env(safe-area-inset-left))] pr-[max(var(--ux-space-2),env(safe-area-inset-right))]"
        >
          <div className="flex min-w-0 items-start gap-[var(--ux-space-3)]">
            <button
              type="button"
              className={`inline-flex h-10 w-10 shrink-0 touch-manipulation items-center justify-center rounded-md border-2 border-[#2c2418] bg-[#fff8dc] text-slate-700 shadow-[3px_3px_0_#2c2418] hover:bg-[#fffef4] active:translate-x-[1px] active:translate-y-[1px] active:shadow-[2px_2px_0_#2c2418] ${
                mobileNavOpen ? 'max-lg:hidden' : ''
              }`}
              onClick={handleToggleNavigation}
              aria-label="Toggle navigation"
            >
              <Menu size={18} />
            </button>
            <div className="min-w-0">
              <p className="axon-label mb-[var(--ux-space-2)]">
                {mode === 'teacher' ? 'Teacher' : mode === 'student' ? 'Student' : 'Parent'} · AxonAI
              </p>
              <p className="axon-h2 text-base sm:text-lg text-slate-800 leading-snug">
                {subtitle || 'Class mastery overview'}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 flex-wrap items-center justify-end gap-[var(--ux-space-3)]">
            <div className="hidden sm:flex items-center gap-[var(--ux-space-2)] rounded-full border border-slate-200 bg-white/60 px-[var(--ux-space-3)] py-[var(--ux-space-2)]">
              <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              <p className="text-xs text-slate-500">
                <span className="font-medium text-slate-700">API Live</span>
              </p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex min-h-0 w-full min-w-0 flex-1 px-[max(var(--ux-space-2),env(safe-area-inset-left))] pr-[max(var(--ux-space-2),env(safe-area-inset-right))]">
        {/* Main region — full width; desktop nav is a fixed overlay */}
        <div className="flex min-h-0 min-w-0 w-full flex-1 flex-col">
          <main
            className="app-shell-main flex-1 px-2 sm:px-3 lg:px-4 py-[var(--ux-space-4)] lg:py-[var(--ux-space-5)]"
            style={{ position: 'relative', zIndex: 0, isolation: 'isolate' }}
          >
            <div className="mx-auto w-full max-w-7xl space-y-[var(--ux-space-4)] sm:space-y-[var(--ux-space-5)]">
              {children}
            </div>
          </main>
        </div>
      </div>

      {/* Desktop (lg+): modal-style nav — dimmed full-screen backdrop (above header), drawer flush to top */}
      {!sidebarCollapsed && (
        <>
          <div
            className="fixed inset-0 z-[500] cursor-default bg-[#2c2418]/55 backdrop-blur-[2px]"
            aria-hidden
            role="presentation"
            onClick={() => {
              logNav('desktop close', { source: 'backdrop click' });
              setSidebarCollapsed(true);
            }}
          />
          <aside
            className="fixed inset-y-0 left-0 z-[510] w-64 min-w-[16rem] flex flex-col overflow-hidden border-r-2 border-[#2c2418] pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] shadow-[8px_0_32px_rgba(44,36,24,0.22)] xl:w-72 xl:min-w-[18rem]"
            style={{ background: '#efe4be' }}
            aria-label="Primary navigation"
            aria-modal="true"
            role="dialog"
          >
            <div className="flex shrink-0 items-center justify-between gap-1.5 border-b border-slate-200/60 px-2 pb-2.5 pt-1">
              <button
                type="button"
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-slate-300/80 bg-white/50 text-slate-600 hover:bg-white/80"
                onClick={() => {
                  logNav('desktop close', { source: 'panel close button' });
                  setSidebarCollapsed(true);
                }}
                aria-label="Collapse navigation"
              >
                <PanelLeftClose size={18} />
              </button>
              <button
                onClick={() => {
                  logNav('desktop nav click', { target: '/', source: 'brand' });
                  navigate('/');
                  setSidebarCollapsed(true);
                }}
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

            <nav className="min-h-0 flex-1 space-y-[var(--ux-space-2)] overflow-y-auto overscroll-y-contain px-2 py-3 [scrollbar-gutter:stable]">
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
                    onClick={() => {
                      logNav('desktop nav click', { target: item.path, source: 'nav item' });
                      navigate(item.path);
                      setSidebarCollapsed(true);
                    }}
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

            <div className="mt-auto shrink-0 border-t border-slate-200/60 bg-[#efe4be] px-2 py-3">
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
        </>
      )}

      {/* Mobile drawer — frosted glass */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-[4000] flex lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
            <div
              className="relative w-72 max-w-full"
              style={{
                background: '#efe4be',
                borderRight: '2px solid #2c2418',
              }}
            >
              <button
                className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white/60 text-slate-600 hover:bg-white"
                onClick={() => {
                  logNav('mobile close', { source: 'panel close button' });
                  setMobileNavOpen(false);
                }}
                aria-label="Close navigation"
              >
                <X size={16} />
              </button>
              <div className="border-b border-slate-200/60 px-3 pb-3 pt-2">
                <button
                  onClick={() => {
                    logNav('mobile nav click', { target: '/', source: 'brand' });
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
                        logNav('mobile nav click', { target: item.path, source: 'nav item' });
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
            onClick={() => {
              logNav('mobile close', { source: 'backdrop click' });
              setMobileNavOpen(false);
            }}
          />
        </div>
      )}
    </div>
  );
}
