from app.services.store import vector_store


MIN_SIMILARITY_SCORE = 0.25


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    results = vector_store.search_chunks(query, top_k=top_k)
    return [item for item in results if item.get("score", 0.0) >= MIN_SIMILARITY_SCORE]
