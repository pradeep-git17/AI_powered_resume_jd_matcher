from __future__ import annotations

import json
import time
from typing import Any

import httpx
from fastapi import HTTPException, status

from .config import Settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_messages(mode: str, resume_text: str, jd_text: str | None = None) -> list[dict[str, str]]:
    if mode == "resume":
        instructions = (
            'Return JSON only with keys '
            'summary,skills,education,experience,warnings. '
            'Summary max 2 sentences. Skills max 12. Education max 3 items. Experience max 4 items. '
            'Each experience item uses role,duration,highlights. '
            'Use empty strings/arrays for missing data. No markdown. No extra keys.'
        )
    else:
        instructions = (
            'Return JSON only with keys '
            'summary,skills,education,experience,warnings,jd_skills,matching_skills,missing_skills,match_score,fit_classification,relevant_experience_highlights. '
            'Summary max 2 sentences. Each list short and high-signal. '
            'match_score must be 0-100 integer. fit_classification must be Good Fit, Moderate Fit, or Low Fit. '
            'Use empty strings/arrays for missing data. No markdown. No extra keys.'
        )

    user_prompt = f"Resume Text:\n{resume_text}"
    if jd_text is not None:
        user_prompt += f"\n\nJob Description Text:\n{jd_text}"

    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_prompt},
    ]


async def call_openrouter(
    *,
    settings: Settings,
    mode: str,
    resume_text: str,
    jd_text: str | None = None,
    timeout_override_seconds: float | None = None,
) -> tuple[dict[str, Any], int]:
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENROUTER_API_KEY is not configured.",
        )

    payload = {
        "model": settings.openrouter_model,
        "messages": build_messages(mode=mode, resume_text=resume_text, jd_text=jd_text),
        "temperature": 0,
        "max_tokens": settings.resume_max_tokens if mode == "resume" else settings.match_max_tokens,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    effective_timeout = timeout_override_seconds or settings.openrouter_timeout_seconds
    timeout = httpx.Timeout(effective_timeout)
    last_error: Exception | None = None

    for _ in range(settings.openrouter_max_retries + 1):
        try:
            started_at = time.perf_counter()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                return json.loads(content), elapsed_ms
        except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
            last_error = exc

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"OpenRouter request failed. {last_error}",
    )
