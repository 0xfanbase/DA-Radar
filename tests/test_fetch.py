"""Tests for pipeline.watcher.fetch."""
from __future__ import annotations

import requests

from pipeline.watcher.fetch import fetch_feed

URL = "https://example.invalid/rss/feed.xml"
UA = "TestAgent/0.1"


def test_200_returns_ok_and_reports_etag(requests_mock):
    requests_mock.get(URL, content=b"<rss></rss>", headers={"ETag": '"abc123"'}, status_code=200)
    result = fetch_feed(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0
    )
    assert result.status == "ok"
    assert result.http_status == 200
    assert result.content == b"<rss></rss>"
    assert result.etag == '"abc123"'
    assert result.attempts == 1
    assert requests_mock.last_request.headers["User-Agent"] == UA


def test_304_short_circuits_with_no_content(requests_mock):
    requests_mock.get(URL, status_code=304)
    result = fetch_feed(
        URL,
        user_agent=UA,
        timeout=5,
        max_retries=3,
        backoff_base=0.01,
        backoff_multiplier=2.0,
        etag='"cached-etag"',
    )
    assert result.status == "not_modified"
    assert result.content is None
    assert requests_mock.last_request.headers["If-None-Match"] == '"cached-etag"'


def test_timeout_retries_then_succeeds(requests_mock, monkeypatch):
    sleeps = []
    monkeypatch.setattr("pipeline.http.time.sleep", lambda s: sleeps.append(s))
    requests_mock.get(
        URL,
        [
            {"exc": requests.exceptions.ConnectTimeout},
            {"exc": requests.exceptions.ConnectTimeout},
            {"content": b"<rss></rss>", "status_code": 200},
        ],
    )
    result = fetch_feed(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=1.0, backoff_multiplier=2.0
    )
    assert result.status == "ok"
    assert result.attempts == 3
    assert sleeps == [1.0, 2.0]


def test_5xx_retries_with_backoff_then_fails(requests_mock, monkeypatch):
    sleeps = []
    monkeypatch.setattr("pipeline.http.time.sleep", lambda s: sleeps.append(s))
    requests_mock.get(URL, status_code=503)
    result = fetch_feed(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=1.0, backoff_multiplier=2.0
    )
    assert result.status == "error"
    assert result.attempts == 3
    assert sleeps == [1.0, 2.0]


def test_terminal_4xx_does_not_retry(requests_mock, monkeypatch):
    sleeps = []
    monkeypatch.setattr("pipeline.http.time.sleep", lambda s: sleeps.append(s))
    requests_mock.get(URL, status_code=404)
    result = fetch_feed(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=1.0, backoff_multiplier=2.0
    )
    assert result.status == "error"
    assert result.http_status == 404
    assert result.attempts == 1
    assert sleeps == []


def test_429_is_retried(requests_mock, monkeypatch):
    sleeps = []
    monkeypatch.setattr("pipeline.http.time.sleep", lambda s: sleeps.append(s))
    requests_mock.get(
        URL,
        [
            {"status_code": 429},
            {"content": b"<rss></rss>", "status_code": 200},
        ],
    )
    result = fetch_feed(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=1.0, backoff_multiplier=2.0
    )
    assert result.status == "ok"
    assert result.attempts == 2
    assert sleeps == [1.0]
