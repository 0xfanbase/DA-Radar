"""Tests for pipeline.watcher.mechanisms.json_api.

Exercises the module directly (not via pipeline.watcher.run, which does
not yet dispatch on a feed's "mechanism" field -- same deferred-wiring note
as tests/test_html_diff.py and tests/test_sitemap_diff.py) against a
frozen, structure-faithful Federal Register documents.json snapshot under
tests/fixtures/, plus the real ledger seen-tracking machinery
(pipeline.watcher.ledger.diff_new_items / upsert_items) to prove the two
layers compose correctly: identity is the API's own document_number, so a
day2 snapshot with 2 new documents prepended to day1's 4 (one of which is
always dropped for a missing html_url) produces exactly 2 new items -- not
4 and not 0.

Also proves relevance filtering is a downstream concern (pipeline.watcher.
relevance.classify_relevance), not something this mechanism does itself --
per the P8 director design, json_api's extraction step performs no keyword
filtering; every item that survives extraction (has a resolvable link) is
handed on unfiltered, exactly as rss/atom/html_diff/sitemap_diff do.
"""
from __future__ import annotations

import json

from pipeline.watcher.ledger import diff_new_items, load_ledger, upsert_items
from pipeline.watcher.mechanisms.base import MechanismError
from pipeline.watcher.mechanisms.json_api import discover
from pipeline.watcher.relevance import classify_relevance

UA = "TestAgent/0.1"
FETCH_CFG = {
    "timeout_seconds": 5,
    "max_retries": 3,
    "backoff_base_seconds": 0.01,
    "backoff_multiplier": 2.0,
}

SOURCE_ID = "fedreg"

# Verbatim shape of the P8 director design's worked json_api config example
# (fedreg_digital_assets), pointed at a fixture URL rather than the live
# Federal Register endpoint.
FEED = {
    "id": "fedreg_digital_assets",
    "kind": "register_documents",
    "mechanism": "json_api",
    "url": (
        "https://www.federalregister.gov/api/v1/documents.json"
        '?conditions%5Bterm%5D=%22digital+asset%22+OR+stablecoin+OR+%22virtual+currency%22'
        "&order=newest&per_page=50"
    ),
    "json_api": {
        "items_path": "results",
        "fields": {
            "id": "document_number",
            "title": "title",
            "link": "html_url",
            "summary": "abstract",
            "published": "publication_date",
        },
    },
}


def _discover(requests_mock, fixture_bytes, fixture_name, *, etag=None):
    requests_mock.get(FEED["url"], content=fixture_bytes(fixture_name))
    return discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=etag, session=None)


def test_day1_response_yields_three_items_dropping_the_missing_link_result(requests_mock, fixture_bytes):
    """4 results in the fixture; one (2026-01077) has html_url: null and
    must be dropped, not hashed on title alone. The remaining 3 include a
    null-abstract result (summary must degrade to "", never crash)."""
    result = _discover(requests_mock, fixture_bytes, "fedreg_documents.json")

    assert result.status == "ok"
    assert result.error is None
    assert result.error_kind is None
    assert len(result.items) == 3

    guids = {item.guid for item in result.items}
    assert guids == {"2026-01001", "2026-01050", "2026-01090"}
    assert "2026-01077" not in guids  # dropped: html_url was null

    by_guid = {item.guid: item for item in result.items}

    custody = by_guid["2026-01001"]
    assert custody.source_id == SOURCE_ID
    assert custody.feed_id == "fedreg_digital_assets"
    assert custody.feed_url == FEED["url"]
    assert custody.link == (
        "https://www.federalregister.gov/documents/2026/01/05/2026-01001/"
        "digital-asset-custody-requirements-for-national-banks"
    )
    assert custody.title == "Digital Asset Custody Requirements for National Banks"
    assert custody.summary.startswith("The Office of the Comptroller of the Currency")
    assert custody.published_at == "2026-01-05T00:00:00Z"  # date-only YYYY-MM-DD padded
    assert custody.raw_published == "2026-01-05"
    assert custody.needs_enrichment is False

    stablecoin = by_guid["2026-01050"]
    assert stablecoin.summary == ""  # null abstract degrades gracefully, never crashes
    assert stablecoin.title == "Stablecoin Reserve Composition; Proposed Rule"
    assert stablecoin.published_at == "2026-01-08T00:00:00Z"
    assert stablecoin.needs_enrichment is False


