"""RAG orchestration for retrieval, generation, and source attribution."""

import time
from collections.abc import AsyncIterator
from functools import lru_cache

import anyio

from app.generation.citations import cited_sources, strip_invalid_citations
from app.generation.llm import GroqGenerator
from app.models.schemas import ChatResponse, RetrievalStrategy, SourceChunk
from app.retrieval.service import RetrievalService


class RAGService:
    """Coordinate retrieval and grounded generation."""

    def __init__(self) -> None:
        self.retrieval = RetrievalService()
        self.generator = GroqGenerator()

    async def answer(self, question: str, strategy: RetrievalStrategy) -> ChatResponse:
        """Retrieve evidence and produce a validated complete answer."""
        started = time.perf_counter()
        sources = await anyio.to_thread.run_sync(self.retrieval.retrieve, question, strategy)
        answer = await self.generator.generate(question, sources)
        answer = strip_invalid_citations(answer, len(sources))
        return ChatResponse(
            answer=answer,
            strategy=strategy,
            sources=cited_sources(answer, sources),
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )

    async def stream_answer(
        self, question: str, strategy: RetrievalStrategy
    ) -> tuple[list[SourceChunk], AsyncIterator[str]]:
        """Retrieve once, then return sources and an async generation stream."""
        sources = await anyio.to_thread.run_sync(self.retrieval.retrieve, question, strategy)
        return sources, self.generator.stream(question, sources)


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """Return the shared RAG service."""
    return RAGService()
