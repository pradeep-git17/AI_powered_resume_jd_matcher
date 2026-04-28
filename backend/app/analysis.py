from __future__ import annotations

from typing import Any

from .match_utils import clamp_score, classify_fit, dedupe_preserve_order
from .schemas import EducationItem, ExperienceItem, ResumeAnalysisResult, ResumeMatchResult


def _normalize_education(items: list[dict[str, Any]] | None) -> list[EducationItem]:
    results: list[EducationItem] = []
    seen: set[tuple[str, str]] = set()

    for item in items or []:
        if isinstance(item, dict):
            degree = str(item.get("degree", "")).strip()
            institution = str(item.get("institution", "")).strip()
        else:
            degree = str(item).strip()
            institution = ""
        key = (degree.casefold(), institution.casefold())
        if key in seen or not any(key):
            continue
        seen.add(key)
        results.append(EducationItem(degree=degree, institution=institution))

    return results


def _normalize_experience(items: list[dict[str, Any]] | None) -> list[ExperienceItem]:
    results: list[ExperienceItem] = []
    seen: set[tuple[str, str, str]] = set()

    for item in items or []:
        if isinstance(item, dict):
            role = str(item.get("role", "")).strip()
            duration = str(item.get("duration", "")).strip()
            highlights = str(item.get("highlights", "")).strip()
        else:
            role = str(item).strip()
            duration = ""
            highlights = ""
        key = (role.casefold(), duration.casefold(), highlights.casefold())
        if key in seen or not any(key):
            continue
        seen.add(key)
        results.append(ExperienceItem(role=role, duration=duration, highlights=highlights))

    return results


def build_resume_analysis(payload: dict[str, Any]) -> ResumeAnalysisResult:
    return ResumeAnalysisResult(
        summary=str(payload.get("summary", "")).strip(),
        skills=dedupe_preserve_order(payload.get("skills", [])),
        education=_normalize_education(payload.get("education")),
        experience=_normalize_experience(payload.get("experience")),
        warnings=dedupe_preserve_order(payload.get("warnings", [])),
    )


def build_resume_match(payload: dict[str, Any], moderate_threshold: int, good_threshold: int) -> ResumeMatchResult:
    score = clamp_score(payload.get("match_score", 0))
    fit_classification = classify_fit(score, moderate_threshold=moderate_threshold, good_threshold=good_threshold)

    return ResumeMatchResult(
        summary=str(payload.get("summary", "")).strip(),
        skills=dedupe_preserve_order(payload.get("skills", [])),
        education=_normalize_education(payload.get("education")),
        experience=_normalize_experience(payload.get("experience")),
        warnings=dedupe_preserve_order(payload.get("warnings", [])),
        jd_skills=dedupe_preserve_order(payload.get("jd_skills", [])),
        matching_skills=dedupe_preserve_order(payload.get("matching_skills", [])),
        missing_skills=dedupe_preserve_order(payload.get("missing_skills", [])),
        match_score=score,
        fit_classification=fit_classification,
        relevant_experience_highlights=dedupe_preserve_order(
            payload.get("relevant_experience_highlights", [])
        ),
    )
