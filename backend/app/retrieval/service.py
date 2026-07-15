"""Strategy dispatcher for ExamRAG retrieval experiments."""

from app.config import get_settings
from app.db.chroma_client import get_collection
from app.models.schemas import RetrievalStrategy, SourceChunk
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.fusion import weighted_reciprocal_rank_fusion
from app.retrieval.reranker import CrossEncoderReranker


class RetrievalService:
    """Expose the three portfolio retrieval strategies behind one interface."""

    def __init__(self) -> None:
        settings = get_settings()
        collection = get_collection()
        self.dense = DenseRetriever(collection)
        self.bm25 = BM25Retriever(collection)
        self.reranker = CrossEncoderReranker(settings.reranker_model)
        self.dense_weight = settings.dense_weight
        self.bm25_weight = settings.bm25_weight

    def retrieve(self, query: str, strategy: RetrievalStrategy) -> list[SourceChunk]:
        """Execute Strategy A, B, or C with the requested candidate depths."""
        if strategy == RetrievalStrategy.DENSE:
            return self.dense.retrieve(query, top_k=5)

        candidate_k = 20 if strategy == RetrievalStrategy.HYBRID_RERANK else 10
        dense = self.dense.retrieve(query, top_k=candidate_k)
        sparse = self.bm25.retrieve(query, top_k=candidate_k)
        fused = weighted_reciprocal_rank_fusion(
            dense,
            sparse,
            dense_weight=self.dense_weight,
            sparse_weight=self.bm25_weight,
            top_k=candidate_k,
        )
        if strategy == RetrievalStrategy.HYBRID_RERANK:
            return self.reranker.rerank(query, fused, top_k=5)
        return fused
