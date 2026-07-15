"""Citation validation and source selection."""

import re

from app.models.schemas import SourceChunk


CITATION_PATTERN = re.compile(r"\[C(\d+)\]")


def cited_sources(answer: str, sources: list[SourceChunk]) -> list[SourceChunk]:
    """Return cited sources in citation order, falling back to all retrieved sources."""
    seen: set[int] = set()
    selected: list[SourceChunk] = []
    for match in CITATION_PATTERN.finditer(answer):
        index = int(match.group(1)) - 1
        if 0 <= index < len(sources) and index not in seen:
            selected.append(sources[index])
            seen.add(index)
    return selected or sources


def strip_invalid_citations(answer: str, source_count: int) -> str:
    """Remove labels that do not map to a supplied source chunk."""
    return CITATION_PATTERN.sub(
        lambda match: match.group(0) if 1 <= int(match.group(1)) <= source_count else "",
        answer,
    )

