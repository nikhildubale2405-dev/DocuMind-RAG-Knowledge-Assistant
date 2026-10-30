<<<<<<< HEAD
from pathlib import Path
from time import perf_counter

from fastapi import APIRouter, File, HTTPException, UploadFile, status

try:
    from app.services.parser import chunk_pages, extract_pdf_pages
    from app.services.store import vector_store
except ImportError:
    try:
        from backend.app.services.parser import chunk_pages, extract_pdf_pages  # type: ignore
        from backend.app.services.store import vector_store  # type: ignore
    except ImportError:
        from ..services.parser import chunk_pages, extract_pdf_pages  # type: ignore
        from ..services.store import vector_store  # type: ignore

router = APIRouter(prefix="/upload", tags=["upload"])

MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB production safety limit


@router.post("/", status_code=status.HTTP_200_OK)
async def upload_pdf(file: UploadFile = File(...)):
    start_time = perf_counter()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file filename provided"
        )

    safe_filename = Path(file.filename).name
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported"
        )

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
        )

    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {MAX_PDF_SIZE_BYTES // (1024 * 1024)}MB",
        )

    try:
        pages = extract_pdf_pages(pdf_bytes)
        chunks = chunk_pages(pages, source=safe_filename)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse PDF: {exc}"
        ) from exc

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extractable text found in PDF. Scanned or image-only PDFs require OCR.",
        )
=======
from time import perf_counter

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.parser import chunk_pages, extract_pdf_pages
from app.services.store import vector_store


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
    start_time = perf_counter()

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        pages = extract_pdf_pages(pdf_bytes)
        chunks = chunk_pages(pages, source=file.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse PDF: {exc}") from exc

    if not chunks:
        raise HTTPException(status_code=400, detail="No extractable text found in PDF")
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46

    vector_store.add_chunks(chunks)
    upload_time_seconds = perf_counter() - start_time

    return {
<<<<<<< HEAD
        "message": f"Successfully uploaded and indexed '{safe_filename}'",
        "filename": safe_filename,
        "pages_extracted": len(pages),
        "chunks_indexed": len(chunks),
        "total_chunks_stored": len(vector_store.metadata),
        "persistence": "FAISS on-disk storage active",
        "upload_time_seconds": round(upload_time_seconds, 3),
    }


@router.get("/status")
def get_store_status():
    """Returns vector store indexing, storage metrics, and persistence state."""
    return {
        "total_chunks": len(vector_store.metadata),
        "faiss_total_vectors": vector_store.index.ntotal,
        "bm25_corpus_size": vector_store.bm25.corpus_size,
        "is_persisted": vector_store.index_path.exists(),
        "persistence_path": str(vector_store.persistence_dir),
        "pinecone_enabled": vector_store.pinecone_index is not None,
    }


@router.delete("/clear")
def clear_store():
    """Resets the vector store in-memory and on-disk."""
    vector_store.clear()
    return {"message": "Vector store memory and persistent files cleared successfully"}
=======
        "message": "File uploaded successfully",
        "upload_time_seconds": round(upload_time_seconds, 3),
    }
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
