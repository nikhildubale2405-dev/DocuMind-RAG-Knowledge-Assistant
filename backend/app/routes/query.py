from time import perf_counter
<<<<<<< HEAD
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from app.services.langchain_service import langchain_service
    from app.services.llm import generate_answer
    from app.services.retriever import retrieve
except ImportError:
    try:
        from backend.app.services.langchain_service import langchain_service  # type: ignore
        from backend.app.services.llm import generate_answer  # type: ignore
        from backend.app.services.retriever import retrieve  # type: ignore
    except ImportError:
        from ..services.langchain_service import langchain_service  # type: ignore
        from ..services.llm import generate_answer  # type: ignore
        from ..services.retriever import retrieve  # type: ignore

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question to ask based on uploaded documents")
    top_k: int = Field(3, ge=1, le=10, description="Number of context chunks to retrieve")
    use_hybrid: bool = Field(True, description="Enable hybrid search (FAISS dense + BM25 sparse)")
    use_langchain: bool = Field(False, description="Process question using LangChain LCEL pipeline")


@router.post("/", status_code=status.HTTP_200_OK)
async def query_documents(
    payload: Optional[QueryRequest] = None,
    query: Optional[str] = Query(None, description="Query parameter fallback"),
    top_k: int = Query(3, ge=1, le=10, description="Number of context chunks to retrieve"),
    use_hybrid: bool = Query(True, description="Enable hybrid search"),
    use_langchain: bool = Query(False, description="Enable LangChain pipeline"),
):
    """Processes document Q&A supporting either a JSON request body or URL query parameters."""
    start_time = perf_counter()

    if payload is not None:
        raw_query = payload.query
        effective_top_k = payload.top_k
        effective_use_hybrid = payload.use_hybrid
        effective_use_langchain = payload.use_langchain
    elif query is not None:
        raw_query = query
        effective_top_k = top_k
        effective_use_hybrid = use_hybrid
        effective_use_langchain = use_langchain
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A 'query' string must be provided in either the request body or as a query parameter.",
        )

    cleaned_query = raw_query.strip()
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty"
        )

    # 1. Optional LangChain pipeline branch
    if effective_use_langchain:
        result = langchain_service.run_chain(cleaned_query, top_k=effective_top_k)
        result["answer_time_seconds"] = round(perf_counter() - start_time, 3)
        return result

    # 2. Native high-performance hybrid retrieval
    results = retrieve(cleaned_query, top_k=effective_top_k, use_hybrid=effective_use_hybrid)
=======

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
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46

    if not results:
        return {
            "answer": "I don't know.",
            "answer_time_seconds": round(perf_counter() - start_time, 3),
            "sources": [],
<<<<<<< HEAD
            "pipeline": "hybrid_faiss_bm25",
        }

    # 3. Grounded answer generation
=======
        }

>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
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
<<<<<<< HEAD
                "score": round(float(item.get("score", 0.0)), 4),
                "search_type": item.get("search_type", "dense_faiss"),
            }
            for item in results
        ],
        "pipeline": "hybrid_faiss_bm25",
    }


@router.post("/langchain", status_code=status.HTTP_200_OK)
async def query_documents_langchain(
    payload: Optional[QueryRequest] = None,
    query: Optional[str] = Query(None),
    top_k: int = Query(3, ge=1, le=10),
):
    """Dedicated endpoint to execute question answering through LangChain LCEL chain."""
    start_time = perf_counter()

    raw_query = payload.query if payload else query
    if not raw_query or not raw_query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty"
        )

    effective_top_k = payload.top_k if payload else top_k
    result = langchain_service.run_chain(raw_query.strip(), top_k=effective_top_k)
    result["answer_time_seconds"] = round(perf_counter() - start_time, 3)
    return result
=======
            }
            for item in results
        ],
    }
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
