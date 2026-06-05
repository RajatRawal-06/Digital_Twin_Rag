"""Embedding service with API-backed and local deterministic modes."""

from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Iterable

from app.config import EMBEDDING_DIM, EMBEDDING_MODEL

_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")
_service: "EmbeddingService | None" = None


class EmbeddingService:
    """Production embedding wrapper with an offline-safe fallback."""

    def __init__(self, model: str = EMBEDDING_MODEL, dim: int = EMBEDDING_DIM):
        self.model = model
        self.dim = dim
        self._openai_enabled = bool(os.getenv("OPENAI_API_KEY"))

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._openai_enabled:
            try:
                return self._openai_embed_batch(texts)
            except Exception as exc:
                print(f"[Embeddings] OpenAI embedding failed, using local fallback: {exc}")
        return [self._hash_embedding(text) for text in texts]

    def _openai_embed_batch(self, texts: list[str]) -> list[list[float]]:
        import openai

        client = openai.OpenAI()
        response = client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    def _hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 else -1.0
            weight = 1.0 + min(len(token), 12) / 12.0
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    a = list(left)
    b = list(right)
    if not a or not b:
        return 0.0

    limit = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(limit))
    norm_a = math.sqrt(sum(value * value for value in a[:limit]))
    norm_b = math.sqrt(sum(value * value for value in b[:limit]))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_embedding_service() -> EmbeddingService:
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service
