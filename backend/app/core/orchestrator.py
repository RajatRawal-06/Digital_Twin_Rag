"""End-to-end chat pipeline orchestration."""

from __future__ import annotations

import asyncio

from app.core.generation import generate_response
from app.core.guardrails import GuardrailEngine
from app.core.intent_router import classify_intent
from app.core.memory import MemoryManager
from app.core.preprocessing import normalize_message
from app.core.retrievers import TriRetrieverEngine
from app.core.schemas import PipelineResult
from app.core.tts import synthesize_voice


class FeynmanPipeline:
    """Coordinates memory, routing, retrieval, generation, guardrails, and TTS."""

    def __init__(self):
        self.retriever = TriRetrieverEngine()
        self.guardrail = GuardrailEngine()

    async def run(self, message: str, memory: MemoryManager) -> PipelineResult:
        normalized = normalize_message(message)
        short_term_ctx = memory.get_short_term_context()
        ltm_profile = memory.get_ltm_profile()

        intent = await classify_intent(normalized, short_term_ctx)
        context_chunks = await self.retriever.retrieve(
            query=normalized,
            intent=intent,
            ltm_profile=ltm_profile,
        )

        raw_reply = await generate_response(
            user_message=normalized,
            context_chunks=context_chunks,
            short_term_ctx=short_term_ctx,
            ltm_profile=ltm_profile,
            intent=intent,
        )
        final_reply = await self.guardrail.check(raw_reply)
        audio_url = await synthesize_voice(final_reply, memory.session_id)

        asyncio.create_task(memory.add_turn(user=normalized, assistant=final_reply))

        sources = [chunk.source for chunk in context_chunks]
        return PipelineResult(
            reply=final_reply,
            intent=intent.value,
            sources=sources,
            audio_url=audio_url,
            trace={
                "normalized_message": normalized,
                "retrieved_chunks": len(context_chunks),
                "sources": sources,
                "ltm_profile": ltm_profile,
            },
        )
