"""Sentence-transformers embedding function compatible with ChromaDB."""

from functools import lru_cache

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer


class BGEEmbeddingFunction(EmbeddingFunction[Documents]):
    """Normalize BGE embeddings for cosine-distance retrieval."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @staticmethod
    @lru_cache(maxsize=2)
    def _load(model_name: str) -> SentenceTransformer:
        return SentenceTransformer(model_name)

    def __call__(self, input: Documents) -> Embeddings:
        model = self._load(self.model_name)
        vectors = model.encode(
            list(input), normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()

    def name(self) -> str:
        """Return a stable identifier used by newer Chroma clients."""
        return f"sentence-transformers-{self.model_name.replace('/', '-') }"

