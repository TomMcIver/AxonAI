import React, { useState, useEffect, useMemo } from 'react';
import katex from 'katex';
import { getConversationMessages } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';
import 'katex/dist/katex.min.css';

const TUTOR_ROLES = ['tutor', 'assistant', 'ai', 'system', 'bot', 'ai_tutor', 'axonai'];

function isTutorRole(role) {
  return TUTOR_ROLES.includes((role || '').toLowerCase().replace(/\s+/g, '_'));
}

function renderKatexHtml(tex, displayMode) {
  const trimmed = (tex || '').trim();
  if (!trimmed) return '';
  try {
    return katex.renderToString(trimmed, {
      displayMode,
      throwOnError: false,
      strict: false,
    });
  } catch {
    return `<span class="text-rose-600">${String(tex).replace(/</g, '&lt;')}</span>`;
  }
}

/** True if message already uses LaTeX delimiters (caret-injection may still be skipped). */
function hasExplicitDelimiters(s) {
  return /\$\$|\$(?!\$)|\\\(|\\\[/.test(String(s));
}

/** Rough count of dictionary-looking words (avoids wrapping paragraphs in $$ / whole-blob KaTeX). */
function countLongAlphaWords(s) {
  return (String(s).match(/\b[a-zA-Z]{5,}\b/g) || []).length;
}

/** True if this line is mostly prose (must NOT be wrapped entirely in math mode; spaces would collapse). */
function isProseHeavyLine(tr) {
  if (!tr) return true;
  if (tr.length > 220) return true;
  if (countLongAlphaWords(tr) > 10) return true;
  if ((tr.match(/[.!?]/g) || []).length >= 2) return true;
  return false;
}

function skipSpaces(str, i) {
  let k = i;
  while (k < str.length && /\s/.test(str[k])) k += 1;
  return k;
}

/** `i` points at `{`; returns index after matching `}`. */
function endOfBalancedBraces(str, i) {
  if (str[i] !== '{') return -1;
  let depth = 0;
  for (let k = i; k < str.length; k += 1) {
    const c = str[k];
    if (c === '{') depth += 1;
    else if (c === '}') {
      depth -= 1;
      if (depth === 0) return k + 1;
    }
  }
  return -1;
}

/**
 * Parse `\\lim_{...}\\frac{...}{...}` with nested braces (e.g. x^{n-1} in the numerator).
 * Returns { tex, end } or null.
 */
function parseBareLimFracAt(s, start) {
  if (!s.startsWith('\\lim_', start)) return null;
  let i = start + 5;
  const subEnd = endOfBalancedBraces(s, i);
  if (subEnd === -1) return null;
  i = skipSpaces(s, subEnd);
  if (!s.startsWith('\\frac', i)) return null;
  i += 5;
  const numEnd = endOfBalancedBraces(s, i);
  if (numEnd === -1) return null;
  i = numEnd;
  const denEnd = endOfBalancedBraces(s, i);
  if (denEnd === -1) return null;
  return { tex: s.slice(start, denEnd), end: denEnd };
}

/** Wrap each bare \\lim\\frac expression in `$...$` (chunk has no $ delimiters yet). */
function wrapBareLimFracInPlainChunk(chunk) {
  let out = '';
  let i = 0;
  while (i < chunk.length) {
    const j = chunk.indexOf('\\lim_', i);
    if (j === -1) {
      out += chunk.slice(i);
      break;
    }
    const parsed = parseBareLimFracAt(chunk, j);
    if (parsed) {
      out += chunk.slice(i, j);
      out += `$${parsed.tex}$`;
      i = parsed.end;
    } else {
      out += chunk.slice(i, j + 1);
      i = j + 1;
    }
  }
  return out;
}

/**
 * Apply `fn` only to runs outside `$$...$$` and single `$...$` so we never inject carets into LaTeX.
 */
function mapOutsideDollarRegions(line, fn) {
  let out = '';
  let i = 0;
  while (i < line.length) {
    if (line.startsWith('$$', i)) {
      const end = line.indexOf('$$', i + 2);
      if (end === -1) {
        out += line.slice(i);
        break;
      }
      out += line.slice(i, end + 2);
      i = end + 2;
      continue;
    }
    if (line[i] === '$') {
      const end = line.indexOf('$', i + 1);
      if (end === -1) {
        out += line.slice(i);
        break;
      }
      out += line.slice(i, end + 1);
      i = end + 1;
      continue;
    }
    const nextDd = line.indexOf('$$', i);
    const nextD = line.indexOf('$', i);
    let endChunk = line.length;
    if (nextDd !== -1) endChunk = Math.min(endChunk, nextDd);
    if (nextD !== -1) endChunk = Math.min(endChunk, nextD);
    out += fn(line.slice(i, endChunk));
    i = endChunk;
  }
  return out;
}

function applyCaretRulesToPlainChunk(chunk) {
  let t = chunk;
  t = t.replace(/(\([^)]{1,160}\))\^([a-zA-Z0-9]+)(?=\s|[.,;:!?)\]]|$)/g, '$$$1^{$2}$$');
  t = t.replace(/([a-zA-Z0-9]+)\^\(([^)]{1,48})\)/g, '$$$1^{$2}$$');
  t = t.replace(
    /(^|[^\w$])([a-zA-Z][a-zA-Z0-9']*|[a-zA-Z0-9]+)\^([a-zA-Z0-9+\-]+)(?=[\s,.,;:!?)\]]|$)/g,
    (m, pre, a, b) => {
      if (/^(the|and|for|you|not|are|was|has|had|how|our|out|its|but)$/i.test(a)) return m;
      return `${pre}$${a}^{${b}}$`;
    },
  );
  return t;
}

/**
 * Lines that are already LaTeX (\\lim, \\frac, …) but have no $ on that line: wrap in $$ so the tokenizer + KaTeX run.
 * Never wrap long / prose-heavy lines (entire paragraph would render as math and eat spaces).
 */
function wrapBareLatexDisplayLines(s) {
  return s
    .split('\n')
    .map((line) => {
      const tr = line.trim();
      if (!tr || tr.length > 800) return line;
      if (/\$/.test(tr)) return line;
      if (!/\\[a-zA-Z]/.test(tr)) return line;
      if (isProseHeavyLine(tr)) return line;
      if (
        !/\\(frac|lim|sqrt|sum|int|iint|iiint|oint|prod|pm|mp|cdot|times|div|equiv|leq|geq|neq|approx|infty|partial|nabla|begin|end|left|right|bigl|bigr|overbrace|underbrace|text)/.test(
          tr,
        )
      ) {
        return line;
      }
      return line.replace(tr, `$$${tr}$$`);
    })
    .join('\n');
}

/** Heuristic: line is mostly formula (tutor sends plain "f(x)=x^n" with no $). */
function looksLikeMathyLine(t) {
  const s = t.trim();
  if (!s || s.length > 500) return false;
  if (isProseHeavyLine(s)) return false;
  if (/[\^\\]/.test(s)) return true;
  if (/→|−/.test(s)) return true;
  if (/\blim\b|\bfrac\b|\bsqrt\b|∫|∑|∏/i.test(s)) return true;
  if (/[a-zA-Z0-9_]\s*=\s*[\(\-a-z0-9]/i.test(s) && /[+\-*/^_()[\]{}]/.test(s)) return true;
  return false;
}

/**
 * Tutor/student messages often omit $...$. Normalize ASCII math and inject $...$ / $$...$$
 * so the delimiter parser + KaTeX can render.
 */
function preprocessPlainMathForDelimiters(raw) {
  let s = String(raw).replace(/→/g, '\\to ').replace(/−/g, '-');

  // ASCII lim / fraction brackets → LaTeX (before wrapping bare \lim/\frac lines)
  const pass1 = s
    .split('\n')
    .map((line) => {
      let t = line;
      t = t.replace(/lim\s*\(\s*(\w+)\s*(?:→|\\to|->)\s*0\s*\)/gi, '\\lim_{$1 \\to 0}');
      t = t.replace(/\[([^\]]+)\]\s*\/\s*([a-zA-Z0-9]+)/g, '\\frac{$1}{$2}');
      return t;
    })
    .join('\n');

  // Raw \lim_{h \to 0} \frac{...}{...} with no $ on the line
  let pass2 = wrapBareLatexDisplayLines(pass1);

  const skipCaretInject = hasExplicitDelimiters(pass2);

  const lines = pass2.split('\n');
  const out = lines.map((line) => {
    let t = line;
    const trimmed = t.trim();
    if (!trimmed) return t;

    const tr = t.trim();
    const words = tr.split(/\s+/).filter(Boolean).length;

    // One-line equation (e.g. f(x) = x^n): only short, non-prose lines (never a full tutor paragraph)
    if (
      !/\$/.test(tr) &&
      words <= 28 &&
      tr.length <= 180 &&
      !isProseHeavyLine(tr) &&
      looksLikeMathyLine(tr) &&
      /^[a-zA-Z_(\\]/.test(tr) &&
      /=\s*[\(\-a-z0-9\\]/i.test(tr)
    ) {
      return t.replace(tr, `$$${tr}$$`);
    }

    // 1) Wrap \\lim\\frac with balanced braces before carets (carets used to break \\frac{(x+h)^n}{h})
    t = mapOutsideDollarRegions(t, wrapBareLimFracInPlainChunk);

    if (skipCaretInject) return t;

    // 2) Caret / ASCII exponents only outside existing $...$ / $$...$$
    t = mapOutsideDollarRegions(t, applyCaretRulesToPlainChunk);

    return t;
  });

  return out.join('\n');
}

/** Split plain / inline / block segments: $$..$$, \\[..\\], then $..$, \\(..\\) in text runs */
function segmentMessageContent(content) {
  const pre = preprocessPlainMathForDelimiters(content);
  if (pre == null || pre === '') return [{ type: 'text', value: '' }];

  const out = [];
  let pos = 0;
  const s = pre;

  while (pos < s.length) {
    const dd = s.indexOf('$$', pos);
    const bb = s.indexOf('\\[', pos);
    let pick = -1;
    let kind = null;
    if (dd !== -1 && (bb === -1 || dd <= bb)) {
      pick = dd;
      kind = 'dd';
    } else if (bb !== -1) {
      pick = bb;
      kind = 'bb';
    }

    if (pick === -1) {
      pushInlineSegments(s.slice(pos), out);
      break;
    }

    if (pick > pos) {
      pushInlineSegments(s.slice(pos, pick), out);
    }

    if (kind === 'dd') {
      const end = s.indexOf('$$', pick + 2);
      if (end === -1) {
        pushInlineSegments(s.slice(pick), out);
        break;
      }
      out.push({ type: 'block', value: s.slice(pick + 2, end) });
      pos = end + 2;
    } else {
      const end = s.indexOf('\\]', pick + 2);
      if (end === -1) {
        pushInlineSegments(s.slice(pick), out);
        break;
      }
      out.push({ type: 'block', value: s.slice(pick + 2, end) });
      pos = end + 2;
    }
  }

  return out;
}

function pushInlineSegments(text, out) {
  if (!text) return;
  let pos = 0;
  while (pos < text.length) {
    const paren = text.indexOf('\\(', pos);
    let dollar = text.indexOf('$', pos);
    while (dollar !== -1 && text[dollar + 1] === '$') {
      dollar = text.indexOf('$', dollar + 2);
    }

    let next = -1;
    let mode = null;
    if (paren === -1 && dollar === -1) {
      out.push({ type: 'text', value: text.slice(pos) });
      return;
    }
    if (paren === -1) {
      next = dollar;
      mode = 'dollar';
    } else if (dollar === -1) {
      next = paren;
      mode = 'paren';
    } else if (paren < dollar) {
      next = paren;
      mode = 'paren';
    } else {
      next = dollar;
      mode = 'dollar';
    }

    if (next > pos) {
      out.push({ type: 'text', value: text.slice(pos, next) });
    }

    if (mode === 'paren') {
      const end = text.indexOf('\\)', next + 2);
      if (end === -1) {
        out.push({ type: 'text', value: text.slice(next) });
        break;
      }
      out.push({ type: 'inline', value: text.slice(next + 2, end) });
      pos = end + 2;
    } else {
      const end = text.indexOf('$', next + 1);
      if (end === -1) {
        out.push({ type: 'text', value: text.slice(next) });
        break;
      }
      out.push({ type: 'inline', value: text.slice(next + 1, end) });
      pos = end + 1;
    }
  }
}

/**
 * Last resort: small text segment still contains raw \\frac / \\lim; never KaTeX an English paragraph.
 */
function TextSpan({ text }) {
  const { html, asBlock } = useMemo(() => {
    const t = text ?? '';
    if (!t || !/\\[a-zA-Z]{2,}/.test(t)) return { html: null, asBlock: false };
    if (/\$(?!\$)/.test(t)) return { html: null, asBlock: false };
    if (!/\\(frac|lim|sqrt|sum|int|iint|oint|prod|cdot|times|div|leq|geq|neq|approx|infty|partial|nabla|begin|left|right|big|overbrace|underbrace)/.test(t)) {
      return { html: null, asBlock: false };
    }
    if (t.length > 160 || isProseHeavyLine(t)) return { html: null, asBlock: false };
    const display =
      /\\frac|\\lim|\\sum|\\int|\\begin\{/.test(t) || t.length > 90;
    const h = katex.renderToString(t.trim(), {
      displayMode: display,
      throwOnError: false,
      strict: false,
    });
    return { html: h, asBlock: display };
  }, [text]);

  if (!html) return <span>{text}</span>;
  const inner = <span dangerouslySetInnerHTML={{ __html: html }} />;
  if (asBlock) {
    return (
      <span className="block max-w-full overflow-x-auto py-0.5 my-0.5">{inner}</span>
    );
  }
  return <span className="inline-block max-w-full align-baseline">{inner}</span>;
}

function MessageBody({ content }) {
  const segments = useMemo(() => segmentMessageContent(content), [content]);

  const blocks = useMemo(() => {
    const out = [];
    let line = [];

    function flushLine(key) {
      if (line.length === 0) return;
      out.push(
        <p key={key} className="whitespace-pre-wrap break-words [word-break:break-word]">
          {line}
        </p>,
      );
      line = [];
    }

    segments.forEach((seg, idx) => {
      if (seg.type === 'block') {
        flushLine(`l-${idx}`);
        out.push(
          <div key={`b-${idx}`} className="my-2 overflow-x-auto py-1">
            <div
              className="katex-display text-center"
              dangerouslySetInnerHTML={{ __html: renderKatexHtml(seg.value, true) }}
            />
          </div>,
        );
        return;
      }
      if (seg.type === 'text') {
        line.push(
          <TextSpan key={`t-${idx}`} text={seg.value} />,
        );
        return;
      }
      if (seg.type === 'inline') {
        line.push(
          <span
            key={`i-${idx}`}
            className="katex-wrap mx-0.5 inline-block align-baseline"
            dangerouslySetInnerHTML={{ __html: renderKatexHtml(seg.value, false) }}
          />,
        );
      }
    });
    flushLine('end');
    return out;
  }, [segments]);

  return (
    <div className="conversation-math space-y-1.5 text-sm leading-relaxed [&_.katex]:text-[0.98em] [&_.katex-display]:my-1">
      {blocks}
    </div>
  );
}

export default function ConversationThread({ conversationId, onClose, variant = 'panel' }) {
  const [messages, setMessages] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const inline = variant === 'inline';

  useEffect(() => {
    if (!conversationId) return;
    setLoading(true);
    getConversationMessages(conversationId)
      .then(data => { setMessages(data.messages || data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, [conversationId]);

  if (loading) {
    return (
      <div className={`p-4 ${inline ? '' : ''}`}>
        <LoadingSpinner message="Loading conversation..." />
      </div>
    );
  }
  if (error) return <p className="text-rose-600 text-sm p-4">{error}</p>;

  const msgs = messages || [];
  const uniqueRoles = [...new Set(msgs.map(m => (m.role || '').toLowerCase()))];
  const allSameRole = uniqueRoles.length <= 1;

  const shellClass = inline
    ? 'border-0 shadow-none rounded-none bg-transparent'
    : '';

  const headerClass = inline
    ? 'flex items-center justify-between px-3 py-2 border-b border-[#2c2418]/15 bg-[#fffef4]/95'
    : 'flex items-center justify-between p-4';
  const headerStyle = inline
    ? {}
    : { borderBottom: '1px solid rgba(148, 163, 184, 0.15)' };

  const bodyClass = inline ? 'p-3 space-y-3 max-h-80 overflow-y-auto' : 'p-4 space-y-3 max-h-96 overflow-y-auto';

  const outerStyle = inline
    ? {}
    : {
        background: 'var(--surface-card)',
        border: '2px solid #2c2418',
        borderRadius: 10,
        boxShadow: '3px 3px 0 #2c2418',
      };

  return (
    <div className={shellClass} style={outerStyle}>
      <div className={headerClass} style={headerStyle}>
        <h3 className={`font-semibold text-slate-700 ${inline ? 'text-xs' : ''}`}>
          {inline ? `Session #${conversationId}` : `Conversation #${conversationId}`}
        </h3>
        {onClose && (
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-700 text-xs sm:text-sm">
            Close
          </button>
        )}
      </div>
      <div className={bodyClass}>
        {msgs.map((msg, i) => {
          const fromTutor = allSameRole ? (i % 2 === 1) : isTutorRole(msg.role);
          const fromStudent = !fromTutor;
          return (
            <div key={i} className={`flex ${fromStudent ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-3 py-2 sm:px-4 sm:py-2.5 text-sm ${
                  fromStudent
                    ? 'bg-amber-300 text-slate-900 rounded-br-md border-2 border-[#2c2418]'
                    : 'bg-[#fffef4] text-slate-700 border-2 border-[#2c2418] rounded-bl-md'
                }`}
              >
                <p className={`text-[10px] font-semibold mb-1 uppercase tracking-wide ${
                  fromStudent ? 'text-amber-900/80' : 'text-slate-400'
                }`}>
                  {fromStudent ? 'You' : 'AI Tutor'}
                </p>
                <MessageBody content={msg.content} />
                {msg.lightbulb_moment && (
                  <span className="inline-block mt-1.5 text-xs bg-amber-50 text-amber-700 border border-amber-200/50 px-2 py-0.5 rounded-full">
                    Lightbulb moment
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
