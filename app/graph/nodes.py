"""
Graph nodes. Thin wrappers around plain, independently-tested
functions -- no business logic lives here.

Per-corpus parameters (collections, rerank depth, cache thresholds,
confidence weights) come from the CorpusProfile in the state rather than
from global settings, so one compiled graph serves every corpus.
"""
from __future__ import annotations

import time

from app.config import settings
from app.corpus import CorpusProfile, get_profile
from app.cache.semantic_cache import cache_lookup, cache_write
from app.retrieval.hybrid import hybrid_retrieve
from app.retrieval.rerank import rerank
from app.generation.generate import generate_answer
from app.verification.verify_citations import verify_citations
from app.verification.confidence import score_confidence as _score_confidence
from app.metrics.tracker import log_event
from app.graph.state import GraphState


def _profile(state: GraphState) -> CorpusProfile:
    return state.get("profile") or get_profile()


def cache_lookup_node(state: GraphState) -> dict:
    profile = _profile(state)
    result = cache_lookup(
        state["query"], state["client"],
        threshold=profile.cache_similarity_threshold,
        collection=profile.cache_collection,
    )
    return {"cache_result": result}


def route_after_cache_lookup(state: GraphState) -> str:
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
    profile = _profile(state)
    pool_size = profile.rerank_candidate_pool_size if settings.rerank_enabled else profile.final_top_k
    chunks = hybrid_retrieve(
        state["query"], state["client"], state.get("collection") or profile.doc_collection,
        state["bm25_index"], top_k=pool_size,
    )
    return {"chunks": chunks}


def rerank_node(state: GraphState) -> dict:
    reranked = rerank(state["query"], state["chunks"], top_n=_profile(state).rerank_top_n)
    return {"chunks": reranked}


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
    score = _score_confidence(
        top_chunk, state["citation_verdicts"], generated.insufficient_context,
        weights=_profile(state).confidence_weights,
    )
    return {
        "confidence": score,
        "final_answer": generated.answer,
        "final_citations": [c.chunk_id for c in generated.citations],
        "final_confidence": score.confidence,
        "source": "generated",
    }


def cache_write_node(state: GraphState) -> dict:
    profile = _profile(state)
    score = state["confidence"]
    if score.confidence >= profile.cache_write_confidence_threshold:
        cache_write(
            query=state["query"], answer=state["final_answer"], client=state["client"],
            confidence=score.confidence, source_chunks=state["final_citations"],
            collection=profile.cache_collection, ttl_days=profile.cache_ttl_days,
        )
        return {"cached": True}
    return {"cached": False}


def log_metrics_node(state: GraphState) -> dict:
    start = state.get("start_time")
    latency_ms = (time.perf_counter() - start) * 1000 if start is not None else None
    log_event(
        query=state["query"], source=state["source"], confidence=state.get("final_confidence"),
        latency_ms=latency_ms, cached_this_run=state.get("cached"),
    )
    return {"logged": True}
