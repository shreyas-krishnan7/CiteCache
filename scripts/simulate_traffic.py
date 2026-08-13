
from __future__ import annotations

import time
import random

from app.config import settings
from app.ingestion.vector_store import get_client
from app.retrieval.bm25_index import build_bm25_index
from app.cache.semantic_cache import cache_clear
from app.graph.build_graph import build_graph
from app.metrics.tracker import clear_log, summarize

# A realistic-ish mix: some exact repeats (obvious cache wins),
# some paraphrases (tests whether the cache generalizes semantically),
# and the out-of-corpus query repeated too (should never get cached).
TRAFFIC = [
    "How do I reset my password?",
    "What is the API rate limit?",
    "How does SSO login work for enterprise accounts?",
    "How do I reset my password?",                          # exact repeat
    "Can I get a refund after 30 days?",
    "I forgot my password, how do I reset it?",              # paraphrase
    "How do I reset my password?",                          # exact repeat again
    "How do I export my account data as a CSV file?",        # out-of-corpus
    "What is the API rate limit?",                           # exact repeat
    "How does enterprise SSO work?",                          # paraphrase
    "Can I get a refund after 30 days?",                      # exact repeat
    "How do I export my account data as a CSV file?",         # out-of-corpus repeat
]


def main() -> None:
    if settings.llm_provider == "openai" and not settings.openai_api_key:
        raise SystemExit("LLM_PROVIDER=openai but OPENAI_API_KEY is not set in .env")
    if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        raise SystemExit("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set in .env")
    if settings.llm_provider == "groq" and not settings.groq_api_key:
        raise SystemExit("LLM_PROVIDER=groq but GROQ_API_KEY is not set in .env")
    if settings.llm_provider == "gemini" and not settings.gemini_api_key:
        raise SystemExit("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set in .env")

    client = get_client()
    print("Clearing cache + metrics log for a clean simulation run...")
    cache_clear(client)
    clear_log()

    print("Building BM25 index...")
    bm25 = build_bm25_index(client, settings.doc_collection)
    graph = build_graph()

    print(f"\nRunning {len(TRAFFIC)} queries through the graph...\n")
    for i, query in enumerate(TRAFFIC, start=1):
        start = time.perf_counter()
        result = graph.invoke({
            "query": query,
            "client": client,
            "bm25_index": bm25,
            "collection": settings.doc_collection,
            "start_time": start,
        })
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  [{i:2d}] {elapsed_ms:7.1f}ms  source={result['source']:<10}  "
              f"confidence={result.get('final_confidence', 0):.2f}  query={query!r}")

    stats = summarize()
    print(f"\n{'='*70}")
    print("CACHE PERFORMANCE SUMMARY")
    print(f"{'='*70}")
    print(f"  Total queries:              {stats['total_queries']}")
    print(f"  Cache hits:                 {stats['cache_hits']}")
    print(f"  Cache misses:               {stats['cache_misses']}")
    print(f"  Cache hit rate:             {stats['cache_hit_rate']*100:.1f}%")
    if stats["avg_latency_hit_ms"] is not None:
        print(f"  Avg latency (cache hit):    {stats['avg_latency_hit_ms']:.1f}ms")
    if stats["avg_latency_miss_ms"] is not None:
        print(f"  Avg latency (cache miss):   {stats['avg_latency_miss_ms']:.1f}ms")
    if stats["latency_reduction_pct"] is not None:
        print(f"  Latency reduction on hit:   {stats['latency_reduction_pct']:.1f}%")
    print(f"  Cache writes:               {stats['cache_writes']}")
    print(f"  Writes rejected (low conf): {stats['cache_write_rejections_low_confidence']}")
    if stats["avg_confidence"] is not None:
        print(f"  Avg confidence:             {stats['avg_confidence']:.3f}")
    print(f"\nRaw log: {settings.metrics_log_path}")


if __name__ == "__main__":
    main()
