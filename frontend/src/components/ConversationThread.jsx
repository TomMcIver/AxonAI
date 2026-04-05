import React, { useState, useEffect } from 'react';
import { getConversationMessages } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';

const TUTOR_ROLES = ['tutor', 'assistant', 'ai', 'system', 'bot', 'ai_tutor', 'axonai'];

function isTutorRole(role) {
  return TUTOR_ROLES.includes((role || '').toLowerCase().replace(/\s+/g, '_'));
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
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
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
