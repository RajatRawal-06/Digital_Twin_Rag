import ImageSequence from './components/ImageSequence.jsx';
import Timeline from './components/Timeline.jsx';
import ChatBubble from './components/ChatBubble.jsx';
import ChatInput from './components/ChatInput.jsx';
import AvatarPresence from './components/AvatarPresence.jsx';
import { useChat } from './hooks/useChat.js';
import { useScroll } from './hooks/useScroll.js';

const WELCOME_PROMPTS = [
  '"Explain quantum electrodynamics like I am in first year."',
  '"What was your time at Los Alamos really like?"',
  '"How did you figure out the path integral formulation?"',
  '"Why do you love physics so much?"',
];

export default function App() {
  const { messages, isThinking, isConnected, sendMessage } = useChat();
  const { messagesEndRef, containerRef } = useScroll(messages, isThinking);
  const showWelcome = messages.length === 0 && !isThinking;

  return (
    <>
      <ImageSequence />
      <div className="scanline-overlay" aria-hidden="true" />

      <div className="app-layout">
        <Timeline messages={messages} />

        <main className="chat-container" role="main">
          <header className="header-bar">
            <div className="header-copy">
              <span className="header-title">Richard P. Feynman</span>
              <span className="header-subtitle">Caltech | 1939-1988 | Physics, Theory</span>
            </div>

            <div className="header-status">
              <div
                className="status-dot"
                style={{ background: isConnected ? '#22c55e' : '#f59e0b' }}
                aria-label={isConnected ? 'Connected' : 'Connecting'}
              />
              <span>{isConnected ? 'Online' : 'Connecting'}</span>
            </div>
          </header>

          <div
            className="chat-messages"
            ref={containerRef}
            role="log"
            aria-live="polite"
            aria-label="Conversation with Richard Feynman"
          >
            {showWelcome && (
              <div className="welcome-screen">
                <h1 className="welcome-title">
                  Talk to
                  <br />
                  Richard Feynman
                </h1>
                <p className="welcome-quote">
                  "I would rather have questions that cannot be answered than answers
                  that cannot be questioned."
                </p>

                <div className="welcome-prompt-grid">
                  {WELCOME_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      className="welcome-prompt-btn"
                      onClick={() => sendMessage(prompt.replace(/^"|"$/g, ''))}
                      aria-label={`Start conversation with: ${prompt}`}
                      type="button"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}

            {isThinking && <AvatarPresence isThinking={isThinking} />}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>

          <ChatInput onSend={sendMessage} isDisabled={isThinking} />
        </main>

        <div className="right-utility-rail" aria-hidden="true" />
      </div>
    </>
  );
}
