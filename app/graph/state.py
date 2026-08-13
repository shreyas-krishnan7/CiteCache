
from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    # --- input ---
    query: str
    client: Any          # QdrantClient
    bm25_index: Any       # BM25Index
    collection: str
    start_time: float      # time.perf_counter() at invoke -- set by the caller, read by log_metrics

    # --- cache_lookup ---
    cache_result: Any      # CacheLookupResult

    # --- hybrid_retrieve ---
    chunks: list

    # --- generate ---
    generated: Any          # GeneratedAnswer

    # --- verify_citations ---
    citation_verdicts: list

    # --- score_confidence ---
    confidence: Any          # ConfidenceScore

    # --- final output (written by either serve_cached or score_confidence) ---
    final_answer: str
    final_citations: list
    final_confidence: float
    source: str               # "cache" or "generated"

    # --- cache_write ---
    cached: bool

    # --- log_metrics ---
    logged: bool
