"""rss mechanism: thin composition of the existing pipeline.watcher.fetch.
fetch_feed + pipeline.watcher.parse.parse_rss into the shared discover()
contract (see pipeline.watcher.mechanisms.base).

This is the default mechanism (a feed entry with no explicit "mechanism"
field dispatches here -- see pipeline.watcher.mechanisms.DISPATCH and
pipeline.watcher.run's per-feed loop), and it is deliberately
behavior-identical to the inline fetch_feed + parse_rss code this module
replaces: same fetch discipline, same FeedParseError containment, same
NormalizedItem output, byte-for-byte on ledger output against the existing
HK fixtures. fetch.py and parse.py themselves are untouched -- this module
only recomposes their existing public APIs into the mechanism shape every
other discover() implementation (html_diff, sitemap_diff, json_api) also
follows, so run.py's per-feed loop can dispatch on "mechanism" without an
if/elif chain.
"""
from __future__ import annotations

from typing import Optional

import requests

from pipeline.watcher.fetch import fetch_feed
from pipeline.watcher.mechanisms.base import MechanismResult
from pipeline.watcher.parse import FeedParseError, parse_rss


def discover(
    feed: dict,
    *,
    source_id: str,
    user_agent: str,
    fetch_cfg: dict,
    etag: Optional[str],
    session: Optional[requests.Session] = None,
) -> MechanismResult:
    """Discover items from an rss-mechanism feed entry.

    Never raises: a FeedParseError from parse_rss (malformed/hostile XML)
    is caught here and returned as MechanismResult(status="error",
    error_kind="parse"), matching the containment contract every other
    mechanism's discover() follows -- one feed's failure is recorded,
    never aborts the run.
    """
    feed_id = feed["id"]
    url = feed["url"]

    fetch_result = fetch_feed(
        url,
        user_agent=user_agent,
        timeout=fetch_cfg["timeout_seconds"],
        max_retries=fetch_cfg["max_retries"],
        backoff_base=fetch_cfg["backoff_base_seconds"],
        backoff_multiplier=fetch_cfg["backoff_multiplier"],
        etag=etag,
        session=session,
    )

    if fetch_result.status == "error":
        return MechanismResult(
            status="error",
            error=fetch_result.error,
            error_kind="fetch",
            http_status=fetch_result.http_status,
        )

    if fetch_result.status == "not_modified":
        return MechanismResult(status="not_modified", etag=fetch_result.etag or etag)

    try:
        items = parse_rss(fetch_result.content, source_id=source_id, feed_id=feed_id, feed_url=url)
    except FeedParseError as exc:
        return MechanismResult(status="error", error=str(exc), error_kind="parse")

    return MechanismResult(status="ok", items=items, etag=fetch_result.etag)
