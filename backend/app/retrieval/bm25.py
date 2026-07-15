"""In-memory BM25 index backed by documents persisted in ChromaDB."""

import re
from threading import RLock

from chromadb import Collection
from rank_bm25 import BM25Okapi

from app.models.schemas import SourceChunk
from app.retrieval.common import to_source_chunk


def tokenize(text: str) -> list[str]:
    """Tokenize English technical text for sparse matching."""
    return re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)?", text.lower())


class BM25Retriever:
    """Build a refreshable BM25 index over all Chroma documents."""

    def __init__(self, collection: Collection) -> None:
        self.collection = collection
        self._lock = RLock()
        self._indexed_count = -1
        self._ids: list[str] = []
        self._documents: list[str] = []
        self._metadatas: list[dict] = []
        self._index: BM25Okapi | None = None

    def _refresh_if_needed(self) -> None:
        count = self.collection.count()
        if count == self._indexed_count:
            return
        with self._lock:
            if count == self._indexed_count:
                return
            raw = self.collection.get(include=["documents", "metadatas"])
            self._ids = list(raw.get("ids", []))
            self._documents = list(raw.get("documents") or [])
            self._metadatas = list(raw.get("metadatas") or [])
            corpus = [tokenize(document) for document in self._documents]
            self._index = BM25Okapi(corpus) if corpus else None
            self._indexed_count = count

    def retrieve(self, query: str, top_k: int = 10) -> list[SourceChunk]:
        """Return normalized BM25 matches for a query."""
        self._refresh_if_needed()
        if self._index is None:
            return []
        scores = self._index.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)[:top_k]
        max_score = max((float(score) for _, score in ranked), default=0.0)
        return [
            to_source_chunk(
                self._ids[index],
                self._documents[index],
                self._metadatas[index],
                float(score) / max_score if max_score > 0 else 0.0,
            )
            for index, score in ranked
        ]

