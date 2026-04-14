import React from 'react';

export default function LoadingSpinner({ message = 'Loading data...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-12 h-12 border-4 border-[#2c2418] border-t-amber-400 rounded-full animate-spin mb-4" />
      <p className="text-slate-700 text-sm font-medium">{message}</p>
      <p className="text-slate-400 text-xs mt-1">First load may take 15-30s (cold start)</p>
    </div>
  );
}
