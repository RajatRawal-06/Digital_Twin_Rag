/**
 * ChatBubble.jsx — Message bubble component.
 *
 * Renders both user and Feynman message bubbles. Feynman bubbles include:
 *  - Intent badge (TECHNICAL / PERSONAL / BLENDED)
 *  - Markdown + LaTeX rendering via react-markdown + remark-math + rehype-katex
 *  - Integrated AudioPlayer for TTS playback
 *  - Sender label and timestamp
 *
 * Props:
 *   message {object} — { role, content, intent, audioUrl, timestamp }
 */

import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import AudioPlayer from './AudioPlayer.jsx';

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function ChatBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`bubble-wrapper ${isUser ? 'user' : 'feynman'}`}>
      {/* Sender label */}
      <span className={`bubble-sender ${isUser ? 'user' : 'feynman'}`}>
        {isUser ? 'You' : 'Richard Feynman'}
      </span>

      {/* Message bubble */}
      <div className={`bubble ${isUser ? 'user' : 'feynman'}`}>
        {isUser ? (
          <span>{message.content}</span>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkMath]}
            rehypePlugins={[rehypeKatex]}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>

      {/* Meta row: time + intent badge */}
      <div className="bubble-meta">
        <span>{formatTime(message.timestamp)}</span>
        {!isUser && message.intent && (
          <span className={`intent-badge ${message.intent}`}>
            {message.intent}
          </span>
        )}
      </div>

      {/* Audio player — only for Feynman replies with audio */}
      {!isUser && message.audioUrl && (
        <AudioPlayer src={message.audioUrl} />
      )}
    </div>
  );
}
