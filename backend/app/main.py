from __future__ import annotations

import asyncio
import time
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from .analysis import build_resume_analysis, build_resume_match
from .config import Settings, get_settings
from .extractors import extract_document_text, extract_resume_text
from .match_utils import normalize_text, shrink_text
from .openrouter import call_openrouter
from .schemas import HealthResponse, ResumeAnalysisResult, ResumeMatchResult, TimingBreakdown

app = FastAPI(title="AI Resume Analyzer & JD Matcher")


async def _read_upload(upload: UploadFile) -> bytes:
    return await upload.read()


def _remaining_budget_seconds(started_at: float, settings: Settings) -> float:
    elapsed = time.perf_counter() - started_at
    return settings.total_request_budget_seconds - elapsed


@app.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_configured=bool(settings.openrouter_api_key),
    )


@app.post("/analyze/resume", response_model=ResumeAnalysisResult)
async def analyze_resume(
    resume: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> ResumeAnalysisResult:
    total_started_at = time.perf_counter()
    read_started_at = time.perf_counter()
    resume_bytes = await _read_upload(resume)
    upload_read_ms = int((time.perf_counter() - read_started_at) * 1000)

    extraction_started_at = time.perf_counter()
    resume_text = await run_in_threadpool(
        lambda: shrink_text(
            extract_resume_text(resume_bytes, resume.filename),
            settings.max_resume_chars,
        )
    )
    extraction_ms = int((time.perf_counter() - extraction_started_at) * 1000)
    remaining_budget = _remaining_budget_seconds(total_started_at, settings)
    if remaining_budget <= 0.25:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request exceeded the configured 10-second processing budget before model analysis started.",
        )
    payload, llm_ms = await call_openrouter(
        settings=settings,
        mode="resume",
        resume_text=resume_text,
        timeout_override_seconds=min(settings.openrouter_timeout_seconds, remaining_budget),
    )
    result = build_resume_analysis(payload)
    result.timing = TimingBreakdown(
        total_ms=int((time.perf_counter() - total_started_at) * 1000),
        upload_read_ms=upload_read_ms,
        extraction_ms=extraction_ms,
        llm_ms=llm_ms,
        fallback_ms=0,
        path="llm",
    )
    return result


@app.post("/analyze/match", response_model=ResumeMatchResult)
async def analyze_match(
    resume: UploadFile = File(...),
    jd_text: Annotated[str | None, Form()] = None,
    jd_file: UploadFile | None = File(default=None),
    settings: Settings = Depends(get_settings),
) -> ResumeMatchResult:
    total_started_at = time.perf_counter()
    read_started_at = time.perf_counter()
    upload_reads = [_read_upload(resume)]
    if jd_file is not None:
        upload_reads.append(_read_upload(jd_file))

    upload_contents = await asyncio.gather(*upload_reads)
    upload_read_ms = int((time.perf_counter() - read_started_at) * 1000)
    resume_bytes = upload_contents[0]
    jd_file_bytes = upload_contents[1] if jd_file is not None else None

    cleaned_jd = normalize_text(jd_text or "")

    extraction_started_at = time.perf_counter()
    extraction_tasks = [
        run_in_threadpool(
            lambda: shrink_text(
                extract_resume_text(resume_bytes, resume.filename),
                settings.max_resume_chars,
            )
        )
    ]

    if not cleaned_jd and jd_file is not None and jd_file_bytes is not None:
        extraction_tasks.append(
            run_in_threadpool(
                lambda: shrink_text(
                    extract_document_text(jd_file_bytes, jd_file.filename, label="job description"),
                    settings.max_jd_chars,
                )
            )
        )

    extraction_results = await asyncio.gather(*extraction_tasks)
    resume_text = extraction_results[0]

    if cleaned_jd:
        cleaned_jd = shrink_text(cleaned_jd, settings.max_jd_chars)
    elif len(extraction_results) > 1:
        cleaned_jd = extraction_results[1]
    extraction_ms = int((time.perf_counter() - extraction_started_at) * 1000)

    if not cleaned_jd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text or a JD PDF/DOCX file is required for JD matching.",
        )
    remaining_budget = _remaining_budget_seconds(total_started_at, settings)
    if remaining_budget <= 0.25:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request exceeded the configured 10-second processing budget before model analysis started.",
        )
    payload, llm_ms = await call_openrouter(
        settings=settings,
        mode="match",
        resume_text=resume_text,
        jd_text=cleaned_jd,
        timeout_override_seconds=min(settings.openrouter_timeout_seconds, remaining_budget),
    )
    result = build_resume_match(
        payload,
        moderate_threshold=settings.moderate_fit_threshold,
        good_threshold=settings.good_fit_threshold,
    )
    result.timing = TimingBreakdown(
        total_ms=int((time.perf_counter() - total_started_at) * 1000),
        upload_read_ms=upload_read_ms,
        extraction_ms=extraction_ms,
        llm_ms=llm_ms,
        fallback_ms=0,
        path="llm",
    )
    return result
