"""Generate a short ElevenLabs voice demo with the configured voice.

Run from the project root:
    python backend/scripts/demo_voice.py "The first principle is that you must not fool yourself."
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.tts import synthesize_voice  # noqa: E402

DEMO_TEXT = "The first principle is that you must not fool yourself."


async def main() -> int:
    text = " ".join(sys.argv[1:]).strip() or DEMO_TEXT
    audio_url = await synthesize_voice(text=text, session_id="demo-elevenlabs")
    if not audio_url:
        print("No audio generated. Check ENABLE_TTS, TTS_PROVIDER, ELEVENLABS_API_KEY, and ELEVENLABS_VOICE_ID.")
        return 1

    print(f"Generated demo audio: {audio_url}")
    print(f"Serve it with the backend running, then open: http://localhost:8000{audio_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
