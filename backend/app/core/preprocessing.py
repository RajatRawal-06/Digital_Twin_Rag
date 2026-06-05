"""Input normalization before routing and retrieval."""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")
_COMMON_REWRITES = {
    r"\bq\s*e\s*d\b": "QED",
    r"\blos alamos\b": "Los Alamos",
    r"\bfar rockaway\b": "Far Rockaway",
    r"\bfeynmann\b": "Feynman",
    r"\bfeyman\b": "Feynman",
}


def normalize_message(message: str) -> str:
    """Cheap orthographic pass; an LLM normalizer can be added later."""
    normalized = _WHITESPACE_RE.sub(" ", message.strip())
    for pattern, replacement in _COMMON_REWRITES.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalized
