"""REST and WebSocket chat routes for the Feynman Digital Twin."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.core.memory import MemoryManager
from app.core.orchestrator import FeynmanPipeline

router = APIRouter()

_sessions: dict[str, MemoryManager] = {}
_pipeline = FeynmanPipeline()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = ""


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    sources: list[str] = []
    audio_url: str | None = None
    trace: dict[str, Any] = {}


def _get_session(session_id: str) -> MemoryManager:
    if session_id not in _sessions:
        _sessions[session_id] = MemoryManager(session_id=session_id)
    return _sessions[session_id]


async def run_pipeline(message: str, memory: MemoryManager):
    return await _pipeline.run(message, memory)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id or str(uuid.uuid4())
    result = await run_pipeline(req.message, _get_session(session_id))
    return ChatResponse(
        session_id=session_id,
        reply=result.reply,
        intent=result.intent,
        sources=result.sources,
        audio_url=result.audio_url,
        trace=result.trace,
    )


@router.websocket("/ws/chat/{session_id}")
async def chat_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    memory = _get_session(session_id)

    try:
        while True:
            data = await websocket.receive_json()
            message = str(data.get("message", "")).strip()
            if not message:
                continue

            await websocket.send_json({"type": "thinking"})
            result = await run_pipeline(message, memory)
            await websocket.send_json(
                {
                    "type": "response",
                    "reply": result.reply,
                    "intent": result.intent,
                    "sources": result.sources,
                    "audio_url": result.audio_url,
                    "trace": result.trace,
                }
            )
    except WebSocketDisconnect:
        return
