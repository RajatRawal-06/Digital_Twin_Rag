"""TTS handoff for Richard's generated replies."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import httpx

from app.config import (
    BACKEND_ROOT,
    ELEVENLABS_API_KEY,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_OUTPUT_FORMAT,
    ELEVENLABS_VOICE_ID,
    ENABLE_TTS,
    TTS_ENDPOINT,
    TTS_PROVIDER,
)

_AUDIO_DIR = Path(BACKEND_ROOT) / "data" / "audio"
_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


async def synthesize_voice(text: str, session_id: str) -> str | None:
    """Return a browser-playable audio URL for a generated reply."""
    if not ENABLE_TTS:
        return None

    if TTS_PROVIDER == "elevenlabs":
        return await _synthesize_elevenlabs(text=text, session_id=session_id)

    return await _synthesize_custom_service(text=text, session_id=session_id)


async def _synthesize_elevenlabs(text: str, session_id: str) -> str | None:
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        print("[TTS] ElevenLabs skipped: missing API key or voice ID.")
        return None

    file_name = _stable_audio_name(text=text, session_id=session_id, suffix=".mp3")
    file_path = _AUDIO_DIR / file_name
    if file_path.exists():
        return f"/audio/{file_name}"

    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        f"?output_format={ELEVENLABS_OUTPUT_FORMAT}"
    )
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.8,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                url,
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            file_path.write_bytes(response.content)
            return f"/audio/{file_name}"
    except httpx.HTTPStatusError as exc:
        detail = _elevenlabs_error_detail(exc.response)
        print(
            "[TTS] ElevenLabs synthesis failed "
            f"with HTTP {exc.response.status_code}: {detail}"
        )
        return None
    except Exception as exc:
        print(f"[TTS] ElevenLabs synthesis failed: {exc}")
        return None


async def _synthesize_custom_service(text: str, session_id: str) -> str | None:
    if not TTS_ENDPOINT:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                TTS_ENDPOINT,
                json={
                    "text": text,
                    "session_id": session_id,
                    "voice": "feynman_acoustic_clone",
                    "format": "wav",
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("audio_url") or payload.get("url")
    except Exception as exc:
        print(f"[TTS] Custom voice service skipped: {exc}")
        return None


def _stable_audio_name(text: str, session_id: str, suffix: str) -> str:
    digest = hashlib.sha256(f"{session_id}:{text}".encode("utf-8")).hexdigest()[:24]
    return f"reply-{digest}{suffix}"


def _elevenlabs_error_detail(response: httpx.Response) -> str:
    try:
        body: dict[str, Any] = response.json()
    except ValueError:
        return response.text[:240] or "no response body"

    detail = body.get("detail")
    if isinstance(detail, dict):
        status = detail.get("status")
        message = detail.get("message")
        return " - ".join(str(item) for item in [status, message] if item)

    if detail:
        return str(detail)

    return response.text[:240] or "no response body"
