import React, { useEffect, useState } from 'react';
import { ProgressBar } from 'pixel-retroui';

/**
 * @param {object} props
 * @param {string} [props.message]
 * @param {number} [props.progress] — 0–100; if omitted, a gentle indeterminate fill runs.
 */
export default function LoadingSpinner({ message = 'Loading data...', progress: progressProp }) {
  const [fallback, setFallback] = useState(0);

  useEffect(() => {
    if (typeof progressProp === 'number') return undefined;
    const start = performance.now();
    let raf;
    const tick = () => {
      const elapsedSec = (performance.now() - start) / 1000;
      setFallback(Math.min(92, 100 * (1 - Math.exp(-0.35 * elapsedSec))));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [progressProp]);

  const p =
    typeof progressProp === 'number'
      ? Math.min(100, Math.max(0, progressProp))
      : fallback;

  return (
    <div className="mx-auto flex w-full max-w-md flex-col items-stretch justify-center px-4 py-16">
      <ProgressBar
        progress={p}
        size="lg"
        color="#14b8a6"
        borderColor="#2c2418"
        className="w-full"
      />
      <p className="mt-6 text-center text-sm font-medium text-slate-700">{message}</p>
    </div>
  );
}
