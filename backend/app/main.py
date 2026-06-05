"""FastAPI application entry point for the Feynman Digital Twin backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BACKEND_ROOT, CORS_ORIGINS, GEMINI_MODEL, KNOWLEDGE_DIR, PERSONA_DIR
from app.routers import chat

app = FastAPI(
    title="Feynman Digital Twin API",
    description="Gemini, GraphRAG, Rhythm Base retrieval, K-Means memory, and TTS handoff.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.mount("/audio", StaticFiles(directory=str(BACKEND_ROOT / "data" / "audio")), name="audio")


@app.get("/health", tags=["meta"])
async def health_check():
    return {
        "status": "ok",
        "model": GEMINI_MODEL,
        "knowledge_dir": KNOWLEDGE_DIR,
        "persona_dir": PERSONA_DIR,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
