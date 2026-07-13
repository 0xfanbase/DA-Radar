"""atom mechanism: thin composition of the existing pipeline.watcher.fetch.
fetch_feed + pipeline.watcher.parse.parse_atom into the shared discover()
contract (see pipeline.watcher.mechanisms.base).

Mirrors pipeline.watcher.mechanisms.rss exactly, one call swapped
(parse_atom instead of parse_rss) -- fetch.py and parse.py themselves are
untouched.
"""
from __future__ import annotations

from typing import Optional

import requests

from pipeline.watcher.fetch import fetch_feed
from pipeline.watcher.mechanisms.base import MechanismResult
from pipeline.watcher.parse import FeedParseError, parse_atom


def discover(
    feed: dict,
    *,
    source_id: str,
    user_agent: str,
    fetch_cfg: dict,
    etag: Optional[str],
    session: Optional[requests.Session] = None,
) -> MechanismResult:
    """Discover items from an atom-mechanism feed entry.

    Never raises: a FeedParseError from parse_atom (malformed/hostile XML)
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
        items = parse_atom(fetch_result.content, source_id=source_id, feed_id=feed_id, feed_url=url)
    except FeedParseError as exc:
        return MechanismResult(status="error", error=str(exc), error_kind="parse")

    return MechanismResult(status="ok", items=items, etag=fetch_result.etag)
