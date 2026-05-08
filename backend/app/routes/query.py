from fastapi import APIRouter, HTTPException, Query

from app.services.llm import generate_answer
from app.services.retriever import retrieve


router = APIRouter(prefix="/query", tags=["query"])


@router.post("/")
async def query_documents(query: str = Query(..., min_length=1)):
    cleaned_query = query.strip()
    if not cleaned_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = retrieve(cleaned_query, top_k=3)
    if not results:
        return {"answer": "I don't know", "sources": []}

    answer = generate_answer(cleaned_query, results)
    if not answer:
        answer = "No answer received"

    sources = [
        {
            "source": item["source"],
            "page": item["page"],
            "text": item["text"],
        }
        for item in results
    ]
    return {"answer": answer, "sources": sources}
