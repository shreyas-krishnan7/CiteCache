
from __future__ import annotations

import math

from app.config import settings
from app.generation.llm_client import call_structured
from app.generation.schemas import Citation
from app.ingestion.embeddings import embed_text
from app.verification.schemas import CitationVerdict, _LLMJudgeVerdict, _BatchJudgeResponse

_BATCH_JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. You will be given a \
numbered list of CLAIM / SOURCE TEXT pairs. For each pair, decide whether the \
source text actually supports the claim.

Evaluate each pair completely independently -- your judgment on one pair must \
NOT be influenced by any other pair in the list. Answer strictly based on what \
each source text states, not on whether the claim seems reasonable in general. \
If a source text is silent on part of a claim, or only loosely related, mark \
that pair as NOT supported.

Respond as JSON matching this schema:
{
  "verdicts": [
    {"index": <int, matching the pair number below>, "supported": <true or false>, "reasoning": "<one sentence>"}
  ]
}
There must be exactly one verdict per pair, each with the correct index."""


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _batch_llm_judge(pairs: list[tuple[str, str]]) -> list[_LLMJudgeVerdict]:
    """
    pairs: list of (claim, source_text). Returns verdicts in the SAME
    order as pairs -- callers zip() the result back against their own
    position list, so order must be preserved even if the model
    returns indices out of order (handled via a dict lookup, not by
    trusting response order directly).
    """
    if not pairs:
        return []

    lines = [f"[{i}]\nSOURCE TEXT: {text}\nCLAIM: {claim}" for i, (claim, text) in enumerate(pairs)]
    user_prompt = "\n\n".join(lines)

    # Token budget scales with batch size -- a single citation and a
    # ten-citation answer both need to fit their full set of verdicts.
    max_tokens = settings.verification_max_tokens * max(1, len(pairs))

    response: _BatchJudgeResponse = call_structured(
        system_prompt=_BATCH_JUDGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=_BatchJudgeResponse,
        max_tokens=max_tokens,
    )

    verdict_by_index = {v.index: v for v in response.verdicts}
    results = []
    for i in range(len(pairs)):
        v = verdict_by_index.get(i)
        if v is None:
            # Model returned fewer verdicts than pairs, or misnumbered one.
            # Fail closed (unsupported) rather than silently misaligning
            # verdicts to the wrong citations.
            results.append(_LLMJudgeVerdict(
                supported=False,
                reasoning="Batch verification response did not include a verdict for this citation.",
            ))
        else:
            results.append(_LLMJudgeVerdict(supported=v.supported, reasoning=v.reasoning))
    return results


def verify_citations(citations: list[Citation], chunks_by_id: dict) -> list[CitationVerdict]:
    """
    chunks_by_id: {chunk_id: RetrievedChunk}, built by the caller from
    the same chunks passed to generate_answer().
    """
    verdicts: list[CitationVerdict | None] = [None] * len(citations)
    pending_pairs: list[tuple[str, str]] = []          # (claim, source_text) for stage B
    pending_positions: list[tuple[int, str, str]] = []  # (position, chunk_id, claim)

    for pos, citation in enumerate(citations):
        chunk = chunks_by_id.get(citation.chunk_id)
        if chunk is None:
            verdicts[pos] = CitationVerdict(
                chunk_id=citation.chunk_id,
                claim=citation.claim,
                supported=False,
                reasoning="Cited chunk_id was not among the retrieved chunks.",
                method="id_check",
            )
            continue

        claim_vec = embed_text(citation.claim)
        chunk_vec = embed_text(chunk.text)
        similarity = _cosine_similarity(claim_vec, chunk_vec)

        if similarity < settings.citation_prefilter_threshold:
            verdicts[pos] = CitationVerdict(
                chunk_id=citation.chunk_id,
                claim=citation.claim,
                supported=False,
                reasoning=f"Embedding similarity ({similarity:.2f}) below prefilter threshold "
                          f"({settings.citation_prefilter_threshold}) -- claim doesn't appear related to this chunk.",
                method="embedding_prefilter",
            )
            continue

        pending_pairs.append((citation.claim, chunk.text))
        pending_positions.append((pos, citation.chunk_id, citation.claim))

    if pending_pairs:
        judged = _batch_llm_judge(pending_pairs)
        for (pos, chunk_id, claim), result in zip(pending_positions, judged):
            verdicts[pos] = CitationVerdict(
                chunk_id=chunk_id,
                claim=claim,
                supported=result.supported,
                reasoning=result.reasoning,
                method="llm_judge_batched",
            )

    return verdicts  # type: ignore[return-value]  -- every position is filled by this point


def citation_support_rate(verdicts: list[CitationVerdict]) -> float:
    if not verdicts:
        return 0.0
    supported = sum(1 for v in verdicts if v.supported)
    return supported / len(verdicts)
