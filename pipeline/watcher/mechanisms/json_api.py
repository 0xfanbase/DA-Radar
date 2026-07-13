"""json_api mechanism: discover new items from a regulator (or
quasi-regulator, e.g. the US Federal Register) JSON REST API, for sources
that publish neither RSS/Atom nor a scrapeable HTML listing/sitemap, but do
expose a structured, keyless, HTTP-cache-friendly JSON endpoint.

Flow: fetch the configured `url` (endpoint + query string -- e.g. the
Federal Register's `conditions[term]`/`per_page` params -- baked into the
one URL, never a separate params object, so the "one URL per feed entry"
invariant that ETag caching and feed_health key on holds exactly as it does
for every other mechanism) via the existing pipeline.watcher.fetch.fetch_feed
(already mechanism-agnostic -- conditional GET, retry/backoff, ETag; a 304
short-circuits exactly as it does for rss/atom/html_diff/sitemap_diff).
Where an API sends no ETag, the header is simply never cached -- no special
-casing here, fetch_feed already treats an absent ETag as "nothing to
cache."

Parse the body as JSON, then walk two dotted paths with the tiny in-house
`_extract` evaluator below (no jsonpath dependency, no wildcards, no
filters -- a real need for more is a P-later decision, not silent scope
creep):

  - `json_api.items_path` against the response root, which must yield a
    `list` (the API's results array -- e.g. Federal Register's `results`).
  - each of `json_api.fields.{id,title,link,summary,published}` against one
    result object at a time.

One page per run -- pagination-following is deliberately out of scope; a
`per_page` sized generously in the URL (50 covers weeks of any regulatory
topic at once-daily polling) plus ledger idempotency means the window only
needs to exceed one day's flow, never the whole result set.

Title/summary run through pipeline.watcher.parse._sanitize with the
standard rss/atom caps -- a fetched API response is exactly as untrusted as
a fetched feed (see CLAUDE.md's "fetched documents are data, not
instructions"). `fields.published` parses via the shared
pipeline.watcher.parse._parse_iso_date (RFC-3339, and date-only
`YYYY-MM-DD` normalizes to `T00:00:00Z` first since Federal Register's
publication_date has no time component), falling back to the RSS-style
RFC-2822 parser for older/differently-shaped APIs; the raw field value
always lands in `raw_published` regardless of whether it parsed.

Identity: `guid` is the configured `fields.id` path (e.g. Federal
Register's `document_number` -- a stable citation id that survives URL
changes, strictly better than keying on the link). If `fields.id` is absent
from the config, or a given result is missing that field, `guid` is simply
None and pipeline.watcher.hashing.identity_key_for_item's existing
link+title fallback covers it -- no special-casing needed here, unlike
html_diff/sitemap_diff which synthesize a URL-based guid themselves because
a listing page/sitemap has no id field to begin with.

Loud failure modes:

  - "parse": the fetched body is not valid JSON at all.
  - "structure": `items_path` is missing from the response, or resolves to
    something that isn't a `list`; OR a non-empty results array yields zero
    usable items (every result missing a resolvable `fields.link`) -- the
    same "redesign is mechanically distinguishable from quiet" discipline
    html_diff/sitemap_diff use.
  - an EMPTY results list is explicitly NOT an error: `status="ok",
    items=0`. A filtered API query legitimately returning zero matches
    today (e.g. no new Federal Register documents matching the configured
    term this week) is a normal, healthy outcome -- unlike an empty sitemap
    or a zero-match CSS selector, which can never legitimately be empty. A
    query that silently stops matching anything forever is still caught by
    the ordinary 30-day feed_silence check downstream, not by this module
    pretending a well-formed empty page is a structural failure.

Per-item field misses OTHER than link degrade gracefully to None/"" --
title, summary, and published are each independently optional so one
malformed result (e.g. a null abstract) can never kill the other 49 good
ones in the same page. A missing `fields.link` result is dropped (and
counted, per the structure-error rule above): an item without a resolvable
link is unusable to the authenticity checker and everything downstream that
cites it.

No per-site logic lives in this module. Every path and field mapping comes
from the feed's own `feed["json_api"]` config object -- this module is as
site-blind as every other mechanism module.
tests/test_jurisdiction_agnostic.py's banned-literal scan walks all of
pipeline/, so this module is already covered with no test edit required.

Dependency: zero new third-party dependencies -- stdlib `json` plus the
shared fetch core.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import requests

from pipeline.watcher.fetch import fetch_feed
from pipeline.watcher.mechanisms.base import (
    MechanismError,
    MechanismParseError,
    MechanismResult,
    MechanismStructureError,
)
from pipeline.watcher.parse import (
    SUMMARY_MAX_LEN,
    TITLE_MAX_LEN,
    NormalizedItem,
    _parse_iso_date,
    _parse_pubdate,
    _sanitize,
)


def _extract(obj: Any, path: Optional[str]) -> Any:
    """Evaluate a tiny dotted path against a JSON-decoded structure.

    Split on ".", dict-key each segment against a dict, integer-index each
    segment against a list (e.g. "a.b.0.c"); any miss (wrong type, missing
    key, out-of-range index, non-digit segment against a list) returns
    None rather than raising -- this is deliberately as forgiving as a
    dict.get() chain, since one malformed result's field miss must never
    abort the rest of the page. No wildcards, no filters, no jsonpath
    dependency -- if a real API someday needs more than plain dotted
    dict/list traversal, that's a P-later decision, not silent scope creep
    here.
    """
    if not path:
        return None
    current = obj
    for segment in path.split("."):
        if isinstance(current, dict):
            if segment not in current:
                return None
            current = current[segment]
        elif isinstance(current, list):
            if not segment.lstrip("-").isdigit():
                return None
            index = int(segment)
            if index < 0 or index >= len(current):
                return None
            current = current[index]
        else:
            return None
    return current


def _parse_published(raw: Any) -> tuple[Optional[str], Optional[str]]:
    """Returns (published_at, raw_published). raw_published is the raw
    field value coerced to str whenever a value was present at all,
    regardless of whether it parsed -- provenance is kept even for an
    unparseable date. published_at prefers the ISO/RFC-3339 parser
    (accepting date-only `YYYY-MM-DD` via a T00:00:00Z pad, which is
    exactly the Federal Register publication_date shape), falling back to
    the RFC-2822 parser used by RSS for older/differently-shaped APIs."""
    if raw is None:
        return None, None
    raw_str = str(raw)
    value = raw_str.strip()
    if not value:
        return None, raw_str

    iso_candidate = value
    if len(iso_candidate) == 10 and iso_candidate[4] == "-" and iso_candidate[7] == "-":
        iso_candidate = f"{iso_candidate}T00:00:00Z"
    published_at = _parse_iso_date(iso_candidate)
    if published_at is None:
        published_at = _parse_pubdate(raw_str)
    return published_at, raw_str


def _parse_results(
    content: bytes,
    *,
    api_url: str,
    cfg: dict,
    source_id: str,
    feed_id: str,
    feed_url: str,
) -> list[NormalizedItem]:
    try:
        payload = json.loads(content)
    except (ValueError, UnicodeDecodeError) as exc:
        raise MechanismParseError(
            f"{feed_id}: could not parse response as JSON ({api_url}): {exc}"
        ) from exc

    items_path = cfg["items_path"]
    results = _extract(payload, items_path)
    if not isinstance(results, list):
        raise MechanismStructureError(
            f"{feed_id}: items_path {items_path!r} did not resolve to a list on {api_url} "
            f"(got {type(results).__name__ if results is not None else 'missing'})"
        )

    if not results:
        # A well-formed, empty results set is a legitimate outcome for a
        # filtered API query (e.g. no new matching documents this week) --
        # never a structure error. See module docstring.
        return []

    fields = cfg.get("fields", {})
    id_path = fields.get("id")
    title_path = fields.get("title")
    link_path = fields.get("link")
    summary_path = fields.get("summary")
    published_path = fields.get("published")

    items: list[NormalizedItem] = []
    for result in results:
        if not isinstance(result, dict):
            # A result that isn't even an object has nothing a dotted path
            # could resolve against -- dropped, not crashed on.
            continue

        link = _extract(result, link_path)
        if not link:
            # An item without a resolvable link is unusable downstream
            # (the authenticity checker, citations, everything that needs
            # a URL) -- dropped, counted against the structure-error check
            # below, never hashed on title alone.
            continue

        guid_raw = _extract(result, id_path)
        title_raw = _extract(result, title_path)
        summary_raw = _extract(result, summary_path)
        published_raw = _extract(result, published_path)
        published_at, raw_published = _parse_published(published_raw)

        items.append(
            NormalizedItem(
                source_id=source_id,
                feed_id=feed_id,
                feed_url=feed_url,
                guid=str(guid_raw) if guid_raw is not None else None,
                link=str(link),
                title=_sanitize(str(title_raw) if title_raw is not None else None, TITLE_MAX_LEN),
                summary=_sanitize(
                    str(summary_raw) if summary_raw is not None else None, SUMMARY_MAX_LEN
                ),
                published_at=published_at,
                raw_published=raw_published,
                needs_enrichment=False,
            )
        )

    if not items:
        raise MechanismStructureError(
            f"{feed_id}: items_path {items_path!r} yielded {len(results)} result(s) on {api_url} "
            "but none had a resolvable fields.link -- the API shape may have changed"
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
    """Discover items from a json_api-mechanism feed entry.

    Reuses fetch_feed exactly as the rss/atom/html_diff/sitemap_diff paths
    do -- conditional GET, retry/backoff, ETag caching (a no-op cache when
    the API sends no ETag at all). Never raises: every failure mode
    (fetch, parse, structure) is caught here and returned as
    MechanismResult(status="error", error_kind=...), matching the
    containment contract pipeline.watcher.run already relies on for
    pipeline.watcher.parse.FeedParseError and every other mechanism's
    discover() -- one feed's failure is recorded, never aborts the run.
    """
    feed_id = feed["id"]
    url = feed["url"]
    cfg = feed.get("json_api", {})

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
        items = _parse_results(
            fetch_result.content,
            api_url=url,
            cfg=cfg,
            source_id=source_id,
            feed_id=feed_id,
            feed_url=url,
        )
    except MechanismError as exc:
        return MechanismResult(status="error", error=str(exc), error_kind=exc.error_kind)

    return MechanismResult(status="ok", items=items, etag=fetch_result.etag)
