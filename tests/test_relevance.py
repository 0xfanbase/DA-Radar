"""Tests for pipeline.watcher.relevance -- the deterministic keyword filter
between "watcher observed an item" and "item is queued for the analyst".
"""
from __future__ import annotations

from pipeline.watcher.relevance import classify_relevance, is_relevant


def test_is_relevant_matches_case_insensitively():
    assert is_relevant("A STABLECOIN licence", "", ["stablecoin"]) is True
    assert is_relevant("stablecoin licence", "", ["STABLECOIN"]) is True


def test_is_relevant_checks_title_and_summary():
    assert is_relevant("Unrelated title", "mentions a virtual asset here", ["virtual asset"]) is True
    assert is_relevant("Unrelated title", "unrelated summary", ["virtual asset"]) is False


def test_is_relevant_fails_open_on_empty_keywords():
    """An unconfigured jurisdiction (no relevance_keywords) should never
    silently queue nothing -- that's a worse failure mode than queuing
    everything."""
    assert is_relevant("Anything at all", "", []) is True
    assert is_relevant("Anything at all", "", None) is True


def test_is_relevant_no_match_among_real_keywords():
    assert is_relevant("Scam alert related to banks", "Scam alert details.", ["stablecoin", "vatp"]) is False


def _ledger_with(entries: dict) -> dict:
    return {"schema_version": 1, "generated_at": None, "items": entries}


def test_classify_relevance_marks_relevant_and_irrelevant_items():
    ledger = _ledger_with(
        {
            "a": {"title": "New stablecoin licence granted", "summary": "", "status": "queued"},
            "b": {"title": "Unrelated banking guideline", "summary": "", "status": "queued"},
        }
    )

    new_ledger, changed = classify_relevance(ledger, ["stablecoin"], "2026-07-09T00:00:00Z")

    assert set(changed) == {"a", "b"}
    assert new_ledger["items"]["a"]["relevant"] is True
    assert new_ledger["items"]["b"]["relevant"] is False


def test_classify_relevance_is_idempotent():
    ledger = _ledger_with({"a": {"title": "stablecoin news", "summary": "", "status": "queued"}})

    ledger, changed_first = classify_relevance(ledger, ["stablecoin"], "2026-07-09T00:00:00Z")
    assert changed_first == ["a"]

    ledger, changed_second = classify_relevance(ledger, ["stablecoin"], "2026-07-10T00:00:00Z")
    assert changed_second == []


def test_classify_relevance_returns_same_ledger_object_when_nothing_to_classify():
    ledger = _ledger_with({"a": {"title": "x", "summary": "", "status": "queued", "relevant": True}})
    new_ledger, changed = classify_relevance(ledger, ["stablecoin"], "2026-07-09T00:00:00Z")
    assert changed == []
    assert new_ledger is ledger


def test_classify_relevance_is_portable_to_a_different_keyword_vocabulary():
    """Proves the filter itself is jurisdiction-agnostic: a completely
    different keyword vocabulary drives completely different outcomes for
    the same titles, with no HK-specific assumption baked into the logic."""
    ledger = _ledger_with(
        {
            "a": {"title": "Freedonia gizmo licence", "summary": "", "status": "queued"},
            "b": {"title": "Freedonia banking rule", "summary": "", "status": "queued"},
        }
    )

    new_ledger, _changed = classify_relevance(ledger, ["gizmo"], "2026-07-09T00:00:00Z")

    assert new_ledger["items"]["a"]["relevant"] is True
    assert new_ledger["items"]["b"]["relevant"] is False
