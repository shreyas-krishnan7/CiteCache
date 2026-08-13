
from __future__ import annotations

from app.config import settings
from app.ingestion.embeddings import embed_text
from app.ingestion.vector_store import get_client, search_vectors

SAMPLE_QUERIES = [
    "How do I reset my password?",
    "What is the API rate limit?",
    "How does SSO login work for enterprise accounts?",
    "Can I get a refund after 30 days?",
    "How do I set up two-factor authentication?",
]


def main() -> None:
    client = get_client()
    for query in SAMPLE_QUERIES:
        vector = embed_text(query)
        results = search_vectors(client, settings.doc_collection, vector, limit=3)

        print(f"\nQuery: {query}")
        if not results:
            print("  (no results — did you run scripts/ingest.py first?)")
            continue
        for r in results:
            heading = r.payload.get("section_heading", "")
            source = r.payload.get("source", "")
            print(f"  score={r.score:.3f}  source={source}  heading={heading!r}")


if __name__ == "__main__":
    main()
