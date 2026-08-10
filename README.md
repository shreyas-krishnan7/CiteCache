# CiteCache — Agentic RAG Support Copilot & Semantic Cache Gateway

## Overview
CiteCache is a production-oriented Retrieval-Augmented Generation (RAG) system designed for support knowledge bases.  
It combines hybrid retrieval, reranking, and semantic caching to deliver accurate, grounded, and low-latency responses.

---

## Features

- Hybrid Retrieval
  - Dense retrieval using embeddings (cosine similarity)
  - Sparse retrieval using BM25
- Fusion Layer
  - Reciprocal Rank Fusion (RRF) to combine dense + sparse results
- Reranking
  - Cross-encoder reranking for high-precision final results
- Semantic Caching
  - Redis-based cache for repeated/similar queries
- Grounded Responses
  - Source-based retrieval for citation support
- Modular Architecture
  - Clean separation of ingestion, retrieval, fusion, and caching layers

---

## Architecture

Query → Dense Retrieval + Sparse Retrieval → RRF Fusion → Cross-Encoder Rerank → Top Results → Cache Layer → Response

---

## Tech Stack

- Python (FastAPI)
- Qdrant (Vector Database)
- Redis (Semantic Cache)
- SentenceTransformers (Embeddings + Reranker)
- Rank-BM25 (Sparse Retrieval)
- Streamlit (Dashboard)

---



## How It Works

### Dense Retrieval
- Uses embedding similarity (cosine similarity)
- Captures semantic meaning

### Sparse Retrieval (BM25)
- Keyword-based matching
- Captures exact term overlap

### Fusion (RRF)
- Combines rankings instead of raw scores
- Rewards documents retrieved by both methods

### Reranking
- Cross-encoder scores query-document pairs
- Produces final top-k results

### Caching
- Redis stores query-response pairs
- Reduces latency and LLM calls

---

## Use Cases

- Customer support copilots
- Knowledge base assistants
- FAQ automation systems
- Internal documentation search

---

