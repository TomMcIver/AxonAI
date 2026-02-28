import React, { useState, useEffect } from 'react';
import { getConversationMessages } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';

// Tutor roles — anything NOT matching these is treated as student
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
  if (error) return <p className="text-[#EF4444] text-sm p-4">{error}</p>;

  // Determine which side each message goes on
  // Strategy: check role field, fallback to alternating if all roles are the same
  const msgs = messages || [];
  const uniqueRoles = [...new Set(msgs.map(m => (m.role || '').toLowerCase()))];
  const allSameRole = uniqueRoles.length <= 1;

  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm">
      <div className="flex items-center justify-between p-4 border-b border-[#E2E8F0]">
        <h3 className="font-semibold text-[#1F2937]">Conversation #{conversationId}</h3>
        {onClose && (
          <button onClick={onClose} className="text-[#6B7280] hover:text-[#1F2937] text-sm">
            Close
          </button>
        )}
      </div>
      <div className="p-4 space-y-3 max-h-96 overflow-y-auto bg-[#F8FAFC]">
        {msgs.map((msg, i) => {
          // If all messages have the same role (or no role), alternate: even=student, odd=tutor
          const fromTutor = allSameRole ? (i % 2 === 1) : isTutorRole(msg.role);
          const fromStudent = !fromTutor;
          return (
            <div key={i} className={`flex ${fromStudent ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                  fromStudent
                    ? 'bg-[#0891B2] text-white rounded-br-md'
                    : 'bg-white text-[#1F2937] border border-[#E2E8F0] rounded-bl-md'
                }`}
              >
                <p className={`text-[10px] font-semibold mb-1 uppercase tracking-wide ${
                  fromStudent ? 'text-white/70' : 'text-[#6B7280]'
                }`}>
                  {fromStudent ? 'Student' : 'AI Tutor'}
                </p>
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                {msg.lightbulb_moment && (
                  <span className="inline-block mt-1.5 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full">
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
