
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone

from app.config import settings
from app.ingestion.chunking import chunk_document
from app.ingestion.embeddings import embed_texts
from app.ingestion.vector_store import ensure_collection, get_client, upsert_chunks

# Lightweight filename -> doc_type guesser. Good enough for the demo
# corpus; a real system would read this from front-matter instead.
DOC_TYPE_BY_FILENAME_HINT = {
    "password": "account_security",
    "sso": "account_security",
    "two_factor": "account_security",
    "refund": "billing",
    "billing": "billing",
    "subscription": "billing",
    "api": "developer",
    "webhook": "developer",
    "data_export": "data",
    "account_deletion": "account_management",
    "team_seat": "account_management",
}


def _guess_doc_type(filename: str) -> str:
    lower = filename.lower()
    for hint, doc_type in DOC_TYPE_BY_FILENAME_HINT.items():
        if hint in lower:
            return doc_type
    return "general"


def ingest(source_dir: str, rebuild: bool) -> None:
    client = get_client()
    source_path = pathlib.Path(source_dir)
    md_files = sorted(source_path.glob("*.md"))

    if not md_files:
        raise SystemExit(f"No markdown files found under {source_dir}")

    all_chunks = []
    print(f"Chunking {len(md_files)} documents...")
    for path in md_files:
        text = path.read_text(encoding="utf-8")
        doc_type = _guess_doc_type(path.stem)
        chunks = chunk_document(
            markdown_text=text,
            source=path.stem,
            doc_type=doc_type,
            last_updated=datetime.now(timezone.utc).date().isoformat(),
            max_chunk_tokens=settings.chunk_size_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        )
        all_chunks.extend(chunks)
        print(f"  {path.name}: {len(chunks)} chunks ({doc_type})")

    print(f"\nEmbedding {len(all_chunks)} chunks (provider={settings.embedding_provider})...")
    embeddings = embed_texts([c.text for c in all_chunks])
    vector_size = len(embeddings[0])

    if rebuild:
        try:
            client.delete_collection(settings.doc_collection)
            print(f"Dropped existing collection '{settings.doc_collection}'.")
        except Exception:
            pass

    ensure_collection(client, settings.doc_collection, vector_size)
    upsert_chunks(client, settings.doc_collection, all_chunks, embeddings)

    manifest = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "embedding_provider": settings.embedding_provider,
        "embedding_model": (
            settings.openai_embedding_model
            if settings.embedding_provider == "openai"
            else settings.local_embedding_model
        ),
        "vector_size": vector_size,
        "total_chunks": len(all_chunks),
        "total_documents": len(md_files),
        "chunk_size_tokens": settings.chunk_size_tokens,
        "chunk_overlap_tokens": settings.chunk_overlap_tokens,
        "documents": [p.name for p in md_files],
    }
    manifest_path = pathlib.Path("data") / "index_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nIndexed {len(all_chunks)} chunks from {len(md_files)} documents into '{settings.doc_collection}'.")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest markdown docs into the CiteCache document collection.")
    parser.add_argument("--source", default="data/docs", help="Directory of .md files to ingest.")
    parser.add_argument("--rebuild", action="store_true", help="Drop and recreate the collection before ingesting.")
    args = parser.parse_args()
    ingest(args.source, args.rebuild)
