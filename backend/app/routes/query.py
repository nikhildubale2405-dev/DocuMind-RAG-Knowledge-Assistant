from time import perf_counter

from fastapi import APIRouter, HTTPException, Query
from app.services.llm import generate_answer
from app.services.retriever import retrieve

router = APIRouter(prefix="/query", tags=["query"])

@router.post("/")
async def query_documents(query: str = Query(..., min_length=1)):
    start_time = perf_counter()
    cleaned_query = query.strip()
    if not cleaned_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = retrieve(cleaned_query, top_k=3)

    print("RESULT COUNT:", len(results))
    for item in results:
        print(item.get("source"), item.get("page"), item.get("text", "")[:150])

    if not results:
        return {
            "answer": "I don't know.",
            "answer_time_seconds": round(perf_counter() - start_time, 3),
            "sources": [],
        }

    answer = generate_answer(cleaned_query, results)
    if not answer or not answer.strip():
        answer = "No answer received."

    return {
        "answer": answer.strip(),
        "answer_time_seconds": round(perf_counter() - start_time, 3),
        "sources": [
            {
                "source": item.get("source", "Unknown"),
                "page": item.get("page", "Unknown"),
                "text": item.get("text", ""),
            }
            for item in results
        ],
    }
