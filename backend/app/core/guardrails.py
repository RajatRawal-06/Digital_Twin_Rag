"""Output guardrails: anomaly detection and jargon filtering."""

from __future__ import annotations

import json
import re
from pathlib import Path

from google import genai

from app.config import (
    ANOMALY_COSINE_THRESHOLD,
    DATA_DIR,
    FALLBACK_RESPONSE,
    GEMINI_API_KEY,
    INTENT_ROUTER_MODEL,
    get_gemini_pool,
)
from app.core.embeddings import cosine_similarity, get_embedding_service

_BASELINE_PATH = Path(DATA_DIR) / "baseline_embedding.json"
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_JARGON_WORDS = {
    "synergy",
    "synergize",
    "leverage",
    "utilize",
    "paradigm",
    "bandwidth",
    "circle back",
    "low-hanging fruit",
    "move the needle",
    "touch base",
    "stakeholder",
    "deliverable",
    "actionable",
    "streamline",
    "best-in-class",
    "cutting-edge",
    "state-of-the-art",
    "empower",
}
_REWRITE_PROMPT = """\
Rewrite this sentence as Richard Feynman would: plain, direct, first-year
college English, no corporate jargon. Return only the rewritten sentence.

Sentence: {sentence}
"""


class GuardrailEngine:
    def __init__(self):
        self.embeddings = get_embedding_service()
        self._baseline_vec = self._load_baseline()

    async def check(self, response: str) -> str:
        response = _repair_mojibake(response)
        if self._baseline_vec is not None and await self._anomaly_check(response):
            print("[Guardrail] Anomaly detected. Using fallback response.")
            return FALLBACK_RESPONSE
        return await self._jargon_filter(response)

    async def _anomaly_check(self, text: str) -> bool:
        try:
            import asyncio

            response_vec = await asyncio.to_thread(self.embeddings.embed, text)
            cosine_distance = 1 - cosine_similarity(self._baseline_vec, response_vec)
            print(f"[Guardrail] Cosine distance from baseline: {cosine_distance:.4f}")
            return cosine_distance > ANOMALY_COSINE_THRESHOLD
        except Exception as exc:
            print(f"[Guardrail] Anomaly check skipped: {exc}")
            return False

    async def _jargon_filter(self, text: str) -> str:
        sentences = _SENTENCE_RE.split(text)
        cleaned: list[str] = []
        for sentence in sentences:
            lower = sentence.lower()
            if any(word in lower for word in _JARGON_WORDS):
                cleaned.append(await self._rewrite_sentence(sentence))
            else:
                cleaned.append(sentence)
        return " ".join(cleaned)

    async def _rewrite_sentence(self, sentence: str) -> str:
        try:
            import asyncio

            pool = get_gemini_pool()
            if pool is None:
                return _local_jargon_rewrite(sentence)
            response = await asyncio.to_thread(
                pool.generate_with_retry,
                INTENT_ROUTER_MODEL,
                _REWRITE_PROMPT.format(sentence=sentence),
            )
            return (response.text or sentence).strip()
        except Exception as exc:
            print(f"[Guardrail] Jargon rewrite skipped: {exc}")
            return _local_jargon_rewrite(sentence)

    def _load_baseline(self) -> list[float] | None:
        if not _BASELINE_PATH.exists():
            return None
        try:
            data = json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))
            return data["embedding"]
        except Exception as exc:
            print(f"[Guardrail] Could not load baseline embedding: {exc}")
            return None



def _local_jargon_rewrite(sentence: str) -> str:
    replacements = {
        "utilize": "use",
        "leverage": "use",
        "paradigm": "way of thinking",
        "actionable": "useful",
        "deliverable": "thing we need to make",
        "state-of-the-art": "new",
        "cutting-edge": "new",
        "streamline": "make simpler",
        "empower": "help",
    }
    rewritten = sentence
    for old, new in replacements.items():
        rewritten = re.sub(old, new, rewritten, flags=re.IGNORECASE)
    return rewritten


def _repair_mojibake(text: str) -> str:
    replacements = {
        "\u00e2\u0080\u0093": "-",
        "\u00e2\u0080\u0094": "-",
        "\u00e2\u0080\u0099": "'",
        "\u00e2\u0080\u0098": "'",
        "\u00e2\u0080\u009c": '"',
        "\u00e2\u0080\u009d": '"',
        "\u00e2\u0080\u00a6": "...",
        "\u00c2\u00b7": "|",
        "\u00c2\u00b1": "+/-",
    }
    cleaned = text
    for bad, good in replacements.items():
        cleaned = cleaned.replace(bad, good)
    return cleaned
