
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
    metadata: dict = field(default_factory=dict) # every chunk a new metadata dictionary is created 


# Indian statutes head each section "25. Daily and weekly working hours.—",
# and the em dash is what divides the heading from the body. The
# arrangement-of-sections table at the front of every Act repeats the same
# titles *without* a dash, so requiring the dash keeps that table from being
# mistaken for section starts. The title may wrap once because PDF extraction
# breaks long headings across lines.
_STATUTE_SECTION_RE = re.compile(
    r"^[ \t]*(\d{1,3})[ \t]*\.[ \t]*"
    r"([A-Z][^\n]{2,120}?(?:\n[ \t]*[^\n]{0,90}?)?)"
    r"[ \t]*\.?[ \t]*—",
    re.M,
)
_MIN_STATUTE_SECTIONS = 5


def _split_by_statute_sections(text: str) -> list[tuple[str, str]]:
    """Sections of a numbered statute, or [] if this doesn't look like one."""
    matches = list(_STATUTE_SECTION_RE.finditer(text))
    if len(matches) < _MIN_STATUTE_SECTIONS:
        return []

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        heading = f"{match.group(1)}. {' '.join(match.group(2).split())}"
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        if body:
            sections.append((heading, body))
    return sections


# A definition clause is a parenthesised letter followed by a QUOTED term:
# '(z) "worker" means ...'. Roman sub-clauses such as '(i) any dispute or
# difference' carry no quoted term, so they are correctly left alone.
_DEFINITION_CLAUSE_RE = re.compile(
    r'^[ \t]*\(([a-z]{1,3})\)[ \t]*[“"]([^”"\n]{2,60})[”"]',
    re.M,
)
_MIN_DEFINITION_CLAUSES = 3


def _expand_definition_sections(
    sections: list[tuple[str, str]], max_chunk_tokens: int
) -> list[tuple[str, str]]:
    """
    Give each defined term its own unit within an oversized definitions section.

    A statute's definitions section runs for pages and defines dozens of terms,
    so fixed-size splitting leaves every piece of it carrying the same heading
    ('2. Definitions'). Identical headings can't discriminate, and a query about
    one term retrieves pieces about others. Splitting per term makes the heading
    name the term it actually defines.
    """
    expanded: list[tuple[str, str]] = []
    for heading, body in sections:
        clauses = (
            _split_definition_clauses(body)
            if token_count(body) > max_chunk_tokens
            else []
        )
        if not clauses:
            expanded.append((heading, body))
            continue
        for label, text in clauses:
            expanded.append((f"{heading} - {label}" if label else heading, text))
    return expanded


def _split_definition_clauses(body: str) -> list[tuple[str, str]]:
    matches = list(_DEFINITION_CLAUSE_RE.finditer(body))
    if len(matches) < _MIN_DEFINITION_CLAUSES:
        return []

    parts: list[tuple[str, str]] = []
    preamble = body[: matches[0].start()].strip()
    if preamble:
        parts.append(("", preamble))

    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[match.start():end].strip()
        if text:
            term = " ".join(match.group(2).split())
            parts.append((f'({match.group(1)}) "{term}"', text))
    return parts


def _split_by_headings(markdown_text: str) -> list[tuple[str, str]]:
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
    sections = _split_by_statute_sections(markdown_text)
    if sections:
        # Only the statute path prefixes the heading onto the chunk text. Just
        # storing it in metadata leaves it out of the embedding and out of the
        # generation prompt, so a query naming a section ("safety officer")
        # can't match the heading that names it, and every fixed-size piece of
        # a long section arrives at the model with no idea which section it is.
        whole_strategy, split_strategy = "statute_section", "statute_section_overlap"
        prefix_heading = True
        sections = _expand_definition_sections(sections, max_chunk_tokens)
    else:
        sections = _split_by_headings(markdown_text)
        whole_strategy, split_strategy = "heading", "fixed_size_overlap"
        prefix_heading = False

    chunks: list[Chunk] = []
    idx = 0

    for heading, body in sections:
        if token_count(body) <= max_chunk_tokens:
            pieces, strategy = [body], whole_strategy
        else:
            pieces = _fixed_size_split(body, max_chunk_tokens, overlap_tokens)
            strategy = split_strategy

        for piece in pieces:
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    text=f"{heading}\n{piece}" if prefix_heading and heading else piece,
                    source=source,
                    section_heading=heading,
                    strategy=strategy,
                    doc_type=doc_type,
                    last_updated=last_updated,
                    chunk_index=idx,
                )
            )
            idx += 1

    return chunks
