import React, { useState, useEffect } from 'react';
import { InlineMath, BlockMath } from 'react-katex';
import { getConversationMessages } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';
import 'katex/dist/katex.min.css';

const TUTOR_ROLES = ['tutor', 'assistant', 'ai', 'system', 'bot', 'ai_tutor', 'axonai'];

function isTutorRole(role) {
  return TUTOR_ROLES.includes((role || '').toLowerCase().replace(/\s+/g, '_'));
}

// Parse content for LaTeX patterns and render with KaTeX
function renderMessageContent(content) {
  // Patterns for LaTeX: $$...$$ (block), $...$ (inline), \[...\] (block), \(...\) (inline)
  const blockPattern = /\$\$(.+?)\$\$|\\\[(.+?)\\\]/gs;
  const inlinePattern = /\$(.+?)\$|\\\((.+?)\\\)/g;

  const parts = [];
  let lastIndex = 0;

  // First handle block equations
  let blockMatches = Array.from(content.matchAll(blockPattern));

  if (blockMatches.length === 0) {
    // No block equations, handle inline only
    let inlineMatches = Array.from(content.matchAll(inlinePattern));

    if (inlineMatches.length === 0) {
      // No LaTeX at all
      return <p className="whitespace-pre-wrap leading-relaxed">{content}</p>;
    }

    inlineMatches.forEach((match, idx) => {
      const matchIndex = match.index;
      const latex = match[1] || match[2];

      // Add text before match
      if (matchIndex > lastIndex) {
        parts.push(
          <span key={`text-${idx}`}>{content.substring(lastIndex, matchIndex)}</span>
        );
      }

      // Add LaTeX
      parts.push(
        <InlineMath key={`inline-${idx}`} math={latex} />
      );

      lastIndex = match.index + match[0].length;
    });

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(<span key="text-end">{content.substring(lastIndex)}</span>);
    }

    return <p className="whitespace-pre-wrap leading-relaxed">{parts}</p>;
  }

  // Handle block equations with potential inline equations
  blockMatches.forEach((match, idx) => {
    const matchIndex = match.index;
    const latex = match[1] || match[2];

    // Add text and inline equations before this block
    if (matchIndex > lastIndex) {
      const textBefore = content.substring(lastIndex, matchIndex);
      const inlineParts = [];
      let textLastIndex = 0;

      Array.from(textBefore.matchAll(inlinePattern)).forEach((inlineMatch, iIdx) => {
        if (inlineMatch.index > textLastIndex) {
          inlineParts.push(
            <span key={`text-${idx}-${iIdx}`}>
              {textBefore.substring(textLastIndex, inlineMatch.index)}
            </span>
          );
        }
        inlineParts.push(
          <InlineMath key={`inline-${idx}-${iIdx}`} math={inlineMatch[1] || inlineMatch[2]} />
        );
        textLastIndex = inlineMatch.index + inlineMatch[0].length;
      });

      if (textLastIndex < textBefore.length) {
        inlineParts.push(
          <span key={`text-${idx}-end`}>{textBefore.substring(textLastIndex)}</span>
        );
      }

      if (inlineParts.length > 0) {
        parts.push(<p key={`before-block-${idx}`} className="whitespace-pre-wrap leading-relaxed">{inlineParts}</p>);
      }
    }

    // Add block equation
    parts.push(
      <div key={`block-${idx}`} className="my-2 overflow-x-auto">
        <BlockMath math={latex} />
      </div>
    );

    lastIndex = match.index + match[0].length;
  });

  // Add remaining text after last block
  if (lastIndex < content.length) {
    const textAfter = content.substring(lastIndex);
    const inlineParts = [];
    let textLastIndex = 0;

    Array.from(textAfter.matchAll(inlinePattern)).forEach((inlineMatch, iIdx) => {
      if (inlineMatch.index > textLastIndex) {
        inlineParts.push(
          <span key={`text-after-${iIdx}`}>
            {textAfter.substring(textLastIndex, inlineMatch.index)}
          </span>
        );
      }
      inlineParts.push(
        <InlineMath key={`inline-after-${iIdx}`} math={inlineMatch[1] || inlineMatch[2]} />
      );
      textLastIndex = inlineMatch.index + inlineMatch[0].length;
    });

    if (textLastIndex < textAfter.length) {
      inlineParts.push(
        <span key="text-after-end">{textAfter.substring(textLastIndex)}</span>
      );
    }

    if (inlineParts.length > 0) {
      parts.push(<p key="after-block" className="whitespace-pre-wrap leading-relaxed">{inlineParts}</p>);
    } else if (textAfter.trim()) {
      parts.push(<p key="after-block-text" className="whitespace-pre-wrap leading-relaxed">{textAfter}</p>);
    }
  }

  return <div className="space-y-1">{parts}</div>;
}

export default function ConversationThread({ conversationId, onClose }) {
  const [messages, setMessages] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!conversationId) return;
    setLoading(true);
    getConversationMessages(conversationId)
      .then(data => { setMessages(data.messages || data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, [conversationId]);

  if (loading) return <LoadingSpinner message="Loading conversation..." />;
  if (error) return <p className="text-rose-600 text-sm p-4">{error}</p>;

  const msgs = messages || [];
  const uniqueRoles = [...new Set(msgs.map(m => (m.role || '').toLowerCase()))];
  const allSameRole = uniqueRoles.length <= 1;

  return (
    <div
      style={{
        background: 'rgba(255, 255, 255, 0.6)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.7)',
        borderRadius: 16,
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
      }}
    >
      <div className="flex items-center justify-between p-4" style={{ borderBottom: '1px solid rgba(148, 163, 184, 0.15)' }}>
        <h3 className="font-semibold text-slate-700">Conversation #{conversationId}</h3>
        {onClose && (
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-sm">
            Close
          </button>
        )}
      </div>
      <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
        {msgs.map((msg, i) => {
          const fromTutor = allSameRole ? (i % 2 === 1) : isTutorRole(msg.role);
          const fromStudent = !fromTutor;
          return (
            <div key={i} className={`flex ${fromStudent ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                  fromStudent
                    ? 'bg-teal-500 text-white rounded-br-md'
                    : 'bg-white/70 text-slate-700 border border-slate-200/60 rounded-bl-md'
                }`}
              >
                <p className={`text-[10px] font-semibold mb-1 uppercase tracking-wide ${
                  fromStudent ? 'text-white/70' : 'text-slate-400'
                }`}>
                  {fromStudent ? 'Student' : 'AI Tutor'}
                </p>
                {renderMessageContent(msg.content)}
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
