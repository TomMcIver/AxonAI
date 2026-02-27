import React, { useState, useEffect } from 'react';
import { getConversationMessages } from '../api/axonai';
import LoadingSpinner from './LoadingSpinner';

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
      <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
        {(messages || []).map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'student' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] rounded-lg px-4 py-2 text-sm ${
              msg.role === 'student'
                ? 'bg-[#0891B2] text-white'
                : 'bg-[#F1F5F9] text-[#1F2937]'
            }`}>
              <p className="text-xs font-medium mb-1 opacity-70 capitalize">{msg.role}</p>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.lightbulb_moment && (
                <span className="inline-block mt-1 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full">
                  Lightbulb moment
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
