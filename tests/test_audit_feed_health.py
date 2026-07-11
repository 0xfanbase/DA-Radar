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


def test_check_feed_coverage_flags_a_structure_error_never_double_reported_as_silent():
    """A feed broken since day one (selector/pattern/path stopped matching)
    has never contributed a ledger item, so the ledger alone can't see it --
    watch_status.json is what makes it visible at all."""
    ledger = _ledger({})
    watch_status = {
        "feeds": {
            "fincen_news": {
                "source_id": "fincen",
                "status": "structure_error",
                "status_since": "2026-02-25T00:00:00Z",
                "mechanism": "html_diff",
                "last_error": "selector 'div.view-news-room div.views-row' matched 0 elements",
            }
        }
    }
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), watch_status=watch_status)
    assert len(events) == 1
    assert events[0]["event_type"] == "feed_structure_error"
    assert events[0]["details"]["feed_id"] == "fincen_news"
    assert events[0]["details"]["mechanism"] == "html_diff"
    # Never also reported as feed_silence for the same feed.
    assert not any(e["event_type"] == "feed_silence" for e in events)


def test_check_feed_coverage_flags_a_fetch_failure_never_double_reported_as_silent_or_structure():
    """A feed whose fetch itself is failing (network/URL problem) or whose
    content won't even parse as the mechanism's expected format -- distinct
    from a structure error, since the remediation differs."""
    ledger = _ledger({})
    watch_status = {
        "feeds": {
            "vara_news": {
                "source_id": "vara",
                "status": "fetch_error",
                "status_since": "2026-02-20T00:00:00Z",
                "mechanism": "html_diff",
                "last_error": "HTTPSConnectionPool: Max retries exceeded (Connection refused)",
            }
        }
    }
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), watch_status=watch_status)
    assert len(events) == 1
    assert events[0]["event_type"] == "feed_fetch_failure"
    assert events[0]["details"]["feed_id"] == "vara_news"
    assert events[0]["details"]["status"] == "fetch_error"
    assert events[0]["details"]["days_broken"] == 9
    assert not any(e["event_type"] in ("feed_silence", "feed_structure_error") for e in events)


def test_check_feed_coverage_fetch_failure_also_fires_for_parse_error_status():
    ledger = _ledger({})
    watch_status = {
        "feeds": {
            "hmt_atom": {
                "source_id": "hmt",
                "status": "parse_error",
                "status_since": "2026-02-20T00:00:00Z",
                "mechanism": "atom",
                "last_error": "hmt_atom: root is not an Atom <feed>",
            }
        }
    }
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), watch_status=watch_status)
    assert len(events) == 1
    assert events[0]["event_type"] == "feed_fetch_failure"
    assert events[0]["details"]["status"] == "parse_error"


def test_check_feed_coverage_fetch_failure_respects_min_days_threshold():
    """A fetch failure that started only 1 day ago must not fire yet at the
    default 3-day threshold -- a single transient blip shouldn't page
    anyone; it's the SUSTAINED failure that's the real signal."""
    ledger = _ledger({})
    watch_status = {
        "feeds": {
            "vara_news": {
                "source_id": "vara",
                "status": "fetch_error",
                "status_since": "2026-02-28T00:00:00Z",
                "mechanism": "html_diff",
                "last_error": "connection timed out",
            }
        }
    }
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), watch_status=watch_status)
    assert events == []


def test_check_feed_coverage_fetch_failure_fires_exactly_at_min_days_threshold():
    ledger = _ledger({})
    watch_status = {
        "feeds": {
            "vara_news": {
                "source_id": "vara",
                "status": "fetch_error",
                "status_since": "2026-02-26T00:00:00Z",
                "mechanism": "html_diff",
                "last_error": "connection timed out",
            }
        }
    }
    events = check_feed_coverage(
        ledger, today=date(2026, 3, 1), watch_status=watch_status, fetch_failure_min_days=3
    )
    assert len(events) == 1
    assert events[0]["details"]["days_broken"] == 3


def test_check_feed_coverage_config_error_status_is_never_silently_folded_into_silence():
    """A feed entry naming an unrecognized "mechanism" string produces
    status="config_error" -- deliberately none of the three explicit event
    types (see the module's own docstring), never mislabeled a false
    "quiet" feed either."""
    ledger = _ledger({})
    watch_status = {
        "feeds": {
            "bogus_feed": {
                "source_id": "vara",
                "status": "config_error",
                "status_since": "2026-01-01T00:00:00Z",
                "mechanism": "totally_bogus_mechanism",
                "last_error": "unrecognized mechanism 'totally_bogus_mechanism'",
            }
        }
    }
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), watch_status=watch_status)
    assert events == []


def test_check_feed_coverage_ok_status_feed_with_no_ledger_item_yet_is_not_flagged():
    """A brand-new, healthy feed (status "ok") that simply hasn't published
    yet has nothing to measure silence against -- must not be flagged."""
    ledger = _ledger({})
    watch_status = {
        "feeds": {
            "new_feed": {
                "source_id": "uk",
                "status": "ok",
                "status_since": "2026-03-01T00:00:00Z",
                "mechanism": "rss",
            }
        }
    }
    events = check_feed_coverage(ledger, today=date(2026, 3, 1), watch_status=watch_status)
    assert events == []
