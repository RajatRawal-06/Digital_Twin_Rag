"""Short-term and K-Means long-term memory management."""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from app.config import DATA_DIR, KMEANS_N_CLUSTERS, KMEANS_UPDATE_EVERY, SHORT_TERM_K
from app.core.embeddings import get_embedding_service

_LTM_DIR = Path(DATA_DIR) / "ltm"
_LTM_DIR.mkdir(parents=True, exist_ok=True)


class MemoryManager:
    """Per-session memory controller."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._stm: list[dict] = []
        self._query_embeddings: list[list[float]] = []
        self._cluster_profile: dict = {}
        self._turns_since_cluster = 0
        self._embeddings = get_embedding_service()
        self._load_ltm()

    def get_short_term_context(self) -> list[dict]:
        return self._stm[-SHORT_TERM_K:]

    def get_ltm_profile(self) -> dict:
        return self._cluster_profile

    async def add_turn(self, user: str, assistant: str) -> None:
        self._stm.append({"user": user, "assistant": assistant})

        try:
            embedding = await asyncio.to_thread(self._embeddings.embed, user)
            self._query_embeddings.append(embedding)
        except Exception as exc:
            print(f"[Memory] Embedding failed for LTM update: {exc}")

        self._turns_since_cluster += 1
        if self._turns_since_cluster >= KMEANS_UPDATE_EVERY:
            await self._update_kmeans_profile()
            self._turns_since_cluster = 0

        self._save_ltm()

    async def _update_kmeans_profile(self) -> None:
        if len(self._query_embeddings) < min(2, KMEANS_N_CLUSTERS):
            return

        def _run_kmeans():
            import numpy as np
            from sklearn.cluster import KMeans

            embeddings = np.array(self._query_embeddings)
            n_clusters = min(KMEANS_N_CLUSTERS, len(embeddings))
            km = KMeans(n_clusters=n_clusters, n_init="auto", random_state=42)
            km.fit(embeddings)
            return n_clusters, km.labels_.tolist(), float(km.inertia_)

        try:
            n_clusters, labels, inertia = await asyncio.to_thread(_run_kmeans)
        except Exception as exc:
            print(f"[Memory] K-Means update skipped: {exc}")
            return

        distribution = Counter(labels)

        self._cluster_profile = {
            "n_clusters": n_clusters,
            "top_cluster_ids": [cid for cid, _ in distribution.most_common(3)],
            "distribution": dict(distribution),
            "inertia": inertia,
            "knowledge_level": self._infer_knowledge_level(),
        }
        print(f"[Memory] LTM profile updated for {self.session_id}: {self._cluster_profile}")

    def _infer_knowledge_level(self) -> str:
        if not self._stm:
            return "unknown"
        avg_len = sum(len(turn["user"].split()) for turn in self._stm) / len(self._stm)
        if avg_len < 8:
            return "beginner"
        if avg_len < 20:
            return "intermediate"
        return "expert"

    def _ltm_path(self) -> Path:
        safe_id = "".join(ch for ch in self.session_id if ch.isalnum() or ch in {"-", "_"})
        return _LTM_DIR / f"{safe_id}.json"

    def _save_ltm(self) -> None:
        try:
            data = {
                "stm": self._stm,
                "query_embeddings": self._query_embeddings,
                "cluster_profile": self._cluster_profile,
            }
            self._ltm_path().write_text(json.dumps(data), encoding="utf-8")
        except Exception as exc:
            print(f"[Memory] Save failed: {exc}")

    def _load_ltm(self) -> None:
        path = self._ltm_path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._stm = data.get("stm", [])
            self._query_embeddings = data.get("query_embeddings", [])
            self._cluster_profile = data.get("cluster_profile", {})
        except Exception as exc:
            print(f"[Memory] Load failed: {exc}")
