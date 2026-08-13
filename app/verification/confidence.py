"""
The `score_confidence` node.

Combines three independently-defensible signals into one number:

  retrieval_score        -- the top result's dense cosine similarity
                             (already 0..1, clamped). NOT the RRF
                             score: RRF has no natural upper bound
                             (it's a sum of 1/(k+rank) terms), so it's
                             useful for RANKING but not as a
                             normalized confidence input. Dense cosine
                             similarity is what actually answers "how
                             close was the best match."
  citation_support_rate  -- fraction of citations the verify_citations
                             node marked as supported.
  completeness            -- 1.0 unless the generate node itself said
                             insufficient_context, in which case 0.3.

confidence = 0.4*retrieval_score + 0.4*citation_support_rate + 0.2*completeness

This score is what gates cache_write in a later phase
(cache_write_confidence_threshold, already in config from phase 2) --
low-confidence answers are still served to the user, but never
written to the cache, so a shaky answer can't poison future lookups.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.config import settings
from app.verification.schemas import CitationVerdict
from app.verification.verify_citations import citation_support_rate


class ConfidenceScore(BaseModel):
    retrieval_score: float
    citation_support_rate: float
    completeness: float
    confidence: float
    summary: str  # human-readable, e.g. "3/4 citations supported"


def score_confidence(
    top_chunk,  # RetrievedChunk or None
    citation_verdicts: list[CitationVerdict],
    insufficient_context: bool,
) -> ConfidenceScore:
    retrieval_score = 0.0
    if top_chunk is not None and getattr(top_chunk, "dense_score", None) is not None:
        retrieval_score = max(0.0, min(1.0, top_chunk.dense_score))

    support_rate = citation_support_rate(citation_verdicts)
    completeness = 1.0 if not insufficient_context else 0.3

    confidence = (
        settings.confidence_retrieval_weight * retrieval_score
        + settings.confidence_citation_weight * support_rate
        + settings.confidence_completeness_weight * completeness
    )

    supported = sum(1 for v in citation_verdicts if v.supported)
    total = len(citation_verdicts)
    summary = f"{supported}/{total} citations supported" if total else "no citations"

    return ConfidenceScore(
        retrieval_score=retrieval_score,
        citation_support_rate=support_rate,
        completeness=completeness,
        confidence=confidence,
        summary=summary,
    )
