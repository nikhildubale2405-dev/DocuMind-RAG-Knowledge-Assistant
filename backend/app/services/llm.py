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
        context_parts.append(
            f"[Source {index}] File: {chunk['source']} | Page: {chunk['page']}\n{chunk['text']}"
        )
    return "\n\n".join(context_parts)


def generate_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I don't know"

    if not settings.groq_api_key or settings.groq_api_key == "your_api_key_here":
        return "Groq API key is not configured. Set GROQ_API_KEY in backend/.env."

    client = Groq(api_key=settings.groq_api_key)
    context = build_context(chunks)

    prompt = f"""Context:
{context}

Question:
{query}

Answer:"""

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
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