def test_day2_diff_against_real_ledger_detects_exactly_two_new_items(requests_mock, fixture_bytes):
    """day1 yields 3 usable items (1 of 4 dropped for missing html_url);
    day2 is day1's 4 results plus 2 new results prepended (6 total, same 1
    still dropped -> 5 usable). Feeding both through the REAL ledger
    diff/upsert machinery must detect exactly 2 new items -- not 5 (that
    would mean seen-tracking is broken) and not 0 (that would mean the new
    rows were silently dropped)."""
    ledger = load_ledger("/nonexistent/ledger.json", jurisdiction_id="test")

    day1 = _discover(requests_mock, fixture_bytes, "fedreg_documents.json")
    assert day1.status == "ok"
    new_items_day1, seen_items_day1 = diff_new_items(day1.items, ledger)
    assert len(new_items_day1) == 3
    assert len(seen_items_day1) == 0
    ledger = upsert_items(ledger, new_items_day1, run_ts="2026-01-15T00:00:00Z")

    day2 = _discover(requests_mock, fixture_bytes, "fedreg_documents_day2.json")
    assert day2.status == "ok"
    assert len(day2.items) == 5

    new_items_day2, seen_items_day2 = diff_new_items(day2.items, ledger)

    assert len(new_items_day2) == 2
    assert len(seen_items_day2) == 3
    new_guids = {item.guid for item in new_items_day2}
    assert new_guids == {"2026-01120", "2026-01130"}

    ledger = upsert_items(ledger, new_items_day2, run_ts="2026-01-25T00:00:00Z")
    assert len(ledger["items"]) == 5

    # Re-running day2 again (idempotency: nothing new the second time).
    day2_again = _discover(requests_mock, fixture_bytes, "fedreg_documents_day2.json")
    new_items_day2_again, _ = diff_new_items(day2_again.items, ledger)
    assert new_items_day2_again == []


def test_identity_is_document_number_not_link(requests_mock, fixture_bytes):
    """guid is the configured fields.id path (document_number), never the
    link -- a stable citation id that survives a URL restructure, unlike
    html_diff/sitemap_diff where guid=canonical link because those sources
    have no id field at all."""
    result = _discover(requests_mock, fixture_bytes, "fedreg_documents.json")
    for item in result.items:
        assert item.guid != item.link
        assert item.guid.startswith("2026-")


def test_relevance_filtering_is_a_downstream_concern_not_done_by_this_mechanism(
    requests_mock, fixture_bytes
):
    """json_api's own extraction step performs no keyword filtering --
    every item with a resolvable link is handed on unfiltered (matching
    rss/atom/html_diff/sitemap_diff). The digital-asset keyword filter is
    applied downstream by pipeline.watcher.relevance.classify_relevance
    against the ledger, exactly as it is for every other mechanism."""
    result = _discover(requests_mock, fixture_bytes, "fedreg_documents.json")
    assert len(result.items) == 3  # unfiltered: all 3 link-having results present

    ledger = load_ledger("/nonexistent/ledger.json", jurisdiction_id="test")
    new_items, _ = diff_new_items(result.items, ledger)
    ledger = upsert_items(ledger, new_items, run_ts="2026-01-15T00:00:00Z")

    keywords = ["digital asset", "stablecoin", "virtual currency"]
    ledger, changed = classify_relevance(ledger, keywords, run_ts="2026-01-15T00:05:00Z")
    assert len(changed) == 3
    # Every fixture item's title genuinely contains one of the configured
    # keywords, so all 3 classify relevant=True -- the filter runs, it
    # isn't a no-op.
    assert all(entry["relevant"] is True for entry in ledger["items"].values())

    # A control: an item whose title/summary contain none of the keywords
    # classifies relevant=False, proving the filter can also reject.
    off_topic_ledger = {
        "schema_version": ledger["schema_version"],
        "jurisdiction_id": "test",
        "generated_at": "2026-01-15T00:00:00Z",
        "items": {
            "fakehash": {
                "item_hash": "fakehash",
                "source_id": SOURCE_ID,
                "feed_id": "fedreg_digital_assets",
                "title": "Annual Report on Postal Rate Adjustments",
                "summary": "This notice concerns postal rate adjustments.",
                "link": "https://www.federalregister.gov/documents/2026/01/01/x",
                "published_at": "2026-01-01T00:00:00Z",
                "status": "queued",
                "first_seen": "2026-01-15T00:00:00Z",
                "last_seen": "2026-01-15T00:00:00Z",
            }
        },
    }
    off_topic_ledger, _ = classify_relevance(off_topic_ledger, keywords, run_ts="2026-01-15T00:05:00Z")
    assert off_topic_ledger["items"]["fakehash"]["relevant"] is False


