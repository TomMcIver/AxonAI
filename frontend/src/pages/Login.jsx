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
    <div className="app-shell min-h-screen flex items-center justify-center px-4">
      <div className="axon-card w-full max-w-md px-6 py-6 sm:px-7 sm:py-7">
        <div className="mb-6 text-center">
          <div className="inline-flex items-center justify-center h-10 w-10 rounded-2xl bg-teal-500 text-white font-semibold text-lg mb-3">
            A
          </div>
          <h1 className="axon-h2 text-lg sm:text-xl text-slate-800 mb-1">
            Choose how you&apos;re signing in
          </h1>
          <p className="text-xs text-slate-500">
            This demo skips passwords — pick the view that matches you.
          </p>
        </div>

        <div className="space-y-2.5">
          {roles.map(role => (
            <button
              key={role.id}
              onClick={() => navigate(role.path)}
              className="group w-full rounded-lg border border-slate-200/80 bg-white/40 hover:border-teal-400/60 hover:bg-white/70 transition-colors px-3.5 py-3 text-left"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-700 group-hover:text-teal-700">
                    {role.label}
                  </p>
                  <p className="text-[0.72rem] text-slate-500 truncate">
                    {role.description}
                  </p>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-teal-600">
                  &#8594;
                </span>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-5 border-t border-slate-200/60 pt-3">
          <p className="text-[0.7rem] text-slate-400 text-center">
            AxonAI demo — no real student data is used here.
          </p>
        </div>
      </div>
    </div>
  );
}
