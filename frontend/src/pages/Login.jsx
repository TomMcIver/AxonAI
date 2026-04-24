import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  primeTeacherClassOverview,
  primeStudentDashboard,
  primeParentDashboard,
} from '../api/primedRequests';
import BlossomDecor from '../components/BlossomDecor';

const roles = [
  {
    id: 'teacher',
    label: 'Teacher',
    description: 'Plan lessons and see class mastery.',
    path: '/teacher',
  },
  {
    id: 'student',
    label: 'Student',
    description: 'Check what you know and what to revise.',
    path: '/student',
  },
  {
    id: 'parent',
    label: 'Parent / Whanau',
    description: 'View calm summaries of progress.',
    path: '/parent',
  },
];

export default function Login() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', background: '#FDF6EE', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', fontFamily: "'Lora', serif", padding: 20 }}>
      <BlossomDecor petals={52} />
      <div style={{ width: '100%', maxWidth: 760, position: 'relative', zIndex: 5 }}>
        <div style={{ marginBottom: 18 }}>
          <button type="button" className="axon-btn axon-btn-quiet" onClick={() => navigate('/')}>
            ← Back
          </button>
        </div>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <h1 style={{ fontFamily: "'Shippori Mincho', serif", fontSize: 42, margin: '0 0 6px', color: '#3D2B1F' }}>AxonAI</h1>
          <p style={{ margin: 0, color: '#6B4A3A', fontStyle: 'italic' }}>Who are you learning with today?</p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 14 }}>
          {roles.map((role) => (
            <button
              key={role.id}
              type="button"
              onClick={() => {
                if (role.id === 'teacher') primeTeacherClassOverview(1);
                else if (role.id === 'student') primeStudentDashboard(1);
                else if (role.id === 'parent') primeParentDashboard(1);
                navigate(role.path);
              }}
              style={{ border: '1.5px solid rgba(61,43,31,0.15)', borderRadius: 20, background: 'rgba(255,255,255,0.8)', textAlign: 'left', padding: '24px 18px', cursor: 'pointer', boxShadow: '0 4px 16px rgba(61,43,31,0.08)' }}
            >
              <div style={{ fontFamily: "'Shippori Mincho', serif", fontWeight: 700, fontSize: 23, color: '#3D2B1F', marginBottom: 8 }}>{role.label}</div>
              <div style={{ fontSize: 13, color: '#6B4A3A', lineHeight: 1.55 }}>{role.description}</div>
            </button>
          ))}
        </div>
        <div style={{ marginTop: 20, textAlign: 'center', fontSize: 12, color: '#6B4A3A' }}>AxonAI demo: no real student data is used here.</div>
      </div>
    </div>
  );
}
