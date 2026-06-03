from functools import lru_cache
import os

from groq import Groq

from app.utils.config import settings


SYSTEM_PROMPT = """You are DocuMind, a careful document Q&A assistant.
Answer ONLY using the provided context.
If the answer is not clearly present in the context, reply exactly: I don't know.
Keep the answer concise.
Do not use outside knowledge."""


def build_context(chunks: list[dict]) -> str:
    context_parts = []
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "Unknown")
        page = chunk.get("page", "Unknown")
        text = chunk.get("text", "")
        context_parts.append(
            f"[Source {index}] File: {source} | Page: {page}\n{text}"
        )
    return "\n\n".join(context_parts)


def _get_api_key() -> str | None:
    # Hugging Face Secrets / local env fallback
    api_key = os.getenv("GROQAPIKEY") or settings.groq_api_key or os.getenv("GROQ_API_KEY")
    if api_key:
        api_key = api_key.strip()
    return api_key or None


@lru_cache(maxsize=1)
def _get_client() -> Groq:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "Groq API key is not configured. Add the Hugging Face secret as GROQAPIKEY or GROQ_API_KEY."
        )
    return Groq(api_key=api_key)


def generate_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I don't know"

    context = build_context(chunks)

    prompt = f"""Context:
{context}

Question:
{query}

Answer:"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=getattr(settings, "groq_model", "llama3-8b-8192"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=300,
        )
    except Exception as exc:
        return f"LLM request failed: {exc}"

    answer = response.choices[0].message.content if response.choices else ""
    return answer.strip() if answer else "No answer received"
