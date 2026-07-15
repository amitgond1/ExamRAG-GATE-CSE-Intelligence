"""End-to-end PDF ingestion orchestration."""

import hashlib
from pathlib import Path

from app.config import get_settings
from app.db.chroma_client import get_collection
from app.ingestion.chunker import chunk_page
from app.ingestion.metadata import infer_metadata
from app.ingestion.pdf_loader import load_pdf
from app.models.schemas import IngestResponse


class IngestionPipeline:
    """Parse, chunk, enrich, embed, and persist PDF study material."""

    def ingest(self, path: Path, original_filename: str) -> IngestResponse:
        """Ingest one PDF idempotently using its content hash as document ID."""
        settings = get_settings()
        document_id = hashlib.sha256(path.read_bytes()).hexdigest()[:20]
        pages = load_pdf(path)

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, str | int]] = []
        subjects: set[str] = set()
        global_index = 0

        for page in pages:
            chunks = chunk_page(
                page.text,
                page.page_number,
                settings.embedding_model,
                settings.chunk_size,
                settings.chunk_overlap,
            )
            for chunk in chunks:
                inferred = infer_metadata(chunk.text, original_filename)
                subjects.add(inferred["subject"])
                chunk_id = f"{document_id}-p{page.page_number}-c{chunk.chunk_index}"
                ids.append(chunk_id)
                documents.append(chunk.text)
                metadatas.append(
                    {
                        **inferred,
                        "source": original_filename,
                        "page": page.page_number,
                        "chunk_index": global_index,
                        "document_id": document_id,
                        "token_count": chunk.token_count,
                    }
                )
                global_index += 1

        if not documents:
            raise ValueError("No chunks could be created from the PDF")
        get_collection().upsert(ids=ids, documents=documents, metadatas=metadatas)
        return IngestResponse(
            filename=original_filename,
            document_id=document_id,
            chunks_created=len(documents),
            subjects_detected=sorted(subjects),
        )

