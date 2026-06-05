"""Tri-Retriever Engine: GraphRAG, Rhythm Base vectors, and Hybrid MMR."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from app.config import (
    KNOWLEDGE_COLLECTION,
    MMR_FETCH_K,
    MMR_LAMBDA,
    PERSONA_COLLECTION,
    PERSONA_DIR,
    QDRANT_API_KEY,
    QDRANT_URL,
    TOP_K_KNOWLEDGE,
    TOP_K_PERSONA,
)
from app.core.context import contextual_compress
from app.core.embeddings import cosine_similarity, get_embedding_service
from app.core.intent_router import IntentType
from app.core.knowledge_graph import KnowledgeGraphStore
from app.core.schemas import RetrievedChunk

_qdrant: QdrantClient | None = None
_WORD_RE = re.compile(r"[a-zA-Z0-9']+")


def _get_qdrant():
    global _qdrant
    if _qdrant is None:
        from qdrant_client import QdrantClient

        _qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    return _qdrant


def _mmr_rerank(
    query_vec: list[float],
    candidates: list[RetrievedChunk],
    top_k: int,
    lambda_: float = MMR_LAMBDA,
) -> list[RetrievedChunk]:
    """Maximal Marginal Relevance over normalized RetrievedChunk objects."""
    remaining = [chunk for chunk in candidates if chunk.embedding]
    selected: list[RetrievedChunk] = []

    while len(selected) < top_k and remaining:
        best_score = -float("inf")
        best_doc: RetrievedChunk | None = None

        for doc in remaining:
            relevance = cosine_similarity(query_vec, doc.embedding or [])
            diversity_penalty = (
                max(cosine_similarity(doc.embedding or [], item.embedding or []) for item in selected)
                if selected
                else 0.0
            )
            score = lambda_ * relevance - (1.0 - lambda_) * diversity_penalty
            if score > best_score:
                best_score = score
                best_doc = doc

        if best_doc is None:
            break

        selected.append(best_doc)
        remaining.remove(best_doc)

    return selected


def _qdrant_search(collection: str, query_vec: list[float], k: int, chunk_type: str) -> list[RetrievedChunk]:
    """Run vector search and fail open when Qdrant has not been started yet."""
    try:
        client = _get_qdrant()
        results = client.search(
            collection_name=collection,
            query_vector=query_vec,
            limit=k,
            with_vectors=True,
            with_payload=True,
        )
    except Exception as exc:
        print(f"[Retriever] Qdrant search skipped for {collection}: {exc}")
        return []

    chunks: list[RetrievedChunk] = []
    for hit in results:
        payload = hit.payload or {}
        vector = hit.vector if isinstance(hit.vector, list) else None
        chunks.append(
            RetrievedChunk(
                text=payload.get("text", ""),
                source=payload.get("source", "unknown"),
                type=payload.get("type", chunk_type),
                score=float(hit.score or 0.0),
                embedding=vector,
                metadata={
                    "format": payload.get("format", "unknown"),
                    "chunk_index": payload.get("chunk_index", 0),
                    "retrieval": "qdrant",
                },
            )
        )
    return [chunk for chunk in chunks if chunk.text.strip()]


class TriRetrieverEngine:
    """Dispatches to the path required by the intent router."""

    def __init__(self):
        self.embeddings = get_embedding_service()
        self.graph = KnowledgeGraphStore()

    async def retrieve(
        self,
        query: str,
        intent: IntentType,
        ltm_profile: dict | None = None,
    ) -> list[RetrievedChunk]:
        query_vec = await asyncio.to_thread(self.embeddings.embed, query)

        if intent == IntentType.TECHNICAL:
            chunks = await self._technical_path(query, query_vec)
            return chunks[:TOP_K_KNOWLEDGE]
        if intent == IntentType.PERSONAL:
            chunks = await self._persona_path(query, query_vec)
            return chunks[:TOP_K_PERSONA]
        return await self._hybrid_path(query, query_vec)

    async def _technical_path(self, query: str, query_vec: list[float]) -> list[RetrievedChunk]:
        graph_chunks = self.graph.query(query, top_k=max(2, TOP_K_KNOWLEDGE // 2))
        await self._ensure_embeddings(graph_chunks)
        vector_chunks = await asyncio.to_thread(
            _qdrant_search,
            KNOWLEDGE_COLLECTION,
            query_vec,
            MMR_FETCH_K,
            "knowledge",
        )
        candidates = contextual_compress(query, graph_chunks + vector_chunks)
        ranked = _mmr_rerank(query_vec, candidates, TOP_K_KNOWLEDGE)
        return ranked or candidates[:TOP_K_KNOWLEDGE]

    async def _persona_path(self, query: str, query_vec: list[float]) -> list[RetrievedChunk]:
        vector_chunks = await asyncio.to_thread(
            _qdrant_search,
            PERSONA_COLLECTION,
            query_vec,
            MMR_FETCH_K,
            "persona",
        )
        fallback_chunks = [] if vector_chunks else await asyncio.to_thread(self._persona_text_fallback, query)
        candidates = contextual_compress(query, vector_chunks + fallback_chunks)
        await self._ensure_embeddings(candidates)
        ranked = _mmr_rerank(query_vec, candidates, TOP_K_PERSONA)
        return ranked or candidates[:TOP_K_PERSONA]

    async def _hybrid_path(self, query: str, query_vec: list[float]) -> list[RetrievedChunk]:
        technical_task = asyncio.create_task(self._technical_path(query, query_vec))
        persona_task = asyncio.create_task(self._persona_path(query, query_vec))
        technical_chunks, persona_chunks = await asyncio.gather(technical_task, persona_task)

        pinned: list[RetrievedChunk] = []
        if technical_chunks:
            pinned.append(technical_chunks[0])
        if persona_chunks:
            pinned.append(persona_chunks[0])

        combined = technical_chunks[1:] + persona_chunks[1:]
        remaining_k = max(0, TOP_K_KNOWLEDGE + TOP_K_PERSONA - len(pinned))
        ranked = _mmr_rerank(query_vec, combined, remaining_k)
        return pinned + ranked

    async def _ensure_embeddings(self, chunks: list[RetrievedChunk]) -> None:
        missing = [chunk for chunk in chunks if chunk.embedding is None]
        if not missing:
            return
        vectors = await asyncio.to_thread(
            self.embeddings.embed_batch,
            [chunk.text for chunk in missing],
        )
        for chunk, vector in zip(missing, vectors):
            chunk.embedding = vector

    def _persona_text_fallback(self, query: str) -> list[RetrievedChunk]:
        """Small local fallback from text transcripts while Qdrant is empty."""
        terms = set(_WORD_RE.findall(query.lower()))
        persona_path = Path(PERSONA_DIR)
        chunks: list[RetrievedChunk] = []

        for txt_path in persona_path.glob("*.txt*"):
            text = txt_path.read_text(encoding="utf-8", errors="replace")
            paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if len(part.split()) >= 12]
            for index, paragraph in enumerate(paragraphs[:400]):
                paragraph_terms = set(_WORD_RE.findall(paragraph.lower()))
                score = len(terms & paragraph_terms)
                if score:
                    chunks.append(
                        RetrievedChunk(
                            text=paragraph[:1600],
                            source=txt_path.name,
                            type="persona",
                            score=float(score),
                            metadata={"chunk_index": index, "retrieval": "local_text_fallback"},
                        )
                    )

        chunks.sort(key=lambda item: item.score, reverse=True)
        return chunks[:TOP_K_PERSONA]
