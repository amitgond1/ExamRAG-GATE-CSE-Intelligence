"""Batch evaluation orchestration."""

import time
from functools import lru_cache
from typing import Any

import anyio

from app.config import get_settings
from app.evaluation.hallucination import HallucinationDetector
from app.evaluation.ragas_pipeline import run_ragas
from app.evaluation.tracking import log_evaluation
from app.generation.service import get_rag_service
from app.models.schemas import (
    EvaluationItem,
    EvaluationResponse,
    MetricScores,
    RetrievalStrategy,
)


class EvaluationService:
    """Generate missing outputs, score them, and log a reproducible evaluation run."""

    def __init__(self) -> None:
        self.rag = get_rag_service()
        self.detector = HallucinationDetector(get_settings().nli_model)

    async def evaluate(
        self,
        items: list[EvaluationItem],
        strategy: RetrievalStrategy,
        run_name: str | None = None,
        extra_tags: dict[str, str] | None = None,
    ) -> EvaluationResponse:
        """Evaluate supplied or freshly generated answer/context pairs."""
        rows: list[dict[str, Any]] = []
        latencies: list[float] = []
        unsupported_claims = 0
        total_claims = 0

        for item in items:
            if item.answer is not None and item.contexts is not None:
                answer, contexts = item.answer, item.contexts
                latency_ms = 0.0
            else:
                started = time.perf_counter()
                response = await self.rag.answer(item.question, strategy)
                latency_ms = (time.perf_counter() - started) * 1000
                answer = item.answer or response.answer
                contexts = item.contexts or [source.text for source in response.sources]

            checks = await anyio.to_thread.run_sync(self.detector.check, answer, contexts)
            total_claims += len(checks)
            unsupported_claims += sum(check.label != "SUPPORTED" for check in checks)
            latencies.append(latency_ms)
            rows.append(
                {
                    "question": item.question,
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": item.ground_truth,
                    "expected_topic": item.expected_topic,
                    "latency_ms": round(latency_ms, 2),
                    "hallucination_checks": [check.model_dump() for check in checks],
                }
            )

        ragas_metrics, scored_rows = await anyio.to_thread.run_sync(run_ragas, rows)
        for source_row, scored_row in zip(rows, scored_rows, strict=False):
            source_row.update(
                {
                    key: scored_row.get(key)
                    for key in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
                }
            )
        metrics = {
            **ragas_metrics,
            "hallucination_rate": unsupported_claims / total_claims if total_claims else 0.0,
            "mean_latency_ms": sum(latencies) / len(latencies),
        }
        run_id = await anyio.to_thread.run_sync(
            log_evaluation,
            run_name or f"{strategy.value}-evaluation",
            strategy,
            metrics,
            rows,
            extra_tags,
        )
        return EvaluationResponse(
            run_id=run_id,
            strategy=strategy,
            metrics=MetricScores(**metrics),
            rows=rows,
        )


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    """Return a cached batch evaluation service."""
    return EvaluationService()
