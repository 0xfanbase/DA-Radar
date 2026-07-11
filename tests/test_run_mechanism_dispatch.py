"""P8 integration tests: pipeline.watcher.run's per-feed loop correctly
dispatches a mixed-mechanism jurisdiction config (one "rss" feed, one
"html_diff" feed) through pipeline.watcher.mechanisms.DISPATCH, and the
two mechanisms' output converges into one correctly-merged, correctly-
namespaced ledger/queue update -- exactly the NormalizedItem convergence
point the mechanism contract promises.

Also covers: watch_status.json's transition-keyed write ("re-run adds
nothing" holds for the new substrate too, not just ledger/queue), an
html_diff structural break flowing all the way from run.py's dispatch
through watch_status.json into pipeline.audit.feed_health.
check_feed_coverage as a real feed_structure_error (never mislabeled a
feed_silence), and an unknown "mechanism" value in a feed entry being a
per-feed failure that never aborts the run for the other feed.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from pipeline.audit.feed_health import check_feed_coverage
from pipeline.watcher.run import run

MIXED_CONFIG_PATH = "tests/fixtures/mixed_mechanism_jurisdiction.json"


def _load_config():
    with open(MIXED_CONFIG_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _register_ok_feeds(requests_mock, fixture_bytes, *, rss_fixture, listing_fixture):
    config = _load_config()
    feeds = {f["id"]: f for f in config["regulators"][0]["feeds"]}
    requests_mock.get(feeds["tfa_notices"]["url"], content=fixture_bytes(rss_fixture))
    requests_mock.get(feeds["tfa_listing"]["url"], content=fixture_bytes(listing_fixture))


def _paths(tmp_path):
    return dict(
        config_path=MIXED_CONFIG_PATH,
        ledger_path=str(tmp_path / "ledger.json"),
        queue_path=str(tmp_path / "queue.json"),
        cache_path=str(tmp_path / "cache" / "etags.json"),
        document_library_path=str(tmp_path / "document_library.json"),
        watch_status_path=str(tmp_path / "watch_status.json"),
    )


def test_mixed_mechanism_first_run_dispatches_both_and_merges_correctly(
    tmp_path, requests_mock, fixture_bytes
):
    _register_ok_feeds(
        requests_mock,
        fixture_bytes,
        rss_fixture="mixed_mechanism_rss_day1.xml",
        listing_fixture="mixed_mechanism_listing_day1.html",
    )
    p = _paths(tmp_path)

    summary = run(**p)

    assert summary.feeds_attempted == 2
    assert summary.feeds_ok == 2
    assert summary.feeds_failed == 0
    # 2 RSS items + 2 html_diff items.
    assert summary.items_seen_total == 4
    assert summary.items_new == 4
    assert summary.ledger_changed is True
    assert summary.queue_changed is True
    assert summary.watch_status_changed is True

    with open(p["ledger_path"]) as fh:
        ledger = json.load(fh)
    items = list(ledger["items"].values())
    assert len(items) == 4
    by_feed = {}
    for item in items:
        by_feed.setdefault(item["feed_id"], []).append(item)
        # Correctly namespaced regardless of which mechanism produced it.
        assert item["source_id"] == "tfa"

    assert {i["title"] for i in by_feed["tfa_notices"]} == {"TFA notice one", "TFA notice two"}
    # RSS identity: guid comes from the feed's own <guid>.
    assert {i["guid"] for i in by_feed["tfa_notices"]} == {"tfa-rss-1", "tfa-rss-2"}

    assert len(by_feed["tfa_listing"]) == 2
    for item in by_feed["tfa_listing"]:
        # html_diff identity: guid == link == the canonicalized URL, never
        # a synthesized value -- see mechanisms/html_diff.py.
        assert item["guid"] == item["link"]
        assert item["link"].startswith("https://tfa.testland.invalid/news/item-")

    # Queue merges relevant items from both mechanisms (no relevance_
    # keywords configured -> classify_relevance fails open, everything
    # relevant) -- all 4 items queued, tagged with their real feed_id.
    with open(p["queue_path"]) as fh:
        queue_doc = json.load(fh)
    assert len(queue_doc["items"]) == 4
    assert {i["feed_id"] for i in queue_doc["items"]} == {"tfa_notices", "tfa_listing"}

    # watch_status.json reports both feeds ok, tagged with the real
    # mechanism each one actually dispatched through.
    with open(p["watch_status_path"]) as fh:
        watch_status = json.load(fh)
    assert watch_status["jurisdiction_id"] == "testland"
    assert watch_status["feeds"]["tfa_notices"]["mechanism"] == "rss"
    assert watch_status["feeds"]["tfa_notices"]["status"] == "ok"
    assert watch_status["feeds"]["tfa_notices"]["last_error"] is None
    assert watch_status["feeds"]["tfa_listing"]["mechanism"] == "html_diff"
    assert watch_status["feeds"]["tfa_listing"]["status"] == "ok"


def test_mixed_mechanism_immediate_rerun_adds_nothing(tmp_path, requests_mock, fixture_bytes):
    """The Phase 1 acceptance criterion ("re-run adds nothing") holds
    across a mixed-mechanism config too, including the new watch_status.json
    substrate -- byte-identical on disk, not just semantically unchanged."""
    _register_ok_feeds(
        requests_mock,
        fixture_bytes,
        rss_fixture="mixed_mechanism_rss_day1.xml",
        listing_fixture="mixed_mechanism_listing_day1.html",
    )
    p = _paths(tmp_path)
    run(**p)

    with open(p["watch_status_path"]) as fh:
        watch_status_1 = fh.read()

    _register_ok_feeds(
        requests_mock,
        fixture_bytes,
        rss_fixture="mixed_mechanism_rss_day1.xml",
        listing_fixture="mixed_mechanism_listing_day1.html",
    )
    summary2 = run(**p)

    assert summary2.items_new == 0
    assert summary2.ledger_changed is False
    assert summary2.queue_changed is False
    assert summary2.watch_status_changed is False

    with open(p["watch_status_path"]) as fh:
        watch_status_2 = fh.read()
    assert watch_status_1 == watch_status_2


def test_mixed_mechanism_day2_picks_up_exactly_the_new_items_from_both(
    tmp_path, requests_mock, fixture_bytes
):
    _register_ok_feeds(
        requests_mock,
        fixture_bytes,
        rss_fixture="mixed_mechanism_rss_day1.xml",
        listing_fixture="mixed_mechanism_listing_day1.html",
    )
    p = _paths(tmp_path)
    run(**p)

    _register_ok_feeds(
        requests_mock,
        fixture_bytes,
        rss_fixture="mixed_mechanism_rss_day2.xml",
        listing_fixture="mixed_mechanism_listing_day2.html",
    )
    summary2 = run(**p)

    assert summary2.items_new == 2
    assert summary2.ledger_changed is True

    with open(p["queue_path"]) as fh:
        queue_doc = json.load(fh)
    assert len(queue_doc["items"]) == 6


def test_html_diff_structure_error_flows_into_watch_status_and_audit_flags_it(
    tmp_path, requests_mock, fixture_bytes
):
    """A redesigned listing page (item_selector matches 0 elements) is a
    per-feed failure recorded with error_kind="structure" -- run.py's
    watch_status.json persists that as status="structure_error", and
    pipeline.audit.feed_health.check_feed_coverage reports it as
    feed_structure_error, never mislabeled feed_silence, once the streak
    clears structure_error_min_days."""
    p = _paths(tmp_path)

    _register_ok_feeds(
        requests_mock,
        fixture_bytes,
        rss_fixture="mixed_mechanism_rss_day1.xml",
        listing_fixture="mixed_mechanism_listing_redesigned.html",
    )
    summary1 = run(**p)

    assert summary1.feeds_ok == 1
    assert summary1.feeds_failed == 1
    broken = [fr for fr in summary1.feed_results if not fr.ok]
    assert len(broken) == 1
    assert broken[0].feed_id == "tfa_listing"
    assert broken[0].error_kind == "structure"

    # Second run: still broken (same redesigned page) -- status_since must
    # NOT move forward, proving the transition-keyed contract.
    _register_ok_feeds(
        requests_mock,
        fixture_bytes,
        rss_fixture="mixed_mechanism_rss_day1.xml",
        listing_fixture="mixed_mechanism_listing_redesigned.html",
    )
    run(**p)

    with open(p["ledger_path"]) as fh:
        ledger = json.load(fh)
    with open(p["watch_status_path"]) as fh:
        watch_status = json.load(fh)

    listing_status = watch_status["feeds"]["tfa_listing"]
    assert listing_status["status"] == "structure_error"
    assert listing_status["mechanism"] == "html_diff"
    notices_status = watch_status["feeds"]["tfa_notices"]
    assert notices_status["status"] == "ok"

    status_since_date = date.fromisoformat(listing_status["status_since"][:10])
    audit_today = status_since_date + timedelta(days=2)

    events = check_feed_coverage(ledger, today=audit_today, watch_status=watch_status)
    events_by_type = {e["event_type"]: e for e in events}

    assert "feed_structure_error" in events_by_type
    structure_event = events_by_type["feed_structure_error"]
    assert structure_event["details"]["feed_id"] == "tfa_listing"
    assert structure_event["details"]["mechanism"] == "html_diff"
    assert structure_event["details"]["days_broken"] == 2

    # Mutual exclusivity: the broken feed must never ALSO show up as
    # merely "silent" -- it has structurally failed, which is a stronger,
    # differently-actionable diagnosis.
    assert "tfa_listing" not in [
        e["details"]["feed_id"] for e in events if e["event_type"] == "feed_silence"
    ]
    assert "feed_silence" not in events_by_type or events_by_type["feed_silence"]["details"]["feed_id"] != "tfa_listing"


def test_unknown_mechanism_is_a_per_feed_failure_not_a_run_abort(tmp_path, requests_mock, fixture_bytes):
    config = _load_config()
    config["regulators"][0]["feeds"][1]["mechanism"] = "totally_bogus_mechanism"
    bad_config_path = tmp_path / "bad_mechanism.json"
    bad_config_path.write_text(json.dumps(config), encoding="utf-8")

    requests_mock.get(
        config["regulators"][0]["feeds"][0]["url"],
        content=fixture_bytes("mixed_mechanism_rss_day1.xml"),
    )

    summary = run(
        config_path=str(bad_config_path),
        ledger_path=str(tmp_path / "ledger.json"),
        queue_path=str(tmp_path / "queue.json"),
        cache_path=str(tmp_path / "cache" / "etags.json"),
        watch_status_path=str(tmp_path / "watch_status.json"),
    )

    assert summary.feeds_attempted == 2
    assert summary.feeds_ok == 1
    assert summary.feeds_failed == 1
    bad = [fr for fr in summary.feed_results if not fr.ok]
    assert len(bad) == 1
    assert bad[0].feed_id == "tfa_listing"
    assert bad[0].error_kind == "config"
    assert "totally_bogus_mechanism" in bad[0].error
    # The other feed still ingested normally -- one bad mechanism config
    # never aborts the rest of the run.
    assert summary.items_new == 2

    with open(str(tmp_path / "watch_status.json")) as fh:
        watch_status = json.load(fh)
    assert watch_status["feeds"]["tfa_listing"]["status"] == "config_error"
