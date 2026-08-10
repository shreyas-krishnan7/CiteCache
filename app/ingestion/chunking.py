"""
Chunking strategies for CiteCache document ingestion.

Two strategies are implemented, and every chunk records which one
produced it. That matters later (phase 6 eval) when comparing
retrieval quality across chunking strategies:

  1. Heading-based: split on markdown '#' headings first. Keeps a
     semantically coherent section (e.g. "Reset your password")
     together in one chunk whenever it's small enough.
  2. Fixed-size + overlap: fallback for any heading section that's
     still too large. Token-aware, with configurable overlap so a
     claim near a chunk boundary isn't cut off in one chunk and
     missing from its neighbour.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

import tiktoken

_ENCODER = tiktoken.get_encoding("cl100k_base")


def token_count(text: str) -> int:
    return len(_ENCODER.encode(text))


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    section_heading: str
    strategy: str
    doc_type: str
    last_updated: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


def _split_by_headings(markdown_text: str) -> list[tuple[str, str]]:
    """
    Splits markdown into (heading, body) pairs on '#'-style headings.
    Content before the first heading is kept under heading '' (intro).
    """
    lines = markdown_text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_heading = ""
    current_body: list[str] = []
    heading_pattern = re.compile(r"^#{1,4}\s+(.*)")

    for line in lines:
        match = heading_pattern.match(line)
        if match:
            if current_body or current_heading:
                sections.append((current_heading, current_body))
            current_heading = match.group(1).strip()
            current_body = []
        else:
            current_body.append(line)

    sections.append((current_heading, current_body))
    return [(h, "\n".join(b).strip()) for h, b in sections if "\n".join(b).strip()]


def _fixed_size_split(text: str, size_tokens: int, overlap_tokens: int) -> list[str]:
    """Token-aware fixed-size splitter with overlap."""
    tokens = _ENCODER.encode(text)
    if len(tokens) <= size_tokens:
        return [text]

    pieces = []
    start = 0
    while start < len(tokens):
        end = min(start + size_tokens, len(tokens))
        pieces.append(_ENCODER.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start = end - overlap_tokens
    return pieces


def chunk_document(
    markdown_text: str,
    source: str,
    doc_type: str,
    last_updated: str,
    max_chunk_tokens: int = 300,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """
    Recursive heading-based chunking with a fixed-size overlap fallback.
    Returns a flat list of Chunk objects ready to embed and upsert.
    """
    sections = _split_by_headings(markdown_text)
    chunks: list[Chunk] = []
    idx = 0

    for heading, body in sections:
        if token_count(body) <= max_chunk_tokens:
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    text=body,
                    source=source,
                    section_heading=heading,
                    strategy="heading",
                    doc_type=doc_type,
                    last_updated=last_updated,
                    chunk_index=idx,
                )
            )
            idx += 1
        else:
            for piece in _fixed_size_split(body, max_chunk_tokens, overlap_tokens):
                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        text=piece,
                        source=source,
                        section_heading=heading,
                        strategy="fixed_size_overlap",
                        doc_type=doc_type,
                        last_updated=last_updated,
                        chunk_index=idx,
                    )
                )
                idx += 1

    return chunks
