"""Request and response schemas shared by the API and services."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RetrievalStrategy(str, Enum):
    """Supported retrieval configurations."""

    DENSE = "dense"
    HYBRID = "hybrid"
    HYBRID_RERANK = "hybrid_rerank"


class SourceChunk(BaseModel):
    """A retrieved chunk and its provenance."""

    chunk_id: str
    text: str
    source: str
    page: int | None = None
    subject: str = "Unknown"
    topic: str = "General"
    difficulty: str = "unknown"
    score: float = 0.0


class ChatRequest(BaseModel):
    """Payload for a grounded RAG query."""

    question: str = Field(min_length=2, max_length=4000)
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID_RERANK
    stream: bool = False

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        """Reject whitespace-only questions and normalize surrounding whitespace."""
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty")
        return value


class HallucinationClaim(BaseModel):
    """NLI support classification for one answer sentence."""

    sentence: str
    label: str
    entailment_score: float
    contradiction_score: float
    neutral_score: float


class ChatResponse(BaseModel):
    """Complete answer returned by the chat endpoint."""

    answer: str
    strategy: RetrievalStrategy
    sources: list[SourceChunk]
    latency_ms: float
    hallucination_checks: list[HallucinationClaim] = Field(default_factory=list)


class EvaluationItem(BaseModel):
    """One question and reference answer for evaluation."""

    question: str = Field(min_length=2)
    ground_truth: str = Field(min_length=1)
    answer: str | None = None
    contexts: list[str] | None = None
    expected_topic: str | None = None


class EvaluationRequest(BaseModel):
    """Batch RAGAS evaluation request."""

    items: list[EvaluationItem] = Field(min_length=1, max_length=200)
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID_RERANK
    run_name: str | None = None


class MetricScores(BaseModel):
    """Aggregate RAG evaluation metrics."""

    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    hallucination_rate: float | None = None
    mean_latency_ms: float | None = None


class EvaluationResponse(BaseModel):
    """Results and row-level details for an evaluation run."""

    run_id: str
    strategy: RetrievalStrategy
    metrics: MetricScores
    rows: list[dict[str, Any]]


class ABTestRequest(BaseModel):
    """Question set to compare across every retrieval strategy."""

    items: list[EvaluationItem] = Field(min_length=1, max_length=100)
    run_name: str | None = None


class ABStrategyResult(BaseModel):
    """Metrics for a single arm of an A/B/C retrieval experiment."""

    strategy: RetrievalStrategy
    run_id: str
    metrics: MetricScores


class ABTestResponse(BaseModel):
    """Comparison results across the three retrieval strategies."""

    experiment_id: str
    results: list[ABStrategyResult]


class IngestResponse(BaseModel):
    """Summary of an ingestion job."""

    filename: str
    document_id: str
    chunks_created: int
    subjects_detected: list[str]


class EvaluationRunSummary(BaseModel):
    """Evaluation history item sourced from MLflow."""

    run_id: str
    run_name: str
    started_at: datetime
    status: str
    strategy: str | None = None
    metrics: dict[str, float]

