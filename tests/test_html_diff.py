"""Tests for pipeline.watcher.mechanisms.html_diff.

Exercises the module directly (not via pipeline.watcher.run, which does
not yet dispatch on a feed's "mechanism" field -- that wiring is a
separate, later step) against frozen HTML snapshots under
tests/fixtures/, plus the real ledger seen-tracking machinery
(pipeline.watcher.ledger.diff_new_items / upsert_items) to prove the two
layers compose correctly: identity is URL-alone (guid=canonical link), so
a day2 snapshot with 2 new rows appended to day1's 3 produces exactly 2
new items, never 5 and never 0.
"""
from __future__ import annotations

from pipeline.watcher.ledger import diff_new_items, load_ledger, upsert_items
from pipeline.watcher.mechanisms.base import MechanismError
from pipeline.watcher.mechanisms.html_diff import discover

UA = "TestAgent/0.1"
FETCH_CFG = {
    "timeout_seconds": 5,
    "max_retries": 3,
    "backoff_base_seconds": 0.01,
    "backoff_multiplier": 2.0,
}

# Verbatim shape of the P8 director design's worked html_diff config
# example -- see CLAUDE.md-adjacent design notes for the field meanings.
FEED = {
    "id": "fincen_news",
    "kind": "press_releases",
    "mechanism": "html_diff",
    "url": "https://www.fincen.gov/news-room/news",
    "html_diff": {
        "item_selector": "div.view-news-room div.views-row",
        "link_selector": "a[href]",
        "title_selector": "a[href]",
        "date_selector": "span.date-display-single",
        "date_format": "%m/%d/%Y",
        "base_url": "https://www.fincen.gov",
    },
}

SOURCE_ID = "fincen"


def _discover(requests_mock, fixture_bytes, fixture_name, *, etag=None):
    requests_mock.get(FEED["url"], content=fixture_bytes(fixture_name))
    return discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=etag, session=None)


def test_day1_listing_yields_all_three_items(requests_mock, fixture_bytes):
    result = _discover(requests_mock, fixture_bytes, "fincen_news.html")

    assert result.status == "ok"
    assert result.error is None
    assert result.error_kind is None
    assert len(result.items) == 3

    links = {item.link for item in result.items}
    assert links == {
        "https://www.fincen.gov/news/news-releases/item-one",
        "https://www.fincen.gov/news/news-releases/item-two",
        "https://www.fincen.gov/news/news-releases/item-three",
    }
    # guid == link (canonical URL) for every item -- identity is URL-alone.
    for item in result.items:
        assert item.guid == item.link
        assert item.source_id == SOURCE_ID
        assert item.feed_id == "fincen_news"
        assert item.feed_url == FEED["url"]
        assert item.needs_enrichment is False  # title_selector extracted real text
        assert item.title  # non-empty
        assert item.summary == ""  # no summary_selector configured
        assert item.published_at is not None
        assert item.published_at.endswith("Z")


def test_day2_diff_against_real_ledger_detects_exactly_two_new_items(requests_mock, fixture_bytes):
    """day1 has 3 items; day2 is day1's 3 rows plus 2 new rows prepended
    (5 total). Feeding both through the REAL ledger diff/upsert machinery
    (not a reimplementation) must detect exactly the 2 new items -- not 5
    (that would mean seen-tracking is broken and every re-run re-queues
    everything) and not 0 (that would mean the new rows were silently
    dropped)."""
    ledger = load_ledger("/nonexistent/ledger.json", jurisdiction_id="test")

    day1 = _discover(requests_mock, fixture_bytes, "fincen_news.html")
    assert day1.status == "ok"
    new_items_day1, seen_items_day1 = diff_new_items(day1.items, ledger)
    assert len(new_items_day1) == 3
    assert len(seen_items_day1) == 0
    ledger = upsert_items(ledger, new_items_day1, run_ts="2026-01-15T00:00:00Z")

    day2 = _discover(requests_mock, fixture_bytes, "fincen_news_day2.html")
    assert day2.status == "ok"
    assert len(day2.items) == 5

    new_items_day2, seen_items_day2 = diff_new_items(day2.items, ledger)

    assert len(new_items_day2) == 2
    assert len(seen_items_day2) == 3
    new_links = {item.link for item in new_items_day2}
    assert new_links == {
        "https://www.fincen.gov/news/news-releases/item-four",
        "https://www.fincen.gov/news/news-releases/item-five",
    }

    ledger = upsert_items(ledger, new_items_day2, run_ts="2026-01-25T00:00:00Z")
    assert len(ledger["items"]) == 5

    # Re-running day2 again (idempotency: nothing new the second time).
    day2_again = _discover(requests_mock, fixture_bytes, "fincen_news_day2.html")
    new_items_day2_again, _ = diff_new_items(day2_again.items, ledger)
    assert new_items_day2_again == []


