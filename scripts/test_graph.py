
from __future__ import annotations

from app.config import settings
from app.ingestion.vector_store import get_client
from app.retrieval.bm25_index import build_bm25_index
from app.cache.semantic_cache import cache_clear
from app.graph.build_graph import build_graph

QUERY = "How do I reset my password?"


def _print_result(label: str, state: dict) -> None:
    print(f"\n  [{label}]")
    print(f"    source: {state.get('source')}")
    print(f"    final_answer: {state.get('final_answer')}")
    print(f"    final_confidence: {state.get('final_confidence')}")
    if "cached" in state:
        print(f"    cached (this run): {state['cached']}")


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

    print("Clearing cache collection (so this test starts from a known MISS state --")
    print("otherwise leftover entries from test_cache.py or earlier test_graph.py runs")
    print("would make Run 1 a HIT, since Qdrant embedded mode persists across runs)...")
    cache_clear(client)

    print("Building BM25 index...")
    bm25 = build_bm25_index(client, settings.doc_collection)
    graph = build_graph()

    base_input = {
        "query": QUERY,
        "client": client,
        "bm25_index": bm25,
        "collection": settings.doc_collection,
    }

    print(f"\n{'='*70}")
    print(f"Run 1: {QUERY!r} (expect cache MISS -> full pipeline)")
    result_1 = graph.invoke(base_input)
    _print_result("Run 1", result_1)
    assert result_1["source"] == "generated", "Expected a cache MISS on the first run!"

    print(f"\n{'='*70}")
    print(f"Run 2: same query again (expect cache HIT -> serve_cached, no LLM call)")
    result_2 = graph.invoke(base_input)
    _print_result("Run 2", result_2)

    if result_2["source"] == "cache":
        print("\nPASS: second run served from cache -- retrieval and generation were skipped entirely.")
    else:
        print("\nNOTE: second run did NOT hit cache. Either confidence on run 1 was below "
              f"cache_write_confidence_threshold={settings.cache_write_confidence_threshold} "
              "(check the 'cached' flag on Run 1 above), or cache_similarity_threshold "
              f"={settings.cache_similarity_threshold} is stricter than this exact-repeat query needs.")


if __name__ == "__main__":
    main()
