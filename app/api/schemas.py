
from __future__ import annotations

from pydantic import BaseModel


class UploadResult(BaseModel):
    filename: str
    chunks_indexed: int
    doc_type: str


class UploadResponse(BaseModel):
    corpus: str = "default"
    files_processed: int
    total_chunks_indexed: int
    results: list[UploadResult]
    total_chunks_in_collection: int
    cache_entries_invalidated: int = 0


class AskRequest(BaseModel):
    question: str


class CitationOut(BaseModel):
    chunk_id: str
    claim: str | None = None
    source: str | None = None
    supported: bool | None = None


class EvidenceClaim(BaseModel):
    text: str
    supported: bool | None = None


class EvidenceOut(BaseModel):
    """One cited chunk, with every answer claim that cites it."""
    chunk_id: str
    document: str
    section: str | None = None
    snippet: str
    similarity: float | None = None   # query-chunk cosine similarity, 0..1
    supported: bool | None = None     # every claim citing this chunk was verified
    claims: list[EvidenceClaim] = []


class RetrievedChunkOut(BaseModel):
    chunk_id: str
    document: str
    section: str | None = None
    dense_score: float | None = None
    rerank_score: float | None = None
    cited: bool = False


class ConfidenceOut(BaseModel):
    retrieval_score: float
    citation_support_rate: float
    completeness: float
    confidence: float


class WorkspaceAskResponse(BaseModel):
    answer: str
    source: str  # "cache" or "generated"
    confidence: float
    latency_ms: float
    insufficient_context: bool | None = None
    evidence: list[EvidenceOut]
    retrieved: list[RetrievedChunkOut]           # empty on a cache hit: retrieval was skipped
    confidence_breakdown: ConfidenceOut | None = None


class DocumentOut(BaseModel):
    filename: str
    source: str
    chunks: int
    doc_type: str
    uploaded_at: str | None = None


class JobOut(BaseModel):
    id: str
    filename: str
    status: str
    stage: str
    progress: int
    chunks_total: int | None = None
    chunks_done: int = 0
    error: str | None = None
    created_at: str
    finished_at: str | None = None


class AskResponse(BaseModel):
    corpus: str = "default"
    answer: str
    source: str  # "cache" or "generated"
    confidence: float
    citations: list[CitationOut]
    latency_ms: float
    insufficient_context: bool | None = None
