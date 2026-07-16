"""Asynchronous Groq-backed answer generation."""

from collections.abc import AsyncIterator

from groq import AsyncGroq, APIConnectionError, APIStatusError, APITimeoutError

from app.config import get_settings
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models.schemas import SourceChunk


INSUFFICIENT_CONTEXT_ANSWER = (
    "I don't have enough information in the provided study material."
)


class GenerationError(RuntimeError):
    """Raised when the configured LLM cannot generate an answer."""


class GroqGenerator:
    """Generate grounded answers with Groq's OpenAI-compatible chat API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.groq_model
        self.api_key = settings.groq_api_key

    def _client(self) -> AsyncGroq:
        if not self.api_key:
            raise GenerationError(
                "GROQ_API_KEY is not configured. Copy .env.example to .env, "
                "add your Groq API key, and restart the backend."
            )
        return AsyncGroq(api_key=self.api_key, timeout=45.0, max_retries=2)

    async def generate(self, question: str, sources: list[SourceChunk]) -> str:
        """Return a complete grounded response."""
        if not sources:
            return INSUFFICIENT_CONTEXT_ANSWER
        try:
            completion = await self._client().chat.completions.create(
                model=self.model,
                temperature=0.1,
                max_tokens=1200,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(question, sources)},
                ],
            )
            content = completion.choices[0].message.content
            if not content:
                raise GenerationError("Groq returned an empty response")
            return content.strip()
        except (APIConnectionError, APIStatusError, APITimeoutError) as exc:
            raise GenerationError(f"Groq generation failed: {exc}") from exc

    async def stream(self, question: str, sources: list[SourceChunk]) -> AsyncIterator[str]:
        """Yield text deltas from Groq; return a deterministic answer when retrieval is empty."""
        if not sources:
            yield INSUFFICIENT_CONTEXT_ANSWER
            return
        try:
            response = await self._client().chat.completions.create(
                model=self.model,
                temperature=0.1,
                max_tokens=1200,
                stream=True,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(question, sources)},
                ],
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except (APIConnectionError, APIStatusError, APITimeoutError) as exc:
            raise GenerationError(f"Groq streaming failed: {exc}") from exc
