import os
import logging
from groq import Groq
from app.utils.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are DocuMind, a careful document Q&A assistant.
Answer ONLY using the provided context.
If the answer is not clearly present in the context, reply exactly: I don't know.
Keep the answer concise.
Do not use outside knowledge."""

PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.2-3b-preview",
    "llama-3.2-1b-preview",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]


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
    candidates = [
        os.getenv("GROQAPIKEY"),
        os.getenv("GROQ_API_KEY"),
        getattr(settings, "groq_api_key", ""),
    ]
    placeholders = {"GROQAPIKEY", "your_groq_api_key_here", "your_key_here", ""}
    for key in candidates:
        if not key:
            continue
        cleaned = key.strip()
        if cleaned and cleaned not in placeholders:
            return cleaned
    return None


def _get_client() -> Groq:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "Groq API key is missing or set to placeholder. "
            "Please add a valid Groq API key (starts with 'gsk_') to backend/.env (GROQ_API_KEY=gsk_...) "
            "or set GROQ_API_KEY in your environment/Hugging Face Secrets."
        )
    return Groq(api_key=api_key)


def _discover_fallback_model(client: Groq) -> str | None:
    """Finds an available chat completion model from the user's Groq account."""
    try:
        model_list = client.models.list()
        available_ids = [m.id for m in model_list.data]
        
        # Check against preferred list first
        for preferred in PREFERRED_MODELS:
            if preferred in available_ids:
                return preferred
        
        # Otherwise find first model that isn't whisper/guard/embed
        for model_id in available_ids:
            lower = model_id.lower()
            if not any(skip in lower for skip in ["whisper", "guard", "embed", "tts", "audio"]):
                return model_id
    except Exception as e:
        logger.warning(f"Failed to query Groq models list: {e}")
    return None


def generate_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I don't know"

    context = build_context(chunks)

    prompt = f"""Context:
{context}

Question:
{query}

Answer:"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        client = _get_client()
    except Exception as exc:
        return f"Configuration Error: {exc}"

    # Determine initial model to try
    model_name = getattr(settings, "groq_model", "").strip() or "llama-3.3-70b-versatile"
    # If the user or config still had the deprecated 3.1 8b instant, switch to 3.3 70b
    if "llama-3.1-8b" in model_name:
        model_name = "llama-3.3-70b-versatile"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
            max_tokens=300,
        )
    except Exception as exc:
        err_msg = str(exc)

        # Handle decommissioned or inaccessible model with automatic fallback
        if "model_not_found" in err_msg or "does not exist or you do not have access" in err_msg:
            fallback = _discover_fallback_model(client)
            if fallback and fallback != model_name:
                try:
                    response = client.chat.completions.create(
                        model=fallback,
                        messages=messages,
                        temperature=0,
                        max_tokens=300,
                    )
                    answer = response.choices[0].message.content if response.choices else ""
                    return answer.strip() if answer else "No answer received"
                except Exception as retry_exc:
                    return f"LLM request failed with fallback model '{fallback}': {retry_exc}"

            return (
                f"Groq Error: Model '{model_name}' is deprecated or unavailable on your Groq account. "
                f"Please update GROQ_MODEL in backend/.env to a supported model such as 'llama-3.3-70b-versatile'."
            )

        if "organization_restricted" in err_msg:
            return (
                "Groq Error: The organization associated with this API key has been restricted by Groq. "
                "Please verify your account status at https://console.groq.com/keys, "
                "or generate an API key from an active Groq account and update GROQ_API_KEY."
            )

        if "invalid_api_key" in err_msg or "Invalid API Key" in err_msg:
            return (
                "Groq Error: Invalid API key. Please check that GROQ_API_KEY in backend/.env "
                "or your environment contains a valid 'gsk_...' key."
            )

        return f"LLM request failed: {exc}"

    answer = response.choices[0].message.content if response.choices else ""
    return answer.strip() if answer else "No answer received"
