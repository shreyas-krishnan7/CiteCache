"""
Central configuration for CiteCache.

Every setting has a working default so the project runs out of the
box with zero API keys (local embeddings, no LLM calls yet in phase 1).
Later phases read llm_model / api keys / cache thresholds from here too,
so this file doesn't need to change as the project grows.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # --- Qdrant ---
    qdrant_mode: str = os.getenv("QDRANT_MODE", "embedded")  # "embedded" or "server"
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_data_path: str = os.getenv("QDRANT_DATA_PATH", "./qdrant_data")
    doc_collection: str = os.getenv("QDRANT_DOC_COLLECTION", "citecache_docs")
    cache_collection: str = os.getenv("QDRANT_CACHE_COLLECTION", "citecache_cache")

    # --- Embeddings ---
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")
    local_embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # --- LLM (phase 3+) ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "anthropic"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    # --- Generation (phase 3) ---
    generation_max_tokens: int = int(os.getenv("GENERATION_MAX_TOKENS", "800"))
    generation_temperature: float = float(os.getenv("GENERATION_TEMPERATURE", "0.0"))
    structured_output_max_retries: int = int(os.getenv("STRUCTURED_OUTPUT_MAX_RETRIES", "2"))

    # --- Citation verification (phase 3) ---
    # Stage A embedding pre-filter: below this cosine similarity, a
    # citation is rejected as an obvious miscite without spending an
    # LLM call on it. Deliberately low (not a quality bar) -- it only
    # exists to catch citations that are unrelated to their claim.
    citation_prefilter_threshold: float = float(os.getenv("CITATION_PREFILTER_THRESHOLD", "0.3"))
    verification_max_tokens: int = int(os.getenv("VERIFICATION_MAX_TOKENS", "300"))

    # --- Confidence scoring (phase 3) ---
    confidence_retrieval_weight: float = float(os.getenv("CONFIDENCE_RETRIEVAL_WEIGHT", "0.4"))
    confidence_citation_weight: float = float(os.getenv("CONFIDENCE_CITATION_WEIGHT", "0.4"))
    confidence_completeness_weight: float = float(os.getenv("CONFIDENCE_COMPLETENESS_WEIGHT", "0.2"))

    # --- Cache policy (phase 5+) ---
    cache_similarity_threshold: float = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.95"))
    cache_write_confidence_threshold: float = float(os.getenv("CACHE_WRITE_CONFIDENCE_THRESHOLD", "0.75"))
    cache_ttl_days: int = int(os.getenv("CACHE_TTL_DAYS", "7"))

    # --- Chunking ---
    chunk_size_tokens: int = int(os.getenv("CHUNK_SIZE_TOKENS", "300"))
    chunk_overlap_tokens: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "50"))

    # --- Hybrid Retrieval (phase 2+) ---
    rrf_k: int = int(os.getenv("RRF_K", "60"))
    hybrid_top_k: int = int(os.getenv("HYBRID_TOP_K", "20"))
    final_top_k: int = int(os.getenv("FINAL_TOP_K", "5"))


settings = Settings()
