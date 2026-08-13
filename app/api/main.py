
from __future__ import annotations

import threading
import time

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ingestion.chunking import chunk_document
from app.ingestion.embeddings import embed_texts
from app.ingestion.vector_store import get_client, ensure_collection, upsert_chunks, scroll_all_points
from app.retrieval.bm25_index import build_bm25_index, BM25Index
from app.graph.build_graph import build_graph
from app.api.schemas import UploadResponse, UploadResult, AskRequest, AskResponse, CitationOut

app = FastAPI(title="CiteCache API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo-scale; tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = get_client()
_graph = build_graph()
_bm25_lock = threading.Lock()
_bm25_index: BM25Index | None = None

# Mirrors ingest.py's DOC_TYPE_BY_FILENAME_HINT -- kept self-contained
# here rather than importing a CLI script's internals into the API.
_DOC_TYPE_HINTS = {
    "password": "account_security", "sso": "account_security", "two_factor": "account_security",
    "refund": "billing", "billing": "billing", "subscription": "billing",
    "api": "developer", "webhook": "developer", "data_export": "data",
    "account_deletion": "account_management", "team_seat": "account_management",
}


def _guess_doc_type(filename: str) -> str:
    lower = filename.lower()
    for hint, doc_type in _DOC_TYPE_HINTS.items():
        if hint in lower:
            return doc_type
    return "general"


def _rebuild_bm25_index() -> None:
    global _bm25_index
    with _bm25_lock:
        try:
            _bm25_index = build_bm25_index(_client, settings.doc_collection)
        except RuntimeError:
            # No points yet -- fresh collection, nothing uploaded/ingested.
            # Leave _bm25_index as None; /ask returns a clear 400 if hit
            # before anything has been indexed.
            _bm25_index = None


@app.on_event("startup")
def _on_startup() -> None:
    _rebuild_bm25_index()


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results: list[UploadResult] = []
    all_chunks = []

    for file in files:
        raw = await file.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename}: only UTF-8 text/markdown files are supported.",
            )

        doc_type = _guess_doc_type(file.filename or "uploaded")
        chunks = chunk_document(
            markdown_text=text,
            source=(file.filename or "uploaded").rsplit(".", 1)[0],
            doc_type=doc_type,
            last_updated="uploaded",
            max_chunk_tokens=settings.chunk_size_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        )
        all_chunks.extend(chunks)
        results.append(UploadResult(
            filename=file.filename or "uploaded",
            chunks_indexed=len(chunks),
            doc_type=doc_type,
        ))

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No content extracted from uploaded file(s).")

    embeddings = embed_texts([c.text for c in all_chunks])
    ensure_collection(_client, settings.doc_collection, len(embeddings[0]))
    upsert_chunks(_client, settings.doc_collection, all_chunks, embeddings)

    _rebuild_bm25_index()

    total_in_collection = len(scroll_all_points(_client, settings.doc_collection))

    return UploadResponse(
        files_processed=len(files),
        total_chunks_indexed=len(all_chunks),
        results=results,
        total_chunks_in_collection=total_in_collection,
    )


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest) -> AskResponse:
    if _bm25_index is None:
        raise HTTPException(
            status_code=400,
            detail="No documents indexed yet -- upload at least one document first.",
        )

    start = time.perf_counter()
    result = _graph.invoke({
        "query": request.question,
        "client": _client,
        "bm25_index": _bm25_index,
        "collection": settings.doc_collection,
        "start_time": start,
    })
    latency_ms = (time.perf_counter() - start) * 1000

    citations_out: list[CitationOut] = []
    generated = result.get("generated")

    if result["source"] == "generated" and generated:
        verdicts_by_id = {v.chunk_id: v for v in result.get("citation_verdicts", [])}
        chunks_by_id = {c.chunk_id: c for c in result.get("chunks", [])}
        for c in generated.citations:
            verdict = verdicts_by_id.get(c.chunk_id)
            chunk = chunks_by_id.get(c.chunk_id)
            citations_out.append(CitationOut(
                chunk_id=c.chunk_id,
                claim=c.claim,
                source=chunk.source if chunk else None,
                supported=verdict.supported if verdict else None,
            ))
    else:
        # Cache hit: only chunk_ids were stored at write time, no claim-level detail.
        for chunk_id in (result.get("final_citations") or []):
            citations_out.append(CitationOut(chunk_id=chunk_id))

    return AskResponse(
        answer=result.get("final_answer", ""),
        source=result.get("source", "unknown"),
        confidence=result.get("final_confidence", 0.0),
        citations=citations_out,
        latency_ms=latency_ms,
        insufficient_context=(generated.insufficient_context if generated else None),
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "documents_indexed": _bm25_index.corpus_size if _bm25_index else 0,
    }
