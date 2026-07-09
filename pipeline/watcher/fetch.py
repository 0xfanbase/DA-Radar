"""HTTP fetching for the watcher: ETag-conditional GET on top of the shared
retry/backoff core in pipeline/http.py.

The User-Agent is sourced from config/jurisdiction.json -- never hardcoded
here, to keep this module jurisdiction-agnostic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from pipeline.http import http_get_with_retry


@dataclass
class FetchResult:
    url: str
    status: str  # "ok" | "not_modified" | "error"
    content: Optional[bytes]
    etag: Optional[str]
    fetched_at: str
    http_status: Optional[int]
    error: Optional[str]
    attempts: int


def fetch_feed(
    url: str,
    *,
    user_agent: str,
    timeout: float,
    max_retries: int,
    backoff_base: float,
    backoff_multiplier: float,
    etag: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> FetchResult:
    """Fetch a single feed URL.

    Retries on timeout, connection error, 429, and 5xx with exponential
    backoff. Does not retry on other 4xx (terminal client errors). A 304
    response short-circuits with status="not_modified" and no content, since
    the body is byte-identical to whatever was fetched last time.
    """
    headers = {"User-Agent": user_agent}
    if etag:
        headers["If-None-Match"] = etag

    result = http_get_with_retry(
        url,
        headers=headers,
        timeout=timeout,
        max_retries=max_retries,
        backoff_base=backoff_base,
        backoff_multiplier=backoff_multiplier,
        session=session,
    )

    return FetchResult(
        url=result.url,
        status=result.status,
        content=result.content,
        etag=result.headers.get("ETag") if result.status == "ok" else etag,
        fetched_at=result.fetched_at,
        http_status=result.http_status,
        error=result.error,
        attempts=result.attempts,
    )
