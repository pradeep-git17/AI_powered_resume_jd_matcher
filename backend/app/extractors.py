from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status
from docx import Document

from .match_utils import normalize_text

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def validate_extension(filename: str | None, *, label: str = "file") -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported {label} type. Please upload a PDF or DOCX file.",
        )
    return extension


def extract_document_text(file_bytes: bytes, filename: str | None, *, label: str = "document") -> str:
    extension = validate_extension(filename, label=label)

    if extension == ".pdf":
        text = _extract_pdf_text(file_bytes, label=label)
    else:
        text = _extract_docx_text(file_bytes, label=label)

    normalized = normalize_text(text)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to extract readable text from the uploaded {label}.",
        )
    return normalized


def extract_resume_text(file_bytes: bytes, filename: str | None) -> str:
    return extract_document_text(file_bytes, filename, label="resume")


def _extract_pdf_text(file_bytes: bytes, *, label: str) -> str:
    extraction_errors: list[str] = []

    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
            if text.strip():
                return text
    except Exception as exc:  # pragma: no cover - depends on parser backend
        extraction_errors.append(f"pdfplumber: {exc}")

    try:
        import fitz

        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            text = "\n".join(page.get_text("text") for page in doc)
            if text.strip():
                return text
    except Exception as exc:  # pragma: no cover - depends on parser backend
        extraction_errors.append(f"PyMuPDF: {exc}")

    error_detail = "; ".join(extraction_errors) if extraction_errors else "No PDF parser available."
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unable to parse PDF {label}. {error_detail}",
    )


def _extract_docx_text(file_bytes: bytes, *, label: str) -> str:
    try:
        document = Document(BytesIO(file_bytes))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse DOCX {label}. {exc}",
        ) from exc

    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)
