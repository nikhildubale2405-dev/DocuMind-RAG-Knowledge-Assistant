import json
import logging
import math
import os
import re
from pathlib import Path
from threading import Lock
from typing import Any

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore

import numpy as np

try:
    from app.utils.config import settings
except ImportError:
    try:
        from backend.app.utils.config import settings  # type: ignore
    except ImportError:
        from ..utils.config import settings  # type: ignore

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class BM25Okapi:
    """Lightweight in-memory BM25 Okapi implementation for keyword/lexical search."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_lengths: list[int] = []
        self.doc_freqs: list[dict[str, int]] = []
        self.idf: dict[str, float] = {}

    @staticmethod
    def tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def fit(self, corpus_tokens: list[list[str]]) -> None:
        self.corpus_size = len(corpus_tokens)
        if self.corpus_size == 0:
            self.avgdl = 0.0
            self.doc_lengths = []
            self.doc_freqs = []
            self.idf = {}
            return

        self.doc_lengths = [len(doc) for doc in corpus_tokens]
        self.avgdl = sum(self.doc_lengths) / self.corpus_size
        self.doc_freqs = []

        df: dict[str, int] = {}
        for doc in corpus_tokens:
            frequencies: dict[str, int] = {}
            for token in doc:
                frequencies[token] = frequencies.get(token, 0) + 1
            self.doc_freqs.append(frequencies)
            for token in frequencies:
                df[token] = df.get(token, 0) + 1

        self.idf = {}
        for token, freq in df.items():
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query_tokens: list[str]) -> np.ndarray:
        scores = np.zeros(self.corpus_size, dtype=np.float32)
        if self.corpus_size == 0 or self.avgdl == 0:
            return scores

        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for i, doc_freq in enumerate(self.doc_freqs):
                tf = doc_freq.get(token, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[i]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                scores[i] += idf_val * (numerator / denominator)

        return scores


class VectorStore:
    """Production vector store supporting:
    1. Persistent FAISS storage (disk save/load)
    2. BM25 Sparse Lexical search (Hybrid search)
    3. Pinecone enterprise cloud vector DB fallback / provider
    """

    def __init__(self) -> None:
        if SentenceTransformer is not None:
            self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            self.dimension = self.model.get_sentence_embedding_dimension()
        else:
            self.model = None
            self.dimension = 384
            logger.warning(
                "sentence-transformers is not installed. Run: pip install sentence-transformers"
            )

        if faiss is not None:
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = None
            logger.warning("faiss is not installed. Run: pip install faiss-cpu")

        self.metadata: list[dict[str, Any]] = []
        self.bm25 = BM25Okapi()
        self.lock = Lock()

        # Persistence paths
        self.persistence_dir = Path(settings.persistence_dir)
        self.index_path = self.persistence_dir / "faiss.index"
        self.metadata_path = self.persistence_dir / "metadata.json"

        # Load persisted FAISS index if present
        self.load_from_disk()

        # Optional Pinecone client initialization
        self.pinecone_client = None
        self.pinecone_index = None
        self._init_pinecone_if_configured()

    def _init_pinecone_if_configured(self) -> None:
        """Initializes Pinecone if configured in settings."""
        if settings.vector_store_provider.lower() != "pinecone":
            return

        api_key = settings.pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if not api_key:
            logger.warning(
                "VECTOR_STORE_PROVIDER is 'pinecone', but PINECONE_API_KEY is not set. "
                "Defaulting to persistent local FAISS."
            )
            return

        try:
            from pinecone import Pinecone
            self.pinecone_client = Pinecone(api_key=api_key)
            self.pinecone_index = self.pinecone_client.Index(settings.pinecone_index_name)
            logger.info(f"Connected to Pinecone index '{settings.pinecone_index_name}'.")
        except Exception as exc:
            logger.warning(
                f"Failed to initialize Pinecone: {exc}. Defaulting to persistent local FAISS."
            )

    def _embed(self, texts: list[str]) -> np.ndarray:
        if self.model is None:
            raise RuntimeError(
                "sentence-transformers is required for embeddings. Please run: pip install sentence-transformers"
            )
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.astype("float32")

    def save_to_disk(self) -> None:
        """Persists the FAISS index and metadata to disk with error handling."""
        if self.index is None or faiss is None:
            return
        try:
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
            with self.lock:
                temp_index = self.persistence_dir / "faiss.index.tmp"
                temp_meta = self.persistence_dir / "metadata.json.tmp"

                faiss.write_index(self.index, str(temp_index))
                with open(temp_meta, "w", encoding="utf-8") as f:
                    json.dump(self.metadata, f, ensure_ascii=False, indent=2)

                if temp_index.exists():
                    temp_index.replace(self.index_path)
                if temp_meta.exists():
                    temp_meta.replace(self.metadata_path)

            logger.info(
                f"Successfully saved {len(self.metadata)} chunks to persistent FAISS storage at {self.persistence_dir}."
            )
        except Exception as exc:
            logger.error(f"Failed to persist FAISS index to disk: {exc}")

    def load_from_disk(self) -> bool:
        """Loads the persisted FAISS index and metadata from disk on startup."""
        if faiss is None or not self.index_path.exists() or not self.metadata_path.exists():
            return False

        try:
            with self.lock:
                loaded_index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    loaded_metadata = json.load(f)

                if loaded_index.ntotal != len(loaded_metadata):
                    logger.warning(
                        f"Index count ({loaded_index.ntotal}) differs from metadata length ({len(loaded_metadata)}). "
                        "Synchronizing metadata to index count."
                    )
                    min_len = min(loaded_index.ntotal, len(loaded_metadata))
                    loaded_metadata = loaded_metadata[:min_len]

                self.index = loaded_index
                self.metadata = loaded_metadata

                corpus_tokens = [
                    self.bm25.tokenize(item.get("text", "")) for item in self.metadata
                ]
                self.bm25.fit(corpus_tokens)

            logger.info(
                f"Loaded {len(self.metadata)} persistent chunks from {self.persistence_dir} (Index total: {self.index.ntotal})."
            )
            return True
        except Exception as exc:
            logger.warning(f"Could not load persisted FAISS storage: {exc}")
            return False

    def clear(self) -> None:
        """Clears all stored vectors and metadata from memory and disk."""
        with self.lock:
            if faiss is not None:
                self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
            self.bm25 = BM25Okapi()
            try:
                if self.index_path.exists():
                    self.index_path.unlink(missing_ok=True)
                if self.metadata_path.exists():
                    self.metadata_path.unlink(missing_ok=True)
            except Exception as exc:
                logger.warning(f"Error removing persistent index files: {exc}")
        logger.info("Cleared vector store memory and persistent files.")

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self._embed(texts)

        with self.lock:
            start_offset = len(self.metadata)
            if self.index is not None:
                self.index.add(embeddings)
            self.metadata.extend(chunks)

            corpus_tokens = [
                self.bm25.tokenize(item.get("text", "")) for item in self.metadata
            ]
            self.bm25.fit(corpus_tokens)

        self.save_to_disk()

        if self.pinecone_index is not None:
            self._upsert_pinecone(chunks, embeddings, start_offset)

    def _upsert_pinecone(
        self, chunks: list[dict[str, Any]], embeddings: np.ndarray, start_offset: int
    ) -> None:
        """Upserts vectors and metadata into Pinecone index."""
        try:
            vectors_to_upsert = []
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=False)):
                doc_id = f"{chunk.get('source', 'doc')}-{chunk.get('page', 0)}-{start_offset + i}"
                clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", doc_id)
                vectors_to_upsert.append(
                    {
                        "id": clean_id,
                        "values": emb.tolist(),
                        "metadata": {
                            "source": str(chunk.get("source", "Unknown")),
                            "page": int(chunk.get("page", 1)),
                            "text": str(chunk.get("text", ""))[:1000],
                        },
                    }
                )
            self.pinecone_index.upsert(vectors=vectors_to_upsert)
            logger.info(f"Upserted {len(vectors_to_upsert)} vectors to Pinecone.")
        except Exception as exc:
            logger.error(f"Pinecone upsert failed: {exc}")

    def _search_pinecone(self, query_embedding: np.ndarray, top_k: int) -> list[dict[str, Any]]:
        """Queries Pinecone index for top_k results."""
        if self.pinecone_index is None:
            return []
        try:
            res = self.pinecone_index.query(
                vector=query_embedding[0].tolist(),
                top_k=top_k,
                include_metadata=True,
            )
            results = []
            for match in res.get("matches", []):
                meta = match.get("metadata", {})
                results.append(
                    {
                        "source": meta.get("source", "Unknown"),
                        "page": meta.get("page", 1),
                        "text": meta.get("text", ""),
                        "score": float(match.get("score", 0.0)),
                    }
                )
            return results
        except Exception as exc:
            logger.warning(f"Pinecone query failed: {exc}. Falling back to FAISS.")
            return []

    def search_chunks(
        self, query: str, top_k: int = 3, use_hybrid: bool | None = None
    ) -> list[dict[str, Any]]:
        """Searches vector store using dense similarity or hybrid search (FAISS dense + BM25 sparse)."""
        has_index = self.index is not None and self.index.ntotal > 0
        if not has_index and self.pinecone_index is None:
            return []

        should_hybrid = (
            settings.enable_hybrid_search if use_hybrid is None else use_hybrid
        )

        query_embedding = self._embed([query])
        total_vectors = self.index.ntotal if self.index is not None else 0
        candidate_k = min(top_k * 4, max(total_vectors, top_k))

        # 1. Dense FAISS search
        dense_results: list[tuple[int, float]] = []
        with self.lock:
            if self.index is not None and self.index.ntotal > 0:
                scores, indices = self.index.search(
                    query_embedding, min(candidate_k, self.index.ntotal)
                )
                for score, idx in zip(scores[0], indices[0], strict=False):
                    if 0 <= idx < len(self.metadata):
                        dense_results.append((int(idx), float(score)))

        if not dense_results and self.pinecone_index is not None:
            pinecone_matches = self._search_pinecone(query_embedding, top_k)
            if pinecone_matches:
                return pinecone_matches

        if not dense_results:
            return []

        if not should_hybrid or self.bm25.corpus_size == 0:
            top_results = []
            for idx, score in dense_results[:top_k]:
                if 0 <= idx < len(self.metadata):
                    item = dict(self.metadata[idx])
                    item["score"] = float(score)
                    item["search_type"] = "dense_faiss"
                    top_results.append(item)
            return top_results

        # 2. Sparse BM25 search
        query_tokens = self.bm25.tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_k = 60
        fused_scores: dict[int, float] = {}

        for rank, (idx, _) in enumerate(dense_results):
            fused_scores[idx] = fused_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank + 1))

        if len(bm25_scores) > 0 and np.max(bm25_scores) > 0:
            sparse_ranked_indices = np.argsort(bm25_scores)[::-1][:candidate_k]
            for rank, idx in enumerate(sparse_ranked_indices):
                if bm25_scores[idx] > 0:
                    idx = int(idx)
                    if 0 <= idx < len(self.metadata):
                        fused_scores[idx] = fused_scores.get(idx, 0.0) + (
                            1.0 / (rrf_k + rank + 1)
                        )

        sorted_candidates = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for idx, rrf_score in sorted_candidates[:top_k]:
            if 0 <= idx < len(self.metadata):
                item = dict(self.metadata[idx])
                item["score"] = float(rrf_score)
                item["search_type"] = "hybrid_rrf (dense_faiss + sparse_bm25)"
                results.append(item)

        return results


vector_store = VectorStore()
