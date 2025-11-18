/**
 * Chat interface with streaming support
 */

import React, { useState, useEffect, useRef } from 'react';
import apiClient, { ChatMessage } from '../api/client';
import './ChatInterface.css';

interface ChatInterfaceProps {
  sessionId?: string;
  userId?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId, userId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);
    setStreamingMessage('');

    try {
      // Use streaming via WebSocket if available
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        wsRef.current = apiClient.connectStreaming(
          (chunk) => {
            setStreamingMessage((prev) => prev + chunk);
          },
          () => {
            setMessages((prev) => [
              ...prev,
              {
                role: 'assistant',
                content: streamingMessage,
              },
            ]);
            setStreamingMessage('');
            setIsStreaming(false);
          },
          (error) => {
            console.error('Streaming error:', error);
            setIsStreaming(false);
            setStreamingMessage('');
          }
        );

        // Wait for connection
        await new Promise((resolve) => {
          if (wsRef.current) {
            wsRef.current.onopen = resolve;
          }
        });
      }

      // Send message via WebSocket
      wsRef.current?.send(
        JSON.stringify({
          type: 'chat',
          message: input,
          session_id: sessionId,
          user_id: userId,
        })
      );
    } catch (error) {
      console.error('Send error:', error);

      // Fallback to HTTP API
      try {
        const response = await apiClient.sendMessage({
          message: input,
          session_id: sessionId,
          user_id: userId,
        });

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.response,
          },
        ]);
      } catch (httpError) {
        console.error('HTTP fallback error:', httpError);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Error: Could not get response from server.',
          },
        ]);
      }

      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Codex Prime Chat</h2>
        {sessionId && <span className="session-id">Session: {sessionId}</span>}
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-role">{msg.role}</div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}

        {isStreaming && streamingMessage && (
          <div className="message message-assistant streaming">
            <div className="message-role">assistant</div>
            <div className="message-content">
              {streamingMessage}
              <span className="cursor">▋</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={isStreaming}
          rows={3}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
        >
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
