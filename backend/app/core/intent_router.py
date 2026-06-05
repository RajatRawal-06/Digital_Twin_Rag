"""Intent routing for technical, personal, and blended queries."""

from __future__ import annotations

from enum import Enum

from google import genai

from app.config import GEMINI_API_KEY, INTENT_ROUTER_MODEL, get_gemini_pool

_ROUTER_PROMPT = """\
You are a query classifier for a Richard Feynman digital twin system.

Classify the user's message into EXACTLY ONE label:
TECHNICAL - physics, science, math, equations, or factual explanation
PERSONAL - Feynman's life, opinions, feelings, stories, or philosophy
BLENDED - both scientific explanation and personal experience are needed

Respond with ONLY the label.

User message: {message}

Recent conversation context:
{context}
"""

_TECHNICAL_TERMS = {
    "physics",
    "quantum",
    "qed",
    "equation",
    "electron",
    "photon",
    "path",
    "integral",
    "diagram",
    "calculus",
    "probability",
    "mechanics",
    "relativity",
    "field",
    "experiment",
}
_PERSONAL_TERMS = {
    "feel",
    "felt",
    "life",
    "story",
    "los alamos",
    "caltech",
    "father",
    "opinion",
    "think about",
    "philosophy",
    "bongo",
    "love",
    "why do you",
}


class IntentType(str, Enum):
    TECHNICAL = "TECHNICAL"
    PERSONAL = "PERSONAL"
    BLENDED = "BLENDED"


async def classify_intent(message: str, context: list[dict]) -> IntentType:
    """Classify the message, with a deterministic heuristic fallback."""
    if not GEMINI_API_KEY:
        return _heuristic_intent(message)

    ctx_str = "\n".join(
        f"User: {turn['user']}\nFeynman: {turn['assistant']}" for turn in context[-3:]
    ) or "None"
    prompt = _ROUTER_PROMPT.format(message=message, context=ctx_str)

    try:
        pool = get_gemini_pool()
        if pool is None:
            return _heuristic_intent(message)
        response = pool.generate_with_retry(
            model=INTENT_ROUTER_MODEL,
            contents=prompt,
        )
        label = (response.text or "").strip().upper()
        for intent in IntentType:
            if intent.value in label:
                return intent
    except Exception as exc:
        print(f"[IntentRouter] Gemini classification failed: {exc}")

    return _heuristic_intent(message)



def _heuristic_intent(message: str) -> IntentType:
    lowered = message.lower()
    technical = any(term in lowered for term in _TECHNICAL_TERMS)
    personal = any(term in lowered for term in _PERSONAL_TERMS)
    if technical and personal:
        return IntentType.BLENDED
    if technical:
        return IntentType.TECHNICAL
    if personal:
        return IntentType.PERSONAL
    return IntentType.BLENDED
