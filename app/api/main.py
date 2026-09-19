
from __future__ import annotations # It postpones evaluation of type annotations, improving performance and avoiding circular import issues.Type hints ko abhi evaluate mat karo, baad mein dekh lena

import re
import threading #Lock ensures only one thread accesses the BM25 index at a time.
import time
import traceback

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.corpus import DEFAULT_CORPUS, CorpusProfile, InvalidCorpusName, get_profile
from app.cache.semantic_cache import cache_clear
from app.ingestion.extractors import SUPPORTED_EXTENSIONS
from app.ingestion.pipeline import guess_doc_type, index_chunks, prepare_document
from app.ingestion.vector_store import get_client, scroll_all_points, clear_collection
from app.retrieval.bm25_index import build_bm25_index, BM25Index
from app.graph.build_graph import build_graph
from app.auth.routes import current_user, router as auth_router
from app.api.jobs import UploadJob, create_job, get_job, jobs_for, update_job
from app.api.schemas import (
    UploadResponse, UploadResult, AskRequest, AskResponse, CitationOut,
    ConfidenceOut, DocumentOut, EvidenceClaim, EvidenceOut, JobOut, RetrievedChunkOut, WorkspaceAskResponse,
)

app = FastAPI(title="CiteCache API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)

_client = get_client() # initialising the connection to the Qdrant client
_graph = build_graph()
_bm25_lock = threading.Lock()
# One BM25 index per corpus, built lazily on first use. A corpus whose
# collection is empty maps to None.
_bm25_indexes: dict[str, BM25Index | None] = {}
# Embedding + Qdrant writes are serialized: the local embedding model and
# embedded Qdrant aren't built for concurrent writers.
_ingest_lock = threading.Lock()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
_USER_CORPUS_PREFIX = "u-"


def _resolve_profile(corpus: str) -> CorpusProfile:
    # Per-user corpora hold private documents; they're reachable only through
    # the authenticated /workspace routes, never by naming them here.
    if corpus.startswith(_USER_CORPUS_PREFIX):
        raise HTTPException(status_code=404, detail="Unknown corpus.")
    try:
        return get_profile(corpus)
    except InvalidCorpusName as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:  # malformed corpora/<name>.json
        raise HTTPException(status_code=500, detail=f"Corpus profile error: {e}")


def _user_profile(user: dict) -> CorpusProfile:
    return get_profile(f"{_USER_CORPUS_PREFIX}{user['id']}")


def _rebuild_bm25_index(profile: CorpusProfile) -> None:
    with _bm25_lock:
        try:
            _bm25_indexes[profile.name] = build_bm25_index(_client, profile.doc_collection)
        except RuntimeError:
            _bm25_indexes[profile.name] = None


def _bm25_for(profile: CorpusProfile) -> BM25Index | None:
    if profile.name not in _bm25_indexes:
        _rebuild_bm25_index(profile)
    return _bm25_indexes.get(profile.name)


@app.on_event("startup")
def _on_startup() -> None:
    default = get_profile(DEFAULT_CORPUS)
    if settings.clear_data_on_startup:
        doc_deleted = clear_collection(_client, default.doc_collection)
        cache_deleted = clear_collection(_client, default.cache_collection) # clearing cache as well , because cache deepends on docs - docs change canche also changes .
        print(f"[startup] CLEAR_DATA_ON_STARTUP=true -- cleared {doc_deleted} doc chunk(s) "
              f"and {cache_deleted} cache entry(ies). Set CLEAR_DATA_ON_STARTUP=false in .env "
              f"to persist data across restarts instead.")
    _rebuild_bm25_index(default)


def _reset(profile: CorpusProfile) -> dict:
    doc_deleted = clear_collection(_client, profile.doc_collection)
    cache_deleted = clear_collection(_client, profile.cache_collection)
    _rebuild_bm25_index(profile)
    return {
        "status": "ok",
        "corpus": profile.name,
        "doc_chunks_deleted": doc_deleted,
        "cache_entries_deleted": cache_deleted,
    }


def _after_corpus_change(profile: CorpusProfile) -> int:
    # Cached answers were produced from the corpus as it was before this
    # upload; a new document can change or contradict them, so they are
    # dropped rather than served until their TTL runs out.
    invalidated = cache_clear(_client, profile.cache_collection)
    _rebuild_bm25_index(profile)
    return invalidated


async def _upload(profile: CorpusProfile, files: list[UploadFile]) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    prepared = []  # (filename, chunks) -- every file is validated before anything is indexed
    for file in files:
        name = file.filename or "uploaded"
        try:
            prepared.append((name, prepare_document(name, await file.read())))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not any(chunks for _, chunks in prepared):
        raise HTTPException(status_code=400, detail="No content extracted from uploaded file(s).")

    with _ingest_lock:
        for _, chunks in prepared:
            index_chunks(_client, profile, chunks)
        cache_invalidated = _after_corpus_change(profile)

    results: list[UploadResult] = [ # empty list of the datype UploadResult definied in the schemas.py file
        UploadResult(filename=name, chunks_indexed=len(chunks),
                     doc_type=chunks[0].doc_type if chunks else guess_doc_type(name))
        for name, chunks in prepared
    ]
    total_in_collection = len(scroll_all_points(_client, profile.doc_collection))

    return UploadResponse(
        corpus=profile.name,
        files_processed=len(files),
        total_chunks_indexed=sum(len(chunks) for _, chunks in prepared),
        results=results,
        total_chunks_in_collection=total_in_collection,
        cache_entries_invalidated=cache_invalidated,
    )


def _run_graph(profile: CorpusProfile, question: str) -> tuple[dict, float]:
    bm25_index = _bm25_for(profile)
    if bm25_index is None:
        raise HTTPException(
            status_code=400,
            detail="No documents indexed yet -- upload at least one document first.",
        )
    start = time.perf_counter()
    result = _graph.invoke({
        "query": question,
        "client": _client,
        "bm25_index": bm25_index,
        "collection": profile.doc_collection,
        "profile": profile,
        "start_time": start,
    })
    return result, (time.perf_counter() - start) * 1000


def _ask(profile: CorpusProfile, request: AskRequest) -> AskResponse:
    result, latency_ms = _run_graph(profile, request.question)

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
        corpus=profile.name,
        answer=result.get("final_answer", ""),
        source=result.get("source", "unknown"),
        confidence=result.get("final_confidence", 0.0),
        citations=citations_out,
        latency_ms=latency_ms,
        insufficient_context=(generated.insufficient_context if generated else None),
    )


