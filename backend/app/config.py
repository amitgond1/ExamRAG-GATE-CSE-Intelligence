"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime settings for ExamRAG."""

    app_name: str = "ExamRAG"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_model: str = Field(
        default="llama-3.1-70b-versatile", validation_alias="GROQ_MODEL"
    )
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    nli_model: str = "cross-encoder/nli-deberta-v3-base"

    chroma_path: Path = Path("./storage/chroma")
    chroma_collection: str = "gate_cse_materials"
    mlflow_tracking_uri: str = "file:./storage/mlruns"
    upload_path: Path = Path("./storage/uploads")

    chunk_size: int = 500
    chunk_overlap: int = 50
    dense_weight: float = 0.6
    bm25_weight: float = 0.4

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins as a normalized list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached settings instance."""
    return Settings()
