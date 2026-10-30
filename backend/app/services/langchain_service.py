import logging
from typing import Any

try:
    from app.services.llm import _get_groq_api_key, _get_openai_api_key
    from app.services.store import vector_store
    from app.utils.config import settings
except ImportError:
    try:
        from backend.app.services.llm import _get_groq_api_key, _get_openai_api_key  # type: ignore
        from backend.app.services.store import vector_store  # type: ignore
        from backend.app.utils.config import settings  # type: ignore
    except ImportError:
        from .llm import _get_groq_api_key, _get_openai_api_key  # type: ignore
        from .store import vector_store  # type: ignore
        from ..utils.config import settings  # type: ignore

logger = logging.getLogger(__name__)


class LangChainRAGService:
    """Full LangChain RAG implementation using LangChain Expression Language (LCEL).

    Integrates:
    - LangChain Document schema & PromptTemplate
    - LangChain ChatGroq or ChatOpenAI
    - VectorStoreRetriever / Custom Retriever adapter
    - LCEL Runnable chain with StrOutputParser
    """

    def __init__(self) -> None:
        self._is_available = False
        self._check_availability()

    def _check_availability(self) -> bool:
        try:
            import langchain  # noqa: F401
            import langchain_core  # noqa: F401
            self._is_available = True
            return True
        except ImportError:
            self._is_available = False
            return False

    def is_available(self) -> bool:
        return self._check_availability()

    def run_chain(self, query: str, top_k: int = 3) -> dict[str, Any]:
        """Executes document Q&A through the LangChain LCEL pipeline."""
        chunks = vector_store.search_chunks(query, top_k=top_k)
        if not chunks:
            return {
                "answer": "I don't know.",
                "sources": [],
                "pipeline": "langchain_lcel",
            }

        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser

            provider = (getattr(settings, "llm_provider", "groq") or "groq").lower().strip()
            openai_key = _get_openai_api_key()
            groq_key = _get_groq_api_key()

            if provider == "openai" and openai_key:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=openai_key,
                    temperature=0,
                )
            else:
                if not groq_key:
                    raise ValueError(
                        "Groq API key is missing. Please configure GROQ_API_KEY in backend/.env."
                    )
                from langchain_groq import ChatGroq
                llm = ChatGroq(
                    model=settings.groq_model,
                    groq_api_key=groq_key,
                    temperature=0,
                )

            context_text = "\n\n".join(
                f"[Source {i+1}] File: {c.get('source')} | Page: {c.get('page')}\n{c.get('text')}"
                for i, c in enumerate(chunks)
            )

            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are DocuMind, a careful document Q&A assistant built with LangChain.\n"
                    "Answer ONLY using the provided context.\n"
                    "If the answer is not clearly present in the context, reply exactly: I don't know.\n"
                    "Keep the answer concise.\n"
                    "Do not use outside knowledge.",
                ),
                (
                    "human",
                    "Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:",
                ),
            ])

            chain = prompt | llm | StrOutputParser()
            result = chain.invoke({"context": context_text, "question": query})

            return {
                "answer": result.strip() if result else "No answer received.",
                "sources": [
                    {
                        "source": c.get("source", "Unknown"),
                        "page": c.get("page", "Unknown"),
                        "text": c.get("text", ""),
                        "score": round(float(c.get("score", 0.0)), 4),
                        "search_type": c.get("search_type", "hybrid_rrf"),
                    }
                    for c in chunks
                ],
                "pipeline": "langchain_lcel",
            }

        except Exception as exc:
            logger.warning(
                f"LangChain execution encountered issue ({exc}). Using native pipeline fallback."
            )
            from app.services.llm import generate_answer
            answer = generate_answer(query, chunks)
            return {
                "answer": answer,
                "sources": [
                    {
                        "source": c.get("source", "Unknown"),
                        "page": c.get("page", "Unknown"),
                        "text": c.get("text", ""),
                        "score": round(float(c.get("score", 0.0)), 4),
                        "search_type": c.get("search_type", "dense_faiss"),
                    }
                    for c in chunks
                ],
                "pipeline": "native_fallback_langchain_ready",
            }


langchain_service = LangChainRAGService()