# --- Default-corpus routes: unchanged paths, so existing clients keep working ---

@app.post("/reset")
def reset_all() -> dict:
    """
    Manual reset without restarting the server -- clears both the
    document collection and the semantic cache of the default corpus, and
    rebuilds (empty) BM25 index state. Useful when CLEAR_DATA_ON_STARTUP=false,
    or when you just want to start over without killing uvicorn.
    """
    return _reset(get_profile(DEFAULT_CORPUS))


@app.post("/upload", response_model=UploadResponse) # output shoudl foolw the schema of UploadResponse
async def upload_documents(files: list[UploadFile] = File(...)) -> UploadResponse:    # ... - represent file is required
    return await _upload(get_profile(DEFAULT_CORPUS), files)


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest) -> AskResponse:
    return _ask(get_profile(DEFAULT_CORPUS), request)


# --- Per-corpus routes: each corpus is isolated (own docs, cache, BM25) ---

@app.post("/corpora/{corpus}/reset")
def reset_corpus(corpus: str) -> dict:
    return _reset(_resolve_profile(corpus))


@app.post("/corpora/{corpus}/upload", response_model=UploadResponse)
async def upload_to_corpus(corpus: str, files: list[UploadFile] = File(...)) -> UploadResponse:
    return await _upload(_resolve_profile(corpus), files)


@app.post("/corpora/{corpus}/ask", response_model=AskResponse)
def ask_corpus(corpus: str, request: AskRequest) -> AskResponse:
    return _ask(_resolve_profile(corpus), request)


# --- Workspace routes (React frontend): signed-in user, private corpus ---

