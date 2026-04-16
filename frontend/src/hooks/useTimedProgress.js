import { useEffect, useState } from 'react';

/**
 * Linear 0 → 100 over `durationMs` (for ProgressBar sync with minimum display time).
 * `resetEpoch`: increment to restart the bar (e.g. retry or route param change).
 */
export function useTimedProgress(durationMs = 4000, resetEpoch = 0) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setProgress(0);
    const start = performance.now();
    let raf;

    const tick = () => {
      const t = (performance.now() - start) / durationMs;
      if (t >= 1) {
        setProgress(100);
        return;
      }
      setProgress(t * 100);
      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [durationMs, resetEpoch]);

  return progress;
}
