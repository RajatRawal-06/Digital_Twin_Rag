"""Gemini generation with persona and context augmentation."""

from __future__ import annotations

from google import genai
from google.genai import types as genai_types

from app.config import GEMINI_API_KEY, GEMINI_MODEL, get_gemini_pool
from app.core.intent_router import IntentType
from app.core.schemas import RetrievedChunk

_FEYNMAN_IDENTITY = """\
You are modeling Richard Phillips Feynman: physicist, teacher, bongo drummer,
and curious adventurer from Far Rockaway, Queens.

Voice rules:
- Be direct, vivid, playful, and plain-spoken.
- Explain hard ideas with simple analogies before formalism.
- Use "look", "see?", "the thing is", and "you know" naturally, not constantly.
- Never use corporate jargon.
- If asked about discoveries or events after 1988, admit you do not know.
- Keep the answer grounded in the retrieved sources when sources are present.
"""


async def generate_response(
    user_message: str,
    context_chunks: list[RetrievedChunk],
    short_term_ctx: list[dict],
    ltm_profile: dict,
    intent: IntentType,
) -> str:
    """Generate the response; fall back to a local scaffold when Gemini is not configured."""
    if not GEMINI_API_KEY:
        return _offline_response(user_message, context_chunks, intent)

    system_prompt = _build_system_prompt(
        context_chunks=context_chunks,
        ltm_profile=ltm_profile,
        short_term_ctx=short_term_ctx,
        intent=intent,
    )

    try:
        pool = get_gemini_pool()
        if pool is None:
            return _offline_response(user_message, context_chunks, intent)
        response = pool.generate_with_retry(
            model=GEMINI_MODEL,
            contents=user_message,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.85,
            ),
        )
        return (response.text or "").strip()
    except Exception as exc:
        print(f"[Generation] Gemini call failed: {exc}")
        return _offline_response(user_message, context_chunks, intent)



def _build_system_prompt(
    context_chunks: list[RetrievedChunk],
    ltm_profile: dict,
    short_term_ctx: list[dict],
    intent: IntentType,
) -> str:
    prompt = _FEYNMAN_IDENTITY + "\n\n"

    if ltm_profile:
        level = ltm_profile.get("knowledge_level", "unknown")
        prompt += f"User knowledge profile: {level}.\n"
        if level == "beginner":
            prompt += "Start from first principles and use everyday analogies.\n"
        elif level == "intermediate":
            prompt += "Assume basic physics vocabulary but define formal terms.\n"
        elif level == "expert":
            prompt += "Use precise language and show the mathematical structure when useful.\n"
        prompt += "\n"

    knowledge_chunks = [chunk for chunk in context_chunks if chunk.type == "knowledge"]
    persona_chunks = [chunk for chunk in context_chunks if chunk.type == "persona"]

    if knowledge_chunks:
        prompt += "Relevant physics context:\n"
        for chunk in knowledge_chunks:
            prompt += f"[{chunk.source}] {chunk.text}\n\n"

    if persona_chunks:
        prompt += "Speech rhythm examples. Use as style guidance, do not quote them verbatim:\n"
        for chunk in persona_chunks[:2]:
            prompt += f"[{chunk.source}] {chunk.text}\n\n"

    if short_term_ctx:
        prompt += "Recent conversation:\n"
        for turn in short_term_ctx:
            prompt += f"Friend: {turn['user']}\nRichard: {turn['assistant']}\n"

    prompt += f"\nIntent route: {intent.value}. Now answer the latest message."
    return prompt


def _offline_response(
    user_message: str,
    context_chunks: list[RetrievedChunk],
    intent: IntentType,
) -> str:
    """Development response so the UI and pipeline can be exercised without keys."""
    source_note = ""
    if context_chunks:
        first = context_chunks[0]
        source_note = f" I am looking at {first.source}, which says: {first.text[:240]}"

    if intent == IntentType.TECHNICAL:
        return (
            "Look, the first trick is not to name the thing and think you understand it. "
            f"For this question, I would start with the mechanism and build up from there.{source_note}"
        )
    if intent == IntentType.PERSONAL:
        return (
            "You know, the personal part matters because it tells you how a fellow actually thinks, "
            f"not just what he wrote on the board.{source_note}"
        )
    return (
        "See, this is the interesting kind of question: half physics, half human being. "
        f"We need the facts, and then we need the little story that makes the facts alive.{source_note}"
    )
