from app.services.store import vector_store


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    results = vector_store.search_chunks(query, top_k=top_k)

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