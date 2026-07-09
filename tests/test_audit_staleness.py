"""Tests for pipeline.audit.staleness."""
from __future__ import annotations

from datetime import date

from pipeline.audit.staleness import check_staleness


def test_check_staleness_flags_pillar_older_than_threshold():
    pillar_states = [{"pillar": "stablecoins", "last_changed": "2026-01-01"}]
    events = check_staleness(pillar_states, today=date(2026, 3, 1), threshold_days=45)
    assert len(events) == 1
    assert events[0]["event_type"] == "staleness"
    assert events[0]["details"]["pillar"] == "stablecoins"
    assert events[0]["details"]["age_days"] == 59


def test_check_staleness_no_event_within_threshold():
    pillar_states = [{"pillar": "stablecoins", "last_changed": "2026-02-20"}]
    events = check_staleness(pillar_states, today=date(2026, 3, 1), threshold_days=45)
    assert events == []


def test_check_staleness_exactly_at_threshold_is_not_flagged():
    pillar_states = [{"pillar": "stablecoins", "last_changed": "2026-01-15"}]
    # 2026-01-15 -> 2026-03-01 is exactly 45 days.
    events = check_staleness(pillar_states, today=date(2026, 3, 1), threshold_days=45)
    assert events == []


def test_check_staleness_checks_every_pillar_independently():
    pillar_states = [
        {"pillar": "fresh", "last_changed": "2026-02-25"},
        {"pillar": "stale", "last_changed": "2025-10-01"},
    ]
    events = check_staleness(pillar_states, today=date(2026, 3, 1), threshold_days=45)
    assert len(events) == 1
    assert events[0]["details"]["pillar"] == "stale"
