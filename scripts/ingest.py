
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone

from app.config import settings
from app.ingestion.chunking import chunk_document
from app.ingestion.embeddings import embed_texts
from app.ingestion.extractors import extract_text, SUPPORTED_EXTENSIONS
from app.ingestion.vector_store import ensure_collection, get_client, upsert_chunks, clear_collection

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
    "osh": "occupational_safety",
    "wages": "wages_and_bonus",
    "bonded": "bonded_labour",
}


def _guess_doc_type(filename: str) -> str:
    lower = filename.lower()
    for hint, doc_type in DOC_TYPE_BY_FILENAME_HINT.items():
        if hint in lower:
            return doc_type
    return "general"


def _find_source_files(source_path: pathlib.Path) -> list[pathlib.Path]:
    files = []
    for ext in sorted(SUPPORTED_EXTENSIONS):
        files.extend(source_path.glob(f"*.{ext}"))
    return sorted(files)


def ingest(source_dir: str, rebuild: bool) -> None:
    client = get_client()
    source_path = pathlib.Path(source_dir)
    source_files = _find_source_files(source_path)

    if not source_files:
        raise SystemExit(
            f"No supported files found under {source_dir} "
            f"(looking for: {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
        )

    all_chunks = []
    print(f"Chunking {len(source_files)} documents...")
    for path in source_files:
        try:
            text = extract_text(path.name, path.read_bytes())
        except ValueError as e:
            print(f"  SKIPPED {path.name}: {e}")
            continue

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

    if not all_chunks:
        raise SystemExit("No chunks produced -- every file was skipped or empty.")

    print(f"\nEmbedding {len(all_chunks)} chunks (provider={settings.embedding_provider})...")
    embeddings = embed_texts([c.text for c in all_chunks])
    vector_size = len(embeddings[0])

    if rebuild:
        deleted = clear_collection(client, settings.doc_collection)
        print(f"Cleared {deleted} existing point(s) from '{settings.doc_collection}' before re-ingesting.")

    ensure_collection(client, settings.doc_collection, vector_size)
    upsert_chunks(client, settings.doc_collection, all_chunks, embeddings)

    manifest = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "embedding_provider": settings.embedding_provider,
        "embedding_model": (
            settings.openai_embedding_model if settings.embedding_provider == "openai" else settings.local_embedding_model
        ),
        "vector_size": vector_size,
        "total_chunks": len(all_chunks),
        "total_documents": len(source_files),
        "chunk_size_tokens": settings.chunk_size_tokens,
        "chunk_overlap_tokens": settings.chunk_overlap_tokens,
        "documents": [p.name for p in source_files],
    }
    manifest_path = pathlib.Path("data") / "index_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nIndexed {len(all_chunks)} chunks from {len(source_files)} documents into '{settings.doc_collection}'.")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into the CiteCache document collection.")
    parser.add_argument("--source", default="data/docs", help="Directory of files to ingest.")
    parser.add_argument("--rebuild", action="store_true", help="Clear existing points before ingesting.")
    args = parser.parse_args()
    ingest(args.source, args.rebuild)
