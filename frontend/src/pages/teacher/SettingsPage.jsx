import React, { useState } from 'react';
import { Settings, Bell, Shield, Palette } from 'lucide-react';
import DashboardShell from '../../components/DashboardShell';

const settingsSections = [
  {
    id: 'notifications',
    icon: Bell,
    title: 'Notifications',
    description: 'Configure alerts for student performance and engagement changes',
    settings: [
      { id: 'risk-alerts', label: 'At-risk student alerts', description: 'Get notified when a student enters at-risk status', enabled: true },
      { id: 'mastery-alerts', label: 'Mastery milestones', description: 'Celebrate when students master new concepts', enabled: true },
      { id: 'inactivity-alerts', label: 'Inactivity warnings', description: 'Alert when a student is inactive for 3+ days', enabled: true },
      { id: 'weekly-digest', label: 'Weekly digest email', description: 'Receive a summary report every Monday', enabled: false },
    ],
  },
  {
    id: 'ai-settings',
    icon: Settings,
    title: 'AI Tutor Preferences',
    description: 'Control how the AI tutor interacts with your students',
    settings: [
      { id: 'ai-auto', label: 'Automatic AI interventions', description: 'Allow AI to proactively offer help to struggling students', enabled: true },
      { id: 'ai-hints', label: 'Hint-based guidance', description: 'AI gives hints rather than direct answers', enabled: true },
      { id: 'ai-pastoral', label: 'Pastoral care suggestions', description: 'AI flags potential wellbeing concerns', enabled: true },
    ],
  },
  {
    id: 'display',
    icon: Palette,
    title: 'Display',
    description: 'Customise your dashboard appearance',
    settings: [
      { id: 'animations', label: 'Dashboard animations', description: 'Enable mastery ring and graph animations', enabled: true },
      { id: 'compact', label: 'Compact view', description: 'Show more data with reduced spacing', enabled: false },
    ],
  },
  {
    id: 'privacy',
    icon: Shield,
    title: 'Privacy & Data',
    description: 'Manage data retention and student privacy settings',
    settings: [
      { id: 'anonymise', label: 'Anonymise demo mode', description: 'Hide student names when presenting the dashboard', enabled: false },
      { id: 'data-export', label: 'Allow data export', description: 'Enable CSV export of student performance data', enabled: true },
    ],
  },
];

function Toggle({ enabled, onToggle }) {
  return (
    <button
      onClick={onToggle}
      role="switch"
      aria-checked={enabled}
      style={{
        width: 44, height: 24, borderRadius: 9999,
        background: enabled
          ? 'linear-gradient(135deg, #0f766e, #14b8a6)'
          : 'rgba(203, 213, 225, 0.6)',
        border: '1px solid ' + (enabled ? 'rgba(20,184,166,0.3)' : 'rgba(148,163,184,0.2)'),
        cursor: 'pointer', position: 'relative',
        transition: 'all 250ms cubic-bezier(0.16, 1, 0.3, 1)',
        flexShrink: 0,
        boxShadow: enabled
          ? '0 2px 8px rgba(20,184,166,0.2), inset 0 1px 0 rgba(255,255,255,0.2)'
          : 'inset 0 1px 2px rgba(0,0,0,0.06)',
      }}
    >
      <div style={{
        width: 18, height: 18, borderRadius: '50%',
        background: '#fff',
        position: 'absolute', top: 2,
        left: enabled ? 23 : 2,
        transition: 'all 250ms cubic-bezier(0.16, 1, 0.3, 1)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
      }} />
    </button>
  );
}

export default function SettingsPage() {
  const [settings, setSettings] = useState(() => {
    const map = {};
    settingsSections.forEach(section => {
      section.settings.forEach(s => { map[s.id] = s.enabled; });
    });
    return map;
  });

  function toggle(id) {
    setSettings(prev => ({ ...prev, [id]: !prev[id] }));
  }

  return (
    <DashboardShell>
      <div style={{ maxWidth: 980, margin: '0 auto', padding: '20px 12px' }}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>
              PREFERENCES
            </span>
            <h1 style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 700, fontSize: 28, letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: '4px 0 4px 0' }}>
              Settings
            </h1>
            <p style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--text-tertiary)', margin: 0 }}>
              Manage your dashboard and notification preferences
            </p>
          </div>
        </div>

        {/* Profile card */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.45)',
          backdropFilter: 'blur(16px) saturate(140%)',
          WebkitBackdropFilter: 'blur(16px) saturate(140%)',
          border: '1px solid rgba(255, 255, 255, 0.6)',
          borderRadius: 16,
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.7)',
          padding: '20px 24px', marginTop: 24, marginBottom: 24,
        }}>
          <div className="flex items-center gap-4">
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: 'var(--primary-100)', color: 'var(--primary-700)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 16,
            }}>
              MW
            </div>
            <div className="flex-1">
              <h3 style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 16, color: 'var(--text-primary)', margin: 0 }}>
                Ms. Williams
              </h3>
              <p style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 14, color: 'var(--text-tertiary)', margin: '2px 0 0 0' }}>
                Year 11 Mathematics · Greenfield Secondary School
              </p>
            </div>
            <span style={{
              fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 11, textTransform: 'uppercase',
              background: 'var(--primary-100)', color: 'var(--primary-700)',
              padding: '3px 10px', borderRadius: 'var(--radius-full)',
            }}>
              Teacher
            </span>
          </div>
        </div>

        {/* Settings sections */}
        <div className="flex flex-col gap-6">
          {settingsSections.map(section => {
            const Icon = section.icon;
            return (
              <div key={section.id} style={{
                background: 'rgba(255, 255, 255, 0.45)',
                backdropFilter: 'blur(16px) saturate(140%)',
                WebkitBackdropFilter: 'blur(16px) saturate(140%)',
                border: '1px solid rgba(255, 255, 255, 0.6)',
                borderRadius: 16,
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.7)',
                overflow: 'hidden',
              }}>
                <div className="flex items-center gap-3 px-6 pt-5 pb-3">
                  <Icon size={18} style={{ color: 'var(--primary-700)' }} />
                  <div>
                    <h3 style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 600, fontSize: 16, color: 'var(--text-primary)', margin: 0 }}>
                      {section.title}
                    </h3>
                    <p style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 13, color: 'var(--text-tertiary)', margin: '2px 0 0 0' }}>
                      {section.description}
                    </p>
                  </div>
                </div>

                {section.settings.map((setting) => (
                  <div key={setting.id} className="flex items-center justify-between px-6 py-4"
                    style={{ borderTop: '1px solid rgba(148, 163, 184, 0.1)' }}>
                    <div>
                      <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                        {setting.label}
                      </div>
                      <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 13, color: 'var(--text-tertiary)', marginTop: 1 }}>
                        {setting.description}
                      </div>
                    </div>
                    <Toggle enabled={settings[setting.id]} onToggle={() => toggle(setting.id)} />
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        <div style={{
          marginTop: 24, padding: '16px 20px', borderRadius: 'var(--radius-md)',
          background: 'rgba(255, 255, 255, 0.3)', textAlign: 'center',
        }}>
          <p style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: 13, color: 'var(--text-tertiary)', margin: 0 }}>
            AxonAI · Greenfield Secondary School
          </p>
        </div>
      </div>
    </DashboardShell>
  );
}
