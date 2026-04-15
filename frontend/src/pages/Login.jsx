import React from 'react';
import { useNavigate } from 'react-router-dom';

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
    <div className="app-shell ux-auth-surface min-h-screen flex items-center justify-center px-[max(var(--ux-space-3),env(safe-area-inset-left))] py-[var(--ux-space-5)] pr-[max(var(--ux-space-3),env(safe-area-inset-right))] pb-[max(var(--ux-space-4),env(safe-area-inset-bottom))] pt-[max(var(--ux-space-4),env(safe-area-inset-top))] sm:px-[max(var(--ux-space-4),env(safe-area-inset-left))] sm:pr-[max(var(--ux-space-4),env(safe-area-inset-right))]">
      <div className="relative mx-auto w-full max-w-sm sm:max-w-md">
        <div
          aria-hidden
          className="axon-card pointer-events-none absolute inset-0 rounded-[20px]"
        />
        <div className="relative z-[1] px-[var(--ux-space-4)] py-[var(--ux-space-5)] sm:px-[var(--ux-space-5)] sm:py-[var(--ux-space-6)]">
          <div className="mb-[var(--ux-space-5)] text-center">
            <div className="mb-[var(--ux-space-4)] inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-500 text-xl font-semibold text-white shadow-sm">
              A
            </div>
            <h1 className="axon-h2 mb-[var(--ux-space-3)] text-xl tracking-tight text-slate-800 sm:text-2xl">
              Choose how you&apos;re signing in
            </h1>
            <p className="mx-auto max-w-[min(100%,var(--ux-max-read))] text-sm leading-[var(--ux-line-relaxed)] text-slate-500">
              This demo skips passwords — pick the view that matches you.
            </p>
          </div>

          <div className="login-role-stack flex flex-col gap-3 overflow-visible sm:gap-4">
            {roles.map((role, index) => {
              const slab = index % 2 === 0;
              return (
                <div key={role.id} className="login-role-pop-wrap">
                  <button
                    type="button"
                    onClick={() => navigate(role.path)}
                    className={`login-role-axon-btn axon-btn w-full text-left ${
                      slab ? 'axon-btn-primary' : 'axon-btn-ghost'
                    }`}
                  >
                    <span className="login-role-title text-[#2c2418]">{role.label}</span>
                    <span className="login-role-desc text-[#3d3429]">{role.description}</span>
                  </button>
                </div>
              );
            })}
          </div>

          <div className="mt-[var(--ux-space-5)] border-t border-slate-200/60 pt-[var(--ux-space-4)]">
            <p className="text-center text-xs leading-[var(--ux-line-relaxed)] text-slate-400">
              AxonAI demo — no real student data is used here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
