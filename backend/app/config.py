"""
Centralized application configuration.

All values are read from environment variables (see .env.example).
Using pydantic-settings so misconfiguration fails fast, at startup,
instead of surfacing as a confusing runtime error deep in a request.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- LLM provider ---
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.3

    # --- Embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Vector store ---
    faiss_index_dir: str = "app/data/faiss_index"
    documents_dir: str = "app/data/documents"
    chunk_size: int = 800
    chunk_overlap: int = 120
    retriever_top_k: int = 4

    # --- API ---
    api_title: str = "Enterprise AI Customer Support Agent"
    api_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Escalation ---
    escalation_confidence_threshold: float = 0.55

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
