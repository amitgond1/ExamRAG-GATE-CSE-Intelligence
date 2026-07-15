"""Prompt templates that enforce context-grounded GATE CSE answers."""

from app.models.schemas import SourceChunk


SYSTEM_PROMPT = """You are ExamRAG, a precise GATE Computer Science expert.
Answer the user's question using ONLY the supplied context. Do not use outside
knowledge, even when you know the answer. If the context does not contain enough
evidence, respond exactly: "I don't have enough information in the provided study material."

Rules:
1. Explain the answer clearly at GATE exam depth and show essential reasoning.
2. Cite every factual claim with one or more inline chunk citations such as [C1] or [C2].
3. Never invent a citation, source, formula, or fact.
4. A citation label must refer to the context block carrying that label.
5. Keep the response concise unless the question requires a derivation.
"""


def build_context(chunks: list[SourceChunk]) -> str:
    """Format retrieved chunks as numbered, provenance-rich prompt blocks."""
    blocks = []
    for index, chunk in enumerate(chunks, start=1):
        location = f"page {chunk.page}" if chunk.page is not None else "page unknown"
        blocks.append(
            f"[C{index}] Source: {chunk.source}; {location}; "
            f"subject: {chunk.subject}; topic: {chunk.topic}\n{chunk.text}"
        )
    return "\n\n".join(blocks)


def build_user_prompt(question: str, chunks: list[SourceChunk]) -> str:
    """Combine a question and retrieved context into the generation request."""
    return f"CONTEXT:\n{build_context(chunks)}\n\nQUESTION:\n{question}"

