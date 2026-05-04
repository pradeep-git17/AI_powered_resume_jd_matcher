from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status
from docx import Document

from .match_utils import normalize_text

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
MAX_RESUME_PDF_PAGES = 3
MAX_JD_PDF_PAGES = 4
MAX_DEFAULT_PDF_PAGES = 5


RESUME_KEYWORDS = {
    "experience", "skills", "education", "summary", "contact", "phone", "email",
    "professional", "employment", "work history", "projects", "certifications",
    "languages", "technical", "achievements", "responsibilities"
}

JD_KEYWORDS = {
    "responsibilities", "requirements", "qualifications", "about the role",
    "job description", "requirements", "skills", "experience", "bachelor's",
    "master's", "responsibilities", "compensation", "benefits", "apply",
    "position", "role", "team", "work with"
}


def validate_extension(filename: str | None, *, label: str = "file") -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="please upload required file",
        )
    return extension


def _is_resume_content(text: str) -> bool:
    """Check if extracted text appears to be a resume based on keyword matching."""
    normalized_text = text.lower()
    matching_keywords = sum(1 for keyword in RESUME_KEYWORDS if keyword in normalized_text)
    return matching_keywords >= 3


def _is_jd_content(text: str) -> bool:
    """Check if extracted text appears to be a job description based on keyword matching."""
    normalized_text = text.lower()
    matching_keywords = sum(1 for keyword in JD_KEYWORDS if keyword in normalized_text)
    return matching_keywords >= 3


def _validate_content(text: str, *, label: str = "file") -> None:
    """Validate that extracted text matches the expected document type."""
    if label == "resume" and not _is_resume_content(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="please upload required file",
        )
    elif label == "job description" and not _is_jd_content(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="please upload required file",
        )


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
    
    _validate_content(normalized, label=label)
    return normalized


def extract_resume_text(file_bytes: bytes, filename: str | None) -> str:
    return extract_document_text(file_bytes, filename, label="resume")


def _pdf_page_limit_for_label(label: str) -> int:
    if label == "resume":
        return MAX_RESUME_PDF_PAGES
    if label == "job description":
        return MAX_JD_PDF_PAGES
    return MAX_DEFAULT_PDF_PAGES


def _extract_pdf_text(file_bytes: bytes, *, label: str) -> str:
    extraction_errors: list[str] = []
    page_limit = _pdf_page_limit_for_label(label)

    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages[:page_limit])
            if text.strip():
                return text
    except Exception as exc:  # pragma: no cover - depends on parser backend
        extraction_errors.append(f"pdfplumber: {exc}")

    try:
        import fitz

        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            page_count = min(len(doc), page_limit)
            text = "\n".join(doc[i].get_text("text") for i in range(page_count))
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
