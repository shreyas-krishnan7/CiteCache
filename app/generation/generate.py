
from __future__ import annotations

from app.config import settings
from app.generation.llm_client import call_structured
from app.generation.prompts import build_generation_prompt
from app.generation.schemas import GeneratedAnswer


def generate_answer(query: str, chunks: list) -> GeneratedAnswer:
    """
    chunks: list of RetrievedChunk from hybrid_retrieve() (or
    dense_only_retrieve() as a degraded fallback).
    """
    if not chunks:
        return GeneratedAnswer(
            answer="I don't have any relevant information to answer that question.",
            citations=[],
            insufficient_context=True,
        )

    system_prompt, user_prompt = build_generation_prompt(query, chunks)
    result = call_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=GeneratedAnswer,
        max_tokens=settings.generation_max_tokens,
    )

    # Defensive check: drop any citation referencing a chunk_id that
    # wasn't actually in the retrieved context. This catches the
    # cheapest class of hallucinated citation (a fabricated ID) before
    # spending an LLM call verifying it in the next node.
    valid_ids = {c.chunk_id for c in chunks}
    filtered_citations = [c for c in result.citations if c.chunk_id in valid_ids]
    dropped = len(result.citations) - len(filtered_citations)
    if dropped:
        print(f"  [generate] dropped {dropped} citation(s) with unrecognized chunk_id")

    return GeneratedAnswer(
        answer=result.answer,
        citations=filtered_citations,
        insufficient_context=result.insufficient_context,
    )
