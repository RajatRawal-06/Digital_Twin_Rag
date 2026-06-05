/**
 * AvatarPresence.jsx — Feynman "thinking" live presence indicator.
 *
 * Implements the Character Animation from ui-ux-design-v1.md §5:
 *  - Shows when the Gemini API is generating a response
 *  - Displays a waveform animation (like audio being synthesized)
 *  - Feynman's avatar glows amber during generation
 *  - Thinking dots bubble shows below the avatar
 *
 * Props:
 *   isThinking  {boolean} — true while generation is in progress
 */

export default function AvatarPresence({ isThinking }) {
  if (!isThinking) return null;

  return (
    <div className="bubble-wrapper feynman" style={{ alignSelf: 'flex-start' }}>
      <span className="bubble-sender feynman">Richard Feynman</span>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Avatar with glow */}
        <div
          style={{
            position: 'relative',
            width: '36px',
            height: '36px',
            flexShrink: 0,
          }}
        >
          <img
            src="/feynman-images/image1.jpg"
            alt="Richard Feynman thinking"
            className="avatar-presence-img"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          {/* Amber glow ring */}
          <div
            aria-hidden="true"
            style={{
              position: 'absolute',
              inset: '-3px',
              borderRadius: '50%',
              border: '2px solid var(--amber-500)',
              animation: 'statusPulse 1.5s infinite',
            }}
          />
        </div>

        {/* Waveform — simulates voice synthesis in progress */}
        <div className="waveform" aria-label="Feynman is thinking">
          {[14, 20, 12, 18, 10, 16, 8].map((h, i) => (
            <div
              key={i}
              className="waveform-bar"
              style={{ height: `${h}px`, animationDelay: `${i * 0.07}s` }}
            />
          ))}
        </div>
      </div>

      {/* Thinking dots bubble */}
      <div className="thinking-indicator" style={{ marginTop: '6px' }}>
        <div className="thinking-dot" />
        <div className="thinking-dot" />
        <div className="thinking-dot" />
      </div>
    </div>
  );
}
