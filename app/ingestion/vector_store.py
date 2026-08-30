
from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
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


def search_vectors(client: QdrantClient, collection: str, query_vector: list[float], limit: int = 5):
    """Dense vector search — returns scored points."""
    return client.query_points(collection_name=collection, query=query_vector, limit=limit).points


def scroll_all_points(client: QdrantClient, collection: str):
    all_points = []
    offset = None
    while True:
        results, next_offset = client.scroll(
            collection_name=collection, limit=100, offset=offset, with_vectors=False, with_payload=True,
        )
        all_points.extend(results)
        if next_offset is None:
            break
        offset = next_offset
    return all_points


def clear_collection(client: QdrantClient, collection: str) -> int:
    """
    Removes every point from a collection, WITHOUT dropping the
    collection itself. Returns the number of points deleted.

    Deliberately point-level, not delete_collection(): on Windows,
    embedded (on-disk) Qdrant's delete_collection() can silently fail
    to release its file handles, leaving the folder (and its stale
    data) intact even though no exception is raised. The next
    ensure_collection() call then reopens that same stale folder,
    and new data gets upserted ON TOP of the old data instead of
    replacing it -- this is exactly what caused the doc collection to
    balloon from 33 to 135 chunks across repeated `ingest --rebuild`
    runs. Deleting points individually never touches the collection's
    folder structure, so it doesn't hit that failure mode.
    """
    existing = [c.name for c in client.get_collections().collections]
    if collection not in existing:
        return 0

    point_ids = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection, limit=256, offset=offset, with_payload=False, with_vectors=False,
        )
        point_ids.extend(p.id for p in points)
        if offset is None:
            break

    if point_ids:
        client.delete(collection_name=collection, points_selector=point_ids)
    return len(point_ids)
