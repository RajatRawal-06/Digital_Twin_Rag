/**
 * Timeline.jsx — Vertical conversation timeline component.
 *
 * Implements the Timeline Component from ui-ux-design-v1.md §3:
 *  - Central visual spine on the left side
 *  - User avatar anchored at top (Friend node)
 *  - Feynman avatar at bottom (Feynman node)
 *  - Conversation turn dots between them (one per exchange)
 *  - Active dot glows amber with each new message
 *
 * Props:
 *   messages  {array}  — the full message list (to count turns)
 *   userAvatar  {string} — optional user avatar URL
 */

export default function Timeline({ messages, userAvatar }) {
  // Count completed exchanges (user + feynman pairs)
  const turnCount = Math.floor(messages.length / 2);
  const activeTurn = Math.max(0, turnCount - 1);

  return (
    <aside className="timeline-rail" aria-label="Conversation timeline">
      {/* The vertical line */}
      <div className="timeline-spine" aria-hidden="true" />

      {/* User node (top) */}
      <div style={{ marginBottom: '12px', position: 'relative', zIndex: 2 }}>
        {userAvatar ? (
          <img
            src={userAvatar}
            alt="You"
            className="timeline-avatar user"
            title="You (Friend)"
          />
        ) : (
          <div className="timeline-avatar-placeholder user" title="You (Friend)">
            YOU
          </div>
        )}
      </div>

      {/* Turn dots — grow as conversation progresses */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '14px',
          padding: '10px 0',
          overflowY: 'auto',
        }}
      >
        {Array.from({ length: Math.max(turnCount, 1) }).map((_, i) => (
          <div
            key={i}
            className={`timeline-event ${i === activeTurn ? 'active' : ''}`}
            title={`Exchange ${i + 1}`}
            aria-label={`Conversation exchange ${i + 1}`}
          />
        ))}
      </div>

      {/* Feynman node (bottom) */}
      <div style={{ marginTop: '12px', position: 'relative', zIndex: 2 }}>
        <img
          src="/feynman-images/image1.jpg"
          alt="Richard Feynman"
          className="timeline-avatar feynman"
          title="Richard Feynman"
          onError={(e) => {
            // Fallback to text placeholder if image missing
            e.target.style.display = 'none';
          }}
        />
      </div>
    </aside>
  );
}
