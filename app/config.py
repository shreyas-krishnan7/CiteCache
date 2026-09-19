
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

    # --- LLM ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # "openai", "anthropic", "groq", or "gemini"
    # Optional separate provider just for eval judge grading (app/eval/llm_judge.py).
    # Empty string = use the same provider as llm_provider. Useful when your best
    # pipeline provider (e.g. Gemini, best answer quality) has a tighter rate limit
    # than a provider you'd rather use for grading (e.g. Groq, 2x the RPM) --
    # keeps the eval's PIPELINE number honest (still Gemini-quality) while making
    # the extra judge calls faster/less rate-limit-prone.
    eval_judge_provider: str = os.getenv("EVAL_JUDGE_PROVIDER", "")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    groq_api_key: str | None = os.getenv("GROQ_API_KEY") or None
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # --- LLM rate-limit retry/backoff ---
    llm_rate_limit_max_retries: int = int(os.getenv("LLM_RATE_LIMIT_MAX_RETRIES", "5"))
    llm_rate_limit_default_delay_seconds: float = float(os.getenv("LLM_RATE_LIMIT_DEFAULT_DELAY_SECONDS", "15"))

    # --- Generation ---
    # Covers the answer AND its per-claim citations in one JSON object; a cap that
    # binds truncates the JSON mid-string and every retry fails the same way.
    generation_max_tokens: int = int(os.getenv("GENERATION_MAX_TOKENS", "2048"))
    generation_temperature: float = float(os.getenv("GENERATION_TEMPERATURE", "0.0"))
    structured_output_max_retries: int = int(os.getenv("STRUCTURED_OUTPUT_MAX_RETRIES", "2"))

    # --- Citation verification ---
    citation_prefilter_threshold: float = float(os.getenv("CITATION_PREFILTER_THRESHOLD", "0.3"))
    verification_max_tokens: int = int(os.getenv("VERIFICATION_MAX_TOKENS", "300"))

    # --- Confidence scoring ---
    confidence_retrieval_weight: float = float(os.getenv("CONFIDENCE_RETRIEVAL_WEIGHT", "0.4"))
    confidence_citation_weight: float = float(os.getenv("CONFIDENCE_CITATION_WEIGHT", "0.4"))
    confidence_completeness_weight: float = float(os.getenv("CONFIDENCE_COMPLETENESS_WEIGHT", "0.2"))

    # --- Cache policy ---
    cache_similarity_threshold: float = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.95"))
    cache_write_confidence_threshold: float = float(os.getenv("CACHE_WRITE_CONFIDENCE_THRESHOLD", "0.75"))
    cache_ttl_days: int = int(os.getenv("CACHE_TTL_DAYS", "7"))

    # --- Chunking ---
    chunk_size_tokens: int = int(os.getenv("CHUNK_SIZE_TOKENS", "300"))
    chunk_overlap_tokens: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "50"))

    # --- Hybrid retrieval ---
    rrf_k: int = int(os.getenv("RRF_K", "60"))
    hybrid_top_k: int = int(os.getenv("HYBRID_TOP_K", "20"))
    final_top_k: int = int(os.getenv("FINAL_TOP_K", "5"))

    # --- Reranking ---
    # Deferred from the original design until phase 6 eval measured a
    # real need: dense+BM25+RRF found the right DOCUMENT but sometimes
    # not the right SECTION within it, especially when a topically
    # adjacent chunk (e.g. SSO content, for a password-requirements
    # query) crowded the actually-relevant chunk out of a small top-5.
    rerank_enabled: bool = os.getenv("RERANK_ENABLED", "true").lower() == "true"
    rerank_model: str = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    rerank_candidate_pool_size: int = int(os.getenv("RERANK_CANDIDATE_POOL_SIZE", "15"))
    rerank_top_n: int = int(os.getenv("RERANK_TOP_N", "10"))

    # --- Metrics / instrumentation ---
    metrics_log_path: str = os.getenv("METRICS_LOG_PATH", "data/metrics_log.jsonl")

    # --- Dev convenience ---
    # Clears the doc + cache collections every time the API starts, so
    # repeated `uvicorn --reload` restarts during dev don't accumulate
    # duplicate chunks from re-uploading the same demo files. Turn off
    # once you have a corpus you want to persist across restarts.
    clear_data_on_startup: bool = os.getenv("CLEAR_DATA_ON_STARTUP", "true").lower() == "true"

    # --- Auth (React frontend) ---
    mongodb_uri: str | None = os.getenv("MONGODB_URI") or None
    mongodb_db: str = os.getenv("MONGODB_DB", "citecache")
    jwt_secret: str | None = os.getenv("JWT_SECRET") or None
    jwt_expire_days: int = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
    # True in production (HTTPS); false lets the cookie work on http://localhost.
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"


settings = Settings()
