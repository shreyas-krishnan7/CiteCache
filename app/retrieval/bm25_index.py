
from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient

from app.ingestion.vector_store import scroll_all_points


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class ScoredChunk:
    """A single result from BM25 search."""
    point_id: str
    score: float
    payload: dict


class BM25Index:

    def __init__(self, corpus_tokens: list[list[str]], point_ids: list[str], payloads: list[dict]):
        self._bm25 = BM25Okapi(corpus_tokens)
        self._point_ids = point_ids
        self._payloads = payloads

    def search(self, query: str, top_k: int = 20) -> list[ScoredChunk]:
        tokens = _tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        # Get top_k indices sorted by score descending
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            ScoredChunk(
                point_id=self._point_ids[i],
                score=float(scores[i]),
                payload=self._payloads[i],
            )
            for i in top_indices
            if scores[i] > 0  # skip zero-score results
        ]

    @property
    def corpus_size(self) -> int:
        return len(self._point_ids)


def build_bm25_index(client: QdrantClient, collection: str) -> BM25Index:
    # A collection that was never created is reported the same way as an empty
    # one; otherwise Qdrant's own ValueError escapes, which callers don't
    # expect (a fresh install, or a corpus nothing has been uploaded to yet).
    existing = {c.name for c in client.get_collections().collections}
    points = scroll_all_points(client, collection) if collection in existing else []
    if not points:
        raise RuntimeError(
            f"No points found in collection '{collection}'. "
            f"Did you run 'python -m scripts.ingest --source data/docs --rebuild' first?"
        )

    corpus_tokens = []
    point_ids = []
    payloads = []

    for point in points:
        text = point.payload.get("text", "")
        corpus_tokens.append(_tokenize(text))
        point_ids.append(str(point.id))
        payloads.append(point.payload)

    print(f"Built BM25 index: {len(point_ids)} chunks from '{collection}'")
    return BM25Index(corpus_tokens, point_ids, payloads)
