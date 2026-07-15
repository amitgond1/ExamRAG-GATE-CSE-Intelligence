"""Token-aware recursive text chunking with overlap."""

from dataclasses import dataclass
from functools import lru_cache

from transformers import AutoTokenizer, PreTrainedTokenizerBase


@dataclass(frozen=True)
class TextChunk:
    """A chunk produced from a single source page."""

    text: str
    token_count: int
    page_number: int
    chunk_index: int


@lru_cache(maxsize=4)
def _get_tokenizer(model_name: str) -> PreTrainedTokenizerBase:
    """Load and cache the tokenizer used by the embedding model."""
    return AutoTokenizer.from_pretrained(model_name)


def chunk_page(
    text: str,
    page_number: int,
    model_name: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[TextChunk]:
    """Split page text on token boundaries with a fixed sliding overlap."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap smaller than chunk_size")
    tokenizer = _get_tokenizer(model_name)
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    if not token_ids:
        return []

    chunks: list[TextChunk] = []
    step = chunk_size - overlap
    for index, start in enumerate(range(0, len(token_ids), step)):
        window = token_ids[start : start + chunk_size]
        decoded = tokenizer.decode(window, skip_special_tokens=True).strip()
        if decoded:
            chunks.append(
                TextChunk(
                    text=decoded,
                    token_count=len(window),
                    page_number=page_number,
                    chunk_index=index,
                )
            )
        if start + chunk_size >= len(token_ids):
            break
    return chunks

