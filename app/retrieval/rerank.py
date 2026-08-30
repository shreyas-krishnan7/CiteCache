
from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _cross_encoder_model():
    # Imported lazily, same reasoning as embeddings.py's _local_model():
    # code paths that never rerank (e.g. dense_only_retrieve's CLI
    # comparison script) shouldn't pay this import cost. Shares the
    # sentence-transformers/transformers stack already used by the
    # bi-encoder embedding model, so most of the heavy import cost is
    # already paid by the time this loads.
    from sentence_transformers import CrossEncoder
    return CrossEncoder(settings.rerank_model)


def rerank(query: str, candidates: list, top_n: int | None = None) -> list:
    """
    candidates: list of RetrievedChunk, expected to be a CANDIDATE
    POOL larger than the final desired count (call hybrid_retrieve
    with top_k=settings.rerank_candidate_pool_size to get one).

    Returns the top_n candidates, reordered by cross-encoder score
    (best first). Each returned chunk has .rerank_score set, so it's
    visible downstream (e.g. in a future dashboard) which score
    actually determined the final ranking, not just RRF's.

    If RERANK_ENABLED=false, falls back to a plain truncation of
    whatever order the candidates arrived in -- lets reranking be
    disabled with zero caller changes, e.g. if the cross-encoder
    model can't be downloaded in a given environment.
    """
    top_n = top_n if top_n is not None else settings.rerank_top_n

    if not candidates:
        return []

    if not settings.rerank_enabled:
        return candidates[:top_n]

    model = _cross_encoder_model()
    pairs = [(query, c.text) for c in candidates]
    scores = model.predict(pairs)

    scored = list(zip(candidates, scores))
    scored.sort(key=lambda pair: pair[1], reverse=True)

    results = []
    for chunk, score in scored[:top_n]:
        chunk.rerank_score = float(score)
        results.append(chunk)
    return results