def test_empty_results_is_ok_with_zero_items_never_a_structure_error(requests_mock, fixture_bytes):
    """A filtered API query genuinely returning zero matches today is a
    legitimate, healthy outcome -- unlike an empty sitemap or a zero-match
    CSS selector, which can never legitimately be empty. Never reported as
    status='error'."""
    result = _discover(requests_mock, fixture_bytes, "fedreg_documents_empty.json")

    assert result.status == "ok"
    assert result.error is None
    assert result.error_kind is None
    assert result.items == []


def test_items_path_miss_raises_structure_error(requests_mock, fixture_bytes):
    """The response shape changed out from under the config (e.g. an API
    error body with no 'results' key at all) -- mechanically distinguishable
    from a legitimate empty result set."""
    result = _discover(requests_mock, fixture_bytes, "fedreg_documents_items_path_miss.json")

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []
    assert "items_path" in result.error
    assert "results" in result.error


def test_items_path_resolving_to_non_list_raises_structure_error(requests_mock, fixture_bytes):
    result = _discover(requests_mock, fixture_bytes, "fedreg_documents_results_not_list.json")

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []


def test_all_results_missing_link_raises_structure_error(requests_mock, fixture_bytes):
    """A non-empty results array where every result is missing the
    configured fields.link path must never masquerade as a healthy
    zero-item response -- the API shape changed, this isn't 'nothing new
    today'."""
    payload = json.dumps(
        {
            "count": 2,
            "results": [
                {"document_number": "2026-09001", "title": "No link here"},
                {"document_number": "2026-09002", "title": "No link here either"},
            ],
        }
    ).encode("utf-8")
    requests_mock.get(FEED["url"], content=payload)
    result = discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []


def test_malformed_json_maps_to_parse_error(requests_mock, fixture_bytes):
    requests_mock.get(FEED["url"], content=fixture_bytes("malformed.json"))
    result = discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "parse"
    assert result.items == []


def test_not_modified_short_circuits_with_no_items(requests_mock):
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


def test_missing_id_field_falls_back_to_link_title_identity(requests_mock):
    """When json_api.fields.id is absent from config, guid is simply None
    and pipeline.watcher.hashing.identity_key_for_item's existing
    link+title fallback covers identity -- no special-casing needed in
    this module, matching the P8 design note."""
    feed = {
        "id": "no_id_field_api",
        "url": "https://example.gov/api/documents.json",
        "json_api": {
            "items_path": "results",
            "fields": {"title": "title", "link": "html_url", "summary": "abstract", "published": "publication_date"},
        },
    }
    payload = json.dumps(
        {
            "results": [
                {
                    "title": "Some Notice",
                    "html_url": "https://example.gov/docs/1",
                    "abstract": "text",
                    "publication_date": "2026-02-01",
                }
            ]
        }
    ).encode("utf-8")
    requests_mock.get(feed["url"], content=payload)
    result = discover(feed, source_id="example", user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "ok"
    assert len(result.items) == 1
    assert result.items[0].guid is None
    assert result.items[0].link == "https://example.gov/docs/1"


def test_discover_never_raises_mechanism_error_itself(requests_mock, fixture_bytes):
    """discover() is the containment boundary: even on the loudest failure
    mode, it returns a MechanismResult rather than propagating an
    exception, matching FeedParseError's / every other mechanism's
    existing per-feed containment contract."""
    requests_mock.get(FEED["url"], content=fixture_bytes("fedreg_documents_items_path_miss.json"))
    try:
        result = discover(FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)
    except MechanismError:
        assert False, "discover() must never raise MechanismError -- it must return it as a result"
    assert result.status == "error"


def test_rfc2822_fallback_for_a_non_iso_published_field(requests_mock):
    """Some older/differently-shaped APIs stamp an RFC-2822 date rather
    than ISO-8601/date-only -- the RSS-style parser is the documented
    fallback."""
    feed = {
        "id": "rfc2822_api",
        "url": "https://example.gov/api/documents.json",
        "json_api": {
            "items_path": "results",
            "fields": {"id": "id", "title": "title", "link": "url", "summary": "summary", "published": "published"},
        },
    }
    payload = json.dumps(
        {
            "results": [
                {
                    "id": "abc123",
                    "title": "Legacy Notice",
                    "url": "https://example.gov/docs/legacy",
                    "summary": "text",
                    "published": "Tue, 03 Feb 2026 10:00:00 GMT",
                }
            ]
        }
    ).encode("utf-8")
    requests_mock.get(feed["url"], content=payload)
    result = discover(feed, source_id="example", user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "ok"
    item = result.items[0]
    assert item.published_at == "2026-02-03T10:00:00Z"
    assert item.raw_published == "Tue, 03 Feb 2026 10:00:00 GMT"
