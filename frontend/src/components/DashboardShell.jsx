import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Network,
  Settings,
  ChevronDown,
} from 'lucide-react';

const cssStyles = `
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700&family=Lexend:wght@400;500&display=swap');

:root {
  /* Brand */
  --primary-900: #134E48;
  --primary-700: #0F766E;
  --primary-500: #14B8A6;
  --primary-300: #5EEAD4;
  --primary-100: #CCFBF1;
  --primary-50:  #F0FDFA;

  /* Surfaces */
  --surface-base:    #F8FAFB;
  --surface-card:    #FFFFFF;
  --surface-sidebar: #F1F5F4;
  --surface-muted:   #F1F5F9;

  /* Text */
  --text-primary:   #0F172A;
  --text-secondary: #475569;
  --text-tertiary:  #94A3B8;
  --text-inverse:   #FFFFFF;

  /* Semantic */
  --mastered:         #059669;
  --mastered-bg:      #ECFDF5;
  --on-track:         #0F766E;
  --on-track-bg:      #F0FDFA;
  --in-progress:      #2563EB;
  --in-progress-bg:   #EFF6FF;
  --needs-attention:  #D97706;
  --needs-attention-bg: #FFFBEB;
  --at-risk:          #DC2626;
  --at-risk-bg:       #FEF2F2;
  --inactive:         #94A3B8;
  --inactive-bg:      #F1F5F9;

  /* Shadows */
  --shadow-1: 0 1px 3px rgba(15,23,42,0.04), 0 1px 2px rgba(15,23,42,0.06);
  --shadow-2: 0 4px 6px rgba(15,23,42,0.04), 0 2px 4px rgba(15,23,42,0.06);
  --shadow-3: 0 12px 24px rgba(15,23,42,0.08), 0 4px 8px rgba(15,23,42,0.04);

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-full: 9999px;
}
`;

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/teacher' },
  { icon: Users, label: 'Students', path: '/teacher/students' },
  { icon: BookOpen, label: 'Subjects', path: '/teacher/subjects' },
  { icon: Network, label: 'Knowledge Graph', path: '/teacher/knowledge-graph' },
  { icon: Settings, label: 'Settings', path: '/teacher/settings' },
];

export default function DashboardShell({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <>
      <style>{cssStyles}</style>
      <div
        style={{
          display: 'flex',
          minHeight: '100vh',
          background: 'var(--surface-base)',
        }}
      >
        {/* Sidebar */}
        <aside
          style={{
            width: 260,
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            background: 'var(--surface-sidebar)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 40,
          }}
        >
          {/* Wordmark */}
          <div className="px-6 pt-6 pb-8">
            <span
              onClick={() => navigate('/teacher')}
              style={{
                fontFamily: "'Plus Jakarta Sans', sans-serif",
                fontWeight: 700,
                fontSize: 20,
                cursor: 'pointer',
              }}
            >
              <span style={{ color: 'var(--text-primary)' }}>axon</span>
              <span style={{ color: 'var(--primary-700)' }}>AI</span>
            </span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 flex flex-col gap-1 px-3">
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={item.label}
                  onClick={() => navigate(item.path)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    height: 44,
                    paddingLeft: 16,
                    paddingRight: 12,
                    borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    cursor: 'pointer',
                    width: '100%',
                    fontFamily: "'Lexend', sans-serif",
                    fontWeight: 500,
                    fontSize: 14,
                    background: isActive ? 'var(--primary-50)' : 'transparent',
                    color: isActive ? 'var(--primary-700)' : 'var(--text-secondary)',
                    borderLeft: isActive ? '3px solid var(--primary-700)' : '3px solid transparent',
                    transition: 'background 150ms, color 150ms',
                  }}
                  onMouseEnter={e => {
                    if (!isActive) e.currentTarget.style.background = 'rgba(0,0,0,0.03)';
                  }}
                  onMouseLeave={e => {
                    if (!isActive) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <Icon size={20} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* User area */}
          <div
            className="px-4 py-4 mx-3 mb-3"
            style={{
              borderTop: '1px solid rgba(0,0,0,0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: 'var(--primary-100)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: "'Plus Jakarta Sans', sans-serif",
                fontWeight: 600,
                fontSize: 13,
                flexShrink: 0,
              }}
            >
              MW
            </div>
            <div className="flex-1" style={{ minWidth: 0 }}>
              <div
                style={{
                  fontFamily: "'Lexend', sans-serif",
                  fontWeight: 500,
                  fontSize: 14,
                  color: 'var(--text-primary)',
                }}
              >
                Ms. Williams
              </div>
              <span
                style={{
                  display: 'inline-block',
                  fontFamily: "'Lexend', sans-serif",
                  fontWeight: 500,
                  fontSize: 11,
                  textTransform: 'uppercase',
                  background: 'var(--primary-100)',
                  color: 'var(--primary-700)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  marginTop: 2,
                }}
              >
                Teacher
              </span>
            </div>
            <ChevronDown size={16} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
          </div>
        </aside>

        {/* Main content */}
        <main
          style={{
            marginLeft: 260,
            flex: 1,
          }}
        >
          {children}
        </main>
      </div>
    </>
  );
}
