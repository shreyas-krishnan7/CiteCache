
from __future__ import annotations

import io


_DOCX_HEADING_STYLE_TO_LEVEL = {
    "Title": 1,
    "Heading 1": 1,
    "Heading 2": 2,
    "Heading 3": 3,
    "Heading 4": 4,
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages_text).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    lines: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style_name = para.style.name if para.style else ""
        level = _DOCX_HEADING_STYLE_TO_LEVEL.get(style_name)
        lines.append(f"{'#' * level} {text}" if level else text)
    return "\n\n".join(lines).strip()


def extract_text_from_plain(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8")


SUPPORTED_EXTENSIONS = {"md", "txt", "pdf", "docx"}


def extract_text(filename: str, file_bytes: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        text = extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        text = extract_text_from_docx(file_bytes)
    elif ext in ("md", "txt"):
        text = extract_text_from_plain(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type '.{ext}' for {filename!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if not text.strip():
        raise ValueError(
            f"No extractable text found in {filename!r}. "
            f"If this is a scanned/image-only PDF, text extraction won't work without OCR."
        )
    return text
