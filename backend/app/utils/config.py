from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # LLM Provider Configuration ("groq" or "openai")
    llm_provider: str = "groq"
    
    # Groq Settings
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # OpenAI Settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Vector Store Provider ("faiss" or "pinecone")
    vector_store_provider: str = "faiss"
    
    # Pinecone Settings
    pinecone_api_key: str = ""
    pinecone_index_name: str = "documind"
    pinecone_environment: str = ""
    
    # Search & Retrieval Configuration
    enable_hybrid_search: bool = True
    hybrid_alpha: float = 0.6  # Weight for dense vector search (1 - alpha for BM25)
    
    # Storage Configuration
    persistence_dir: str = str(BACKEND_DIR / "data" / "vector_store")

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

