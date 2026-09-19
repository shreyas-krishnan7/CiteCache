"""
Corpus profiles: one isolated use case served by the shared pipeline.

Each corpus gets its own document collection and its own semantic cache, so
documents and cached answers from one use case can never surface in another,
and carries the retrieval and caching parameters that suit its documents
(long statutes want a deeper rerank cut than short FAQs, for example).

The "default" corpus maps onto the collection names and values in app.config,
so single-corpus usage behaves exactly as before. Any other valid name works
without setup, getting its own collections and the same default parameters.
To tune one, add corpora/<name>.json with just the fields to override:

    {"rerank_top_n": 10, "cache_similarity_threshold": 0.93}

Secrets and infrastructure (API keys, Qdrant location, models) stay in .env;
only per-use-case behaviour belongs in a profile.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields, replace
from pathlib import Path

from app.config import settings

DEFAULT_CORPUS = "default"

# The name becomes part of a Qdrant collection name and a file path, so it is
# restricted to a safe alphabet -- this is what stops "../x" reaching the
# filesystem when the name arrives from an API path parameter.
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
_PROFILE_DIR = Path(__file__).resolve().parent.parent / "corpora"


class InvalidCorpusName(ValueError):
    pass


@dataclass(frozen=True)
class CorpusProfile:
    name: str
    doc_collection: str
    cache_collection: str
    rerank_candidate_pool_size: int
    rerank_top_n: int
    final_top_k: int
    cache_similarity_threshold: float
    cache_write_confidence_threshold: float
    cache_ttl_days: int
    confidence_retrieval_weight: float
    confidence_citation_weight: float
    confidence_completeness_weight: float

    @property
    def confidence_weights(self) -> tuple[float, float, float]:
        return (
            self.confidence_retrieval_weight,
            self.confidence_citation_weight,
            self.confidence_completeness_weight,
        )


def validate_corpus_name(name: str) -> str:
    if not _NAME_RE.match(name or ""):
        raise InvalidCorpusName(
            f"Invalid corpus name {name!r}: use 1-40 lowercase letters, digits, "
            f"'_' or '-', starting with a letter or digit."
        )
    return name


def _defaults_for(name: str) -> CorpusProfile:
    if name == DEFAULT_CORPUS:
        doc_collection, cache_collection = settings.doc_collection, settings.cache_collection
    else:
        doc_collection, cache_collection = f"citecache_{name}_docs", f"citecache_{name}_cache"

    return CorpusProfile(
        name=name,
        doc_collection=doc_collection,
        cache_collection=cache_collection,
        rerank_candidate_pool_size=settings.rerank_candidate_pool_size,
        rerank_top_n=settings.rerank_top_n,
        final_top_k=settings.final_top_k,
        cache_similarity_threshold=settings.cache_similarity_threshold,
        cache_write_confidence_threshold=settings.cache_write_confidence_threshold,
        cache_ttl_days=settings.cache_ttl_days,
        confidence_retrieval_weight=settings.confidence_retrieval_weight,
        confidence_citation_weight=settings.confidence_citation_weight,
        confidence_completeness_weight=settings.confidence_completeness_weight,
    )


def get_profile(name: str = DEFAULT_CORPUS) -> CorpusProfile:
    name = validate_corpus_name(name)
    profile = _defaults_for(name)

    path = _PROFILE_DIR / f"{name}.json"
    if path.exists():
        overrides = json.loads(path.read_text(encoding="utf-8"))
        allowed = {f.name for f in fields(CorpusProfile)} - {"name"}
        unknown = sorted(set(overrides) - allowed)
        if unknown:
            raise ValueError(f"{path.name}: unknown profile field(s) {unknown}; allowed: {sorted(allowed)}")
        profile = replace(profile, **overrides)

    return profile
