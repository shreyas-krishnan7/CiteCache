
from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    """
    Returns a singleton Qdrant client.

    Embedded mode stores data in a local directory (no server needed).
    Server mode connects to a running Qdrant instance.  The mode is
    selected via the QDRANT_MODE environment variable.
    """
    if settings.qdrant_mode == "embedded":
        return QdrantClient(path=settings.qdrant_data_path)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if name in existing:
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def upsert_chunks(client: QdrantClient, collection: str, chunks, embeddings: list[list[float]]) -> None:
    points = [
        PointStruct(
            id=chunk.chunk_id,
            vector=embedding,
            payload={
                "text": chunk.text,
                "source": chunk.source,
                "section_heading": chunk.section_heading,
                "strategy": chunk.strategy,
                "doc_type": chunk.doc_type,
                "last_updated": chunk.last_updated,
                "chunk_index": chunk.chunk_index,
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    client.upsert(collection_name=collection, points=points)


def search_vectors(
    client: QdrantClient,
    collection: str,
    query_vector: list[float],
    limit: int = 5,
):
    """Dense vector search — returns scored points."""
    return client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=limit,
    ).points


def scroll_all_points(client: QdrantClient, collection: str):
    """
    Retrieve every point from a collection using scroll pagination.

    This is used by the BM25 index builder to read all chunk texts
    without knowing their IDs upfront. For a demo corpus of ~33
    chunks this is perfectly fine; a production system would build
    the BM25 index at ingest time instead.
    """
    all_points = []
    offset = None
    while True:
        results, next_offset = client.scroll(
            collection_name=collection,
            limit=100,
            offset=offset,
            with_vectors=False,
            with_payload=True,
        )
        all_points.extend(results)
        if next_offset is None:
            break
        offset = next_offset
    return all_points
