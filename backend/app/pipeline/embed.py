"""Embedding generation and Qdrant vector store management."""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import (
    DATA_DIR,
    EMBEDDING_DIM,
    KNOWLEDGE_COLLECTION,
    PERSONA_COLLECTION,
    QDRANT_API_KEY,
    QDRANT_URL,
)
from app.core.embeddings import get_embedding_service

_BASELINE_PATH = Path(DATA_DIR) / "baseline_embedding.json"
_BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
_BATCH_SIZE = 50
_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    return _client


async def ensure_collections_exist() -> None:
    client = _get_client()
    existing = {collection.name for collection in client.get_collections().collections}

    for name in [KNOWLEDGE_COLLECTION, PERSONA_COLLECTION]:
        if name in existing:
            print(f"[Embed] Collection already exists: {name}")
            continue
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"[Embed] Created Qdrant collection: {name}")


async def embed_and_upsert(chunks: list[dict], collection: str) -> None:
    client = _get_client()
    embeddings = get_embedding_service()
    total = len(chunks)
    print(f"[Embed] Embedding {total} chunks into {collection}")

    for batch_start in range(0, total, _BATCH_SIZE):
        batch = chunks[batch_start : batch_start + _BATCH_SIZE]
        texts = [chunk["text"] for chunk in batch]

        try:
            vectors = await asyncio.to_thread(embeddings.embed_batch, texts)
        except Exception as exc:
            print(f"[Embed] Batch {batch_start}-{batch_start + len(batch)} failed: {exc}")
            continue

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "source": chunk.get("source", "unknown"),
                    "type": chunk.get("type", "unknown"),
                    "format": chunk.get("format", "unknown"),
                    "chunk_index": chunk.get("chunk_index", 0),
                },
            )
            for chunk, vector in zip(batch, vectors)
        ]

        await asyncio.to_thread(client.upsert, collection_name=collection, points=points)
        print(f"[Embed] Upserted {batch_start + len(batch)}/{total}")


async def build_baseline_embedding() -> None:
    client = _get_client()
    print("[Embed] Building baseline embedding from Persona collection")

    all_vectors: list[list[float]] = []
    offset = None
    limit = 100

    while True:
        results, next_offset = client.scroll(
            collection_name=PERSONA_COLLECTION,
            with_vectors=True,
            limit=limit,
            offset=offset,
        )
        for point in results:
            if isinstance(point.vector, list):
                all_vectors.append(point.vector)
        if next_offset is None or len(results) < limit:
            break
        offset = next_offset

    if not all_vectors:
        print("[Embed] No persona vectors found. Run ingestion first.")
        return

    mean_vector = np.mean(np.array(all_vectors), axis=0).tolist()
    _BASELINE_PATH.write_text(json.dumps({"embedding": mean_vector}), encoding="utf-8")
    print(f"[Embed] Baseline embedding saved from {len(all_vectors)} vectors.")


if __name__ == "__main__":
    if "--rebuild-baseline" in sys.argv:
        asyncio.run(build_baseline_embedding())
    else:
        print("Usage: python -m app.pipeline.embed --rebuild-baseline")
