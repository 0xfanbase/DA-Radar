"""Shared HTTP retry/backoff core.

Used by both the RSS watcher (pipeline/watcher/fetch.py) and the document
fetcher (pipeline/verify/docfetch.py) so retry/backoff logic exists in
exactly one place. Every caller must pass an explicit timeout -- requests
has no default, and a hung request would hang a daily or per-item CI job.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import requests

from pipeline.watcher.clock import utc_now_iso

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass
class HttpResult:
    url: str
    status: str  # "ok" | "not_modified" | "error"
    content: Optional[bytes]
    headers: dict
    fetched_at: str
    http_status: Optional[int]
    error: Optional[str]
    attempts: int


def http_get_with_retry(
    url: str,
    *,
    headers: dict,
    timeout: float,
    max_retries: int,
    backoff_base: float,
    backoff_multiplier: float,
    session: Optional[requests.Session] = None,
) -> HttpResult:
    """GET url with retry/backoff on timeout, connection error, 429, and 5xx.

    Does not retry other 4xx (terminal client errors). A 304 is a distinct
    terminal status with no content, for callers sending conditional-GET
    headers.
    """
    sess = session or requests.Session()
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
            return HttpResult(
                url=url,
                status="not_modified",
                content=None,
                headers=dict(response.headers),
                fetched_at=utc_now_iso(),
                http_status=304,
                error=None,
                attempts=attempts,
            )

        if response.status_code == 200:
            return HttpResult(
                url=url,
                status="ok",
                content=response.content,
                headers=dict(response.headers),
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
        return HttpResult(
            url=url,
            status="error",
            content=None,
            headers=dict(response.headers),
            fetched_at=utc_now_iso(),
            http_status=response.status_code,
            error=f"HTTP {response.status_code}",
            attempts=attempts,
        )

    return HttpResult(
        url=url,
        status="error",
        content=None,
        headers={},
        fetched_at=utc_now_iso(),
        http_status=None,
        error=last_error or "unknown fetch error",
        attempts=attempts,
    )
