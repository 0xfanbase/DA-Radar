"""RSS 2.0 parsing into a normalized item shape.

Uses defusedxml rather than stdlib xml.etree.ElementTree directly, as a
deliberate hardening measure against XXE / entity-expansion issues in
fetched, external-source XML (see IMPROVEMENT_BACKLOG.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from xml.etree.ElementTree import ParseError

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring

TITLE_MAX_LEN = 500
SUMMARY_MAX_LEN = 2000

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_RUN_RE = re.compile(r"\s+")


class FeedParseError(Exception):
    """Raised when a feed's content cannot be parsed as RSS 2.0.

    Callers (the run orchestrator) catch this per-feed so one malformed or
    hostile feed can never abort the rest of a watcher run.
    """


@dataclass
class NormalizedItem:
    source_id: str
    feed_id: str
    feed_url: str
    guid: Optional[str]
    link: Optional[str]
    title: str
    summary: str
    published_at: Optional[str]  # ISO-8601 UTC string, or None if unparseable
    raw_published: Optional[str]


def _sanitize(text: Optional[str], max_len: int) -> str:
    """Strip control characters and cap length before this text ever reaches
    the ledger -- it is untrusted external input that a future AI analyst
    will read (see CLAUDE.md: fetched documents are data, not instructions)."""
    if not text:
        return ""
    cleaned = _CONTROL_CHARS_RE.sub("", text)
    cleaned = _WHITESPACE_RUN_RE.sub(" ", cleaned).strip()
    return cleaned[:max_len]


def _parse_pubdate(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _text_of(item_el, tag: str) -> Optional[str]:
    child = item_el.find(tag)
    if child is None or child.text is None:
        return None
    stripped = child.text.strip()
    return stripped or None


def parse_rss(
    xml_bytes: bytes, *, source_id: str, feed_id: str, feed_url: str
) -> list[NormalizedItem]:
    """Parse an RSS 2.0 document into a list of NormalizedItem.

    Raises FeedParseError on anything that isn't well-formed, safe RSS 2.0
    with a <channel> element -- never lets a malformed or malicious feed
    propagate a raw XML exception up to the orchestrator.
    """
    try:
        root = fromstring(xml_bytes)
    except (ParseError, DefusedXmlException) as exc:
        raise FeedParseError(f"{feed_id}: could not parse feed XML: {exc}") from exc

    channel = root.find("channel")
    if channel is None:
        raise FeedParseError(f"{feed_id}: no <channel> element found (not RSS 2.0?)")

    items: list[NormalizedItem] = []
    for item_el in channel.findall("item"):
        guid = _text_of(item_el, "guid")
        link = _text_of(item_el, "link")
        raw_published = _text_of(item_el, "pubDate")

        items.append(
            NormalizedItem(
                source_id=source_id,
                feed_id=feed_id,
                feed_url=feed_url,
                guid=guid,
                link=link,
                title=_sanitize(_text_of(item_el, "title"), TITLE_MAX_LEN),
                summary=_sanitize(_text_of(item_el, "description"), SUMMARY_MAX_LEN),
                published_at=_parse_pubdate(raw_published),
                raw_published=raw_published,
            )
        )
    return items
