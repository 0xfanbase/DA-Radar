"""RSS 2.0 / Atom 1.0 feed parsing into a normalized item shape.

Uses defusedxml rather than stdlib xml.etree.ElementTree directly, as a
deliberate hardening measure against XXE / entity-expansion issues in
fetched, external-source XML (see IMPROVEMENT_BACKLOG.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from xml.etree.ElementTree import ParseError

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring

TITLE_MAX_LEN = 500
SUMMARY_MAX_LEN = 2000

ATOM_NS = "{http://www.w3.org/2005/Atom}"

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_RUN_RE = re.compile(r"\s+")


class FeedParseError(Exception):
    """Raised when a feed's content cannot be parsed as RSS 2.0 or Atom 1.0.

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
    needs_enrichment: bool = False


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


def _parse_iso_date(raw: Optional[str]) -> Optional[str]:
    """Parse an RFC 3339 (Atom) timestamp into the same UTC shape _parse_pubdate
    produces for RSS's RFC 2822 dates."""
    if not raw:
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
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


def _atom_link(entry_el) -> Optional[str]:
    """Atom's <link> is an element with an href attribute, not text content.

    Select the href of the first <link> whose rel is "alternate" or absent
    (Atom's default rel is alternate); fall back to the first <link> with an
    href of any rel.
    """
    fallback: Optional[str] = None
    for link_el in entry_el.findall(f"{ATOM_NS}link"):
        href = link_el.get("href")
        if not href:
            continue
        rel = link_el.get("rel")
        if rel is None or rel == "alternate":
            return href
        if fallback is None:
            fallback = href
    return fallback


def parse_atom(
    xml_bytes: bytes, *, source_id: str, feed_id: str, feed_url: str
) -> list[NormalizedItem]:
    """Parse an Atom 1.0 document into a list of NormalizedItem.

    Raises FeedParseError on anything that isn't a well-formed, safe Atom
    feed with a root <feed> element -- never lets a malformed or malicious
    feed propagate a raw XML exception up to the orchestrator.
    """
    try:
        root = fromstring(xml_bytes)
    except (ParseError, DefusedXmlException) as exc:
        raise FeedParseError(f"{feed_id}: could not parse feed XML: {exc}") from exc

    if root.tag != f"{ATOM_NS}feed":
        raise FeedParseError(f"{feed_id}: root is not an Atom <feed>")

    items: list[NormalizedItem] = []
    for entry_el in root.findall(f"{ATOM_NS}entry"):
        guid = _text_of(entry_el, f"{ATOM_NS}id")
        link = _atom_link(entry_el)

        raw_published = _text_of(entry_el, f"{ATOM_NS}published")
        if raw_published is None:
            raw_published = _text_of(entry_el, f"{ATOM_NS}updated")

        summary_raw = _text_of(entry_el, f"{ATOM_NS}summary")
        if summary_raw is None:
            summary_raw = _text_of(entry_el, f"{ATOM_NS}content")

        items.append(
            NormalizedItem(
                source_id=source_id,
                feed_id=feed_id,
                feed_url=feed_url,
                guid=guid,
                link=link,
                title=_sanitize(_text_of(entry_el, f"{ATOM_NS}title"), TITLE_MAX_LEN),
                summary=_sanitize(summary_raw, SUMMARY_MAX_LEN),
                published_at=_parse_iso_date(raw_published),
                raw_published=raw_published,
            )
        )
    return items
