from typing import Any

try:
    from app.services.store import vector_store
except ImportError:
    try:
        from backend.app.services.store import vector_store  # type: ignore
    except ImportError:
        from .store import vector_store  # type: ignore


def retrieve(
    query: str, top_k: int = 3, use_hybrid: bool | None = None
) -> list[dict[str, Any]]:
    """Retrieves top_k relevant document chunks using hybrid search (FAISS + BM25) or pure dense search."""
    results = vector_store.search_chunks(query, top_k=top_k, use_hybrid=use_hybrid)

    cleaned_results = []
    for item in results:
        # keep the result even if score is missing
        score = item.get("score", None)

        if score is not None:
            try:
                item["score"] = float(score)
            except (TypeError, ValueError):
                item["score"] = 0.0
        else:
            item["score"] = 0.0

        cleaned_results.append(item)

    return cleaned_results
