"""Shared retrieval helpers."""

from typing import Any

from app.models.schemas import SourceChunk


def to_source_chunk(
    chunk_id: str,
    text: str,
    metadata: dict[str, Any] | None,
    score: float,
) -> SourceChunk:
    """Convert raw store data into a stable API source model."""
    metadata = metadata or {}
    return SourceChunk(
        chunk_id=chunk_id,
        text=text,
        source=str(metadata.get("source", "unknown")),
        page=int(metadata["page"]) if metadata.get("page") is not None else None,
        subject=str(metadata.get("subject", "Unknown")),
        topic=str(metadata.get("topic", "General")),
        difficulty=str(metadata.get("difficulty", "unknown")),
        score=round(float(score), 6),
    )

