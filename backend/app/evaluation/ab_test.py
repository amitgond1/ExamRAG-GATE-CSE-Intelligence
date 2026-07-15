"""Three-arm retrieval experiment runner."""

import uuid

from app.evaluation.service import get_evaluation_service
from app.models.schemas import (
    ABStrategyResult,
    ABTestResponse,
    EvaluationItem,
    RetrievalStrategy,
)


async def run_ab_test(
    items: list[EvaluationItem], run_name: str | None = None
) -> ABTestResponse:
    """Run identical questions through dense, hybrid, and reranked retrieval."""
    experiment_id = uuid.uuid4().hex[:12]
    results: list[ABStrategyResult] = []
    evaluator = get_evaluation_service()
    for strategy in RetrievalStrategy:
        evaluation = await evaluator.evaluate(
            items,
            strategy,
            run_name=f"{run_name or 'ab-test'}-{strategy.value}",
            extra_tags={"ab_experiment_id": experiment_id},
        )
        results.append(
            ABStrategyResult(
                strategy=strategy,
                run_id=evaluation.run_id,
                metrics=evaluation.metrics,
            )
        )
    return ABTestResponse(experiment_id=experiment_id, results=results)
