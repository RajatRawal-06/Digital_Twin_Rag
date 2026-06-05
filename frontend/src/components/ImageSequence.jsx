/**
 * ImageSequence.jsx — Dynamic parallax background component.
 *
 * Implements the ImageSequence architecture from ui-ux-design-v1.md §2:
 *  - Displays 4 existing Feynman photos (+ more when added to public/feynman-images/)
 *  - Cross-fades between images on a timer
 *  - Applies subtle parallax on mouse move
 *  - Images are desaturated, blurred, and darkened to remain aesthetic
 *    but never overwhelming for the text layer
 *
 * Props:
 *   images    {string[]} — array of image URLs
 *   interval  {number}  — ms between cross-fades (default 6000)
 */

import { useState, useEffect, useRef } from 'react';

const FEYNMAN_IMAGES = [
  '/feynman-images/image1.jpg',
  '/feynman-images/image2.jpg',
  '/feynman-images/image3.jpg',
  '/feynman-images/image4.jpg',
];

export default function ImageSequence({ images = FEYNMAN_IMAGES, interval = 6000 }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [parallax, setParallax] = useState({ x: 0, y: 0 });
  const timerRef = useRef(null);

  // ── Auto-advance ──────────────────────────────────────────────────────────
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % images.length);
    }, interval);
    return () => clearInterval(timerRef.current);
  }, [images.length, interval]);

  // ── Parallax on mouse move ────────────────────────────────────────────────
  useEffect(() => {
    const handleMouseMove = (e) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 12;  // ±6px
      const y = (e.clientY / window.innerHeight - 0.5) * 8;  // ±4px
      setParallax({ x, y });
    };
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="image-sequence-bg" aria-hidden="true">
      {images.map((src, i) => (
        <img
          key={src}
          src={src}
          alt=""
          className={i === activeIndex ? 'active' : ''}
          style={{
            transform: `scale(${i === activeIndex ? 1.0 : 1.05}) translate(${parallax.x}px, ${parallax.y}px)`,
          }}
          loading={i === 0 ? 'eager' : 'lazy'}
        />
      ))}
    </div>
  );
}
