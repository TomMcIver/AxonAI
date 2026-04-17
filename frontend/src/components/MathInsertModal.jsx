import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

/** Strip characters that break $…$ wrapping; keep typical school LaTeX. */
function sanitizeTexPart(s) {
  return String(s ?? '')
    .trim()
    .replace(/\$/g, '')
    .slice(0, 200);
}

const NOTATIONS = [
  { id: 'fraction', label: 'Fraction', hint: 'Top and bottom boxes' },
  { id: 'sqrt', label: 'Square root', hint: '√' },
  { id: 'power', label: 'Power', hint: 'xⁿ' },
  { id: 'subscript', label: 'Subscript', hint: 'xₙ' },
  { id: 'sum', label: 'Sum Σ', hint: 'Insert Σ' },
  { id: 'integral', label: 'Integral ∫', hint: 'Insert ∫' },
  { id: 'pi', label: 'Pi π', hint: 'Insert π' },
  { id: 'times', label: 'Times ×', hint: 'Insert ×' },
];

/**
 * Build LaTeX for the API (inside $…$). Returns { latex: full inline math string }.
 */
function buildLatex(kind, fields) {
  switch (kind) {
    case 'fraction': {
      const a = sanitizeTexPart(fields.num);
      const b = sanitizeTexPart(fields.den);
      if (!a && !b) return null;
      return `$\\frac{${a || '?'}}{${b || '?'}}$`;
    }
    case 'sqrt': {
      const inner = sanitizeTexPart(fields.inner);
      if (!inner) return null;
      return `$\\sqrt{${inner}}$`;
    }
    case 'power': {
      const base = sanitizeTexPart(fields.base);
      const exp = sanitizeTexPart(fields.exp);
      if (!base && !exp) return null;
      return `$${base || '?'}^{${exp || '?'}}$`;
    }
    case 'subscript': {
      const base = sanitizeTexPart(fields.base);
      const sub = sanitizeTexPart(fields.sub);
      if (!base && !sub) return null;
      return `$${base || '?'}_{${sub || '?'}}$`;
    }
    case 'sum':
      return '$\\sum$';
    case 'integral':
      return '$\\int$';
    case 'pi':
      return '$\\pi$';
    case 'times':
      return '$\\times$';
    default:
      return null;
  }
}

