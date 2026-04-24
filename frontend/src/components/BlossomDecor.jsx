import React, { useMemo } from 'react';

const PETAL_COLORS = ['#F8AFC0', '#EE98AF', '#F7B9C9', '#E684A2', '#F3A7BB', '#E07496'];

function randomBetween(min, max) {
  return Math.random() * (max - min) + min;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function PetalLayer({ count = 44 }) {
  const petals = useMemo(
    () =>
      Array.from({ length: count }, (_, i) => ({
        id: i,
        // Evenly spread petals across the full viewport width with slight jitter.
        left: clamp(((i + 0.5) / count) * 100 + randomBetween(-6, 6), -3, 103),
        size: randomBetween(11, 24),
        duration: randomBetween(10, 20),
        delay: randomBetween(0, 8),
        // Start part-way through the animation so petals are already visible on first paint.
        preProgress: randomBetween(0.35, 0.95),
        drift: randomBetween(-120, 120),
        rotate: randomBetween(200, 520),
        sway: randomBetween(-36, 36),
        opacity: randomBetween(0.48, 0.9),
        color: PETAL_COLORS[Math.floor(Math.random() * PETAL_COLORS.length)],
      })),
    [count],
  );

  return (
    <div aria-hidden style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 1 }}>
      {petals.map((p) => (
        <span
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.left}%`,
            top: -24,
            width: p.size,
            height: p.size,
            borderRadius: '50% 50% 50% 10px',
            background: p.color,
            opacity: p.opacity,
            animation: `petal-fall-${p.id} ${p.duration}s linear ${p.delay - p.duration * p.preProgress}s infinite`,
            transformOrigin: 'center',
            filter: 'blur(0.1px)',
          }}
        />
      ))}
      <style>
        {petals
          .map(
            (p) => `@keyframes petal-fall-${p.id} {
          0% { transform: translate(0, 0) rotate(0deg); opacity: 0; }
          7% { opacity: ${p.opacity}; }
          52% { transform: translate(${p.sway}px, 48vh) rotate(${p.rotate * 0.48}deg); }
          100% { transform: translate(${p.drift}px, 108vh) rotate(${p.rotate}deg); opacity: 0; }
        }`,
          )
          .join('\n')}
      </style>
    </div>
  );
}

function BlossomTree({ style }) {
  return (
    <svg viewBox="0 0 500 700" fill="none" style={style} aria-hidden>
      <path d="M252 698 C248 658 242 608 236 566 C230 524 224 490 226 456 C228 424 234 398 238 368 C242 340 244 316 242 292" stroke="#2E1A0E" strokeWidth="30" strokeLinecap="round" />
      <path d="M236 308 C218 280 194 250 164 222 C138 198 106 176 74 160" stroke="#2E1A0E" strokeWidth="16" strokeLinecap="round" />
      <path d="M242 300 C260 270 284 240 312 214 C336 192 368 170 402 154" stroke="#2E1A0E" strokeWidth="16" strokeLinecap="round" />
      <path d="M240 278 C236 246 230 212 224 178 C218 148 212 120 208 94" stroke="#2E1A0E" strokeWidth="13" strokeLinecap="round" />
      <path d="M74 160 C52 142 32 120 14 96" stroke="#2E1A0E" strokeWidth="10" strokeLinecap="round" />
      <path d="M402 154 C424 136 446 114 464 90" stroke="#2E1A0E" strokeWidth="10" strokeLinecap="round" />
      <path d="M222 186 C206 164 186 144 164 128" stroke="#2E1A0E" strokeWidth="8" strokeLinecap="round" />
      <path d="M220 204 C238 182 260 162 282 146" stroke="#2E1A0E" strokeWidth="8" strokeLinecap="round" />
      {[
        [62, 144, 56],
        [2, 48, 46],
        [72, 32, 48],
        [98, 178, 34],
        [412, 142, 58],
        [490, 40, 48],
        [394, 24, 50],
        [346, 198, 34],
        [204, 78, 50],
        [184, 24, 42],
        [232, 24, 40],
        [98, 308, 40],
        [350, 304, 40],
      ].map(([cx, cy, r], idx) => (
        <g key={idx}>
          <ellipse cx={cx} cy={cy} rx={r * 1.28} ry={r * 0.98} fill="#FBD1DB" opacity="0.62" />
          <ellipse cx={cx - r * 0.25} cy={cy + r * 0.08} rx={r * 0.9} ry={r * 0.7} fill="#F3A7BB" opacity="0.78" />
          <ellipse cx={cx + r * 0.22} cy={cy - r * 0.08} rx={r * 0.8} ry={r * 0.63} fill="#EB8DA8" opacity="0.82" />
          <ellipse cx={cx + r * 0.05} cy={cy + r * 0.18} rx={r * 0.58} ry={r * 0.45} fill="#DE6F90" opacity="0.74" />
        </g>
      ))}
    </svg>
  );
}

export default function BlossomDecor({ petals = 24 }) {
  return (
    <>
      <BlossomTree
        style={{
          position: 'fixed',
          left: -110,
          top: -70,
          width: 560,
          height: 760,
          opacity: 0.24,
          pointerEvents: 'none',
          zIndex: 0,
          transform: 'scaleX(-1)',
        }}
      />
      <BlossomTree
        style={{
          position: 'fixed',
          right: -110,
          top: -70,
          width: 560,
          height: 760,
          opacity: 0.26,
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />
      <PetalLayer count={petals} />
    </>
  );
}

