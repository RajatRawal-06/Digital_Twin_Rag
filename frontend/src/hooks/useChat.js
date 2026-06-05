/**
 * Chat state hook for message bubbles, socket lifecycle, and REST fallback.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  FeynmanSocket,
  getOrCreateSessionId,
  resolveMediaUrl,
  sendMessage as sendRestMessage,
} from '../api/feynmanApi';

function newMessage(fields) {
  return {
    id: crypto.randomUUID(),
    timestamp: new Date(),
    ...fields,
  };
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const sessionId = useRef(getOrCreateSessionId());
  const socketRef = useRef(null);

  const addFeynmanMessage = useCallback((data) => {
    setMessages((prev) => [
      ...prev,
      newMessage({
        role: 'feynman',
        content: data.reply,
        intent: data.intent,
        audioUrl: resolveMediaUrl(data.audio_url),
        sources: data.sources ?? [],
      }),
    ]);
  }, []);

  useEffect(() => {
    const socket = new FeynmanSocket(sessionId.current, {
      onOpen: () => setIsConnected(true),
      onClose: () => setIsConnected(false),
      onThinking: () => setIsThinking(true),
      onResponse: (data) => {
        setIsThinking(false);
        addFeynmanMessage(data);
      },
      onError: (error) => {
        console.error('[useChat] WebSocket error', error);
        setIsConnected(false);
        setIsThinking(false);
      },
    });

    socket.connect();
    socketRef.current = socket;

    return () => socket.disconnect();
  }, [addFeynmanMessage]);

  const sendMessage = useCallback(
    async (text) => {
      const content = text.trim();
      if (!content || isThinking) return;

      setMessages((prev) => [...prev, newMessage({ role: 'user', content })]);

      if (socketRef.current?.isConnected()) {
        setIsThinking(true);
        socketRef.current.send(content);
        return;
      }

      setIsThinking(true);
      try {
        const data = await sendRestMessage(content, sessionId.current);
        addFeynmanMessage(data);
      } catch (error) {
        console.error('[useChat] REST fallback failed', error);
        addFeynmanMessage({
          reply: "The connection to the lab bench is loose. Start the backend and try me again.",
          intent: 'SYSTEM',
          audio_url: null,
          sources: [],
        });
      } finally {
        setIsThinking(false);
      }
    },
    [addFeynmanMessage, isThinking],
  );

  const clearChat = useCallback(() => setMessages([]), []);

  return {
    messages,
    isThinking,
    isConnected,
    sendMessage,
    clearChat,
    sessionId: sessionId.current,
  };
}
