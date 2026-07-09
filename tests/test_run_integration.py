"""End-to-end tests for pipeline.watcher.run against mocked HK feeds.

These tests are the fixture-based stand-in for the Phase 1 acceptance
criterion ("watcher run produces a correct queue from live feeds; re-run
adds nothing") -- the literal live-feed verification happens separately as
a manual, dated run recorded in PROGRESS.md.
"""
from __future__ import annotations

import hashlib
import json
import os

import pytest

from pipeline.watcher import run as run_module
from pipeline.watcher.run import main, run
from tests.conftest import HK_JURISDICTION_PATH

FEED_FIXTURES = {
    "sfc_press_releases": "sfc_press_releases_day1.xml",
    "sfc_circulars": "sfc_circulars_day1.xml",
    "sfc_consultations": "sfc_consultations_day1.xml",
    "hkma_press_release": "hkma_press_release_day1.xml",
    "hkma_circulars": "hkma_circulars_day1.xml",
    "hkma_speeches": "hkma_speeches_day1.xml",
    "hkma_guidelines": "hkma_guidelines_day1.xml",
    "hkma_legislative_council_issues": "hkma_legislative_council_issues_day1.xml",
    "hkma_consultations": "hkma_consultations_day1.xml",
}


@pytest.fixture(autouse=True)
def _no_real_backoff_delay(monkeypatch):
    """Retry/backoff behavior itself is covered by tests/test_fetch.py --
    these integration tests only care about the outcome, so don't burn real
    wall-clock time on the retryable-failure test cases."""
    monkeypatch.setattr("pipeline.http.time.sleep", lambda seconds: None)


@pytest.fixture
def hk_config():
    with open(HK_JURISDICTION_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _register_feeds(requests_mock, config, fixture_bytes, overrides=None):
    overrides = overrides or {}
    for regulator in config["regulators"]:
        for feed in regulator["feeds"]:
            feed_id = feed["id"]
            fixture_name = overrides.get(feed_id, FEED_FIXTURES[feed_id])
            requests_mock.get(feed["url"], content=fixture_bytes(fixture_name))


def _file_hash(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def test_first_run_ingests_all_feeds(tmp_path, requests_mock, hk_config, fixture_bytes):
    _register_feeds(requests_mock, hk_config, fixture_bytes)
    ledger_path = str(tmp_path / "ledger.json")
    queue_path = str(tmp_path / "queue.json")
    cache_path = str(tmp_path / "cache" / "etags.json")

    summary = run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)

    assert summary.feeds_attempted == 9
    assert summary.feeds_ok == 9
    assert summary.feeds_failed == 0
    # hkma_circulars_day1.xml intentionally repeats one <item> verbatim
    # (mirrors a real duplicate observed live) -- 20 seen, 19 unique.
    assert summary.items_seen_total == 20
    assert summary.items_new == 19
    assert summary.ledger_changed is True
    assert summary.queue_changed is True

    with open(queue_path) as fh:
        queue_doc = json.load(fh)
    assert len(queue_doc["items"]) == 19
    assert all(item["status"] == "queued" for item in queue_doc["items"])


def test_immediate_rerun_adds_nothing(tmp_path, requests_mock, hk_config, fixture_bytes):
    """The literal Phase 1 acceptance criterion: re-run adds nothing."""
    _register_feeds(requests_mock, hk_config, fixture_bytes)
    ledger_path = str(tmp_path / "ledger.json")
    queue_path = str(tmp_path / "queue.json")
    cache_path = str(tmp_path / "cache" / "etags.json")

    run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)
    ledger_hash_1 = _file_hash(ledger_path)
    queue_hash_1 = _file_hash(queue_path)

    summary2 = run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)

    assert summary2.items_new == 0
    assert summary2.ledger_changed is False
    assert summary2.queue_changed is False
    assert _file_hash(ledger_path) == ledger_hash_1
    assert _file_hash(queue_path) == queue_hash_1


