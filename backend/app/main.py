import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Ensure backend directory is in sys.path regardless of execution root
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app.routes import query, upload
except ImportError:
    try:
        from backend.app.routes import query, upload  # type: ignore
    except ImportError:
        from .routes import query, upload  # type: ignore


def _resolve_frontend_dir() -> Path:
    candidates = [
        CURRENT_FILE.parents[2] / "frontend",
        CURRENT_FILE.parents[1] / "frontend",
        Path.cwd() / "frontend",
        Path.cwd().parent / "frontend",
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / "index.html").exists():
            return candidate
    return candidates[0]


FRONTEND_DIR = _resolve_frontend_dir()

app = FastAPI(
    title="DocuMind API",
    description="AI-powered document Q&A grounded in uploaded PDF content with hybrid search and persistent storage.",
    version="1.0.0",
)

# Standard production CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(query.router)

# Mount static frontend assets if directory exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        content={
            "service": "DocuMind API",
            "status": "online",
            "docs": "/docs",
            "message": "Frontend index.html not found at expected static path.",
        }
    )


@app.get("/health", tags=["system"])
def health_check():
    """Healthcheck endpoint for Docker containers, Kubernetes probes, and monitoring."""
    return {
        "status": "healthy",
        "service": "DocuMind API",
        "version": "1.0.0",
    }
