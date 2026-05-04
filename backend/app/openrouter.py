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
            'summary,skills,education,experience,projects,suitable_fields,warnings. '
            'Summary max 2 sentences. Skills max 12. Education max 3 items. Experience max 4 items. Projects max 5 items. '
            'Each experience item uses role,duration,highlights. '
            'Each project item uses title,description,technologies. '
            'suitable_fields is a list of 2-4 recommended career fields based on skills and projects. '
            'Use empty strings/arrays for missing data. No markdown. No extra keys.'
        )
    else:
        instructions = (
            'Return JSON only with keys '
            'summary,skills,education,experience,projects,suitable_fields,warnings,jd_skills,matching_skills,missing_skills,match_score,fit_classification,relevant_experience_highlights. '
            'Summary max 2 sentences. Each list short and high-signal. '
            'match_score must be 0-100 integer. fit_classification must be Good Fit, Moderate Fit, or Low Fit. '
            'suitable_fields is a list of 2-4 recommended career fields based on skills and projects. '
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

    # Try with and without response_format constraint for provider compatibility
    payload_variants = [
        {
            "model": settings.openrouter_model,
            "messages": build_messages(mode=mode, resume_text=resume_text, jd_text=jd_text),
            "temperature": 0,
            "max_tokens": settings.resume_max_tokens if mode == "resume" else settings.match_max_tokens,
            "response_format": {"type": "json_object"},
        },
        {
            "model": settings.openrouter_model,
            "messages": build_messages(mode=mode, resume_text=resume_text, jd_text=jd_text),
            "temperature": 0,
            "max_tokens": settings.resume_max_tokens if mode == "resume" else settings.match_max_tokens,
        },
    ]

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    effective_timeout = timeout_override_seconds or settings.openrouter_timeout_seconds
    timeout = httpx.Timeout(effective_timeout)
    last_error: Exception | None = None

    for attempt in range(settings.openrouter_max_retries + 1):
        for payload_idx, payload in enumerate(payload_variants):
            try:
                started_at = time.perf_counter()
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    # Check for upstream errors from OpenRouter/OpenInference
                    if isinstance(data, dict) and "error" in data:
                        error_obj = data["error"]
                        if isinstance(error_obj, dict):
                            error_msg = error_obj.get("message", "unknown error")
                            # Upstream errors are retryable, skip to next variant or retry
                            last_error = KeyError(f"OpenRouter upstream error: {error_msg}")
                            continue
                        else:
                            last_error = KeyError(f"OpenRouter error: {error_obj}")
                            continue

                    # Normal OpenRouter/OpenAI-like response
                    content = None

                    try:
                        if isinstance(data, dict) and "choices" in data and data["choices"]:
                            choice = data["choices"][0]
                            # choice may have different shapes depending on model/provider
                            if isinstance(choice, dict):
                                content = (
                                    choice.get("message", {})
                                    and choice.get("message", {}).get("content")
                                ) or choice.get("text") or choice.get("message")

                        # Some providers return an `output` key or `result`
                        if content is None and isinstance(data, dict):
                            if "output" in data:
                                out = data["output"]
                                if isinstance(out, list) and out:
                                    elem = out[0]
                                    content = elem.get("content") if isinstance(elem, dict) else elem
                                elif isinstance(out, dict):
                                    content = out.get("content") or out
                            elif "result" in data:
                                content = data["result"]
                            elif "message" in data:
                                content = data["message"]

                        # If content is a dict already, use it; if string, try parsing JSON
                        if isinstance(content, dict):
                            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                            return content, elapsed_ms

                        if isinstance(content, str):
                            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                            return json.loads(content), elapsed_ms

                        # Last resort: unexpected response shape
                        last_error = KeyError(f"unexpected OpenRouter response shape: {data}")
                    except json.JSONDecodeError as exc:
                        # content was not valid JSON
                        last_error = json.JSONDecodeError(
                            f"failed to decode OpenRouter content: {exc.msg}", exc.doc, exc.pos
                        )
            except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
                last_error = exc

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"OpenRouter request failed. {last_error}",
    )
