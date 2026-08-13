"""
The `verify_citations` node.

Two stages, run per-citation (not batched):

  Stage A -- embedding pre-filter (no LLM call): cosine similarity
  between the claim text and the cited chunk's text. Below
  citation_prefilter_threshold, the citation is rejected outright as
  an obvious miscite -- this catches the cheap case (wrong chunk
  entirely) without spending an LLM call on it.

  Stage B -- LLM-as-judge, for everything that passes stage A: does
  the source text actually entail the claim? This is what a
  similarity score alone can't tell you -- two sentences can be
  topically related (high cosine similarity) while one directly
  contradicts or doesn't actually support the other.

Why per-citation, not one LLM call for the whole answer's citations:
batching lets a weak citation ride on the coattails of strong ones in
the same response -- the model tends to give an overall "looks fine"
verdict rather than scrutinizing each claim independently. One call
per citation costs more but is the only way to get an independent
judgment on each one.
"""
from __future__ import annotations

import math

from app.config import settings
from app.generation.llm_client import call_structured
from app.generation.schemas import Citation
from app.ingestion.embeddings import embed_text
from app.verification.schemas import CitationVerdict, _LLMJudgeVerdict

_JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. Given a SOURCE TEXT \
and a CLAIM, decide whether the source text actually supports the claim.

Answer strictly based on what the source text states -- not on whether the \
claim seems reasonable or true in general. If the source text is silent on \
part of the claim, or only loosely related, mark it as NOT supported.

Respond as JSON matching this schema:
{"supported": <true or false>, "reasoning": "<one sentence>"}"""


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _llm_judge(claim: str, source_text: str) -> _LLMJudgeVerdict:
    user_prompt = f"SOURCE TEXT: {source_text}\n\nCLAIM: {claim}"
    return call_structured(
        system_prompt=_JUDGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=_LLMJudgeVerdict,
        max_tokens=settings.verification_max_tokens,
    )


def verify_citations(citations: list[Citation], chunks_by_id: dict) -> list[CitationVerdict]:
    """
    chunks_by_id: {chunk_id: RetrievedChunk}, built by the caller from
    the same chunks passed to generate_answer(). Citations referencing
    a chunk_id not in this dict have already been filtered out by
    generate_answer()'s defensive check, but we handle it defensively
    here too in case this is called independently.
    """
    verdicts: list[CitationVerdict] = []

    for citation in citations:
        chunk = chunks_by_id.get(citation.chunk_id)
        if chunk is None:
            verdicts.append(CitationVerdict(
                chunk_id=citation.chunk_id,
                claim=citation.claim,
                supported=False,
                reasoning="Cited chunk_id was not among the retrieved chunks.",
                method="id_check",
            ))
            continue

        claim_vec = embed_text(citation.claim)
        chunk_vec = embed_text(chunk.text)
        similarity = _cosine_similarity(claim_vec, chunk_vec)

        if similarity < settings.citation_prefilter_threshold:
            verdicts.append(CitationVerdict(
                chunk_id=citation.chunk_id,
                claim=citation.claim,
                supported=False,
                reasoning=f"Embedding similarity ({similarity:.2f}) below prefilter threshold "
                          f"({settings.citation_prefilter_threshold}) -- claim doesn't appear related to this chunk.",
                method="embedding_prefilter",
            ))
            continue

        judged = _llm_judge(citation.claim, chunk.text)
        verdicts.append(CitationVerdict(
            chunk_id=citation.chunk_id,
            claim=citation.claim,
            supported=judged.supported,
            reasoning=judged.reasoning,
            method="llm_judge",
        ))

    return verdicts


def citation_support_rate(verdicts: list[CitationVerdict]) -> float:
    if not verdicts:
        return 0.0
    supported = sum(1 for v in verdicts if v.supported)
    return supported / len(verdicts)
