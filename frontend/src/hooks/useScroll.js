/**
 * useScroll.js — Auto-scroll management for the chat message list.
 *
 * Automatically scrolls to the bottom when new messages arrive,
 * but only if the user hasn't scrolled up to read history.
 */

import { useRef, useEffect } from 'react';

/**
 * @param {Array} messages - The current message list (triggers the effect)
 * @param {boolean} isThinking - Thinking indicator also should trigger scroll
 * @returns {{ messagesEndRef }} - Attach to the bottom sentinel element
 */
export function useScroll(messages, isThinking) {
  const messagesEndRef = useRef(null);
  const containerRef   = useRef(null);
  const userScrolled   = useRef(false);

  // Detect user manual scrolling
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      // If user is within 80px of bottom, we consider them "at bottom"
      userScrolled.current = scrollHeight - scrollTop - clientHeight > 80;
    };

    container.addEventListener('scroll', onScroll, { passive: true });
    return () => container.removeEventListener('scroll', onScroll);
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    if (!userScrolled.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking]);

  return { messagesEndRef, containerRef };
}
