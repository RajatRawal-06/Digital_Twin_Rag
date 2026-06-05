/**
 * Glass-morphic pill input with auto-growing textarea.
 */

import { useEffect, useRef, useState } from 'react';

const PLACEHOLDERS = [
  'Ask Richard anything...',
  'What is quantum electrodynamics?',
  'Tell me about Los Alamos...',
  'How does the double-slit experiment work?',
  'What was it like working with Einstein?',
];

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18">
      <path
        d="M4 12L20 4L16.6 20L11.3 13.8L4 12Z"
        fill="currentColor"
      />
    </svg>
  );
}

export default function ChatInput({ onSend, isDisabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);
  const [placeholder] = useState(
    () => PLACEHOLDERS[Math.floor(Math.random() * PLACEHOLDERS.length)],
  );

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }, [text]);

  const handleSend = () => {
    if (!text.trim() || isDisabled) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-area">
      <div className="input-pill">
        <textarea
          ref={textareaRef}
          id="chat-input"
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isDisabled ? 'Richard is thinking...' : placeholder}
          disabled={isDisabled}
          rows={1}
          aria-label="Message input"
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={isDisabled || !text.trim()}
          aria-label="Send message"
          id="send-message-btn"
          type="button"
        >
          <SendIcon />
        </button>
      </div>
    </div>
  );
}