def test_third_run_picks_up_exactly_the_new_items(tmp_path, requests_mock, hk_config, fixture_bytes):
    ledger_path = str(tmp_path / "ledger.json")
    queue_path = str(tmp_path / "queue.json")
    cache_path = str(tmp_path / "cache" / "etags.json")

    _register_feeds(requests_mock, hk_config, fixture_bytes)
    run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)
    run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)

    # Day 2: sfc_circulars and hkma_press_release each publish one new item.
    _register_feeds(
        requests_mock,
        hk_config,
        fixture_bytes,
        overrides={
            "sfc_circulars": "sfc_circulars_day2.xml",
            "hkma_press_release": "hkma_press_release_day2.xml",
        },
    )
    summary3 = run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)

    assert summary3.items_new == 2
    assert summary3.ledger_changed is True
    assert summary3.queue_changed is True

    with open(queue_path) as fh:
        queue_doc = json.load(fh)
    assert len(queue_doc["items"]) == 21  # 19 + 2 new


def test_one_feed_failure_does_not_abort_the_run(tmp_path, requests_mock, hk_config, fixture_bytes):
    _register_feeds(requests_mock, hk_config, fixture_bytes)
    # Break exactly one feed -- terminal 4xx, no retries burned.
    broken_url = hk_config["regulators"][0]["feeds"][0]["url"]
    requests_mock.get(broken_url, status_code=404)

    summary = run(
        HK_JURISDICTION_PATH,
        str(tmp_path / "ledger.json"),
        str(tmp_path / "queue.json"),
        str(tmp_path / "cache" / "etags.json"),
    )

    assert summary.feeds_attempted == 9
    assert summary.feeds_failed == 1
    assert summary.feeds_ok == 8
    failed = [fr for fr in summary.feed_results if not fr.ok]
    assert len(failed) == 1
    assert failed[0].error == "HTTP 404"
    # The other 8 feeds still got ingested.
    assert summary.items_new > 0


def test_all_feeds_failing_returns_nonzero_exit(tmp_path, requests_mock, hk_config):
    for regulator in hk_config["regulators"]:
        for feed in regulator["feeds"]:
            requests_mock.get(feed["url"], status_code=500)

    exit_code = main(
        [
            "--config",
            HK_JURISDICTION_PATH,
            "--ledger",
            str(tmp_path / "ledger.json"),
            "--queue",
            str(tmp_path / "queue.json"),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )
    assert exit_code == 1


def test_partial_failure_still_returns_success_exit_code(tmp_path, requests_mock, hk_config, fixture_bytes):
    _register_feeds(requests_mock, hk_config, fixture_bytes)
    broken_url = hk_config["regulators"][0]["feeds"][0]["url"]
    requests_mock.get(broken_url, status_code=404)

    exit_code = main(
        [
            "--config",
            HK_JURISDICTION_PATH,
            "--ledger",
            str(tmp_path / "ledger.json"),
            "--queue",
            str(tmp_path / "queue.json"),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )
    assert exit_code == 0


def test_missing_config_file_returns_nonzero_exit(tmp_path):
    exit_code = main(
        [
            "--config",
            str(tmp_path / "does-not-exist.json"),
            "--ledger",
            str(tmp_path / "ledger.json"),
            "--queue",
            str(tmp_path / "queue.json"),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )
    assert exit_code == 1


def test_304_response_short_circuits_without_parsing(
    tmp_path, requests_mock, hk_config, fixture_bytes, monkeypatch
):
    _register_feeds(requests_mock, hk_config, fixture_bytes)
    ledger_path = str(tmp_path / "ledger.json")
    queue_path = str(tmp_path / "queue.json")
    cache_path = str(tmp_path / "cache" / "etags.json")

    # First run: a feed returns an ETag we can cache.
    watched_feed = hk_config["regulators"][0]["feeds"][0]
    requests_mock.get(
        watched_feed["url"],
        content=fixture_bytes(FEED_FIXTURES[watched_feed["id"]]),
        headers={"ETag": '"v1"'},
    )
    run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)

    # Second run: same feed now answers 304 given the cached ETag.
    requests_mock.get(watched_feed["url"], status_code=304)

    calls = []
    real_parse_rss = run_module.parse_rss

    def _spy(xml_bytes, **kwargs):
        calls.append(kwargs["feed_id"])
        return real_parse_rss(xml_bytes, **kwargs)

    monkeypatch.setattr(run_module, "parse_rss", _spy)
    run(HK_JURISDICTION_PATH, ledger_path, queue_path, cache_path)

    assert watched_feed["id"] not in calls
