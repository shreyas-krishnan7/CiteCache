"""
Qdrant-backed semantic cache for CiteCache.

Uses a separate Qdrant collection ("citecache_cache") to store
verified Q&A pairs keyed by their query embedding.  This is one of
the two cache strategies from the original design doc (the other
being Redis + cosine similarity).  Using Qdrant for both the doc
store and the cache means zero additional infrastructure in dev —
when you add Docker later, swapping in Redis is a one-file change.

Cache lifecycle:
  1. cache_lookup(query) → embed query, search cache collection.
     If top hit score ≥ threshold → HIT, return cached answer.
  2. cache_write(query, answer, metadata) → embed query, upsert into
     cache collection with the answer + metadata as payload.

Why a separate collection instead of a metadata filter on the doc
collection?  See vector_store.py docstring — TL;DR: keeps cache
lookups fast, prevents a cached Q&A from polluting retrieval.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from app.config import settings
from app.ingestion.embeddings import embed_text
from app.ingestion.vector_store import ensure_collection, search_vectors


@dataclass
class CacheHit:
    """Returned when the cache finds a match above the threshold."""
    query: str
    answer: str
    confidence: float
    similarity_score: float
    cached_at: str
    source_chunks: list[str]


@dataclass
class CacheLookupResult:
    """Result of a cache lookup — either a hit or a miss."""
    is_hit: bool
    hit: CacheHit | None = None
    best_score: float = 0.0


def cache_lookup(
    query: str,
    client: QdrantClient,
    threshold: float | None = None,
) -> CacheLookupResult:
    """
    Check the semantic cache for a similar enough previous answer.

    Embeds the query, searches the cache collection, and returns a
    hit if the best match exceeds the similarity threshold AND has
    not expired (cached_at + ttl_days > now).
    """
    _threshold = threshold if threshold is not None else settings.cache_similarity_threshold
    query_vector = embed_text(query)

    # Make sure collection exists (first run may not have it yet)
    ensure_collection(client, settings.cache_collection, len(query_vector))

    results = search_vectors(client, settings.cache_collection, query_vector, limit=1)

    if not results:
        return CacheLookupResult(is_hit=False, best_score=0.0)

    best = results[0]
    score = best.score

    if score >= _threshold:
        payload = best.payload

        cached_at_str = payload.get("cached_at", "")
        ttl_days = payload.get("ttl_days", settings.cache_ttl_days)
        if cached_at_str:
            cached_at = datetime.fromisoformat(cached_at_str)
            age = datetime.now(timezone.utc) - cached_at
            if age > timedelta(days=ttl_days):
                # Expired: treat as a miss and clean up the stale entry
                # so it doesn't keep costing a similarity search hit.
                client.delete(collection_name=settings.cache_collection, points_selector=[best.id])
                return CacheLookupResult(is_hit=False, best_score=score)

        return CacheLookupResult(
            is_hit=True,
            best_score=score,
            hit=CacheHit(
                query=payload.get("query", ""),
                answer=payload.get("answer", ""),
                confidence=payload.get("confidence", 0.0),
                similarity_score=score,
                cached_at=payload.get("cached_at", ""),
                source_chunks=payload.get("source_chunks", []),
            ),
        )

    return CacheLookupResult(is_hit=False, best_score=score)


def cache_write(
    query: str,
    answer: str,
    client: QdrantClient,
    confidence: float = 1.0,
    source_chunks: list[str] | None = None,
) -> str:
    """
    Write a verified answer into the semantic cache.

    Returns the point ID of the cached entry.
    """
    query_vector = embed_text(query)
    ensure_collection(client, settings.cache_collection, len(query_vector))

    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=settings.cache_collection,
        points=[
            PointStruct(
                id=point_id,
                vector=query_vector,
                payload={
                    "query": query,
                    "answer": answer,
                    "confidence": confidence,
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "source_chunks": source_chunks or [],
                    "ttl_days": settings.cache_ttl_days,
                },
            )
        ],
    )
    return point_id


def cache_clear(client: QdrantClient) -> None:
    """Drop and recreate the cache collection. Useful for testing."""
    try:
        client.delete_collection(settings.cache_collection)
    except Exception:
        pass
