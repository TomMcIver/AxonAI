import React, { useMemo, useState } from 'react';
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
  MessageSquare,
} from 'lucide-react';
import BlossomDecor from './BlossomDecor';

const NAVS = {
  teacher: [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/teacher' },
    { icon: Users, label: 'Students', path: '/teacher/students' },
    { icon: BookOpen, label: 'Subjects', path: '/teacher/subjects' },
    { icon: Network, label: 'Knowledge Graph', path: '/teacher/knowledge-graph' },
    { icon: Settings, label: 'Settings', path: '/teacher/settings' },
  ],
  parent: [{ icon: LayoutDashboard, label: 'Overview', path: '/parent' }],
};

export default function DashboardShell({ children, subtitle, mode: modeProp }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const mode = useMemo(() => {
    if (modeProp) return modeProp;
    if (location.pathname.startsWith('/student')) return 'student';
    if (location.pathname.startsWith('/parent')) return 'parent';
    return 'teacher';
  }, [location.pathname, modeProp]);

  const navItems = useMemo(() => {
    if (mode === 'student') {
      const m = location.pathname.match(/^\/student\/(\d+)(?:\/|$)/);
      const studentBase = m ? `/student/${m[1]}` : '/student';
      const graphPath =
        studentBase === '/student' ? '/student/knowledge-graph' : `${studentBase}/knowledge-graph`;
      return [
        { icon: LayoutDashboard, label: 'Overview', path: studentBase },
        { icon: Network, label: 'Learning map', path: graphPath },
        { icon: MessageSquare, label: 'AI Tutor', path: '/student/chat' },
      ];
    }
    return NAVS[mode] || NAVS.teacher;
  }, [mode, location.pathname]);

  function handleToggleNavigation() {
    if (window.innerWidth >= 1024) {
      setSidebarOpen((v) => !v);
    } else {
      setMobileNavOpen((v) => !v);
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#FDF6EE', fontFamily: "'Lora', serif", position: 'relative' }}>
      <BlossomDecor petals={46} />
      <header style={{ position: 'sticky', top: 0, zIndex: 200, borderBottom: '2px solid #3D2B1F', background: 'rgba(253,246,238,0.95)', backdropFilter: 'blur(10px)' }}>
        <div style={{ maxWidth: 1240, margin: '0 auto', padding: '12px 22px', display: 'flex', alignItems: 'center', gap: 14 }}>
          <button type="button" onClick={handleToggleNavigation} aria-label="Toggle navigation" style={{ width: 40, height: 40, borderRadius: 10, border: '1.5px solid #3D2B1F', background: '#FDF6EE', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Menu size={18} color="#3D2B1F" />
          </button>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: '#2D7D6F', fontStyle: 'italic' }}>
              {mode === 'teacher' ? 'Teacher' : mode === 'student' ? 'Student' : 'Parent'} · AxonAI
            </div>
            <div style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 16, color: '#3D2B1F', fontWeight: 600 }}>{subtitle || 'Dashboard'}</div>
          </div>
        </div>
      </header>
      <main style={{ position: 'relative', zIndex: 5, maxWidth: 1240, margin: '0 auto', padding: '24px 22px 34px' }}>{children}</main>

      {sidebarOpen && (
        <>
          <div onClick={() => setSidebarOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 500, background: 'rgba(61,43,31,0.45)' }} />
          <aside style={{ position: 'fixed', top: 0, left: 0, bottom: 0, width: 288, zIndex: 510, background: '#F0E6D6', borderRight: '2px solid #3D2B1F', padding: 16, overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <button onClick={() => setSidebarOpen(false)} style={{ width: 30, height: 30, borderRadius: 8, border: '1px solid rgba(61,43,31,0.2)', background: 'white', cursor: 'pointer' }}>
                ✕
              </button>
              <button onClick={() => { navigate('/'); setSidebarOpen(false); }} style={{ border: 'none', background: 'transparent', fontFamily: "'Shippori Mincho', serif", fontWeight: 700, fontSize: 20, color: '#3D2B1F', cursor: 'pointer' }}>AxonAI</button>
              <span />
            </div>
            <nav style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {navItems.map(item => {
                const Icon = item.icon;
                const isActive =
                  mode === 'student'
                    ? location.pathname === item.path
                    : location.pathname === item.path ||
                      (item.path !== '/teacher' && location.pathname.startsWith(item.path));

                return <button key={item.path} onClick={() => { navigate(item.path); setSidebarOpen(false); }} style={{ display: 'flex', alignItems: 'center', gap: 10, border: 'none', cursor: 'pointer', textAlign: 'left', padding: '10px 12px', borderRadius: 12, background: isActive ? 'rgba(45,125,111,0.12)' : 'transparent', color: isActive ? '#2D7D6F' : '#6B4A3A' }}><span style={{ width: 28, height: 28, borderRadius: 8, border: '1px solid rgba(61,43,31,0.15)', background: 'rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Icon size={16} /></span>{item.label}</button>;
              })}
            </nav>
            <div style={{ marginTop: 12, borderTop: '1px solid rgba(61,43,31,0.12)', paddingTop: 12 }}>
              <button type="button" onClick={() => { navigate('/login'); setSidebarOpen(false); }} style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid rgba(61,43,31,0.2)', background: 'transparent', color: '#6B4A3A', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                <ChevronDown size={14} /> Log out
              </button>
            </div>
          </aside>
        </>
      )}

      {mobileNavOpen && (
        <div className="fixed inset-0 z-[4000] flex lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div className="relative w-72 max-w-full" style={{ background: '#F0E6D6', borderRight: '2px solid #3D2B1F', paddingTop: 12 }}>
            <button className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white/60 text-slate-600 hover:bg-white" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation">
              <X size={16} />
            </button>
            <nav className="space-y-2 px-2 py-3">
                {navItems.map(item => {
                  const Icon = item.icon;
                  const isActive =
                    mode === 'student'
                      ? location.pathname === item.path
                      : location.pathname === item.path ||
                        (item.path !== '/teacher' && location.pathname.startsWith(item.path));
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
                <button type="button" onClick={() => { navigate('/login'); setMobileNavOpen(false); }} className="axon-btn axon-btn-quiet mt-2 w-full justify-center">
                  Log out
                </button>
            </nav>
          </div>
          <div
            className="flex-1 bg-black/20 backdrop-blur-sm"
            onClick={() => setMobileNavOpen(false)}
          />
        </div>
      )}
    </div>
  );
}