def test_selector_matching_zero_elements_raises_structure_error_not_empty_result(
    requests_mock, fixture_bytes
):
    """The critical loud-failure case: a redesigned page where the
    configured item_selector matches nothing must be mechanically
    distinguishable from a genuinely quiet source. It is never reported as
    status="ok" with 0 items."""
    result = _discover(requests_mock, fixture_bytes, "fincen_news_redesigned.html")

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []
    assert "div.view-news-room div.views-row" in result.error
    assert "0" in result.error


def test_selector_matches_elements_but_none_yield_a_link_raises_structure_error(
    requests_mock, fixture_bytes
):
    """Structure-error case (b): item_selector matches N >= 1 elements,
    but none of them yielded a resolvable link (e.g. the anchor markup was
    dropped in a redesign, even though the row wrapper survived)."""
    result = _discover(requests_mock, fixture_bytes, "fincen_news_no_links.html")

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []
    assert "div.view-news-room div.views-row" in result.error


def test_a_healthy_quiet_day_is_ok_with_zero_new_items_never_a_structure_error(
    requests_mock, fixture_bytes
):
    """Positive control distinguishing the two states the structure-error
    design explicitly guards apart: re-fetching the SAME day1 snapshot
    (selector still matches 3 real items, all already in the ledger) is a
    healthy, quiet re-run -- status="ok", not an error -- even though the
    outcome (0 new items) looks superficially similar to the broken-
    selector case at the ledger-diff layer."""
    ledger = load_ledger("/nonexistent/ledger.json", jurisdiction_id="test")
    day1 = _discover(requests_mock, fixture_bytes, "fincen_news.html")
    new_items, _ = diff_new_items(day1.items, ledger)
    ledger = upsert_items(ledger, new_items, run_ts="2026-01-15T00:00:00Z")

    rerun = _discover(requests_mock, fixture_bytes, "fincen_news.html")
    assert rerun.status == "ok"
    assert rerun.error_kind is None
    assert len(rerun.items) == 3

    new_items_rerun, seen_items_rerun = diff_new_items(rerun.items, ledger)
    assert new_items_rerun == []
    assert len(seen_items_rerun) == 3


def test_relative_and_absolute_hrefs_canonicalize_via_urljoin(requests_mock, fixture_bytes):
    """Root-relative, path-relative, and an absolute href with an
    upper-case host, an explicit default port, and a fragment must all
    canonicalize correctly -- proving real urljoin resolution + urlnorm
    normalization, not naive string concatenation."""
    result = _discover(requests_mock, fixture_bytes, "fincen_news_relative_hrefs.html")

    assert result.status == "ok"
    links = {item.link for item in result.items}
    assert links == {
        "https://www.fincen.gov/news/news-releases/item-root-relative",
        "https://www.fincen.gov/news-releases/item-path-relative",
        # default port stripped, fragment stripped, query preserved, host lowercased
        "https://www.fincen.gov/news/news-releases/item-absolute?ref=1",
    }
    for item in result.items:
        assert item.guid == item.link


def test_not_modified_short_circuits_with_no_items(requests_mock, fixture_bytes):
    requests_mock.get(FEED["url"], status_code=304)
    result = discover(
        FEED,
        source_id=SOURCE_ID,
        user_agent=UA,
        fetch_cfg=FETCH_CFG,
        etag='"cached-etag"',
        session=None,
    )
    assert result.status == "not_modified"
    assert result.items == []
    assert result.error is None


def test_fetch_failure_maps_to_error_kind_fetch(requests_mock):
    requests_mock.get(FEED["url"], status_code=404)
    result = discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "fetch"
    assert result.items == []


def test_discover_never_raises_mechanism_error_itself(requests_mock, fixture_bytes):
    """discover() is the containment boundary: even on the loudest failure
    mode, it returns a MechanismResult rather than propagating an
    exception, matching FeedParseError's existing per-feed containment
    contract in pipeline.watcher.run."""
    requests_mock.get(FEED["url"], content=fixture_bytes("fincen_news_redesigned.html"))
    try:
        result = discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)
    except MechanismError:
        assert False, "discover() must never raise MechanismError -- it must return it as a result"
    assert result.status == "error"
