import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Send, Sigma } from 'lucide-react';
import DashboardShell from '../../components/DashboardShell';
import { MessageBody, MessageBodyComposerMirror } from '../../components/ConversationThread';
import MathInsertModal from '../../components/MathInsertModal';
import {
  getStudentMastery,
  sendChatMessage,
  getStudentConversations,
  getConversationMessages,
} from '../../api/axonai';

const DEMO_STUDENT_ID = 1;

function SessionBubble({ role, children, extra }) {
  const fromStudent = role === 'user';
  const bubbleClass =
    'max-w-[85%] rounded-2xl px-3 py-2 sm:px-4 sm:py-2.5 text-sm ' +
    (fromStudent
      ? 'rounded-br-md border-2 border-[#2c2418] bg-amber-300 text-slate-900'
      : 'rounded-bl-md border-2 border-[#2c2418] bg-[#fffef4] text-slate-700');
  return (
    <div className={bubbleClass}>
      <p
        className={`mb-1 text-[10px] font-semibold uppercase tracking-wide ${
          fromStudent ? 'text-amber-900/80' : 'text-slate-400'
        }`}
      >
        {fromStudent ? 'You' : 'AI Tutor'}
      </p>
      {children}
      {extra}
    </div>
  );
}

function normMastery(x) {
  const v = typeof x === 'number' && x > 1 ? x / 100 : x;
  return (typeof v === 'number' && !Number.isNaN(v) ? v : 0) || 0;
}

function masteryPct(raw) {
  return Math.round(normMastery(raw) * 1000) / 10;
}

function badgeClassForPct(pct) {
  if (pct > 60) return 'bg-teal-100 text-teal-800 border-teal-200/80';
  if (pct >= 40) return 'bg-amber-100 text-amber-900 border-amber-200/80';
  return 'bg-rose-100 text-rose-800 border-rose-200/80';
}

const QUICK_PROMPTS = [
  'Can you explain this to me?',
  "I'm stuck — can we go through it step by step?",
  'Give me a hint without telling me the answer',
];

function mapApiMessagesToUi(msgs) {
  if (!Array.isArray(msgs)) return [];
  return msgs.map((m) => {
    const rawRole = (m.role || m.sender || '').toLowerCase();
    const role = rawRole === 'user' || rawRole === 'student' ? 'user' : 'ai';
    return {
      role,
      content: m.content ?? '',
      lightbulb: Boolean(m.lightbulb_moment ?? m.is_lightbulb_moment),
    };
  });
}

function formatChatOptionLabel(c) {
  const d = c.started_at ? new Date(c.started_at) : null;
  const when =
    d && !Number.isNaN(d.getTime())
      ? d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
      : '';
  const topic = c.concept_name || 'General';
  return when ? `#${c.id} · ${topic} · ${when}` : `#${c.id} · ${topic}`;
}

