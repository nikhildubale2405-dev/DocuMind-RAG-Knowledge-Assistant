import re
from io import BytesIO
from typing import Any

from pypdf import PdfReader


CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict[str, Any]]:
    reader = PdfReader(BytesIO(pdf_bytes))
    pages: list[dict[str, Any]] = []

    for index, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append({"page": index, "text": text})

    return pages


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def chunk_pages(pages: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []

    for page in pages:
        for text in split_text(page["text"]):
            chunks.append(
                {
                    "source": source,
                    "page": page["page"],
                    "text": text,
                }
            )

    return chunks
