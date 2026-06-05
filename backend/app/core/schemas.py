"""Shared data shapes for the Feynman Digital Twin backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievedChunk:
    """A normalized retrieval result from the graph, vector DB, or fallback loaders."""

    text: str
    source: str = "unknown"
    type: str = "knowledge"
    score: float = 0.0
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "RetrievedChunk":
        return cls(
            text=value.get("text", ""),
            source=value.get("source", "unknown"),
            type=value.get("type", "knowledge"),
            score=float(value.get("score", 0.0) or 0.0),
            embedding=value.get("embedding"),
            metadata={
                key: item
                for key, item in value.items()
                if key not in {"text", "source", "type", "score", "embedding"}
            },
        )

    def for_prompt(self) -> dict[str, Any]:
        """Return a prompt-safe dict without the large embedding vector."""
        return {
            "text": self.text,
            "source": self.source,
            "type": self.type,
            "score": self.score,
            **self.metadata,
        }


@dataclass(slots=True)
class PipelineResult:
    """Final response plus lightweight trace data for UI/debugging."""

    reply: str
    intent: str
    sources: list[str]
    audio_url: str | None = None
    trace: dict[str, Any] = field(default_factory=dict)
