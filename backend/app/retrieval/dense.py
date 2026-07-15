"""Cosine dense retrieval from ChromaDB."""

from chromadb import Collection

from app.models.schemas import SourceChunk
from app.retrieval.common import to_source_chunk


class DenseRetriever:
    """Retrieve chunks using normalized BGE embeddings and cosine distance."""

    def __init__(self, collection: Collection) -> None:
        self.collection = collection

    def retrieve(self, query: str, top_k: int = 5) -> list[SourceChunk]:
        """Return the top-k chunks, with similarity normalized to higher-is-better."""
        count = self.collection.count()
        if count == 0:
            return []
        result = self.collection.query(
            query_texts=[query], n_results=min(top_k, count), include=["documents", "metadatas", "distances"]
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            to_source_chunk(chunk_id, text, metadata, max(0.0, 1.0 - distance))
            for chunk_id, text, metadata, distance in zip(
                ids, documents, metadatas, distances, strict=False
            )
        ]