def _run_upload_job(job: UploadJob, profile: CorpusProfile, filename: str, raw: bytes) -> None:
    with _ingest_lock:
        try:
            update_job(job, status="processing", stage="Extracting text", progress=5)
            chunks = prepare_document(filename, raw)
            update_job(job, stage="Embedding chunks", progress=15, chunks_total=len(chunks))

            def on_batch(done: int, total: int) -> None:
                update_job(job, chunks_done=done, progress=15 + int(75 * done / total))

            index_chunks(_client, profile, chunks, on_batch)
            update_job(job, stage="Updating search index", progress=95)
            _after_corpus_change(profile)
            update_job(job, status="done", stage="Ready", progress=100)
        except ValueError as e:
            update_job(job, status="error", stage="Failed", error=str(e))
        except Exception as e:
            traceback.print_exc()
            update_job(job, status="error", stage="Failed", error=f"Indexing failed ({type(e).__name__}).")


@app.post("/workspace/upload", response_model=list[JobOut], status_code=202)
async def workspace_upload(background: BackgroundTasks, files: list[UploadFile] = File(...),
                           user: dict = Depends(current_user)) -> list[JobOut]:
    received = []
    for file in files:
        name = file.filename or "uploaded"
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(400, f"'{name}' is not supported. Upload {', '.join(sorted(SUPPORTED_EXTENSIONS))} files.")
        raw = await file.read()
        if not raw:
            raise HTTPException(400, f"'{name}' is empty.")
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"'{name}' is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
        received.append((name, raw))

    profile = _user_profile(user)
    jobs = []
    for name, raw in received:
        job = create_job(user["id"], name)
        background.add_task(_run_upload_job, job, profile, name, raw)
        jobs.append(JobOut(**job.public()))
    return jobs


@app.get("/workspace/jobs", response_model=list[JobOut])
def workspace_jobs(user: dict = Depends(current_user)) -> list[JobOut]:
    return [JobOut(**j.public()) for j in jobs_for(user["id"])]


@app.get("/workspace/jobs/{job_id}", response_model=JobOut)
def workspace_job(job_id: str, user: dict = Depends(current_user)) -> JobOut:
    job = get_job(job_id, user["id"])
    if job is None:
        raise HTTPException(404, "Job not found.")
    return JobOut(**job.public())


@app.get("/workspace/documents", response_model=list[DocumentOut])
def workspace_documents(user: dict = Depends(current_user)) -> list[DocumentOut]:
    profile = _user_profile(user)
    if profile.doc_collection not in {c.name for c in _client.get_collections().collections}:
        return []
    docs: dict[str, dict] = {}
    for point in scroll_all_points(_client, profile.doc_collection):
        p = point.payload
        doc = docs.setdefault(p.get("source", ""), {
            "source": p.get("source", ""), "filename": p.get("filename") or p.get("source", ""),
            "chunks": 0, "doc_type": p.get("doc_type", "general"), "uploaded_at": p.get("uploaded_at"),
        })
        doc["chunks"] += 1
    return [DocumentOut(**d) for d in sorted(docs.values(), key=lambda d: d["uploaded_at"] or "", reverse=True)]


_WORD = re.compile(r"[a-z0-9]{4,}")


def _snippet(text: str, heading: str | None, focus: list[str], limit: int = 420) -> str:
    """
    The part of a chunk worth quoting: the window starting at whichever sentence
    or numbered sub-clause shares the most words with `focus` (the claims citing
    it). A long chunk's supporting sentence is often past the first 420 chars,
    and quoting the chunk's opening would show evidence for something else.
    """
    if heading and text.startswith(heading):
        text = text[len(heading):]
    text = re.sub(r"\s+", " ", text).strip()
    start = 0
    wanted = {w for f in focus for w in _WORD.findall(f.lower())}
    if wanted and len(text) > limit:
        starts = [0] + [m.start() for m in re.finditer(r"(?<=[.;:] )\S|\(\d+[a-z]?\) ", text)]
        start = max(starts, key=lambda s: len(wanted & set(_WORD.findall(text[s:s + limit].lower()))))
        # Quote from the top of the numbered sub-section holding the match, so a
        # list like "(2) ... (a) ... (b) ... (c)" isn't shown starting at (c).
        clauses = [m.start() for m in re.finditer(r"\(\d+[a-z]?\) ", text) if m.start() <= start]
        if clauses and start - clauses[-1] <= limit * 3 // 4:
            start = clauses[-1]
    snippet = text[start:start + limit]
    if start + limit < len(text):
        snippet = snippet.rsplit(" ", 1)[0] + "…"
    # A lowercase opening means the chunk itself begins mid-sentence (a later
    # window of a long section), so it gets an ellipsis too.
    return ("…" + snippet) if start or snippet[:1].islower() else snippet


