
from __future__ import annotations

import time

from app.config import settings
from app.cache.semantic_cache import cache_lookup, cache_write
from app.retrieval.hybrid import hybrid_retrieve
from app.generation.generate import generate_answer
from app.verification.verify_citations import verify_citations
from app.verification.confidence import score_confidence as _score_confidence
from app.metrics.tracker import log_event
from app.graph.state import GraphState


def cache_lookup_node(state: GraphState) -> dict:
    result = cache_lookup(state["query"], state["client"])
    return {"cache_result": result}


def route_after_cache_lookup(state: GraphState) -> str:
    """Conditional edge: cache hit -> serve_cached, miss -> continue the pipeline."""
    return "serve_cached" if state["cache_result"].is_hit else "hybrid_retrieve"


def serve_cached_node(state: GraphState) -> dict:
    hit = state["cache_result"].hit
    return {
        "final_answer": hit.answer,
        "final_citations": hit.source_chunks,
        "final_confidence": hit.confidence,
        "source": "cache",
    }


def hybrid_retrieve_node(state: GraphState) -> dict:
    chunks = hybrid_retrieve(
        state["query"], state["client"], state["collection"], state["bm25_index"]
    )
    return {"chunks": chunks}


def generate_node(state: GraphState) -> dict:
    generated = generate_answer(state["query"], state["chunks"])
    return {"generated": generated}


def verify_citations_node(state: GraphState) -> dict:
    chunks_by_id = {c.chunk_id: c for c in state["chunks"]}
    verdicts = verify_citations(state["generated"].citations, chunks_by_id)
    return {"citation_verdicts": verdicts}


def score_confidence_node(state: GraphState) -> dict:
    chunks = state["chunks"]
    top_chunk = chunks[0] if chunks else None
    generated = state["generated"]
    score = _score_confidence(top_chunk, state["citation_verdicts"], generated.insufficient_context)
    return {
        "confidence": score,
        "final_answer": generated.answer,
        "final_citations": [c.chunk_id for c in generated.citations],
        "final_confidence": score.confidence,
        "source": "generated",
    }


def cache_write_node(state: GraphState) -> dict:
    """
    The confidence gate lives here, not inside cache_write() itself --
    cache_write() stays a dumb, testable key-value-by-similarity store
    (per its own docstring from phase 2); the decision of WHEN to call
    it is orchestration logic, which belongs in the graph.
    """
    score = state["confidence"]
    if score.confidence >= settings.cache_write_confidence_threshold:
        cache_write(
            query=state["query"],
            answer=state["final_answer"],
            client=state["client"],
            confidence=score.confidence,
            source_chunks=state["final_citations"],
        )
        return {"cached": True}
    return {"cached": False}


def log_metrics_node(state: GraphState) -> dict:
    """
    Final node on both branches (serve_cached and cache_write both
    lead here before END). Times the whole run using start_time set
    by the caller at invoke(), and logs one line to the metrics JSONL
    -- this is what scripts/simulate_traffic.py reads back to compute
    cache hit rate and latency reduction.
    """
    start = state.get("start_time")
    latency_ms = (time.perf_counter() - start) * 1000 if start is not None else None
    log_event(
        query=state["query"],
        source=state["source"],
        confidence=state.get("final_confidence"),
        latency_ms=latency_ms,
        cached_this_run=state.get("cached"),  # True/False on generated branch, None on cache-hit branch
    )
    return {"logged": True}
