/**
 * API layer for the Feynman Digital Twin frontend.
 *
 * REST is used as a fallback. WebSocket is preferred for live thinking events
 * and future token/audio streaming.
 */

const BASE_URL = import.meta.env.VITE_API_BASE ?? '';
const WS_BASE = import.meta.env.VITE_WS_BASE ?? `ws://${window.location.host}`;

export function resolveMediaUrl(url) {
  if (!url) return null;
  if (/^(https?:|blob:|data:)/i.test(url)) return url;
  if (!BASE_URL) return url;
  return `${BASE_URL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`;
}

export function getOrCreateSessionId() {
  let id = sessionStorage.getItem('feynman_session_id');
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem('feynman_session_id', id);
  }
  return id;
}

export async function sendMessage(message, sessionId) {
  const response = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export class FeynmanSocket {
  constructor(sessionId, { onThinking, onResponse, onError, onOpen, onClose }) {
    this.sessionId = sessionId;
    this.onThinking = onThinking ?? (() => {});
    this.onResponse = onResponse ?? (() => {});
    this.onError = onError ?? ((error) => console.error('[FeynmanSocket]', error));
    this.onOpen = onOpen ?? (() => {});
    this.onClose = onClose ?? (() => {});
    this._ws = null;
    this._queue = [];
  }

  connect() {
    const url = `${WS_BASE}/api/ws/chat/${this.sessionId}`;
    this._ws = new WebSocket(url);

    this._ws.onopen = () => {
      this.onOpen();
      this._queue.forEach((message) => this._ws.send(JSON.stringify({ message })));
      this._queue = [];
    };

    this._ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'thinking') {
          this.onThinking();
        }
        if (data.type === 'response') {
          this.onResponse(data);
        }
      } catch (error) {
        this.onError(error);
      }
    };

    this._ws.onerror = (event) => this.onError(event);
    this._ws.onclose = () => this.onClose();
  }

  send(message) {
    if (this.isConnected()) {
      this._ws.send(JSON.stringify({ message }));
      return true;
    }
    this._queue.push(message);
    return false;
  }

  disconnect() {
    this._ws?.close();
    this._ws = null;
  }

  isConnected() {
    return this._ws?.readyState === WebSocket.OPEN;
  }
}
