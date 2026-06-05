/**
 * Integrated TTS audio player for Feynman's voice stream.
 */

import { useEffect, useMemo, useRef, useState } from 'react';

function PlayIcon({ isPlaying }) {
  if (isPlaying) {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" width="14" height="14">
        <path d="M7 5H10V19H7V5ZM14 5H17V19H14V5Z" fill="currentColor" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" width="14" height="14">
      <path d="M8 5V19L18 12L8 5Z" fill="currentColor" />
    </svg>
  );
}

export default function AudioPlayer({ src }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const waveHeights = useMemo(
    () => Array.from({ length: 20 }, (_, index) => Math.round(35 + Math.sin(index * 0.9) * 28)),
    [],
  );

  useEffect(() => {
    if (src && audioRef.current) {
      audioRef.current.play().catch(() => {
        // Browser autoplay may require a user click first.
      });
    }
  }, [src]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
  };

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio || !audio.duration) return;
    setProgress(audio.currentTime / audio.duration);
  };

  return (
    <div className="audio-player">
      <button
        className="audio-play-btn"
        onClick={togglePlay}
        aria-label={isPlaying ? 'Pause Feynman voice' : "Play Feynman's voice"}
        id="feynman-audio-play-btn"
        type="button"
      >
        <PlayIcon isPlaying={isPlaying} />
      </button>

      <div className="audio-waveform-mini" aria-hidden="true">
        {waveHeights.map((height, index) => (
          <span
            key={index}
            style={{
              height: `${height}%`,
              opacity: index / waveHeights.length < progress ? 0.9 : 0.3,
              background:
                index / waveHeights.length < progress ? 'var(--amber-400)' : 'var(--slate-600)',
              transition: 'opacity 0.1s, background 0.1s',
            }}
          />
        ))}
      </div>

      <audio
        ref={audioRef}
        src={src}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => {
          setIsPlaying(false);
          setProgress(0);
        }}
        onTimeUpdate={handleTimeUpdate}
      />
    </div>
  );
}
