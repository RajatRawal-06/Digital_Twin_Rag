"""Gemini API key pool with automatic rotation on quota exhaustion."""

from __future__ import annotations

import itertools
import threading
from typing import Any

from google import genai


class GeminiKeyPool:
    """Thread-safe round-robin key pool that rotates on 429/503 errors."""

    def __init__(self, keys: list[str]):
        self._keys = [k for k in keys if k.strip()]
        if not self._keys:
            raise ValueError("No Gemini API keys provided")
        self._cycle = itertools.cycle(range(len(self._keys)))
        self._current_index = next(self._cycle)
        self._clients: dict[int, genai.Client] = {}
        self._lock = threading.Lock()

    @property
    def current_key(self) -> str:
        with self._lock:
            return self._keys[self._current_index]

    @property
    def has_keys(self) -> bool:
        return len(self._keys) > 0

    def get_client(self) -> genai.Client:
        with self._lock:
            idx = self._current_index
            if idx not in self._clients:
                self._clients[idx] = genai.Client(api_key=self._keys[idx])
        return self._clients[idx]

    def rotate(self) -> None:
        with self._lock:
            old = self._current_index
            self._current_index = next(self._cycle)
            print(
                f"[KeyPool] Rotated from key #{old + 1} to key "
                f"#{self._current_index + 1} of {len(self._keys)}"
            )

    def generate_with_retry(
        self,
        model: str,
        contents: Any,
        config: Any = None,
    ) -> Any:
        """Try each key up to one full rotation before giving up."""
        last_exc = None
        for _ in range(len(self._keys)):
            client = self.get_client()
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "contents": contents,
                }
                if config is not None:
                    kwargs["config"] = config
                return client.models.generate_content(**kwargs)
            except Exception as exc:
                error_str = str(exc)
                if "429" in error_str or "503" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"[KeyPool] Key #{self._current_index + 1} exhausted: {error_str[:120]}")
                    self.rotate()
                    last_exc = exc
                    continue
                raise
        raise last_exc  # type: ignore[misc]
