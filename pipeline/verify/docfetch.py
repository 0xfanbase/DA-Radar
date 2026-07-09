"""Document fetching + plain-text extraction, for the analyst/verifier.

Reuses the shared retry/backoff core (pipeline/http.py) rather than
duplicating it. Extracts plain text from HTML (stdlib html.parser -- no
extra dependency for the common case) and PDF (pypdf -- a narrow,
single-purpose dependency; see IMPROVEMENT_BACKLOG.md).

Fetched content is DATA to extract text from, never instructions to
follow (see CLAUDE.md) -- this module only ever returns plain text; it
never executes, evaluates, or interprets anything found in a document.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Optional

import requests
from pypdf import PdfReader

from pipeline.http import http_get_with_retry

_SKIP_TAGS = {"script", "style", "noscript", "head"}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data.strip())

    def get_text(self) -> str:
        return " ".join(self._chunks)


def extract_html_text(html_bytes: bytes) -> str:
    extractor = _HTMLTextExtractor()
    extractor.feed(html_bytes.decode("utf-8", errors="replace"))
    return extractor.get_text()


def extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return " ".join(page.extract_text() or "" for page in reader.pages)


def extract_text(content: bytes, *, content_type: Optional[str] = None, url: Optional[str] = None) -> str:
    """Dispatch to HTML or PDF extraction, preferring Content-Type, then
    the URL's extension, then a raw PDF-magic-bytes sniff."""
    is_pdf = False
    if content_type and "pdf" in content_type.lower():
        is_pdf = True
    elif url and url.lower().split("?")[0].endswith(".pdf"):
        is_pdf = True
    elif content.startswith(b"%PDF-"):
        is_pdf = True

    if is_pdf:
        return extract_pdf_text(content)
    return extract_html_text(content)


@dataclass
class DocumentFetchResult:
    url: str
    status: str  # "ok" | "error"
    text: Optional[str]
    http_status: Optional[int]
    error: Optional[str]
    attempts: int


def fetch_document(
    url: str,
    *,
    user_agent: str,
    timeout: float,
    max_retries: int,
    backoff_base: float,
    backoff_multiplier: float,
    session: Optional[requests.Session] = None,
) -> DocumentFetchResult:
    """Fetch a document (HTML or PDF) and return its extracted plain text."""
    headers = {"User-Agent": user_agent}
    result = http_get_with_retry(
        url,
        headers=headers,
        timeout=timeout,
        max_retries=max_retries,
        backoff_base=backoff_base,
        backoff_multiplier=backoff_multiplier,
        session=session,
    )

    if result.status != "ok":
        return DocumentFetchResult(
            url=url,
            status="error",
            text=None,
            http_status=result.http_status,
            error=result.error,
            attempts=result.attempts,
        )

    try:
        text = extract_text(result.content, content_type=result.headers.get("Content-Type"), url=url)
    except Exception as exc:
        # Untrusted external content (malformed PDF/HTML) must never crash
        # the pipeline -- same per-item error isolation as FeedParseError.
        return DocumentFetchResult(
            url=url,
            status="error",
            text=None,
            http_status=result.http_status,
            error=f"text extraction failed: {exc}",
            attempts=result.attempts,
        )

    return DocumentFetchResult(
        url=url, status="ok", text=text, http_status=result.http_status, error=None, attempts=result.attempts
    )
