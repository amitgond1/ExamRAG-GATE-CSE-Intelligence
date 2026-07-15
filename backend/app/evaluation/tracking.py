"""Local MLflow experiment tracking helpers."""

from datetime import datetime, timezone
from typing import Any

import mlflow
from mlflow import MlflowClient

from app.config import get_settings
from app.models.schemas import EvaluationRunSummary, RetrievalStrategy


EXPERIMENT_NAME = "ExamRAG-Evaluation"


def configure_mlflow() -> str:
    """Configure local tracking and return the experiment ID."""
    settings = get_settings()
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    experiment = mlflow.set_experiment(EXPERIMENT_NAME)
    return experiment.experiment_id


def log_evaluation(
    run_name: str,
    strategy: RetrievalStrategy,
    metrics: dict[str, float],
    rows: list[dict[str, Any]],
    extra_tags: dict[str, str] | None = None,
) -> str:
    """Persist metrics, configuration, and row-level JSON as an MLflow run."""
    configure_mlflow()
    tags = {"strategy": strategy.value, "component": "evaluation", **(extra_tags or {})}
    with mlflow.start_run(run_name=run_name, tags=tags) as run:
        mlflow.log_params({"strategy": strategy.value, "question_count": len(rows)})
        mlflow.log_metrics({key: value for key, value in metrics.items() if value is not None})
        mlflow.log_dict({"rows": rows}, "results/evaluation_rows.json")
        return run.info.run_id


def list_evaluation_runs(limit: int = 50) -> list[EvaluationRunSummary]:
    """Read recent evaluation runs without requiring a separate MLflow service."""
    experiment_id = configure_mlflow()
    client = MlflowClient()
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="tags.component = 'evaluation'",
        order_by=["attributes.start_time DESC"],
        max_results=limit,
    )
    return [
        EvaluationRunSummary(
            run_id=run.info.run_id,
            run_name=run.data.tags.get("mlflow.runName", "unnamed"),
            started_at=datetime.fromtimestamp(
                (run.info.start_time or 0) / 1000, tz=timezone.utc
            ),
            status=run.info.status,
            strategy=run.data.tags.get("strategy"),
            metrics={key: float(value) for key, value in run.data.metrics.items()},
        )
        for run in runs
    ]