export default function MathInsertModal({ open, onClose, onInsert }) {
  const [panel, setPanel] = useState('menu');
  const [num, setNum] = useState('');
  const [den, setDen] = useState('');
  const [sqrtInner, setSqrtInner] = useState('');
  const [powBase, setPowBase] = useState('');
  const [powExp, setPowExp] = useState('');
  const [subBase, setSubBase] = useState('');
  const [subSub, setSubSub] = useState('');

  useEffect(() => {
    if (open) {
      setPanel('menu');
      setNum('');
      setDen('');
      setSqrtInner('');
      setPowBase('');
      setPowExp('');
      setSubBase('');
      setSubSub('');
    }
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  function handleInsert(kind, fields = {}) {
    const latex = buildLatex(kind, fields);
    if (latex) {
      onInsert(latex);
      onClose();
    }
  }

  function footer() {
    return (
      <div className="mt-4 flex justify-between gap-2 border-t border-slate-200 pt-3">
        <button
          type="button"
          onClick={() => (panel === 'menu' ? onClose() : setPanel('menu'))}
          className="axon-btn axon-btn-ghost text-sm"
        >
          {panel === 'menu' ? 'Close' : '← Back'}
        </button>
      </div>
    );
  }

  /** Portal to document.body so z-index is not trapped by main { isolation: isolate }. */
  return createPortal(
    <div
      className="fixed inset-0 z-[20000] flex items-end justify-center p-3 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="math-insert-title"
    >
      <button
        type="button"
        className="absolute inset-0 z-0 bg-[#2c2418]/60 backdrop-blur-sm"
        aria-label="Close"
        onClick={onClose}
      />
      <div
        className="relative z-10 flex max-h-[min(90dvh,36rem)] w-full max-w-md flex-col overflow-hidden rounded-2xl border-2 border-[#2c2418] bg-[#fffef4] shadow-[6px_6px_0_#2c2418]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain p-4 sm:p-5">
        <div className="mb-3 flex items-start justify-between gap-2">
          <div>
            <h2 id="math-insert-title" className="axon-h2 text-base text-slate-800">
              Insert math
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Choose a notation — it’s inserted as LaTeX so the tutor can read it.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 bg-white/80 p-1.5 text-slate-600 hover:bg-white"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {panel === 'menu' && (
          <>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {NOTATIONS.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => {
                    if (['sum', 'integral', 'pi', 'times'].includes(n.id)) {
                      handleInsert(n.id);
                    } else {
                      setPanel(n.id);
                    }
                  }}
                  className="flex flex-col items-start rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-left text-sm text-slate-800 shadow-sm transition-colors hover:bg-slate-50"
                >
                  <span className="font-medium">{n.label}</span>
                  <span className="text-[0.65rem] text-slate-500">{n.hint}</span>
                </button>
              ))}
            </div>
            {footer()}
          </>
        )}

        {panel === 'fraction' && (
          <>
            <p className="mb-3 text-xs text-slate-600">Type the top and bottom of the fraction (LaTeX inside each part is OK, e.g. x+1).</p>
            <div className="mx-auto max-w-[220px] space-y-2">
              <input
                type="text"
                value={num}
                onChange={(e) => setNum(e.target.value)}
                placeholder="Numerator"
                className="w-full rounded-lg border-2 border-[#2c2418]/30 bg-white px-2 py-2 text-center font-mono text-sm text-slate-900 placeholder:text-slate-400"
                autoFocus
              />
              <div className="h-0.5 w-full bg-[#2c2418]" aria-hidden />
              <input
                type="text"
                value={den}
                onChange={(e) => setDen(e.target.value)}
                placeholder="Denominator"
                className="w-full rounded-lg border-2 border-[#2c2418]/30 bg-white px-2 py-2 text-center font-mono text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => handleInsert('fraction', { num, den })}
                disabled={!sanitizeTexPart(num) && !sanitizeTexPart(den)}
                className="axon-btn axon-btn-primary flex-1 justify-center text-sm disabled:opacity-50"
              >
                Insert into message
              </button>
            </div>
            {footer()}
          </>
        )}

        {panel === 'sqrt' && (
          <>
            <p className="mb-3 text-xs text-slate-600">What goes under the square root?</p>
            <input
              type="text"
              value={sqrtInner}
              onChange={(e) => setSqrtInner(e.target.value)}
              placeholder="e.g. x+1 or 16"
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-sm"
              autoFocus
            />
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => handleInsert('sqrt', { inner: sqrtInner })}
                disabled={!sanitizeTexPart(sqrtInner)}
                className="axon-btn axon-btn-primary flex-1 justify-center text-sm disabled:opacity-50"
              >
                Insert into message
              </button>
            </div>
            {footer()}
          </>
        )}

        {panel === 'power' && (
          <>
            <p className="mb-3 text-xs text-slate-600">Base and exponent (e.g. x and 2 for x²).</p>
            <div className="flex flex-wrap items-end justify-center gap-2">
              <div className="flex flex-col gap-1">
                <span className="text-[0.65rem] uppercase text-slate-500">Base</span>
                <input
                  type="text"
                  value={powBase}
                  onChange={(e) => setPowBase(e.target.value)}
                  className="w-24 rounded-lg border border-slate-200 bg-white px-2 py-2 text-center font-mono text-sm"
                  placeholder="x"
                />
              </div>
              <span className="pb-2 text-lg font-light text-slate-400">^</span>
              <div className="flex flex-col gap-1">
                <span className="text-[0.65rem] uppercase text-slate-500">Power</span>
                <input
                  type="text"
                  value={powExp}
                  onChange={(e) => setPowExp(e.target.value)}
                  className="w-24 rounded-lg border border-slate-200 bg-white px-2 py-2 text-center font-mono text-sm"
                  placeholder="2"
                />
              </div>
            </div>
            <div className="mt-4">
              <button
                type="button"
                onClick={() => handleInsert('power', { base: powBase, exp: powExp })}
                disabled={!sanitizeTexPart(powBase) && !sanitizeTexPart(powExp)}
                className="axon-btn axon-btn-primary w-full justify-center text-sm disabled:opacity-50"
              >
                Insert into message
              </button>
            </div>
            {footer()}
          </>
        )}

        {panel === 'subscript' && (
          <>
            <p className="mb-3 text-xs text-slate-600">Base and subscript (e.g. x and n for xₙ).</p>
            <div className="flex flex-wrap items-end justify-center gap-2">
              <div className="flex flex-col gap-1">
                <span className="text-[0.65rem] uppercase text-slate-500">Base</span>
                <input
                  type="text"
                  value={subBase}
                  onChange={(e) => setSubBase(e.target.value)}
                  className="w-24 rounded-lg border border-slate-200 bg-white px-2 py-2 text-center font-mono text-sm"
                  placeholder="x"
                />
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-[0.65rem] uppercase text-slate-500">Sub</span>
                <input
                  type="text"
                  value={subSub}
                  onChange={(e) => setSubSub(e.target.value)}
                  className="w-24 rounded-lg border border-slate-200 bg-white px-2 py-2 text-center font-mono text-sm"
                  placeholder="n"
                />
              </div>
            </div>
            <div className="mt-4">
              <button
                type="button"
                onClick={() => handleInsert('subscript', { base: subBase, sub: subSub })}
                disabled={!sanitizeTexPart(subBase) && !sanitizeTexPart(subSub)}
                className="axon-btn axon-btn-primary w-full justify-center text-sm disabled:opacity-50"
              >
                Insert into message
              </button>
            </div>
            {footer()}
          </>
        )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
