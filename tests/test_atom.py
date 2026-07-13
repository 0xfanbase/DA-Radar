"""Tests for pipeline.watcher.mechanisms.atom.

Mirrors tests/test_html_diff.py's structure: exercises the module
directly against frozen Atom snapshots under tests/fixtures/, plus the
real ledger seen-tracking machinery (pipeline.watcher.ledger.diff_new_items
/ upsert_items), to prove a day2 snapshot with 2 new entries appended to
day1's 2 produces exactly 2 new items -- never 4 and never 0. Atom's
guid comes from each entry's own <id> (unlike html_diff/sitemap_diff,
which synthesize guid=canonical-link), so this also exercises the
existing hashing.py guid identity path, the same one rss already uses.
"""
from __future__ import annotations

from pipeline.watcher.ledger import diff_new_items, load_ledger, upsert_items
from pipeline.watcher.mechanisms.atom import discover

UA = "TestAgent/0.1"
FETCH_CFG = {
    "timeout_seconds": 5,
    "max_retries": 3,
    "backoff_base_seconds": 0.01,
    "backoff_multiplier": 2.0,
}

FEED = {
    "id": "hmt_atom",
    "kind": "press_releases",
    "mechanism": "atom",
    "url": "https://www.gov.uk/government/organisations/hm-treasury.atom",
}

SOURCE_ID = "hmt"


def _discover(requests_mock, fixture_bytes, fixture_name, *, etag=None):
    requests_mock.get(FEED["url"], content=fixture_bytes(fixture_name))
    return discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=etag, session=None)


def test_day1_feed_yields_both_entries(requests_mock, fixture_bytes):
    result = _discover(requests_mock, fixture_bytes, "hmt.atom")

    assert result.status == "ok"
    assert result.error is None
    assert len(result.items) == 2

    guids = {item.guid for item in result.items}
    assert guids == {
        "https://www.gov.uk/government/publications/digital-assets-consultation-response",
        "https://www.gov.uk/government/news/stablecoin-regime-update",
    }
    for item in result.items:
        assert item.source_id == SOURCE_ID
        assert item.feed_id == "hmt_atom"
        assert item.feed_url == FEED["url"]
        assert item.title
        assert item.published_at is not None
        assert item.published_at.endswith("Z")


def test_day2_diff_against_real_ledger_detects_exactly_two_new_items(requests_mock, fixture_bytes):
    """day1 has 2 entries; day2 (hmt_day2.atom) is day1's 2 entries plus 2
    new entries appended (4 total). Feeding both through the REAL ledger
    diff/upsert machinery must detect exactly the 2 new items -- not 4
    (seen-tracking broken, every re-run re-queues everything) and not 0
    (new entries silently dropped)."""
    ledger = load_ledger("/nonexistent/ledger.json", jurisdiction_id="test")

    day1 = _discover(requests_mock, fixture_bytes, "hmt.atom")
    assert day1.status == "ok"
    new_items_day1, seen_items_day1 = diff_new_items(day1.items, ledger)
    assert len(new_items_day1) == 2
    assert len(seen_items_day1) == 0
    ledger = upsert_items(ledger, new_items_day1, run_ts="2026-06-23T12:00:00Z")

    day2 = _discover(requests_mock, fixture_bytes, "hmt_day2.atom")
    assert day2.status == "ok"
    assert len(day2.items) == 4

    new_items_day2, seen_items_day2 = diff_new_items(day2.items, ledger)

    assert len(new_items_day2) == 2
    assert len(seen_items_day2) == 2
    new_guids = {item.guid for item in new_items_day2}
    assert new_guids == {
        "https://www.gov.uk/government/publications/travel-rule-guidance",
        "https://www.gov.uk/government/news/tokenised-gilts-pilot",
    }

    ledger = upsert_items(ledger, new_items_day2, run_ts="2026-06-25T12:00:00Z")
    assert len(ledger["items"]) == 4

    # Re-running day2 again (idempotency: nothing new the second time).
    day2_again = _discover(requests_mock, fixture_bytes, "hmt_day2.atom")
    new_items_day2_again, _ = diff_new_items(day2_again.items, ledger)
    assert new_items_day2_again == []


def test_malformed_feed_is_a_parse_error_not_an_exception(requests_mock, fixture_bytes):
    result = _discover(requests_mock, fixture_bytes, "malformed.atom")

    assert result.status == "error"
    assert result.error_kind == "parse"
    assert result.items == []
