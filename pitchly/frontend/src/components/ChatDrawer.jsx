import React, { useState, useRef, useEffect } from 'react';
import styles from './ChatDrawer.module.css';

const QUICK_PROMPTS = [
  { text: 'Explain the tradeoff between in-memory vs Redis channels.', reasoning: true },
  { text: 'What are the biggest architectural risks in this plan?', reasoning: true },
  { text: 'Why did you estimate 2 days for the backend models?', reasoning: true },
  { text: 'Break down the frontend testing tasks further.', reasoning: false },
];

export default function ChatDrawer({
  isOpen,
  onClose,
  messages = [],
  onSendMessage,
  isSending = false,
}) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSend = (textToSend) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isSending) return;
    onSendMessage(text);
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isReasoningText = (t) => {
    const lower = t.toLowerCase();
    return ['why', 'risk', 'compare', 'tradeoff', 'explain'].some((kw) =>
      lower.includes(kw)
    );
  };

  return (
    <div className={styles.drawerOverlay}>
      <div className={styles.drawerHeader}>
        <div className={styles.titleArea}>
          <span className={styles.title}>Pitchly Copilot</span>
          <span className={styles.aiBadge}>NVIDIA / Nebius</span>
        </div>
        <button className={styles.closeButton} onClick={onClose} title="Close chat">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div className={styles.messageList}>
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          const isSystem = msg.role === 'system';

          return (
            <div
              key={idx}
              className={`${styles.messageRow} ${
                isUser ? styles.userRow : styles.assistantRow
              }`}
            >
              <div
                className={`${styles.bubble} ${
                  isSystem
                    ? styles.systemBubble
                    : isUser
                    ? styles.userBubble
                    : styles.assistantBubble
                }`}
              >
                {msg.content}
              </div>

              {!isUser && !isSystem && (
                <div className={styles.modelBadge}>
                  {msg.reasoning_mode ? (
                    <span className={styles.reasoningIndicator}>
                      ✦ Reasoning Model Activated
                    </span>
                  ) : (
                    <span>⚡ Fast Model</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {isSending && (
          <div className={`${styles.messageRow} ${styles.assistantRow}`}>
            <div className={`${styles.bubble} ${styles.assistantBubble}`}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.quickPromptsRow}>
        {QUICK_PROMPTS.map((p, i) => (
          <button
            key={i}
            className={`${styles.quickChip} ${p.reasoning ? styles.reasoningChip : ''}`}
            onClick={() => handleSend(p.text)}
            disabled={isSending}
            title={p.reasoning ? 'Triggers REASONING_MODEL' : 'Triggers FAST_MODEL'}
          >
            {p.reasoning ? '✦ ' : ''}{p.text}
          </button>
        ))}
      </div>

      <div className={styles.inputArea}>
        <input
          type="text"
          className={styles.inputField}
          placeholder={
            isReasoningText(inputValue)
              ? "Detected reasoning keyword! (REASONING_MODEL)"
              : "Ask follow-up questions ('why', 'risk', 'compare')..."
          }
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending}
        />
        <button
          className={styles.sendButton}
          onClick={() => handleSend()}
          disabled={!inputValue.trim() || isSending}
        >
          Send
        </button>
      </div>
    </div>
  );
}
