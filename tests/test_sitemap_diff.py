"""Tests for pipeline.watcher.mechanisms.sitemap_diff.

Exercises the module directly (not via pipeline.watcher.run, which does
not yet dispatch on a feed's "mechanism" field -- same deferred-wiring
note as tests/test_html_diff.py) against frozen sitemap XML snapshots
under tests/fixtures/, plus the real ledger seen-tracking machinery
(pipeline.watcher.ledger.diff_new_items / upsert_items) to prove the two
layers compose correctly: identity is URL-alone (guid=canonical link), so
a day2 snapshot with 3 new matching URLs appended across two child
sitemaps produces exactly 3 new items -- never fewer (silently dropped)
and never more (re-queuing already-known URLs).
"""
from __future__ import annotations

from pipeline.watcher.ledger import diff_new_items, load_ledger, upsert_items
from pipeline.watcher.mechanisms.base import MechanismError
from pipeline.watcher.mechanisms.sitemap_diff import discover

UA = "TestAgent/0.1"
FETCH_CFG = {
    "timeout_seconds": 5,
    "max_retries": 3,
    "backoff_base_seconds": 0.01,
    "backoff_multiplier": 2.0,
}

SOURCE_ID = "mas"

# Verbatim shape of the P8 director design's worked sitemap_diff config
# example (mas_media_releases), pointed at a sitemapindex fixture rather
# than the live MAS URL.
INDEX_FEED = {
    "id": "mas_media_releases",
    "kind": "press_releases",
    "mechanism": "sitemap_diff",
    "url": "https://www.mas.gov.sg/sitemap.xml",
    "sitemap_diff": {
        "url_pattern": r"^https://www\.mas\.gov\.sg/news/(media-releases|speeches)/",
        "max_new_per_run": 50,
        "max_child_sitemaps": 5,
        "index_pattern": "news",
    },
}

MEDIA_URL = "https://www.mas.gov.sg/sitemap-news-media-releases.xml"
SPEECHES_URL = "https://www.mas.gov.sg/sitemap-news-speeches.xml"
PRODUCTS_URL = "https://www.mas.gov.sg/sitemap-products.xml"


def _mock_index_day1(requests_mock, fixture_bytes):
    requests_mock.get(INDEX_FEED["url"], content=fixture_bytes("mas_sitemap_index.xml"))
    requests_mock.get(MEDIA_URL, content=fixture_bytes("mas_sitemap_news_media_releases.xml"))
    requests_mock.get(SPEECHES_URL, content=fixture_bytes("mas_sitemap_news_speeches.xml"))
    requests_mock.get(PRODUCTS_URL, content=fixture_bytes("mas_sitemap_pattern_miss.xml"))


def _mock_index_day2(requests_mock, fixture_bytes):
    requests_mock.get(INDEX_FEED["url"], content=fixture_bytes("mas_sitemap_index.xml"))
    requests_mock.get(MEDIA_URL, content=fixture_bytes("mas_sitemap_news_media_releases_day2.xml"))
    requests_mock.get(SPEECHES_URL, content=fixture_bytes("mas_sitemap_news_speeches_day2.xml"))
    requests_mock.get(PRODUCTS_URL, content=fixture_bytes("mas_sitemap_pattern_miss.xml"))


def _discover_index(requests_mock, fixture_bytes, *, day2=False, etag=None):
    if day2:
        _mock_index_day2(requests_mock, fixture_bytes)
    else:
        _mock_index_day1(requests_mock, fixture_bytes)
    return discover(
        INDEX_FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=etag, session=None
    )


def test_day1_sitemap_index_yields_all_matching_items_across_children(requests_mock, fixture_bytes):
    result = _discover_index(requests_mock, fixture_bytes)

    assert result.status == "ok"
    assert result.error is None
    assert result.error_kind is None
    # 10 media-releases + 8 speeches match url_pattern; the products child
    # sitemap is excluded entirely by index_pattern, and the 4
    # non-matching URLs within the two followed children are excluded by
    # url_pattern.
    assert len(result.items) == 18

    links = {item.link for item in result.items}
    assert "https://www.mas.gov.sg/news/media-releases/2026/item-01" in links
    assert "https://www.mas.gov.sg/news/speeches/2026/speech-01" in links
    # Non-matching URLs (even ones seen in a followed child) never appear.
    assert "https://www.mas.gov.sg/news/announcements/routine-notice" not in links
    assert "https://www.mas.gov.sg/who-we-are/history" not in links
    assert "https://www.mas.gov.sg/regulation/some-notice" not in links

    for item in result.items:
        # guid == link (canonical URL) for every item -- identity is URL-alone.
        assert item.guid == item.link
        assert item.source_id == SOURCE_ID
        assert item.feed_id == "mas_media_releases"
        assert item.feed_url == INDEX_FEED["url"]
        # A sitemap gives a URL and nothing trustworthy else -- never a
        # fabricated title or date.
        assert item.title == ""
        assert item.summary == ""
        assert item.needs_enrichment is True
        assert item.published_at is None
        # lastmod is provenance-only, never promoted to published_at.
        assert item.raw_published is not None


