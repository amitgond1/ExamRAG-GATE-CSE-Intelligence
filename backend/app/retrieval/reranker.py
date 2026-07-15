"""Cross-encoder reranking of candidate chunks."""

from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.models.schemas import SourceChunk


class CrossEncoderReranker:
    """Score query/chunk pairs jointly for stronger final ranking."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @staticmethod
    @lru_cache(maxsize=2)
    def _load(model_name: str) -> CrossEncoder:
        return CrossEncoder(model_name)

    def rerank(
        self, query: str, candidates: list[SourceChunk], top_k: int = 5
    ) -> list[SourceChunk]:
        """Rerank candidates by cross-encoder relevance score."""
        if not candidates:
            return []
        pairs = [(query, candidate.text) for candidate in candidates]
        scores = self._load(self.model_name).predict(pairs, show_progress_bar=False)
        reranked = [
            candidate.model_copy(update={"score": float(score)})
            for candidate, score in zip(candidates, scores, strict=False)
        ]
        return sorted(reranked, key=lambda item: item.score, reverse=True)[:top_k]




