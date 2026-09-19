from __future__ import annotations
from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    query: str
    client: Any
    bm25_index: Any
    collection: str
    profile: Any  # app.corpus.CorpusProfile; the default corpus when absent
    start_time: float

    cache_result: Any
    chunks: list
    generated: Any
    citation_verdicts: list
    confidence: Any

    final_answer: str
    final_citations: list
    final_confidence: float
    source: str

    cached: bool
    logged: bool
