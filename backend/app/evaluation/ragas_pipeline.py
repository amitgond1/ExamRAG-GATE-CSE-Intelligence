"""RAGAS integration for grounded answer quality metrics."""

from typing import Any

from datasets import Dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from app.config import get_settings


class RagasConfigurationError(RuntimeError):
    """Raised when RAGAS cannot be run with the current configuration."""


def run_ragas(rows: list[dict[str, Any]]) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Compute four canonical RAGAS metrics and return aggregate plus row scores."""
    settings = get_settings()
    if not settings.groq_api_key:
        raise RagasConfigurationError("GROQ_API_KEY is required for RAGAS judge metrics")

    dataset = Dataset.from_dict(
        {
            "question": [row["question"] for row in rows],
            "answer": [row["answer"] for row in rows],
            "contexts": [row["contexts"] for row in rows],
            "ground_truth": [row["ground_truth"] for row in rows],
        }
    )
    llm = ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0,
        max_retries=2,
    )
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False,
    )
    frame = result.to_pandas()
    metric_names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    aggregates = {
        name: float(frame[name].dropna().mean()) if name in frame and not frame[name].dropna().empty else 0.0
        for name in metric_names
    }
    scored_rows = frame.where(frame.notna(), None).to_dict(orient="records")
    return aggregates, scored_rows
