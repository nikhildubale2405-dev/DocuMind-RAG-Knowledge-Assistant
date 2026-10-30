import re
from io import BytesIO
from typing import Any

<<<<<<< HEAD
try:
    from pypdf import PdfReader
    from pypdf.errors import FileNotDecryptedError, PdfReadError
except ImportError:
    PdfReader = None  # type: ignore
    FileNotDecryptedError = Exception  # type: ignore
    PdfReadError = Exception  # type: ignore
=======
from pypdf import PdfReader

>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def clean_text(text: str) -> str:
<<<<<<< HEAD
    """Normalizes whitespace and removes null bytes or unprintable control characters."""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extracts text from PDF pages with 1-based page indexing and error resilience."""
    if PdfReader is None:
        raise RuntimeError(
            "pypdf is not installed. Please run: pip install pypdf==5.1.0"
        )

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise ValueError(f"Invalid or corrupted PDF file: {exc}") from exc

    if reader.is_encrypted:
        try:
            decrypt_success = reader.decrypt("")
            if not decrypt_success:
                raise FileNotDecryptedError("Password required to read encrypted PDF.")
        except Exception as exc:
            raise ValueError(f"Encrypted PDF cannot be read without a password: {exc}") from exc

    pages: list[dict[str, Any]] = []

    for index, page in enumerate(reader.pages, start=1):
        try:
            raw_text = page.extract_text() or ""
            text = clean_text(raw_text)
            if text:
                pages.append({"page": index, "text": text})
        except Exception:
            continue
=======
    return re.sub(r"\s+", " ", text).strip()


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict[str, Any]]:
    reader = PdfReader(BytesIO(pdf_bytes))
    pages: list[dict[str, Any]] = []

    for index, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append({"page": index, "text": text})
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46

    return pages


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
<<<<<<< HEAD
    """Splits text into chunks with smart word-boundary snapping to preserve context coherence."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be strictly greater than overlap")

    if not text:
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        if end < text_len:
            snap_pos = text.rfind(" ", start + (chunk_size // 2), end)
            if snap_pos != -1:
                end = snap_pos

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        start = max(end - overlap, start + 1)
=======
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
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46

    return chunks


def chunk_pages(pages: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
<<<<<<< HEAD
    """Generates structured chunks tagged with document source and page number."""
=======
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
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
