from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Insurance Policy RAG API"
    app_version: str = "0.1.0"
    environment: str = "development"

    openai_api_key: str = Field(repr=False)
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    database_url: str = (
        "postgresql+psycopg://rag_user:rag_password@db:5432/rag_db"
    )
    pgvector_collection: str = "insurance_policy_chunks"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    default_top_k: int = 4

    user_agent: str = "insurance-policy-rag/0.1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
