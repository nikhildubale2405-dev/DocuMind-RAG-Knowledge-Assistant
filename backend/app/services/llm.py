import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Optional

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore

try:
    from app.utils.config import settings
except ImportError:
    try:
        from backend.app.utils.config import settings  # type: ignore
    except ImportError:
        from ..utils.config import settings  # type: ignore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are DocuMind, a careful document Q&A assistant.
Answer ONLY using the provided context.
If the answer is not clearly present in the context, reply exactly: I don't know.
Keep the answer concise.
Do not use outside knowledge."""

PREFERRED_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.2-3b-preview",
    "llama-3.2-1b-preview",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]


def build_context(chunks: list[dict[str, Any]]) -> str:
    context_parts = []
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "Unknown")
        page = chunk.get("page", "Unknown")
        text = chunk.get("text", "")
        context_parts.append(
            f"[Source {index}] File: {source} | Page: {page}\n{text}"
        )
    return "\n\n".join(context_parts)


def _get_groq_api_key() -> Optional[str]:
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


def _get_openai_api_key() -> Optional[str]:
    candidates = [
        os.getenv("OPENAI_API_KEY"),
        getattr(settings, "openai_api_key", ""),
    ]
    placeholders = {"your_openai_api_key_here", "your_key_here", ""}
    for key in candidates:
        if not key:
            continue
        cleaned = key.strip()
        if cleaned and cleaned not in placeholders:
            return cleaned
    return None


def _get_groq_client() -> Any:
    if Groq is None:
        raise ValueError(
            "The 'groq' package is not installed in the active Python environment. "
            "Please install dependencies with: pip install -r backend/requirements.txt"
        )
    api_key = _get_groq_api_key()
    if not api_key:
        raise ValueError(
            "Groq API key is missing or set to placeholder. "
            "Please add a valid Groq API key (starts with 'gsk_') to backend/.env (GROQ_API_KEY=gsk_...) "
            "or set GROQ_API_KEY in your environment/Hugging Face Secrets."
        )
    return Groq(api_key=api_key)


def _discover_groq_fallback_model(client: Any) -> Optional[str]:
    """Finds an available chat completion model from the user's Groq account."""
    try:
        model_list = client.models.list()
        available_ids = [m.id for m in model_list.data]

        for preferred in PREFERRED_GROQ_MODELS:
            if preferred in available_ids:
                return preferred

        for model_id in available_ids:
            lower = model_id.lower()
            if not any(skip in lower for skip in ["whisper", "guard", "embed", "tts", "audio"]):
                return model_id
    except Exception as e:
        logger.warning(f"Failed to query Groq models list: {e}")
    return None


def _call_openai(messages: list[dict[str, str]], model: Optional[str] = None) -> str:
    """Invokes OpenAI Chat Completions API using either the openai library or standard HTTP request."""
    api_key = _get_openai_api_key()
    if not api_key:
        raise ValueError(
            "OpenAI API key is missing. Please set OPENAI_API_KEY in backend/.env or your environment."
        )

    selected_model = model or getattr(settings, "openai_model", "gpt-4o-mini")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,  # type: ignore
            temperature=0,
            max_tokens=300,
        )
        return response.choices[0].message.content or ""
    except ImportError:
        payload = json.dumps({
            "model": selected_model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 300,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"] or ""


def _call_groq(messages: list[dict[str, str]], model: Optional[str] = None) -> str:
    """Invokes Groq Chat Completions API with automatic model deprecation fallback."""
    client = _get_groq_client()
    model_name = model or getattr(settings, "groq_model", "").strip() or "llama-3.3-70b-versatile"
    if "llama-3.1-8b" in model_name:
        model_name = "llama-3.3-70b-versatile"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
            max_tokens=300,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        err_msg = str(exc)
        if "model_not_found" in err_msg or "does not exist or you do not have access" in err_msg:
            fallback = _discover_groq_fallback_model(client)
            if fallback and fallback != model_name:
                response = client.chat.completions.create(
                    model=fallback,
                    messages=messages,
                    temperature=0,
                    max_tokens=300,
                )
                return response.choices[0].message.content or ""
        raise exc


def generate_answer(query: str, chunks: list[dict[str, Any]]) -> str:
    """Generates a grounded answer from context using Groq or OpenAI."""
    if not chunks:
        return "I don't know."

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

    provider = (getattr(settings, "llm_provider", "groq") or "groq").lower().strip()

    # Route based on provider preference
    if provider == "openai":
        try:
            answer = _call_openai(messages)
            return answer.strip() if answer else "No answer received."
        except Exception as oai_err:
            logger.warning(f"OpenAI call failed ({oai_err}), attempting Groq fallback if configured...")
            try:
                answer = _call_groq(messages)
                return answer.strip() if answer else "No answer received."
            except Exception:
                return f"OpenAI Error: {oai_err}"

    # Default: Groq provider with optional OpenAI fallback
    try:
        answer = _call_groq(messages)
        return answer.strip() if answer else "No answer received."
    except Exception as exc:
        err_msg = str(exc)

        # Check for OpenAI fallback if key is configured
        if _get_openai_api_key():
            try:
                logger.info("Falling back to OpenAI chat completion...")
                answer = _call_openai(messages)
                return answer.strip() if answer else "No answer received."
            except Exception as oai_fallback_err:
                logger.error(f"OpenAI fallback also failed: {oai_fallback_err}")

        # If it was a missing key or missing package ValueError, return the direct clean message
        if "Groq API key is missing" in err_msg or "package is not installed" in err_msg:
            return err_msg

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
