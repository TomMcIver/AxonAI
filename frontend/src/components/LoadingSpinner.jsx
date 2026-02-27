import React from 'react';

export default function LoadingSpinner({ message = 'Loading data...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-12 h-12 border-4 border-[#E2E8F0] border-t-[#0891B2] rounded-full animate-spin mb-4" />
      <p className="text-[#6B7280] text-sm">{message}</p>
      <p className="text-[#94A3B8] text-xs mt-1">First load may take 15-30s (cold start)</p>
    </div>
  );
}
