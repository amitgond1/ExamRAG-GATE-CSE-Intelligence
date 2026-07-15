"""Fast unit tests for deterministic ExamRAG components."""

from app.generation.citations import cited_sources, strip_invalid_citations
from app.ingestion.metadata import infer_metadata
from app.models.schemas import SourceChunk
from app.retrieval.fusion import weighted_reciprocal_rank_fusion


def source(chunk_id: str, score: float = 0.5) -> SourceChunk:
    """Build a compact source fixture."""
    return SourceChunk(chunk_id=chunk_id, text=f"text {chunk_id}", source="notes.pdf", score=score)


def test_weighted_rrf_rewards_agreement() -> None:
    """A chunk appearing in both result lists should win the fusion."""
    fused = weighted_reciprocal_rank_fusion(
        [source("dense-only"), source("both")],
        [source("both"), source("sparse-only")],
        top_k=3,
    )
    assert fused[0].chunk_id == "both"
    assert len({item.chunk_id for item in fused}) == 3


def test_citations_are_bounded_and_ordered() -> None:
    """Only real citation labels should survive or select sources."""
    sources = [source("one"), source("two")]
    answer = "Claim [C2]. Bad [C9]. Another [C2]."
    assert strip_invalid_citations(answer, 2) == "Claim [C2]. Bad . Another [C2]."
    assert [item.chunk_id for item in cited_sources(answer, sources)] == ["two"]


def test_gate_metadata_inference() -> None:
    """Domain keyword inference should recognize operating systems material."""
    metadata = infer_metadata("A process may enter deadlock while holding a semaphore.", "OS.pdf")
    assert metadata["subject"] == "OS"
    assert metadata["topic"] in {"Process", "Deadlock", "Semaphore"}
