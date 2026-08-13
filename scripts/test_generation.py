
from __future__ import annotations

from app.config import settings
from app.ingestion.vector_store import get_client
from app.retrieval.bm25_index import build_bm25_index
from app.retrieval.hybrid import hybrid_retrieve
from app.generation.generate import generate_answer
from app.verification.verify_citations import verify_citations
from app.verification.confidence import score_confidence

SAMPLE_QUERIES = [
    "How do I reset my password?",
    "What is the API rate limit?",
    "How does SSO login work for enterprise accounts?",
    "Can I get a refund after 30 days?",
]

# Deliberately not answerable from the 8-doc corpus.
OUT_OF_CORPUS_QUERY = "How do I export my account data as a CSV file?"


def _run_one(query: str, chunks_by_id_cache: dict) -> None:
    print(f"\n{'='*70}")
    print(f"Query: {query}")

    chunks = hybrid_retrieve(query, chunks_by_id_cache["client"], settings.doc_collection, chunks_by_id_cache["bm25"], top_k=5)
    print(f"\n  Retrieved {len(chunks)} chunks: {[c.source for c in chunks]}")

    result = generate_answer(query, chunks)
    print(f"\n  Answer: {result.answer}")
    print(f"  insufficient_context: {result.insufficient_context}")
    print(f"  Citations ({len(result.citations)}):")
    for c in result.citations:
        print(f"    - chunk_id={c.chunk_id[:8]}...  claim={c.claim!r}")

    chunks_by_id = {c.chunk_id: c for c in chunks}
    verdicts = verify_citations(result.citations, chunks_by_id)
    print(f"\n  Citation verdicts:")
    for v in verdicts:
        status = "✓ supported" if v.supported else "✗ NOT supported"
        print(f"    [{status}] ({v.method}) {v.reasoning}")

    top_chunk = chunks[0] if chunks else None
    score = score_confidence(top_chunk, verdicts, result.insufficient_context)
    print(f"\n  Confidence: {score.confidence:.3f}  "
          f"(retrieval={score.retrieval_score:.2f}, citations={score.citation_support_rate:.2f}, "
          f"completeness={score.completeness:.2f})  -- {score.summary}")
    gate = "would cache" if score.confidence >= settings.cache_write_confidence_threshold else "would NOT cache"
    print(f"  Against cache_write_confidence_threshold={settings.cache_write_confidence_threshold}: {gate}")


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
    print("Building BM25 index...")
    bm25 = build_bm25_index(client, settings.doc_collection)
    ctx = {"client": client, "bm25": bm25}

    for query in SAMPLE_QUERIES:
        _run_one(query, ctx)

    print(f"\n\n{'#'*70}")
    print("# Out-of-corpus query -- expect insufficient_context=True, NOT a hallucinated answer")
    print(f"{'#'*70}")
    _run_one(OUT_OF_CORPUS_QUERY, ctx)


if __name__ == "__main__":
    main()
