"""Safe PDF extraction using PyMuPDF."""

from dataclasses import dataclass
from pathlib import Path

import fitz


class PDFLoadError(ValueError):
    """Raised when a PDF cannot be parsed into usable text."""


@dataclass(frozen=True)
class PDFPage:
    """Text extracted from one PDF page."""

    page_number: int
    text: str


def load_pdf(path: Path) -> list[PDFPage]:
    """Extract non-empty pages from a PDF while preserving page numbers."""
    try:
        document = fitz.open(path)
    except (fitz.FileDataError, RuntimeError) as exc:
        raise PDFLoadError(f"Malformed or unreadable PDF: {path.name}") from exc

    try:
        if document.needs_pass:
            raise PDFLoadError("Password-protected PDFs are not supported")
        pages = [
            PDFPage(page_number=index + 1, text=page.get_text("text").strip())
            for index, page in enumerate(document)
            if page.get_text("text").strip()
        ]
    finally:
        document.close()

    if not pages:
        raise PDFLoadError("The PDF contains no extractable text")
    return pages

