from __future__ import annotations

from typing import Iterable


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r", "\n").split("\n")]
    collapsed = [line for line in lines if line]
    return "\n".join(collapsed)


def shrink_text(text: str, max_chars: int) -> str:
    normalized = normalize_text(text)
    if len(normalized) <= max_chars:
        return normalized

    separator = "\n...\n"
    head_chars = int(max_chars * 0.7)
    tail_chars = max(0, max_chars - head_chars - len(separator))
    return f"{normalized[:head_chars].rstrip()}{separator}{normalized[-tail_chars:].lstrip()}"


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        cleaned = " ".join(item.split()).strip(" ,;")
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)

    return result


def clamp_score(score: int | float | str) -> int:
    try:
        numeric = int(float(score))
    except (TypeError, ValueError):
        numeric = 0

    return max(0, min(100, numeric))


def classify_fit(score: int, moderate_threshold: int = 60, good_threshold: int = 80) -> str:
    if score >= good_threshold:
        return "Good Fit"
    if score >= moderate_threshold:
        return "Moderate Fit"
    return "Low Fit"
