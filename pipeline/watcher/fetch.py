"""HTTP fetching for the watcher: retry/backoff and ETag-conditional GET.

Every request carries an explicit timeout (requests has no default) and a
descriptive User-Agent sourced from config/jurisdiction.json -- never
hardcoded here, to keep this module jurisdiction-agnostic.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import requests

from pipeline.watcher.clock import utc_now_iso

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


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
    sess = session or requests.Session()
    headers = {"User-Agent": user_agent}
    if etag:
        headers["If-None-Match"] = etag

    attempts = 0
    last_error: Optional[str] = None

    while attempts < max_retries:
        attempts += 1
        try:
            response = sess.get(url, headers=headers, timeout=timeout)
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = str(exc)
            if attempts < max_retries:
                time.sleep(backoff_base * (backoff_multiplier ** (attempts - 1)))
            continue

        if response.status_code == 304:
            return FetchResult(
                url=url,
                status="not_modified",
                content=None,
                etag=etag,
                fetched_at=utc_now_iso(),
                http_status=304,
                error=None,
                attempts=attempts,
            )

        if response.status_code == 200:
            return FetchResult(
                url=url,
                status="ok",
                content=response.content,
                etag=response.headers.get("ETag"),
                fetched_at=utc_now_iso(),
                http_status=200,
                error=None,
                attempts=attempts,
            )

        if response.status_code in RETRYABLE_STATUS_CODES:
            last_error = f"HTTP {response.status_code}"
            if attempts < max_retries:
                time.sleep(backoff_base * (backoff_multiplier ** (attempts - 1)))
            continue

        # Terminal client error (e.g. 404) -- retrying won't help.
        return FetchResult(
            url=url,
            status="error",
            content=None,
            etag=etag,
            fetched_at=utc_now_iso(),
            http_status=response.status_code,
            error=f"HTTP {response.status_code}",
            attempts=attempts,
        )

    return FetchResult(
        url=url,
        status="error",
        content=None,
        etag=etag,
        fetched_at=utc_now_iso(),
        http_status=None,
        error=last_error or "unknown fetch error",
        attempts=attempts,
    )
