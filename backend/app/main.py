from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import query, upload


app = FastAPI(
    title="DocuMind API",
    description="AI-powered document Q&A grounded in uploaded PDF content.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(query.router)


@app.get("/")
def root():
    return {"message": "DocuMind API is running"}
