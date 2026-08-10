# CiteCache — Verified RAG with Semantic Cache

A support/knowledge-base Q&A API where every query first checks a
semantic cache; on a miss, it runs hybrid retrieval → rerank →
grounded generation with citations → citation verification →
confidence scoring, and writes the verified answer back to cache.

## Current Status: Phase 2 — Hybrid Retrieval + Semantic Cache

```
citecache/
  .env.example
  requirements.txt
  docker-compose.yml          # (for later — not needed in phase 2)
  app/
    config.py                  # central settings, loaded from .env
    ingestion/
      chunking.py              # heading-based + fixed-size-overlap chunker
      embeddings.py            # local (sentence-transformers) or OpenAI
      vector_store.py          # Qdrant wrapper: embedded or server mode
    retrieval/
      bm25_index.py            # BM25 sparse index built from Qdrant data
      hybrid.py                # dense + sparse fusion with Reciprocal Rank Fusion
    cache/
      semantic_cache.py        # Qdrant-backed semantic cache (no Redis needed)
  data/
    docs/                      # 8 sample support docs (markdown)
  scripts/
    ingest.py                  # CLI: chunk + embed + upsert into Qdrant
    test_retrieval.py          # phase 1 sanity check (dense-only)
    test_hybrid.py             # phase 2: dense vs hybrid side-by-side
    test_cache.py              # phase 2: semantic cache lifecycle test
```

## Setup (Local — No Docker Required)

### 1. Create virtual environment and install dependencies

```powershell
cd C:\Users\SHREYAS\OneDrive\Desktop\rag
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Copy the environment file

```powershell
copy .env.example .env
```

The defaults work with zero API keys — embeddings run locally via
`sentence-transformers` (`BAAI/bge-small-en-v1.5`), and Qdrant runs
in embedded mode (data stored in `./qdrant_data/`, no server needed).

### 3. Ingest the sample corpus

```powershell
python -m scripts.ingest --source data/docs --rebuild
```

First run will download the `bge-small-en-v1.5` model (~130MB) —
this only happens once. You should see output like:

```
Chunking 8 documents...
  password_reset_policy.md: 4 chunks (account_security)
  sso_enterprise_login.md: 4 chunks (account_security)
  ...
Embedding 33 chunks (provider=local)...
Indexed 33 chunks from 8 documents into 'citecache_docs'.
Manifest written to data/index_manifest.json
```

### 4. Run the dense-only retrieval sanity check (Phase 1)

```powershell
python -m scripts.test_retrieval
```

The SSO query should return chunks from `sso_enterprise_login.md`,
not `password_reset_policy.md`.

### 5. Run the hybrid retrieval comparison (Phase 2)

```powershell
python -m scripts.test_hybrid
```

Side-by-side dense-only vs hybrid (BM25 + dense + RRF) results for
8 queries. Hybrid should match or beat dense on all queries, and
notably improve on keyword-heavy ones like "API error code 429."

### 6. Run the semantic cache lifecycle test (Phase 2)

```powershell
python -m scripts.test_cache
```

Demonstrates: MISS → write → HIT → semantic HIT → MISS.

## Design Decisions Worth Remembering for Interviews

- **Two Qdrant collections, not one with a type filter.** The
  document collection and the semantic cache collection are kept
  separate. This keeps cache lookups fast and makes it structurally
  impossible for a cached Q&A pair to accidentally get retrieved as
  if it were a source document.
- **Embedded Qdrant for development, server mode for production.**
  One config flag (`QDRANT_MODE=embedded` vs `server`) switches
  between local file storage and a running Qdrant server. Zero
  infrastructure setup for development.
- **Heading-based chunking first, fixed-size-overlap as fallback.**
  Every chunk records which strategy produced it (`chunk.strategy`),
  so retrieval quality across strategies can be compared later in
  the eval phase.
- **RRF instead of score blending for hybrid retrieval.** Dense
  cosine and BM25 scores are on different scales, so a weighted
  average needs tuning. RRF uses ranks, not scores — no alpha to
  tune. Same approach as Elasticsearch's RRF.
- **BM25 index built from Qdrant at startup.** For a demo corpus
  this is fine (<100ms). A production system would build it
  incrementally at ingest time or use Qdrant's native sparse vectors.
- **Semantic cache uses Qdrant, not Redis.** Zero additional
  infrastructure. When adding Docker later, swapping in Redis is a
  one-file change.
- **The SSO doc is a deliberate near-duplicate trap.** It shares
  vocabulary with the password reset doc but describes a completely
  different flow.

## Phase Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Scaffold, ingestion, indexing | ✅ Done |
| 2 | Hybrid retrieval (BM25 + RRF) + semantic cache | ✅ Done |
| 3 | LangGraph state machine (10 nodes) | 🔲 Next |
| 4 | LLM generation + citation verification | 🔲 |
| 5 | Cache policy, TTL, confidence gating | 🔲 |
| 6 | Eval (golden set + RAGAS/DeepEval) | 🔲 |
| 7 | FastAPI + Streamlit dashboard | 🔲 |
| 8 | Docker Compose + deployment | 🔲 |
