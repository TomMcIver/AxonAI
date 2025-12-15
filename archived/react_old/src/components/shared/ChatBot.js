import React, { useState, useEffect, useRef } from 'react';
import { Card, Form, Button, Alert, Badge, Spinner } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPaperPlane, faRobot, faUser, faClock } from '@fortawesome/free-solid-svg-icons';
import ApiService from '../../services/ApiService';

function ChatBot({ classId, className, user }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (classId) {
      loadChatHistory();
    }
  }, [classId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const response = await ApiService.getChatHistory(classId);
      setChatHistory(response.messages || []);
      setMessages(response.messages || []);
    } catch (err) {
      setError('Failed to load chat history');
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      message: newMessage.trim(),
      response: '',
      message_type: 'user',
      created_at: new Date().toISOString(),
      isTemporary: true
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);
    setError('');

    try {
      const response = await ApiService.sendChatMessage(classId, newMessage.trim());
      
      const aiMessage = {
        id: Date.now() + 1,
        message: response.message,
        response: response.response,
        message_type: 'ai',
        created_at: response.timestamp,
        isTemporary: false
      };

      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== userMessage.id);
        return [...filtered, 
          { ...userMessage, isTemporary: false },
          aiMessage
        ];
      });

    } catch (err) {
      setError('Failed to send message. Please try again.');
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <Card className="h-100 d-flex flex-column">
      <Card.Header className="bg-primary text-white">
        <div className="d-flex align-items-center">
          <FontAwesomeIcon icon={faRobot} className="me-2" />
          <div>
            <h6 className="mb-0">AI Learning Assistant</h6>
            <small className="opacity-75">{className}</small>
          </div>
        </div>
      </Card.Header>

      <Card.Body className="flex-grow-1 p-0 d-flex flex-column">
        {/* Chat Messages */}
        <div className="flex-grow-1 overflow-auto p-3" style={{ maxHeight: '400px' }}>
          {messages.length === 0 ? (
            <div className="text-center text-muted py-5">
              <FontAwesomeIcon icon={faRobot} size="3x" className="mb-3 opacity-50" />
              <p>Start a conversation with your AI learning assistant!</p>
              <p className="small">Ask questions about class content, assignments, or concepts.</p>
            </div>
          ) : (
            <>
              {messages.map((msg, index) => (
                <div key={msg.id || index} className={`mb-3 ${msg.message_type === 'user' ? 'text-end' : 'text-start'}`}>
                  <div className={`d-inline-block p-3 rounded-3 ${
                    msg.message_type === 'user' 
                      ? 'bg-primary text-white' 
                      : 'bg-light border'
                  }`} style={{ maxWidth: '80%' }}>
                    <div className="d-flex align-items-center mb-1">
                      <FontAwesomeIcon 
                        icon={msg.message_type === 'user' ? faUser : faRobot} 
                        className="me-2"
                      />
                      <small className="opacity-75">
                        {msg.message_type === 'user' ? user.first_name : 'AI Assistant'}
                      </small>
                      {msg.isTemporary && (
                        <Spinner size="sm" className="ms-2" />
                      )}
                    </div>
                    <div className="mb-1">
                      {msg.message_type === 'user' ? msg.message : msg.response}
                    </div>
                    <div className="text-end">
                      <small className="opacity-50">
                        <FontAwesomeIcon icon={faClock} className="me-1" />
                        {formatTimestamp(msg.created_at)}
                      </small>
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="danger" className="m-3 mb-0">
            {error}
          </Alert>
        )}

        {/* Message Input */}
        <div className="p-3 border-top">
          <div className="d-flex">
            <Form.Control
              as="textarea"
              rows={1}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about this class..."
              disabled={isLoading}
              className="me-2"
              style={{ resize: 'none' }}
            />
            <Button
              variant="primary"
              onClick={sendMessage}
              disabled={!newMessage.trim() || isLoading}
              className="px-3"
            >
              {isLoading ? (
                <Spinner size="sm" />
              ) : (
                <FontAwesomeIcon icon={faPaperPlane} />
              )}
            </Button>
          </div>
          <small className="text-muted mt-2 d-block">
            Press Enter to send, Shift+Enter for new line
          </small>
        </div>
      </Card.Body>
    </Card>
  );
}

export default ChatBot;