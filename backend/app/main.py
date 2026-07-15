"""FastAPI entry point for the ExamRAG backend."""

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
import anyio
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.evaluation.ab_test import run_ab_test
from app.evaluation.ragas_pipeline import RagasConfigurationError
from app.evaluation.service import get_evaluation_service
from app.evaluation.tracking import configure_mlflow, list_evaluation_runs
from app.generation.llm import GenerationError
from app.generation.service import get_rag_service
from app.ingestion.pdf_loader import PDFLoadError
from app.ingestion.pipeline import IngestionPipeline
from app.models.schemas import (
    ABTestRequest,
    ABTestResponse,
    ChatRequest,
    ChatResponse,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationRunSummary,
    IngestResponse,
)


logger = logging.getLogger("examrag")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize local storage and experiment tracking at application startup."""
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    configure_mlflow()
    yield


settings = get_settings()
app = FastAPI(
    title="ExamRAG API",
    version="1.0.0",
    description="Production-oriented GATE CSE retrieval-augmented generation and evaluation",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sse(event: str, data: object) -> str:
    """Serialize one server-sent event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a lightweight liveness response without loading ML models."""
    return {"status": "ok", "service": settings.app_name}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse | StreamingResponse:
    """Answer a question using a selected strategy, optionally over SSE."""
    rag = get_rag_service()
    if not request.stream:
        try:
            return await rag.answer(request.question, request.strategy)
        except GenerationError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    started = time.perf_counter()
    sources, token_stream = await rag.stream_answer(request.question, request.strategy)

    async def event_stream() -> AsyncIterator[str]:
        yield sse("sources", [source.model_dump() for source in sources])
        try:
            async for token in token_stream:
                yield sse("token", {"text": token})
            yield sse(
                "done",
                {
                    "strategy": request.strategy.value,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
        except GenerationError as exc:
            logger.exception("Streaming generation failed")
            yield sse("error", {"detail": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_batch(request: EvaluationRequest) -> EvaluationResponse:
    """Run RAGAS and sentence-level NLI evaluation over a batch."""
    try:
        return await get_evaluation_service().evaluate(
            request.items, request.strategy, request.run_name
        )
    except (GenerationError, RagasConfigurationError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@app.post("/ab-test", response_model=ABTestResponse)
async def ab_test(request: ABTestRequest) -> ABTestResponse:
    """Compare all three retrieval strategies on the same question set."""
    try:
        return await run_ab_test(request.items, request.run_name)
    except (GenerationError, RagasConfigurationError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@app.get("/eval-history", response_model=list[EvaluationRunSummary])
async def eval_history(
    limit: int = Query(default=50, ge=1, le=500),
) -> list[EvaluationRunSummary]:
    """Fetch recent local MLflow evaluation runs."""
    return await anyio.to_thread.run_sync(list_evaluation_runs, limit)


@app.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """Upload and ingest one text-based PDF with bounded disk usage."""
    filename = Path(file.filename or "document.pdf").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are accepted")

    destination = settings.upload_path / f"{uuid.uuid4().hex}.pdf"
    written = 0
    try:
        async with aiofiles.open(destination, "wb") as output:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="PDF exceeds the 50 MB limit")
                await output.write(chunk)
        async with aiofiles.open(destination, "rb") as uploaded:
            if await uploaded.read(5) != b"%PDF-":
                raise HTTPException(status_code=415, detail="Uploaded file is not a valid PDF")
        return await anyio.to_thread.run_sync(IngestionPipeline().ingest, destination, filename)
    except PDFLoadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()
        destination.unlink(missing_ok=True)
