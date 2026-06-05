"""One-time ingestion pipeline for Knowledge and Persona source folders."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import numpy as np

from app.config import (
    KNOWLEDGE_COLLECTION,
    KNOWLEDGE_DIR,
    LLAMA_PARSE_API_KEY,
    PERSONA_COLLECTION,
    PERSONA_DIR,
)
from app.core.embeddings import cosine_similarity, get_embedding_service
from app.pipeline.embed import embed_and_upsert, ensure_collections_exist


def _get_llama_parser():
    from llama_parse import LlamaParse

    return LlamaParse(
        api_key=LLAMA_PARSE_API_KEY,
        result_type="markdown",
        language="en",
        verbose=True,
    )


def semantic_chunk(text: str, threshold: float = 0.3) -> list[str]:
    """Split knowledge text on topic changes, with paragraph fallback."""
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if len(sentences) <= 2:
        return [text] if text.strip() else []

    try:
        vectors = [np.array(vector) for vector in get_embedding_service().embed_batch(sentences)]
        chunks: list[str] = []
        current = [sentences[0]]

        for index in range(1, len(sentences)):
            similarity = cosine_similarity(vectors[index - 1], vectors[index])
            if similarity < threshold:
                chunks.append(" ".join(current))
                current = [sentences[index]]
            else:
                current.append(sentences[index])

        chunks.append(" ".join(current))
        return [chunk for chunk in chunks if len(chunk.split()) >= 20]
    except Exception as exc:
        print(f"[Ingest] Semantic chunking fell back to paragraphs: {exc}")
        return [part.strip() for part in text.split("\n\n") if len(part.split()) >= 20]


def dialogue_chunk(text: str) -> list[str]:
    """Split persona text at paragraph or speaker-turn boundaries."""
    pattern = re.compile(r"\n{2,}|(?=(?:Feynman|Richard|Q|Interviewer)\s*:)", re.IGNORECASE)
    return [part.strip() for part in pattern.split(text) if len(part.split()) >= 15]


async def ingest_knowledge_folder() -> None:
    knowledge_path = Path(KNOWLEDGE_DIR)
    pdfs = list(knowledge_path.glob("*.pdf"))
    print(f"[Ingest] Found {len(pdfs)} Knowledge PDFs in {knowledge_path}")

    parser = _get_llama_parser() if LLAMA_PARSE_API_KEY else None
    all_chunks: list[dict] = []

    for pdf in pdfs:
        print(f"[Ingest] Parsing knowledge PDF: {pdf.name}")
        if parser is not None:
            try:
                documents = await asyncio.to_thread(parser.load_data, str(pdf))
                full_text = "\n\n".join(document.text for document in documents)
            except Exception as exc:
                print(f"[Ingest] LlamaParse failed for {pdf.name}, using PyPDF: {exc}")
                full_text = _pypdf_fallback(pdf)
        else:
            full_text = _pypdf_fallback(pdf)

        chunks = semantic_chunk(full_text)
        print(f"[Ingest] {pdf.name}: {len(chunks)} semantic chunks")
        for index, chunk_text in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk_text,
                    "source": pdf.name,
                    "type": "knowledge",
                    "format": "physics_text",
                    "chunk_index": index,
                }
            )

    await embed_and_upsert(all_chunks, collection=KNOWLEDGE_COLLECTION)


async def ingest_persona_folder() -> None:
    persona_path = Path(PERSONA_DIR)
    all_chunks: list[dict] = []

    for pdf in persona_path.glob("*.pdf"):
        print(f"[Ingest] Loading persona PDF: {pdf.name}")
        chunks = dialogue_chunk(_pypdf_fallback(pdf))
        for index, chunk_text in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk_text,
                    "source": pdf.stem,
                    "type": "persona",
                    "format": "book_or_transcript",
                    "chunk_index": index,
                }
            )

    for txt in persona_path.glob("*.txt*"):
        print(f"[Ingest] Loading persona text: {txt.name}")
        text = txt.read_text(encoding="utf-8", errors="replace")
        chunks = dialogue_chunk(text)
        for index, chunk_text in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk_text,
                    "source": txt.stem,
                    "type": "persona",
                    "format": "video_transcript",
                    "chunk_index": index,
                }
            )

    await embed_and_upsert(all_chunks, collection=PERSONA_COLLECTION)


def _pypdf_fallback(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        print(f"[Ingest] PyPDF failed for {pdf_path.name}: {exc}")
        return ""


async def main() -> None:
    print("[Ingest] Starting Feynman data ingestion pipeline")
    await ensure_collections_exist()
    await ingest_knowledge_folder()
    await ingest_persona_folder()
    print("[Ingest] All data ingested successfully")


if __name__ == "__main__":
    asyncio.run(main())
