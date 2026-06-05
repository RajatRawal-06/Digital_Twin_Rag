"""Contextual compression helpers for retrieved chunks."""

from __future__ import annotations

import re

from app.core.schemas import RetrievedChunk

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "this",
    "with",
    "from",
    "what",
    "why",
    "how",
    "about",
    "into",
    "like",
    "your",
    "you",
}


def contextual_compress(
    query: str,
    chunks: list[RetrievedChunk],
    max_chars_per_chunk: int = 1200,
) -> list[RetrievedChunk]:
    """Keep the most query-relevant sentences from each retrieved chunk."""
    terms = {
        token
        for token in re.findall(r"[a-zA-Z0-9']+", query.lower())
        if len(token) > 2 and token not in _STOPWORDS
    }
    if not terms:
        return [_truncate(chunk, max_chars_per_chunk) for chunk in chunks]

    compressed: list[RetrievedChunk] = []
    for chunk in chunks:
        sentences = _SENTENCE_RE.split(chunk.text)
        scored = []
        for index, sentence in enumerate(sentences):
            lower = sentence.lower()
            score = sum(1 for term in terms if term in lower)
            if score:
                scored.append((score, index, sentence.strip()))

        if not scored:
            compressed.append(_truncate(chunk, max_chars_per_chunk))
            continue

        scored.sort(key=lambda item: (-item[0], item[1]))
        selected = sorted(scored[:4], key=lambda item: item[1])
        text = " ".join(sentence for _, _, sentence in selected)
        compressed.append(
            RetrievedChunk(
                text=text[:max_chars_per_chunk],
                source=chunk.source,
                type=chunk.type,
                score=chunk.score,
                embedding=chunk.embedding,
                metadata=chunk.metadata,
            )
        )
    return compressed


def _truncate(chunk: RetrievedChunk, max_chars: int) -> RetrievedChunk:
    if len(chunk.text) <= max_chars:
        return chunk
    return RetrievedChunk(
        text=chunk.text[:max_chars].rstrip() + "...",
        source=chunk.source,
        type=chunk.type,
        score=chunk.score,
        embedding=chunk.embedding,
        metadata=chunk.metadata,
    )
