from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.parser import chunk_pages, extract_pdf_pages
from app.services.store import vector_store


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
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

    vector_store.add_chunks(chunks)
    return {"message": "File uploaded successfully"}
