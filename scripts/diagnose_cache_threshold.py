
from __future__ import annotations

import math

from app.config import settings
from app.ingestion.embeddings import embed_text


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


PAIRS = [
    ("Password paraphrase #1",
     "How do I reset my password?",
     "I forgot my password, how do I reset it?"),
    ("Password paraphrase #2",
     "What are the password requirements?",
     "What are the rules for creating a password?"),
    ("SSO paraphrase",
     "How does SSO login work for enterprise accounts?",
     "How does enterprise SSO work?"),
    ("Refund paraphrase",
     "What is the standard refund window?",
     "How many days do I have to request a refund?"),
    ("Near-duplicate trap (should stay well BELOW threshold)",
     "How do I reset my password?",
     "How does SSO login work for enterprise accounts?"),
]


def main() -> None:
    print(f"cache_similarity_threshold = {settings.cache_similarity_threshold}\n")
    for label, q1, q2 in PAIRS:
        v1 = embed_text(q1)
        v2 = embed_text(q2)
        sim = cosine_similarity(v1, v2)
        verdict = (
            "ABOVE threshold (would cache-hit)"
            if sim >= settings.cache_similarity_threshold
            else "below threshold (would MISS)"
        )
        print(f"[{label}]")
        print(f"  Q1: {q1!r}")
        print(f"  Q2: {q2!r}")
        print(f"  cosine similarity: {sim:.4f}  -- {verdict}\n")


if __name__ == "__main__":
    main()
