from backend.app.match_utils import clamp_score, classify_fit, dedupe_preserve_order, normalize_text, shrink_text


def test_normalize_text_removes_blank_lines() -> None:
    raw = "Alice\n\n  Software Engineer \r\n\r\nPython"
    assert normalize_text(raw) == "Alice\nSoftware Engineer\nPython"


def test_dedupe_preserve_order_is_case_insensitive() -> None:
    items = ["Python", " python ", "SQL", "", "sql"]
    assert dedupe_preserve_order(items) == ["Python", "SQL"]


def test_clamp_score_limits_values() -> None:
    assert clamp_score(104) == 100
    assert clamp_score(-3) == 0
    assert clamp_score("79.7") == 79


def test_classify_fit_uses_thresholds() -> None:
    assert classify_fit(80) == "Good Fit"
    assert classify_fit(79) == "Moderate Fit"
    assert classify_fit(60) == "Moderate Fit"
    assert classify_fit(59) == "Low Fit"


def test_shrink_text_preserves_size_limit() -> None:
    text = "A" * 100 + "\n" + "B" * 100
    shrunk = shrink_text(text, 60)
    assert len(shrunk) <= 60
    assert "..." in shrunk
