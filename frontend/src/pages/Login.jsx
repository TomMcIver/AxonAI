import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from 'pixel-retroui';

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
      <Card className="axon-card mx-auto w-full max-w-sm px-[var(--ux-space-4)] py-[var(--ux-space-5)] sm:max-w-md sm:px-[var(--ux-space-5)] sm:py-[var(--ux-space-6)]">
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

        <div className="flex flex-col gap-[var(--ux-space-3)] sm:gap-[var(--ux-space-4)]">
          {roles.map(role => (
            <button
              key={role.id}
              type="button"
              onClick={() => navigate(role.path)}
              className="group relative w-full rounded-[6px] border-2 border-[#2c2418] bg-[#f6c445] px-[var(--ux-space-3)] py-[var(--ux-space-3)] text-left shadow-[3px_3px_0_#2c2418] transition-[transform,box-shadow,background-color] duration-150 ease-out hover:bg-[#ffd66f] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2c2418] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fffef4] active:translate-x-[1px] active:translate-y-[1px] active:shadow-[2px_2px_0_#2c2418] sm:px-[var(--ux-space-4)] sm:py-[var(--ux-space-4)]"
            >
              <div className="flex items-start justify-between gap-[var(--ux-space-3)] sm:gap-[var(--ux-space-4)]">
                <div className="min-w-0 flex-1">
                  <p className="font-['Press_Start_2P',Inter,system-ui,sans-serif] text-[11px] font-normal uppercase leading-snug tracking-[0.04em] text-[#2c2418] sm:text-xs">
                    {role.label}
                  </p>
                  <p className="mt-2 text-sm leading-[var(--ux-line-relaxed)] text-[#3d3429]">
                    {role.description}
                  </p>
                </div>
                <span
                  className="mt-0.5 shrink-0 text-base text-[#2c2418]/50 transition-transform duration-150 group-hover:translate-x-0.5"
                  aria-hidden
                >
                  &#8594;
                </span>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-[var(--ux-space-5)] border-t border-slate-200/60 pt-[var(--ux-space-4)]">
          <p className="text-center text-xs leading-[var(--ux-line-relaxed)] text-slate-400">
            AxonAI demo — no real student data is used here.
          </p>
        </div>
      </Card>
    </div>
  );
}
