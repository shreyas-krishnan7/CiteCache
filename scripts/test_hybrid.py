
from __future__ import annotations

import time

from app.config import settings
from app.ingestion.vector_store import get_client
from app.retrieval.bm25_index import build_bm25_index
from app.retrieval.hybrid import dense_only_retrieve, hybrid_retrieve

SAMPLE_QUERIES = [
    "How do I reset my password?",
    "What is the API rate limit?",
    "How does SSO login work for enterprise accounts?",
    "Can I get a refund after 30 days?",
    "How do I set up two-factor authentication?",
    "API error code 429 too many requests",   # keyword-heavy, BM25 should shine
    "delete my account and all data",         # tests account_deletion doc retrieval
    "billing cycle monthly annual upgrade",   # tests billing FAQ retrieval
]


def _print_results(label: str, results, elapsed_ms: float) -> None:
    print(f"\n  [{label}] ({elapsed_ms:.0f}ms)")
    if not results:
        print("    (no results)")
        return
    for i, r in enumerate(results, 1):
        dense = f"dense={r.dense_score:.3f}" if r.dense_score is not None else "dense=N/A"
        sparse = f"sparse={r.sparse_score:.2f}" if r.sparse_score is not None else "sparse=N/A"
        rrf = f"rrf={r.rrf_score:.4f}" if r.rrf_score > 0 else ""
        scores = f"{dense}  {sparse}  {rrf}".strip()
        print(f"    {i}. source={r.source}  heading={r.section_heading!r}  {scores}")


def main() -> None:
    client = get_client()

    print("Building BM25 index from Qdrant doc collection...")
    bm25_index = build_bm25_index(client, settings.doc_collection)

    for query in SAMPLE_QUERIES:
        print(f"\n{'='*70}")
        print(f"Query: {query}")

        # Dense-only
        t0 = time.perf_counter()
        dense_results = dense_only_retrieve(query, client, settings.doc_collection, top_k=5)
        dense_ms = (time.perf_counter() - t0) * 1000

        # Hybrid (dense + BM25 + RRF)
        t0 = time.perf_counter()
        hybrid_results = hybrid_retrieve(query, client, settings.doc_collection, bm25_index, top_k=5)
        hybrid_ms = (time.perf_counter() - t0) * 1000

        _print_results("Dense Only", dense_results, dense_ms)
        _print_results("Hybrid RRF", hybrid_results, hybrid_ms)

    print(f"\n{'='*70}")
    print("Done. Compare the top sources — hybrid should match or beat dense")
    print("on all queries, and notably improve on keyword-heavy ones.")


if __name__ == "__main__":
    main()
