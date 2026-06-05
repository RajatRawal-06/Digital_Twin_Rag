from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core import tts


class FakeResponse:
    content = b"fake-mp3"

    def raise_for_status(self) -> None:
        return None


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.posts = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, headers=None, json=None):
        self.posts.append((url, headers, json))
        return FakeResponse()


class ElevenLabsTtsTest(unittest.IsolatedAsyncioTestCase):
    async def test_synthesize_voice_saves_mp3_and_returns_audio_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_dir = Path(tmpdir)

            with (
                patch.object(tts, "ENABLE_TTS", True),
                patch.object(tts, "TTS_PROVIDER", "elevenlabs"),
                patch.object(tts, "ELEVENLABS_API_KEY", "test-key"),
                patch.object(tts, "ELEVENLABS_VOICE_ID", "test-voice"),
                patch.object(tts, "ELEVENLABS_MODEL_ID", "eleven_flash_v2_5"),
                patch.object(tts, "ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"),
                patch.object(tts, "_AUDIO_DIR", audio_dir),
                patch.object(tts.httpx, "AsyncClient", FakeClient),
            ):
                audio_url = await tts.synthesize_voice("hello there", "session-1")

            self.assertIsNotNone(audio_url)
            self.assertTrue(audio_url.startswith("/audio/reply-"))
            self.assertTrue(audio_url.endswith(".mp3"))
            generated_file = audio_dir / audio_url.removeprefix("/audio/")
            self.assertEqual(generated_file.read_bytes(), b"fake-mp3")


if __name__ == "__main__":
    unittest.main()
