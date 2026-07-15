"""Weighted reciprocal-rank fusion for dense and sparse results."""

from app.models.schemas import SourceChunk


def weighted_reciprocal_rank_fusion(
    dense: list[SourceChunk],
    sparse: list[SourceChunk],
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
    top_k: int = 10,
    rank_constant: int = 60,
) -> list[SourceChunk]:
    """Fuse ranked lists without requiring calibrated score distributions."""
    if dense_weight < 0 or sparse_weight < 0 or dense_weight + sparse_weight == 0:
        raise ValueError("Fusion weights must be non-negative and not both zero")
    by_id: dict[str, SourceChunk] = {}
    scores: dict[str, float] = {}
    for results, weight in ((dense, dense_weight), (sparse, sparse_weight)):
        for rank, chunk in enumerate(results, start=1):
            by_id[chunk.chunk_id] = chunk
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + weight / (
                rank_constant + rank
            )
    ranked_ids = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [by_id[chunk_id].model_copy(update={"score": scores[chunk_id]}) for chunk_id in ranked_ids]