def test_day2_diff_against_real_ledger_detects_exactly_three_new_items(requests_mock, fixture_bytes):
    """day1 yields 18 matching items; day2 adds 2 new media-releases URLs
    and 1 new speech URL (3 new matching total), plus 2 new NON-matching
    URLs that must never surface as items at all. Feeding both through the
    REAL ledger diff/upsert machinery must detect exactly 3 new items --
    never 21 (that would mean seen-tracking is broken) and never 0 (that
    would mean the new rows were silently dropped)."""
    ledger = load_ledger("/nonexistent/ledger.json", jurisdiction_id="test")

    day1 = _discover_index(requests_mock, fixture_bytes)
    assert day1.status == "ok"
    new_items_day1, seen_items_day1 = diff_new_items(day1.items, ledger)
    assert len(new_items_day1) == 18
    assert len(seen_items_day1) == 0
    ledger = upsert_items(ledger, new_items_day1, run_ts="2026-07-01T00:00:00Z")

    day2 = _discover_index(requests_mock, fixture_bytes, day2=True)
    assert day2.status == "ok"
    # Still only the url_pattern-matching URLs: 12 media-releases + 9
    # speeches (day1's counts + 2 and + 1 respectively).
    assert len(day2.items) == 21

    new_items_day2, seen_items_day2 = diff_new_items(day2.items, ledger)

    assert len(new_items_day2) == 3
    assert len(seen_items_day2) == 18
    new_links = {item.link for item in new_items_day2}
    assert new_links == {
        "https://www.mas.gov.sg/news/media-releases/2026/item-11",
        "https://www.mas.gov.sg/news/media-releases/2026/item-12",
        "https://www.mas.gov.sg/news/speeches/2026/speech-09",
    }
    # The new non-matching URLs never made it into day2.items at all.
    all_day2_links = {item.link for item in day2.items}
    assert "https://www.mas.gov.sg/news/announcements/new-routine-notice" not in all_day2_links
    assert "https://www.mas.gov.sg/news/announcements/new-office-closure" not in all_day2_links

    for item in new_items_day2:
        assert item.title == ""
        assert item.published_at is None
        assert item.needs_enrichment is True

    ledger = upsert_items(ledger, new_items_day2, run_ts="2026-07-11T00:00:00Z")
    assert len(ledger["items"]) == 21

    # Re-running day2 again (idempotency: nothing new the second time).
    day2_again = _discover_index(requests_mock, fixture_bytes, day2=True)
    new_items_day2_again, _ = diff_new_items(day2_again.items, ledger)
    assert new_items_day2_again == []


def test_index_pattern_excludes_the_products_child_sitemap(requests_mock, fixture_bytes):
    """The products child sitemap is never fetched at all -- index_pattern
    'news' filters it out before any child fetch happens."""
    _mock_index_day1(requests_mock, fixture_bytes)
    discover(INDEX_FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)
    assert not requests_mock.request_history or all(
        req.url != PRODUCTS_URL for req in requests_mock.request_history
    )


def test_url_pattern_matches_zero_raises_structure_error(requests_mock, fixture_bytes):
    """A single urlset whose URLs never match url_pattern at all -- the
    critical loud-failure case distinguishing a URL-scheme change from a
    genuinely quiet source."""
    feed = {
        "id": "mas_pattern_miss",
        "url": "https://www.mas.gov.sg/sitemap-products.xml",
        "sitemap_diff": {
            "url_pattern": r"^https://www\.mas\.gov\.sg/news/(media-releases|speeches)/",
        },
    }
    requests_mock.get(feed["url"], content=fixture_bytes("mas_sitemap_pattern_miss.xml"))
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []
    assert "matched 0 of" in result.error


def test_new_url_count_exceeding_max_new_per_run_raises_structure_error(requests_mock, fixture_bytes):
    """55 URLs match url_pattern in a single fetch, exceeding the default
    max_new_per_run=50 -- reported as a structure error rather than
    silently flooding the queue with what could be a mass URL-scheme
    migration wrongly read as "55 brand-new items"."""
    feed = {
        "id": "mas_oversize",
        "url": "https://www.mas.gov.sg/sitemap-oversize.xml",
        "sitemap_diff": {
            "url_pattern": r"^https://www\.mas\.gov\.sg/news/(media-releases|speeches)/",
        },
    }
    requests_mock.get(feed["url"], content=fixture_bytes("mas_sitemap_oversize.xml"))
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []
    assert "55" in result.error
    assert "max_new_per_run=50" in result.error


def test_new_url_count_within_a_raised_cap_succeeds(requests_mock, fixture_bytes):
    """The same 55-URL fixture succeeds once max_new_per_run is raised
    deliberately -- proving the cap is a configured threshold, not a hard
    ceiling in the code."""
    feed = {
        "id": "mas_oversize",
        "url": "https://www.mas.gov.sg/sitemap-oversize.xml",
        "sitemap_diff": {
            "url_pattern": r"^https://www\.mas\.gov\.sg/news/(media-releases|speeches)/",
            "max_new_per_run": 100,
        },
    }
    requests_mock.get(feed["url"], content=fixture_bytes("mas_sitemap_oversize.xml"))
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "ok"
    assert len(result.items) == 55