export default function AITutorPage() {
  const [concepts, setConcepts] = useState([]);
  const [conceptFilter, setConceptFilter] = useState('');
  const [activeConcept, setActiveConcept] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');
  const [mathModalOpen, setMathModalOpen] = useState(false);
  const [composerLayerH, setComposerLayerH] = useState(48);
  const [caretIdx, setCaretIdx] = useState(0);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [priorChats, setPriorChats] = useState([]);
  const [priorChatsLoading, setPriorChatsLoading] = useState(false);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const mirrorRef = useRef(null);

  const syncCaretFromTextarea = useCallback(() => {
    const t = textareaRef.current;
    if (t) setCaretIdx(t.selectionStart);
  }, []);

  useEffect(() => {
    getStudentMastery(DEMO_STUDENT_ID)
      .then((data) => setConcepts(data?.concepts || []))
      .catch(() => setConcepts([]));
  }, []);

  const refreshPriorChats = useCallback(() => {
    setPriorChatsLoading(true);
    getStudentConversations(DEMO_STUDENT_ID, 40, 0)
      .then((data) => {
        setPriorChats(data?.conversations || []);
      })
      .catch(() => setPriorChats([]))
      .finally(() => setPriorChatsLoading(false));
  }, []);

  useEffect(() => {
    refreshPriorChats();
  }, [refreshPriorChats]);

  const startNewChat = useCallback(() => {
    setMessages([]);
    setInput('');
    setCaretIdx(0);
    setActiveConversationId(null);
  }, []);

  const loadPriorChat = useCallback(async (conversationId) => {
    if (conversationId == null || Number.isNaN(Number(conversationId))) return;
    setLoadingConversation(true);
    try {
      const data = await getConversationMessages(Number(conversationId), DEMO_STUDENT_ID);
      const raw = data.messages ?? data;
      setMessages(mapApiMessagesToUi(raw));
      setActiveConversationId(Number(conversationId));
      setInput('');
      setCaretIdx(0);
    } catch (e) {
      console.error(e);
      setMessages([]);
    } finally {
      setLoadingConversation(false);
    }
  }, []);

  const filteredConcepts = useMemo(() => {
    const q = conceptFilter.trim().toLowerCase();
    if (!q) return concepts;
    return concepts.filter((c) => (c.concept_name || '').toLowerCase().includes(q));
  }, [concepts, conceptFilter]);

  const chatSelectOptions = useMemo(() => {
    const ids = new Set(priorChats.map((c) => c.id));
    if (activeConversationId != null && !ids.has(activeConversationId)) {
      return [
        ...priorChats,
        {
          id: activeConversationId,
          concept_name: 'This chat',
          started_at: null,
        },
      ];
    }
    return priorChats;
  }, [priorChats, activeConversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const COMPOSER_MIN = 48;
  const COMPOSER_MAX = 200;

  useLayoutEffect(() => {
    const m = mirrorRef.current;
    if (!m) return;
    const h = Math.min(Math.max(m.scrollHeight, COMPOSER_MIN), COMPOSER_MAX);
    setComposerLayerH(h);
  }, [input, caretIdx]);

  const insertAtCursor = useCallback((snippet) => {
    const el = textareaRef.current;
    let s = 0;
    let e = 0;
    if (el) {
      s = el.selectionStart;
      e = el.selectionEnd;
    }
    setInput((prev) => {
      if (!el) return `${prev}${snippet}`;
      return `${prev.slice(0, s)}${snippet}${prev.slice(e)}`;
    });
    const pos = s + snippet.length;
    requestAnimationFrame(() => {
      const ta = textareaRef.current;
      if (!ta) return;
      ta.focus();
      ta.setSelectionRange(pos, pos);
      setCaretIdx(pos);
    });
  }, []);

  const send = useCallback(
    async (rawText) => {
      const text = (rawText ?? '').trim();
      if (!text || loading) return;

      setMessages((m) => [...m, { role: 'user', content: text, lightbulb: false }]);
      setInput('');
      setCaretIdx(0);
      setLoading(true);

      try {
        const data = await sendChatMessage(
          DEMO_STUDENT_ID,
          text,
          activeConcept?.concept_id ?? null,
          activeConversationId,
        );
        if (data?.conversation_id != null) {
          setActiveConversationId(data.conversation_id);
        }
        setMessages((m) => [
          ...m,
          {
            role: 'ai',
            content: data?.response ?? '',
            lightbulb: Boolean(data?.lightbulb_detected),
          },
        ]);
        refreshPriorChats();
      } catch (e) {
        console.error(e);
        setMessages((m) => [
          ...m,
          {
            role: 'ai',
            content: "Sorry, I couldn't reach the tutor just now. Please try again.",
            lightbulb: false,
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loading, activeConcept, activeConversationId, refreshPriorChats],
  );

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <DashboardShell subtitle="AI Tutor">
      <MathInsertModal open={mathModalOpen} onClose={() => setMathModalOpen(false)} onInsert={insertAtCursor} />

      <div className="flex min-h-[560px] flex-col gap-4 lg:h-[min(85vh,900px)] lg:min-h-0 lg:flex-row lg:gap-6">
        <aside className="axon-card-subtle hidden min-h-0 w-64 shrink-0 flex-col overflow-hidden p-4 sm:p-5 lg:flex">
          <p className="axon-label mb-1">Concepts</p>
          <h2 className="axon-h2 text-base text-slate-800">Your topics</h2>
          <p className="mb-3 text-xs leading-relaxed text-slate-500">
            Weakest first — tap one to focus the tutor (optional).
          </p>
          <input
            type="search"
            placeholder="Search concepts…"
            value={conceptFilter}
            onChange={(e) => setConceptFilter(e.target.value)}
            className="mb-3 w-full rounded-lg border border-slate-200 bg-white/90 px-2 py-1.5 text-sm text-slate-800 placeholder:text-slate-400"
            aria-label="Filter concepts"
          />
          <div className="min-h-0 flex-1 rounded-xl border border-[#2c2418]/15 bg-white/65 p-2">
            <div className="h-full space-y-2 overflow-y-auto pr-1 [scrollbar-gutter:stable]">
              {filteredConcepts.map((c) => {
                const pct = masteryPct(c.mastery_score);
                const active = activeConcept?.concept_id === c.concept_id;
                return (
                  <button
                    key={c.concept_id}
                    type="button"
                    onClick={() => setActiveConcept(c)}
                    className={`flex w-full flex-col items-start gap-1 rounded-lg border px-3 py-2.5 text-left text-sm transition-colors ${
                      active
                        ? 'border-teal-400/80 bg-teal-50/70 ring-1 ring-teal-200/60'
                        : 'border-slate-200 bg-white/70 hover:bg-white'
                    }`}
                  >
                    <span className="font-medium text-slate-800 line-clamp-2">{c.concept_name}</span>
                    <span
                      className={`inline-flex rounded-full border px-2 py-0.5 text-[0.65rem] font-semibold tabular-nums ${badgeClassForPct(pct)}`}
                    >
                      {pct.toFixed(0)}%
                    </span>
                  </button>
                );
              })}
              {filteredConcepts.length === 0 && (
                <p className="text-xs text-slate-500">No concepts match your search.</p>
              )}
            </div>
          </div>
        </aside>

        <section className="axon-card-subtle flex min-h-[480px] min-w-0 flex-1 flex-col overflow-hidden p-0 sm:min-h-[520px] lg:min-h-0">
          <div className="shrink-0 space-y-1 border-b border-slate-200/80 px-4 pb-3 pt-4 sm:px-5 sm:pt-5">
            <p className="axon-label mb-0">Tutor</p>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <h1 className="axon-h2 text-base text-slate-800 sm:text-lg">AxonAI Tutor</h1>
                <p className="mt-1 text-xs leading-relaxed text-slate-500">
                  Same bubbles as AI learning sessions. Use Insert math for fractions and symbols — sent as LaTeX.
                </p>
              </div>
              {activeConcept && (
                <div className="flex max-w-[min(100%,18rem)] items-center gap-1 rounded-full border border-teal-200 bg-teal-50/80 px-2.5 py-1 text-xs text-teal-900">
                  <span className="truncate">
                    Focus: <span className="font-medium">{activeConcept.concept_name}</span>
                  </span>
                  <button
                    type="button"
                    className="shrink-0 rounded-full px-1.5 text-teal-700 hover:bg-teal-100"
                    onClick={() => setActiveConcept(null)}
                    aria-label="Clear focused concept"
                  >
                    ×
                  </button>
                </div>
              )}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-200/80 pt-3">
              <label htmlFor="tutor-prior-chat" className="text-xs font-medium text-slate-600">
                Session
              </label>
              <select
                id="tutor-prior-chat"
                disabled={priorChatsLoading || loadingConversation}
                value={activeConversationId ?? ''}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v === '') startNewChat();
                  else loadPriorChat(v);
                }}
                className="min-w-0 max-w-full flex-1 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-800 sm:max-w-md"
              >
                <option value="">New conversation</option>
                {chatSelectOptions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {formatChatOptionLabel(c)}
                  </option>
                ))}
              </select>
              {priorChatsLoading && <span className="text-xs text-slate-400">Loading sessions…</span>}
              {loadingConversation && <span className="text-xs text-slate-400">Opening…</span>}
            </div>
          </div>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-4 sm:px-5">
            {messages.length === 0 && !loading && (
              <div className="flex flex-wrap gap-2">
                {QUICK_PROMPTS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => send(q)}
                    className="rounded-lg border border-slate-200 bg-white/50 px-3 py-2 text-left text-xs text-slate-700 transition-colors hover:bg-white/80"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}

            {messages.map((msg, idx) => (
              <div
                key={`${msg.role}-${idx}-${msg.content.slice(0, 12)}`}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <SessionBubble
                  role={msg.role}
                  extra={
                    msg.role === 'ai' && msg.lightbulb ? (
                      <span className="mt-1.5 inline-block rounded-full border border-amber-200/50 bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                        Lightbulb moment
                      </span>
                    ) : null
                  }
                >
                  <MessageBody content={msg.content} />
                </SessionBubble>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <SessionBubble role="ai">
                  <span className="inline-flex gap-1 text-slate-400">
                    <span className="animate-pulse">●</span>
                    <span className="animate-pulse [animation-delay:150ms]">●</span>
                    <span className="animate-pulse [animation-delay:300ms]">●</span>
                  </span>
                </SessionBubble>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="sticky bottom-0 z-10 border-t border-[#2c2418]/20 bg-[#fffef4]/85 px-3 py-3 backdrop-blur-[12px] sm:px-5">
            <div className="mx-auto flex max-w-4xl flex-col gap-2">
              <div className="flex flex-wrap items-center gap-2 text-[0.7rem] text-slate-500">
                <button
                  type="button"
                  onClick={() => setMathModalOpen(true)}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 rounded-lg border-2 border-[#2c2418] bg-amber-200/90 px-3 py-1.5 text-xs font-medium text-slate-900 shadow-[2px_2px_0_#2c2418] hover:bg-amber-200 disabled:opacity-50"
                >
                  <Sigma className="h-3.5 w-3.5" aria-hidden />
                  Insert math
                </button>
                <span className="text-slate-400">Fractions, roots, powers — inserts LaTeX into your message.</span>
              </div>
              <div className="flex items-end gap-2">
                <div
                  className="relative min-w-0 flex-1 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-inner transition-shadow focus-within:border-teal-400/80 focus-within:ring-2 focus-within:ring-teal-400/25"
                  style={{ height: composerLayerH, minHeight: COMPOSER_MIN, maxHeight: COMPOSER_MAX }}
                >
                  <div
                    ref={mirrorRef}
                    className="pointer-events-none absolute inset-0 z-20 overflow-y-auto overflow-x-hidden px-3 py-2.5 [scrollbar-width:none] [&::-webkit-scrollbar]:w-0"
                    aria-hidden
                  >
                    <MessageBodyComposerMirror content={input} caretOffset={caretIdx} />
                  </div>
                  <textarea
                    id="axon-math-composer-input"
                    ref={textareaRef}
                    value={input}
                    disabled={loading}
                    onChange={(e) => {
                      setInput(e.target.value);
                      setCaretIdx(e.target.selectionStart);
                    }}
                    onSelect={syncCaretFromTextarea}
                    onKeyUp={syncCaretFromTextarea}
                    onClick={syncCaretFromTextarea}
                    onKeyDown={(e) => {
                      onKeyDown(e);
                      requestAnimationFrame(syncCaretFromTextarea);
                    }}
                    onScroll={(e) => {
                      const mir = mirrorRef.current;
                      if (mir) mir.scrollTop = e.currentTarget.scrollTop;
                    }}
                    placeholder="Type here — math shows as you type (use $…$ for LaTeX). Enter sends, Shift+Enter new line."
                    className="math-composer-overlay absolute inset-0 z-10 box-border resize-none overflow-y-auto border-0 bg-transparent px-3 py-2.5 font-sans text-sm leading-relaxed text-transparent outline-none shadow-none placeholder:text-slate-400 placeholder:opacity-100 selection:bg-teal-200/35 disabled:opacity-60"
                    spellCheck={false}
                    aria-label="Message — equations render in place as you type"
                  />
                </div>
                <button
                  type="button"
                  disabled={loading || !input.trim()}
                  onClick={() => send(input)}
                  className="axon-btn inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border-2 border-[#2c2418] bg-teal-600 px-0 text-white shadow-[2px_2px_0_#2c2418] hover:bg-teal-500 disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="Send message"
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
