"""ChromaDB persistent client and collection setup."""

from functools import lru_cache

import chromadb
from chromadb import Collection

from app.config import get_settings
from app.ingestion.embedder import BGEEmbeddingFunction


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    """Create the local persistent Chroma client once per process."""
    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_path))


@lru_cache(maxsize=1)
def get_collection() -> Collection:
    """Return the cosine-similarity collection used by ExamRAG."""
    settings = get_settings()
    return get_chroma_client().get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=BGEEmbeddingFunction(settings.embedding_model),
        metadata={"hnsw:space": "cosine", "description": "GATE CSE study chunks"},
    )
