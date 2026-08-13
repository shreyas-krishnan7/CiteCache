
from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import QdrantClient

from app.config import settings
from app.ingestion.embeddings import embed_text
from app.ingestion.vector_store import search_vectors
from app.retrieval.bm25_index import BM25Index


@dataclass
class RetrievedChunk:
    """A single result after hybrid retrieval + RRF fusion."""
    chunk_id: str
    text: str
    source: str
    section_heading: str
    dense_score: float | None
    sparse_score: float | None
    rrf_score: float


def _reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> dict[str, float]:
    """
    Compute RRF scores for document IDs across multiple ranked lists.

    Args:
        ranked_lists: Each inner list is an ordered sequence of
                      document IDs (best first).
        k: Damping constant (default 60, standard in literature).

    Returns:
        Dict mapping doc_id → RRF score.
    """
    rrf_scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return rrf_scores


def hybrid_retrieve(
    query: str,
    client: QdrantClient,
    collection: str,
    bm25_index: BM25Index,
    top_k: int | None = None,
    hybrid_top_k: int | None = None,
) -> list[RetrievedChunk]:
    """
    Run hybrid retrieval (dense + sparse) with RRF fusion.

    1. Dense: embed query → Qdrant vector search → top hybrid_top_k
    2. Sparse: tokenize query → BM25 search → top hybrid_top_k
    3. Fuse with RRF → return top final_top_k results
    """
    _hybrid_top_k = hybrid_top_k or settings.hybrid_top_k
    _final_top_k = top_k or settings.final_top_k

    # --- Dense retrieval ---
    query_vector = embed_text(query)
    dense_results = search_vectors(client, collection, query_vector, limit=_hybrid_top_k)
    dense_ids = [str(r.id) for r in dense_results]
    dense_scores = {str(r.id): r.score for r in dense_results}
    dense_payloads = {str(r.id): r.payload for r in dense_results}

    # --- Sparse retrieval ---
    sparse_results = bm25_index.search(query, top_k=_hybrid_top_k)
    sparse_ids = [r.point_id for r in sparse_results]
    sparse_scores = {r.point_id: r.score for r in sparse_results}
    sparse_payloads = {r.point_id: r.payload for r in sparse_results}

    # --- RRF fusion ---
    rrf_scores = _reciprocal_rank_fusion(
        ranked_lists=[dense_ids, sparse_ids],
        k=settings.rrf_k,
    )

    # Merge payloads from both retrievers (dense takes priority if both have it)
    all_payloads: dict[str, dict] = {}
    all_payloads.update(sparse_payloads)
    all_payloads.update(dense_payloads)

    # Sort by RRF score descending, take top_k
    sorted_ids = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)[:_final_top_k]

    results = []
    for doc_id in sorted_ids:
        payload = all_payloads.get(doc_id, {})
        results.append(
            RetrievedChunk(
                chunk_id=doc_id,
                text=payload.get("text", ""),
                source=payload.get("source", ""),
                section_heading=payload.get("section_heading", ""),
                dense_score=dense_scores.get(doc_id),
                sparse_score=sparse_scores.get(doc_id),
                rrf_score=rrf_scores[doc_id],
            )
        )

    return results


def dense_only_retrieve(
    query: str,
    client: QdrantClient,
    collection: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """
    Dense-only retrieval (no BM25, no RRF).
    Used as the baseline for Phase 2 comparison.
    """
    _top_k = top_k or settings.final_top_k
    query_vector = embed_text(query)
    results = search_vectors(client, collection, query_vector, limit=_top_k)

    return [
        RetrievedChunk(
            chunk_id=str(r.id),
            text=r.payload.get("text", ""),
            source=r.payload.get("source", ""),
            section_heading=r.payload.get("section_heading", ""),
            dense_score=r.score,
            sparse_score=None,
            rrf_score=0.0,
        )
        for r in results
    ]
