from threading import Lock
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class VectorStore:
    def __init__(self) -> None:
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata: list[dict[str, Any]] = []
        self.lock = Lock()

    def _embed(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.astype("float32")

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self._embed(texts)

        with self.lock:
            self.index.add(embeddings)
            self.metadata.extend(chunks)

    def search_chunks(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        query_embedding = self._embed([query])
        k = min(top_k, self.index.ntotal)

        with self.lock:
            scores, indices = self.index.search(query_embedding, k)

        results: list[dict[str, Any]] = []
        for score, index in zip(scores[0], indices[0], strict=False):
            if index < 0:
                continue

            item = dict(self.metadata[int(index)])
            item["score"] = float(score)
            results.append(item)

        return results


vector_store = VectorStore()
