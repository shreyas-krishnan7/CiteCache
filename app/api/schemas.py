
from __future__ import annotations

from pydantic import BaseModel


class UploadResult(BaseModel):
    filename: str
    chunks_indexed: int
    doc_type: str


class UploadResponse(BaseModel):
    files_processed: int
    total_chunks_indexed: int
    results: list[UploadResult]
    total_chunks_in_collection: int


class AskRequest(BaseModel):
    question: str


class CitationOut(BaseModel):
    chunk_id: str
    claim: str | None = None
    source: str | None = None
    supported: bool | None = None


class AskResponse(BaseModel):
    answer: str
    source: str  # "cache" or "generated"
    confidence: float
    citations: list[CitationOut]
    latency_ms: float
    insufficient_context: bool | None = None
