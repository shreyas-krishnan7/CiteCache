"""
Document ingestion in two steps, so the API can report progress as it goes:

    prepare_document  extract text + chunk        (fast)
    index_chunks      embed in batches + upsert   (slow part; reports per batch)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue

from app.config import settings
from app.corpus import CorpusProfile
from app.ingestion.chunking import Chunk, chunk_document
from app.ingestion.embeddings import embed_texts
from app.ingestion.extractors import extract_text
from app.ingestion.vector_store import ensure_collection, upsert_chunks

EMBED_BATCH_SIZE = 16

_DOC_TYPE_HINTS = {
    "password": "account_security", "sso": "account_security", "two_factor": "account_security",
    "refund": "billing", "billing": "billing", "subscription": "billing",
    "api": "developer", "webhook": "developer", "data_export": "data",
    "account_deletion": "account_management", "team_seat": "account_management",
}
# future improvment use an llm classifier


def guess_doc_type(filename: str) -> str:
    lower = filename.lower()
    for hint, doc_type in _DOC_TYPE_HINTS.items():
        if hint in lower:
            return doc_type
    return "general"


def prepare_document(filename: str, raw: bytes) -> list[Chunk]:
    """Raises ValueError for unsupported or empty files."""
    text = extract_text(filename, raw)
    uploaded_at = datetime.now(timezone.utc).isoformat()
    chunks = chunk_document(
        markdown_text=text,
        source=filename.rsplit(".", 1)[0],
        doc_type=guess_doc_type(filename),
        last_updated=uploaded_at,
        max_chunk_tokens=settings.chunk_size_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    for c in chunks:
        c.metadata.update({"filename": filename, "uploaded_at": uploaded_at})
    return chunks


def index_chunks(client, profile: CorpusProfile, chunks: list[Chunk],
                 on_batch: Callable[[int, int], None] | None = None) -> None:
    """Embed and store `chunks`, replacing any earlier upload of the same document."""
    if not chunks:
        return
    vectors: list[list[float]] = []
    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[start:start + EMBED_BATCH_SIZE]
        vectors.extend(embed_texts([c.text for c in batch]))
        if on_batch:
            on_batch(len(vectors), len(chunks))

    ensure_collection(client, profile.doc_collection, len(vectors[0]))
    # Re-uploading a file replaces its chunks instead of duplicating them.
    client.delete(
        collection_name=profile.doc_collection,
        points_selector=FilterSelector(filter=Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=chunks[0].source))])),
    )
    upsert_chunks(client, profile.doc_collection, chunks, vectors)
