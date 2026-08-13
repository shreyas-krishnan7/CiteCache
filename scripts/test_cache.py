
from __future__ import annotations

import time

from app.config import settings
from app.ingestion.vector_store import get_client
from app.cache.semantic_cache import cache_clear, cache_lookup, cache_write

# We'll use a lower threshold for this test so near-matches are visible
TEST_THRESHOLD = 0.90


def _print_lookup(label: str, result, elapsed_ms: float) -> None:
    status = "HIT ✓" if result.is_hit else "MISS ✗"
    print(f"\n  [{label}] {status}  (best_score={result.best_score:.4f}, {elapsed_ms:.0f}ms)")
    if result.is_hit and result.hit:
        print(f"    Cached answer: {result.hit.answer[:100]}...")
        print(f"    Cached at:     {result.hit.cached_at}")
        print(f"    Confidence:    {result.hit.confidence}")


def main() -> None:
    client = get_client()

    # Start with a clean cache
    print("Clearing cache collection...")
    cache_clear(client)

    original_query = "How do I reset my password?"
    similar_query = "I forgot my password, how can I reset it?"
    different_query = "What are the API rate limits?"

    simulated_answer = (
        "To reset your password, go to Settings > Security > Reset Password. "
        "Enter the email address associated with your account and a reset link "
        "will be sent. The link expires after 24 hours. [source: password_reset_policy, "
        "section: 'Resetting your password (consumer accounts)']"
    )

    # --- Step 1: Query before anything is cached → MISS ---
    print(f"\n{'='*60}")
    print("Step 1: Query before cache is populated")
    print(f"  Query: {original_query!r}")
    t0 = time.perf_counter()
    result = cache_lookup(original_query, client, threshold=TEST_THRESHOLD)
    ms = (time.perf_counter() - t0) * 1000
    _print_lookup("Before cache write", result, ms)

    # --- Step 2: Write a simulated answer to cache ---
    print(f"\n{'='*60}")
    print("Step 2: Writing simulated verified answer to cache")
    point_id = cache_write(
        query=original_query,
        answer=simulated_answer,
        client=client,
        confidence=0.92,
        source_chunks=["password_reset_policy__chunk_0", "password_reset_policy__chunk_1"],
    )
    print(f"  Written to cache with point_id={point_id}")

    # --- Step 3: Same query again → HIT ---
    print(f"\n{'='*60}")
    print("Step 3: Same query again (should be a HIT)")
    print(f"  Query: {original_query!r}")
    t0 = time.perf_counter()
    result = cache_lookup(original_query, client, threshold=TEST_THRESHOLD)
    ms = (time.perf_counter() - t0) * 1000
    _print_lookup("Exact same query", result, ms)

    # --- Step 4: Slightly rephrased query → HIT (semantic match) ---
    print(f"\n{'='*60}")
    print("Step 4: Semantically similar query (should also HIT)")
    print(f"  Query: {similar_query!r}")
    t0 = time.perf_counter()
    result = cache_lookup(similar_query, client, threshold=TEST_THRESHOLD)
    ms = (time.perf_counter() - t0) * 1000
    _print_lookup("Similar query", result, ms)

    # --- Step 5: Completely different query → MISS ---
    print(f"\n{'='*60}")
    print("Step 5: Completely different query (should be a MISS)")
    print(f"  Query: {different_query!r}")
    t0 = time.perf_counter()
    result = cache_lookup(different_query, client, threshold=TEST_THRESHOLD)
    ms = (time.perf_counter() - t0) * 1000
    _print_lookup("Different query", result, ms)

    print(f"\n{'='*60}")
    print("Cache lifecycle test complete.")
    print("Expected: MISS → write → HIT → HIT (similar) → MISS (different)")


if __name__ == "__main__":
    main()