def test_max_child_sitemaps_cap_exceeded_raises_structure_error(requests_mock, fixture_bytes):
    """A cap of 1 with index_pattern 'news' still matches 2 children
    (media-releases and speeches) -- exceeding the cap after filtering,
    never silently truncated to the first one."""
    feed = dict(INDEX_FEED)
    feed["sitemap_diff"] = dict(INDEX_FEED["sitemap_diff"])
    feed["sitemap_diff"]["max_child_sitemaps"] = 1
    _mock_index_day1(requests_mock, fixture_bytes)
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []
    assert "max_child_sitemaps=1" in result.error


def test_root_neither_urlset_nor_sitemapindex_raises_structure_error(requests_mock, fixture_bytes):
    feed = {
        "id": "mas_bad_root",
        "url": "https://www.mas.gov.sg/not-a-sitemap.xml",
        "sitemap_diff": {"url_pattern": r".*"},
    }
    requests_mock.get(
        feed["url"],
        content=b'<?xml version="1.0"?><rss version="2.0"><channel><title>t</title></channel></rss>',
    )
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []


def test_zero_loc_entries_raises_structure_error(requests_mock, fixture_bytes):
    feed = {
        "id": "mas_empty",
        "url": "https://www.mas.gov.sg/sitemap-empty.xml",
        "sitemap_diff": {"url_pattern": r".*"},
    }
    requests_mock.get(
        feed["url"],
        content=b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',
    )
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "structure"
    assert result.items == []
    assert "0 <loc>" in result.error


def test_malformed_xml_maps_to_parse_error(requests_mock, fixture_bytes):
    feed = {
        "id": "mas_malformed",
        "url": "https://www.mas.gov.sg/sitemap-malformed.xml",
        "sitemap_diff": {"url_pattern": r".*"},
    }
    requests_mock.get(feed["url"], content=fixture_bytes("malformed.xml"))
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "parse"
    assert result.items == []


def test_billion_laughs_xxe_maps_to_parse_error_not_a_hang_or_crash(requests_mock, fixture_bytes):
    """defusedxml must reject entity-expansion attacks rather than
    hang/crash -- a fetched sitemap is exactly as untrusted as a fetched
    RSS/Atom feed (see pipeline/watcher/parse.py's identical discipline)."""
    xxe_payload = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ELEMENT lolz (#PCDATA)>
 <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>&lol1;</loc></url>
</urlset>"""
    feed = {
        "id": "mas_xxe",
        "url": "https://www.mas.gov.sg/sitemap-xxe.xml",
        "sitemap_diff": {"url_pattern": r".*"},
    }
    requests_mock.get(feed["url"], content=xxe_payload)
    result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)

    assert result.status == "error"
    assert result.error_kind == "parse"
    assert result.items == []


def test_not_modified_short_circuits_with_no_items(requests_mock, fixture_bytes):
    requests_mock.get(INDEX_FEED["url"], status_code=304)
    result = discover(
        INDEX_FEED,
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
    requests_mock.get(INDEX_FEED["url"], status_code=404)
    result = discover(
        INDEX_FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None
    )

    assert result.status == "error"
    assert result.error_kind == "fetch"
    assert result.items == []


def test_child_sitemap_fetch_failure_maps_to_error_kind_fetch(requests_mock, fixture_bytes):
    requests_mock.get(INDEX_FEED["url"], content=fixture_bytes("mas_sitemap_index.xml"))
    requests_mock.get(MEDIA_URL, status_code=500)
    requests_mock.get(SPEECHES_URL, content=fixture_bytes("mas_sitemap_news_speeches.xml"))
    result = discover(
        INDEX_FEED, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None
    )

    assert result.status == "error"
    assert result.error_kind == "fetch"
    assert result.items == []


def test_discover_never_raises_mechanism_error_itself(requests_mock, fixture_bytes):
    """discover() is the containment boundary: even on the loudest failure
    mode, it returns a MechanismResult rather than propagating an
    exception, matching FeedParseError's / html_diff.discover's existing
    per-feed containment contract."""
    feed = {
        "id": "mas_pattern_miss",
        "url": "https://www.mas.gov.sg/sitemap-products.xml",
        "sitemap_diff": {
            "url_pattern": r"^https://www\.mas\.gov\.sg/news/(media-releases|speeches)/",
        },
    }
    requests_mock.get(feed["url"], content=fixture_bytes("mas_sitemap_pattern_miss.xml"))
    try:
        result = discover(feed, source_id=SOURCE_ID, user_agent=UA, fetch_cfg=FETCH_CFG, etag=None, session=None)
    except MechanismError:
        assert False, "discover() must never raise MechanismError -- it must return it as a result"
    assert result.status == "error"
