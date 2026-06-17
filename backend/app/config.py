"""Central configuration for the Feynman Digital Twin backend."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = APP_DIR.parent
PROJECT_ROOT = BACKEND_ROOT.parent

load_dotenv(BACKEND_ROOT / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Paths
DATA_DIR = str(BACKEND_ROOT / "data")
KNOWLEDGE_DIR = str(PROJECT_ROOT / "Knowledge")
PERSONA_DIR = str(PROJECT_ROOT / "Persona")

# API keys
_raw_gemini_keys = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEYS: list[str] = [k.strip() for k in _raw_gemini_keys.split(",") if k.strip()]
GEMINI_API_KEY: str = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
LLAMA_PARSE_API_KEY: str = os.getenv("LLAMA_PARSE_API_KEY", "")
LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")

# Gemini key pool (lazy init)
_gemini_pool = None

def get_gemini_pool():
    global _gemini_pool
    if _gemini_pool is None and GEMINI_API_KEYS:
        from app.core.key_pool import GeminiKeyPool
        _gemini_pool = GeminiKeyPool(GEMINI_API_KEYS)
        print(f"[Config] Gemini key pool initialized with {len(GEMINI_API_KEYS)} key(s)")
    return _gemini_pool

# Gemini models
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
INTENT_ROUTER_MODEL: str = os.getenv("INTENT_ROUTER_MODEL", "gemini-2.0-flash-lite")

# Qdrant vector DB
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
KNOWLEDGE_COLLECTION: str = os.getenv("KNOWLEDGE_COLLECTION", "feynman_knowledge")
PERSONA_COLLECTION: str = os.getenv("PERSONA_COLLECTION", "feynman_persona")

# Embeddings
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))

# Retrieval
TOP_K_KNOWLEDGE: int = int(os.getenv("TOP_K_KNOWLEDGE", "6"))
TOP_K_PERSONA: int = int(os.getenv("TOP_K_PERSONA", "4"))
MMR_LAMBDA: float = float(os.getenv("MMR_LAMBDA", "0.6"))
MMR_FETCH_K: int = int(os.getenv("MMR_FETCH_K", "20"))

# Memory
SHORT_TERM_K: int = int(os.getenv("SHORT_TERM_K", "5"))
KMEANS_N_CLUSTERS: int = int(os.getenv("KMEANS_N_CLUSTERS", "8"))
KMEANS_UPDATE_EVERY: int = int(os.getenv("KMEANS_UPDATE_EVERY", "5"))

# Guardrails
ANOMALY_COSINE_THRESHOLD: float = float(os.getenv("ANOMALY_COSINE_THRESHOLD", "0.35"))
FALLBACK_RESPONSE: str = (
    "You know, I haven't the slightest idea about that - "
    "it must be something you young folks came up with after my time."
)

# TTS
ENABLE_TTS: bool = _env_bool("ENABLE_TTS", False)
TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "elevenlabs").strip().lower()
TTS_ENDPOINT: str = os.getenv("TTS_ENDPOINT", "http://localhost:8001/synthesize")
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL_ID: str = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
ELEVENLABS_OUTPUT_FORMAT: str = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")

# Frontend/dev access
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
