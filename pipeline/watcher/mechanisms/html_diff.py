"""html_diff mechanism: discover new items from a regulator's HTML listing
page, for sources that publish no machine-readable feed at all.

Flow: fetch the listing page via the existing pipeline.watcher.fetch.
fetch_feed (already mechanism-agnostic -- conditional GET, retry/backoff,
ETag; a 304 short-circuits exactly as it does for rss/atom) -> parse with
BeautifulSoup on the stdlib html.parser backend -> soup.select(the
configured item_selector) -> per matched element, resolve a link, extract
title/summary/date per optional selectors, canonicalize the link
(pipeline.watcher.mechanisms.urlnorm.canonicalize), sanitize text through
pipeline.watcher.parse._sanitize with the same caps rss/atom use, and build
a NormalizedItem with guid=link=<canonical URL> so identity is URL-alone
(see hashing.identity_key_for_item -- a listing page has no independent
guid, and CMS titles get edited post-publication, so keying on link+title
would spawn a duplicate ledger entry on every title touch-up).

Dependency: beautifulsoup4 (pulls in soupsieve, its CSS-selector engine,
as its own transitive dependency), on the stdlib html.parser backend --
deliberately not lxml. This avoids a C-extension dependency, and
html.parser has no XML-entity-expansion (XXE) attack surface at all,
which matters here for the same reason pipeline/watcher/parse.py parses
RSS/Atom with defusedxml rather than stock ElementTree: fetched listing
pages are untrusted external input (see CLAUDE.md's "fetched documents are
data, not instructions").

No per-site logic lives in this module. Every selector, date format, and
base URL comes from the feed's own `feed["html_diff"]` config object --
this module is as site-blind as pipeline.watcher.parse.parse_rss is
feed-blind. tests/test_jurisdiction_agnostic.py's banned-literal scan
walks all of pipeline/, so this module is already covered with no test
edit required.

Loud failure modes -- the point of this module, not an afterthought. Three
distinct conditions map to MechanismResult(status="error", error_kind=...):

  - "fetch": fetch_feed's own HTTP failure. Mapped directly from
    fetch_feed's status=="error" result; never raised as an exception
    here.
  - "parse": the fetched content isn't parseable as HTML at all. Kept for
    symmetry with the other mechanisms -- html.parser is lenient enough
    that this is essentially unreachable in practice, since even garbage
    bytes parse into *some* (empty) soup rather than raising.
  - "structure": item_selector matched zero elements on an HTTP-200 page,
    OR it matched one or more elements but none of them yielded a
    resolvable link. This is what makes "the page got redesigned"
    mechanically distinguishable from "nothing new today": a healthy quiet
    day is "selector matched N >= 1 elements, all N already known to the
    ledger" -> status="ok", 0 new after the ledger diff. A broken selector
    can never masquerade as that, because there is no code path in this
    module that returns an empty items list from a status="ok" result --
    zero usable items is always a raised structure error, by construction.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from pipeline.watcher.fetch import fetch_feed
from pipeline.watcher.mechanisms.base import (
    MechanismError,
    MechanismParseError,
    MechanismResult,
    MechanismStructureError,
)
from pipeline.watcher.mechanisms.urlnorm import canonicalize
from pipeline.watcher.parse import SUMMARY_MAX_LEN, TITLE_MAX_LEN, NormalizedItem, _sanitize


def _resolve_link_element(item_el, link_selector: Optional[str]):
    """Per the html_diff config design's link_selector default: a
    configured relative selector wins; absent that, the item element
    itself if it is an <a>, else its first descendant a[href]."""
    if link_selector:
        return item_el.select_one(link_selector)
    if getattr(item_el, "name", None) == "a" and item_el.has_attr("href"):
        return item_el
    return item_el.select_one("a[href]")


def _text_of(el) -> Optional[str]:
    if el is None:
        return None
    text = el.get_text(strip=True)
    return text or None


def _parse_item_date(raw: Optional[str], date_format: Optional[str]) -> Optional[str]:
    if not raw or not date_format:
        return None
    try:
        dt = datetime.strptime(raw.strip(), date_format)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_listing(
    content: bytes,
    *,
    page_url: str,
    cfg: dict,
    source_id: str,
    feed_id: str,
    feed_url: str,
) -> list[NormalizedItem]:
    try:
        soup = BeautifulSoup(content, "html.parser")
    except Exception as exc:  # pragma: no cover -- html.parser practically never raises
        raise MechanismParseError(f"{feed_id}: could not parse listing page as HTML: {exc}") from exc

    item_selector = cfg["item_selector"]
    try:
        matched = soup.select(item_selector)
    except Exception as exc:
        # An invalid CSS selector is a config-authoring bug, but it must
        # still surface as a loud, per-feed structure error rather than
        # crashing the whole watcher run.
        raise MechanismStructureError(
            f"{feed_id}: item_selector {item_selector!r} is not a valid CSS selector "
            f"(against {page_url}): {exc}"
        ) from exc

    if not matched:
        raise MechanismStructureError(
            f"{feed_id}: item_selector {item_selector!r} matched 0 elements on {page_url} "
            "-- the listing page may have been redesigned"
        )

    base_url = cfg.get("base_url") or feed_url
    link_selector = cfg.get("link_selector")
    title_selector = cfg.get("title_selector")
    summary_selector = cfg.get("summary_selector")
    date_selector = cfg.get("date_selector")
    date_format = cfg.get("date_format")

    items: list[NormalizedItem] = []
    for item_el in matched:
        link_el = _resolve_link_element(item_el, link_selector)
        href = link_el.get("href") if link_el is not None else None
        if not href:
            # A pathological match with no resolvable link is dropped, not
            # hashed on title alone -- counted against `matched` below so a
            # page where every row lost its link still raises structure,
            # never silently reports fewer items.
            continue

        canonical_url = canonicalize(href, base_url)

        if title_selector:
            title_el = item_el.select_one(title_selector)
        else:
            # Config design default: title_selector absent falls back to
            # the resolved link element's own text.
            title_el = link_el
        title_raw = _text_of(title_el)

        summary_raw = _text_of(item_el.select_one(summary_selector)) if summary_selector else None

        raw_date = _text_of(item_el.select_one(date_selector)) if date_selector else None
        published_at = _parse_item_date(raw_date, date_format)

        items.append(
            NormalizedItem(
                source_id=source_id,
                feed_id=feed_id,
                feed_url=feed_url,
                guid=canonical_url,
                link=canonical_url,
                title=_sanitize(title_raw, TITLE_MAX_LEN),
                summary=_sanitize(summary_raw, SUMMARY_MAX_LEN),
                published_at=published_at,
                raw_published=raw_date,
                needs_enrichment=not bool(title_raw),
            )
        )

    if not items:
        raise MechanismStructureError(
            f"{feed_id}: item_selector {item_selector!r} matched {len(matched)} element(s) on "
            f"{page_url} but none yielded a resolvable link -- the listing page may have been "
            "redesigned"
        )

    return items


def discover(
    feed: dict,
    *,
    source_id: str,
    user_agent: str,
    fetch_cfg: dict,
    etag: Optional[str],
    session: Optional[requests.Session] = None,
) -> MechanismResult:
    """Discover items from an html_diff-mechanism feed entry.

    Reuses fetch_feed exactly as the rss/atom path does -- conditional GET,
    retry/backoff, ETag caching -- so html_diff differs from rss/atom only
    in what happens to the response body once fetched, never in fetch
    discipline. Never raises: every failure mode (fetch, parse, structure)
    is caught here and returned as MechanismResult(status="error",
    error_kind=...), matching the containment contract run.py already
    relies on for pipeline.watcher.parse.FeedParseError -- one feed's
    failure is recorded, never aborts the run.
    """
    feed_id = feed["id"]
    url = feed["url"]
    cfg = feed.get("html_diff", {})

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
        items = _parse_listing(
            fetch_result.content,
            page_url=url,
            cfg=cfg,
            source_id=source_id,
            feed_id=feed_id,
            feed_url=url,
        )
    except MechanismError as exc:
        return MechanismResult(status="error", error=str(exc), error_kind=exc.error_kind)

    return MechanismResult(status="ok", items=items, etag=fetch_result.etag)