@app.post("/workspace/ask", response_model=WorkspaceAskResponse)
def workspace_ask(request: AskRequest, user: dict = Depends(current_user)) -> WorkspaceAskResponse:
    if not request.question.strip():
        raise HTTPException(400, "Please enter a question.")
    profile = _user_profile(user)
    result, latency_ms = _run_graph(profile, request.question.strip())
    generated = result.get("generated")
    chunks = result.get("chunks") or []
    chunks_by_id = {c.chunk_id: c for c in chunks}

    # Claims grouped by the chunk they cite, in answer order.
    claims: dict[str, list[EvidenceClaim]] = {}
    if result["source"] == "generated" and generated:
        verdicts = {(v.chunk_id, v.claim): v for v in result.get("citation_verdicts") or []}
        for c in generated.citations:
            v = verdicts.get((c.chunk_id, c.claim))
            claims.setdefault(c.chunk_id, []).append(
                EvidenceClaim(text=c.claim, supported=v.supported if v else None))
    else:
        for chunk_id in result.get("final_citations") or []:
            claims.setdefault(chunk_id, [])

    wanted = list(dict.fromkeys(list(claims) + [c.chunk_id for c in chunks]))
    payloads = {str(p.id): p.payload for p in _client.retrieve(profile.doc_collection, ids=wanted, with_payload=True)} if wanted else {}
    name_of = lambda p: p.get("filename") or p.get("source", "")

    evidence = []
    for chunk_id, chunk_claims in claims.items():
        p = payloads.get(chunk_id)
        if p is None:
            continue
        flags = [c.supported for c in chunk_claims if c.supported is not None]
        retrieved = chunks_by_id.get(chunk_id)
        evidence.append(EvidenceOut(
            chunk_id=chunk_id, document=name_of(p), section=p.get("section_heading") or None,
            snippet=_snippet(p.get("text", ""), p.get("section_heading"),
                             [c.text for c in chunk_claims] or [result.get("final_answer", "")]),
            similarity=retrieved.dense_score if retrieved else None,
            supported=all(flags) if flags else None, claims=chunk_claims,
        ))

    retrieved_out = [
        RetrievedChunkOut(
            chunk_id=c.chunk_id, document=name_of(payloads.get(c.chunk_id, {})) or c.source,
            section=c.section_heading or None, dense_score=c.dense_score,
            rerank_score=getattr(c, "rerank_score", None), cited=c.chunk_id in claims,
        )
        for c in chunks
    ]
    conf = result.get("confidence")
    return WorkspaceAskResponse(
        answer=result.get("final_answer", ""),
        source=result.get("source", "unknown"),
        confidence=result.get("final_confidence", 0.0),
        latency_ms=latency_ms,
        insufficient_context=(generated.insufficient_context if generated else None),
        evidence=evidence,
        retrieved=retrieved_out,
        confidence_breakdown=ConfidenceOut(
            retrieval_score=conf.retrieval_score, citation_support_rate=conf.citation_support_rate,
            completeness=conf.completeness, confidence=conf.confidence,
        ) if conf else None,
    )


@app.get("/health")
def health() -> dict:
    default_index = _bm25_indexes.get(DEFAULT_CORPUS)
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "documents_indexed": default_index.corpus_size if default_index else 0,
        "corpora_loaded": {
            name: (index.corpus_size if index else 0) for name, index in _bm25_indexes.items()
            if not name.startswith(_USER_CORPUS_PREFIX)
        },
    }
