"""Tests for pipeline.audit.feed_health."""
from __future__ import annotations

from datetime import date

from pipeline.audit.feed_health import check_feed_coverage


def _ledger(items: dict) -> dict:
    return {"schema_version": 1, "generated_at": None, "items": items}


def test_check_feed_coverage_flags_a_silent_feed():
    ledger = _ledger(
        {
            "h1": {
                "source_id": "hkma",
                "feed_id": "hkma_press_release",
                "first_seen": "2025-12-01T00:00:00Z",
            }
        }
    )
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), silence_threshold_days=30)
    assert len(events) == 1
    assert events[0]["event_type"] == "feed_silence"
    assert events[0]["details"]["source_id"] == "hkma"
    assert events[0]["details"]["feed_id"] == "hkma_press_release"


def test_check_feed_coverage_no_event_for_recently_active_feed():
    ledger = _ledger(
        {"h1": {"source_id": "sfc", "feed_id": "sfc_circulars", "first_seen": "2026-02-20T00:00:00Z"}}
    )
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), silence_threshold_days=30)
    assert events == []


def test_check_feed_coverage_uses_most_recent_item_per_feed():
    ledger = _ledger(
        {
            "old": {"source_id": "sfc", "feed_id": "sfc_circulars", "first_seen": "2025-01-01T00:00:00Z"},
            "new": {"source_id": "sfc", "feed_id": "sfc_circulars", "first_seen": "2026-02-25T00:00:00Z"},
        }
    )
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), silence_threshold_days=30)
    assert events == []


def test_check_feed_coverage_treats_each_feed_independently():
    ledger = _ledger(
        {
            "a": {"source_id": "sfc", "feed_id": "sfc_circulars", "first_seen": "2026-02-25T00:00:00Z"},
            "b": {"source_id": "hkma", "feed_id": "hkma_speeches", "first_seen": "2025-01-01T00:00:00Z"},
        }
    )
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), silence_threshold_days=30)
    assert len(events) == 1
    assert events[0]["details"]["feed_id"] == "hkma_speeches"
