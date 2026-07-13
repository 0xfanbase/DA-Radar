"""sitemap_diff mechanism: discover new items from a regulator's XML
sitemap, for sources that publish a canonical sitemap.xml (or a sitemap
index fanning out to child sitemaps) but no RSS/Atom feed and no
scrapeable listing page markup stable enough for html_diff.

Flow: fetch the configured sitemap URL via the existing
pipeline.watcher.fetch.fetch_feed (already mechanism-agnostic --
conditional GET, retry/backoff, ETag; a 304 short-circuits exactly as it
does for rss/atom/html_diff -- sitemaps are the case where conditional GET
pays off most, since a whole-site sitemap can be large and is often
unchanged run to run). Parse the root with defusedxml exactly as
pipeline/watcher/parse.py parses RSS/Atom -- a fetched sitemap is exactly
as untrusted as a fetched feed (see CLAUDE.md's "fetched documents are
data, not instructions"):

  - <urlset> root: collect every <url><loc> (with its sibling <lastmod>,
    kept for provenance only -- see below).
  - <sitemapindex> root: collect <sitemap><loc> child entries, optionally
    filtered by the configured index_pattern (default: all), capped at
    max_child_sitemaps (default 5) -- exceeding the cap AFTER filtering is
    a structure error, never a silent truncation, so a config that fans
    out wider than expected is caught rather than quietly under-covered.
    Each followed child is fetched with the same fetch_feed discipline
    (no per-child ETag persistence in this signature -- only the top-level
    feed URL's ETag is cached by the caller across runs) and must itself
    be a <urlset> (a nested sitemapindex is not supported; that shape
    would need its own config knob, not a silent recursive-fetch decision
    made here).
  - anything else: a structure error -- the root isn't sitemap XML at all.

Every collected <loc> (whether from a direct <urlset> or aggregated across
followed children) is filtered through the required url_pattern regex,
canonicalized with pipeline.watcher.mechanisms.urlnorm.canonicalize (using
the top-level sitemap URL as the urljoin base -- sitemap <loc> entries are
normally already absolute, so this only matters for a pathologically
relative one), and de-duplicated by canonical URL (two sitemap files can
legitimately list the same page). One NormalizedItem is emitted per
surviving URL, with guid=link=<canonical URL> so identity is URL-alone --
same rationale as html_diff: a sitemap has no independent guid, and this
also gives URL-stable identity through the existing ledger/hashing chain
with zero hashing.py changes (see hashing.identity_key_for_item).

A sitemap gives a URL and nothing else trustworthy:

  - title = "" and summary = "" always, needs_enrichment = True always.
    This is the explicit "analyst must fetch-and-derive" placeholder: an
    empty title is never slug-humanized or guessed at here.
  - published_at = None always. A sibling <lastmod>, when present, is
    carried into raw_published for provenance only -- lastmod is a
    page-modification timestamp with no publication-date guarantee, and
    promoting it to published_at would fabricate a date on what may be a
    static Document Library page. The analyst runbook supplies the true
    date from the fetched document itself.

Loud failure modes -- three distinct conditions, all mapped onto
MechanismResult(status="error", error_kind="structure"), because each one
means "the sitemap doesn't look like what this feed was configured to
expect" rather than "nothing new today":

  (a) the sitemap (after following any child sitemaps) parses fine but
      yields zero <loc> entries in total -- a real sitemap is never
      legitimately empty.
  (b) url_pattern matches zero of a non-empty loc set -- url_pattern is
      chosen against a site section that always has history, so zero
      matches means the URL scheme changed out from under the config, not
      that nothing is relevant today. This is deliberately the same
      "redesign is mechanically distinguishable from quiet" discipline
      html_diff's item_selector-matched-zero case uses.
  (c) the number of URLs surviving url_pattern (after canonicalization and
      de-duplication) exceeds max_new_per_run (default 50) -- a
      mis-scoped pattern or a mass URL-scheme migration would otherwise
      flood the queue with hundreds of "new" items that are really
      renames. This is a per-run volume cap on this mechanism's own
      output, independent of ledger state (this module has no ledger
      access, by design -- see discover()'s signature, which is
      deliberately identical to html_diff.discover's), on the premise
      that a feed's url_pattern is meant to be scoped narrowly enough
      that a healthy run's matched-and-deduplicated count stays well
      under the cap; tripping it is a signal for a human/improve-loop to
      narrow the pattern, not something this module can resolve alone.

Dependency note: no new third-party dependency -- defusedxml is already a
dependency of pipeline/watcher/parse.py.

No per-site logic lives in this module. Every URL, pattern, and cap comes
from the feed's own feed["sitemap_diff"] config object -- this module is
as site-blind as pipeline.watcher.parse.parse_rss and
pipeline.watcher.mechanisms.html_diff.discover are feed-blind.
tests/test_jurisdiction_agnostic.py's banned-literal scan walks all of
pipeline/, so this module is already covered with no test edit required.
"""
from __future__ import annotations

import re
from typing import Optional
from xml.etree.ElementTree import Element, ParseError

import requests
from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring

from pipeline.watcher.fetch import fetch_feed
from pipeline.watcher.mechanisms.base import (
    MechanismError,
    MechanismFetchError,
    MechanismParseError,
    MechanismResult,
    MechanismStructureError,
)
from pipeline.watcher.mechanisms.urlnorm import canonicalize
from pipeline.watcher.parse import NormalizedItem

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

DEFAULT_MAX_NEW_PER_RUN = 50
DEFAULT_MAX_CHILD_SITEMAPS = 5


def _text_of(el: Element, tag: str) -> Optional[str]:
    child = el.find(tag)
    if child is None or child.text is None:
        return None
    stripped = child.text.strip()
    return stripped or None


def _parse_sitemap_xml(content: bytes, *, feed_id: str, sitemap_url: str) -> Element:
    try:
        return fromstring(content)
    except (ParseError, DefusedXmlException) as exc:
        raise MechanismParseError(
            f"{feed_id}: could not parse sitemap XML ({sitemap_url}): {exc}"
        ) from exc


def _collect_urlset_locs(root: Element) -> list[tuple[str, Optional[str]]]:
    """Return (loc, lastmod) pairs from a <urlset> root, dropping any
    <url> element whose <loc> is missing or blank."""
    out: list[tuple[str, Optional[str]]] = []
    for url_el in root.findall(f"{SITEMAP_NS}url"):
        loc = _text_of(url_el, f"{SITEMAP_NS}loc")
        if not loc:
            continue
        lastmod = _text_of(url_el, f"{SITEMAP_NS}lastmod")
        out.append((loc, lastmod))
    return out


def _collect_sitemapindex_locs(root: Element) -> list[str]:
    out: list[str] = []
    for sitemap_el in root.findall(f"{SITEMAP_NS}sitemap"):
        loc = _text_of(sitemap_el, f"{SITEMAP_NS}loc")
        if loc:
            out.append(loc)
    return out


def _fetch_child_sitemap_locs(
    child_url: str,
    *,
    feed_id: str,
    user_agent: str,
    fetch_cfg: dict,
    session: Optional[requests.Session],
) -> list[tuple[str, Optional[str]]]:
    """Fetch one child sitemap named by a sitemapindex entry and return its
    (loc, lastmod) pairs. Raises MechanismError (fetch/parse/structure) on
    any failure -- never returns a partial result silently."""
    fetch_result = fetch_feed(
        child_url,
        user_agent=user_agent,
        timeout=fetch_cfg["timeout_seconds"],
        max_retries=fetch_cfg["max_retries"],
        backoff_base=fetch_cfg["backoff_base_seconds"],
        backoff_multiplier=fetch_cfg["backoff_multiplier"],
        etag=None,
        session=session,
    )
    if fetch_result.status == "error":
        raise MechanismFetchError(
            f"{feed_id}: could not fetch child sitemap {child_url}: {fetch_result.error}"
        )
    if fetch_result.status == "not_modified" or fetch_result.content is None:
        # etag is always None on a child fetch, so a real sitemap server
        # should never 304 here -- treated defensively as "no content",
        # which surfaces as this child contributing zero locs (folded into
        # the overall zero-loc / pattern-miss checks by the caller).
        return []

    child_root = _parse_sitemap_xml(fetch_result.content, feed_id=feed_id, sitemap_url=child_url)
    if child_root.tag != f"{SITEMAP_NS}urlset":
        raise MechanismStructureError(
            f"{feed_id}: child sitemap {child_url} root is {child_root.tag!r}, expected <urlset> "
            "-- nested sitemap indexes are not supported"
        )
    return _collect_urlset_locs(child_root)


def _compile_pattern(pattern: str, *, feed_id: str, label: str) -> "re.Pattern":
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise MechanismStructureError(f"{feed_id}: {label} {pattern!r} is not a valid regex: {exc}") from exc


def _collect_all_locs(
    root: Element,
    *,
    sitemap_url: str,
    cfg: dict,
    feed_id: str,
    user_agent: str,
    fetch_cfg: dict,
    session: Optional[requests.Session],
) -> list[tuple[str, Optional[str]]]:
    if root.tag == f"{SITEMAP_NS}urlset":
        return _collect_urlset_locs(root)

    if root.tag == f"{SITEMAP_NS}sitemapindex":
        max_child_sitemaps = cfg.get("max_child_sitemaps", DEFAULT_MAX_CHILD_SITEMAPS)
        index_pattern_raw = cfg.get("index_pattern")

        child_locs = _collect_sitemapindex_locs(root)
        if index_pattern_raw:
            index_pattern = _compile_pattern(index_pattern_raw, feed_id=feed_id, label="index_pattern")
            child_locs = [loc for loc in child_locs if index_pattern.search(loc)]

        if len(child_locs) > max_child_sitemaps:
            raise MechanismStructureError(
                f"{feed_id}: sitemap index at {sitemap_url} has {len(child_locs)} child sitemap(s) "
                f"matching the configured index_pattern, exceeding max_child_sitemaps="
                f"{max_child_sitemaps} -- the site's sitemap index fanned out wider than "
                "configured, or index_pattern needs narrowing"
            )

        all_locs: list[tuple[str, Optional[str]]] = []
        for child_url in child_locs:
            all_locs.extend(
                _fetch_child_sitemap_locs(
                    child_url,
                    feed_id=feed_id,
                    user_agent=user_agent,
                    fetch_cfg=fetch_cfg,
                    session=session,
                )
            )
        return all_locs

    raise MechanismStructureError(
        f"{feed_id}: sitemap root at {sitemap_url} is {root.tag!r}, expected <urlset> or "
        "<sitemapindex>"
    )


def _discover_items(
    content: bytes,
    *,
    sitemap_url: str,
    cfg: dict,
    source_id: str,
    feed_id: str,
    user_agent: str,
    fetch_cfg: dict,
    session: Optional[requests.Session],
) -> list[NormalizedItem]:
    url_pattern_raw = cfg["url_pattern"]
    max_new_per_run = cfg.get("max_new_per_run", DEFAULT_MAX_NEW_PER_RUN)

    root = _parse_sitemap_xml(content, feed_id=feed_id, sitemap_url=sitemap_url)
    locs = _collect_all_locs(
        root,
        sitemap_url=sitemap_url,
        cfg=cfg,
        feed_id=feed_id,
        user_agent=user_agent,
        fetch_cfg=fetch_cfg,
        session=session,
    )

    if not locs:
        raise MechanismStructureError(
            f"{feed_id}: sitemap at {sitemap_url} yielded 0 <loc> entries -- a real sitemap is "
            "never legitimately empty"
        )

    url_pattern = _compile_pattern(url_pattern_raw, feed_id=feed_id, label="url_pattern")
    matched = [(loc, lastmod) for loc, lastmod in locs if url_pattern.search(loc)]

    if not matched:
        raise MechanismStructureError(
            f"{feed_id}: url_pattern {url_pattern_raw!r} matched 0 of {len(locs)} <loc> entries at "
            f"{sitemap_url} -- the site's URL scheme may have changed"
        )

    items: list[NormalizedItem] = []
    seen_urls: set[str] = set()
    for loc, lastmod in matched:
        canonical_url = canonicalize(loc, sitemap_url)
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)
        items.append(
            NormalizedItem(
                source_id=source_id,
                feed_id=feed_id,
                feed_url=sitemap_url,
                guid=canonical_url,
                link=canonical_url,
                title="",
                summary="",
                published_at=None,
                raw_published=lastmod,
                needs_enrichment=True,
            )
        )

    if len(items) > max_new_per_run:
        raise MechanismStructureError(
            f"{feed_id}: {len(items)} URL(s) matched url_pattern at {sitemap_url}, exceeding "
            f"max_new_per_run={max_new_per_run} -- a mass URL-scheme migration or an "
            "over-broad url_pattern would otherwise flood the queue with renamed items; "
            "narrow url_pattern or raise the cap deliberately"
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
    """Discover items from a sitemap_diff-mechanism feed entry.

    Reuses fetch_feed exactly as the rss/atom/html_diff paths do --
    conditional GET, retry/backoff, ETag caching. Never raises: every
    failure mode (fetch, parse, structure) is caught here and returned as
    MechanismResult(status="error", error_kind=...), matching the
    containment contract pipeline.watcher.run already relies on for
    pipeline.watcher.parse.FeedParseError and
    pipeline.watcher.mechanisms.html_diff.discover -- one feed's failure is
    recorded, never aborts the run.
    """
    feed_id = feed["id"]
    url = feed["url"]
    cfg = feed.get("sitemap_diff", {})

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
        items = _discover_items(
            fetch_result.content,
            sitemap_url=url,
            cfg=cfg,
            source_id=source_id,
            feed_id=feed_id,
            user_agent=user_agent,
            fetch_cfg=fetch_cfg,
            session=session,
        )
    except MechanismError as exc:
        return MechanismResult(status="error", error=str(exc), error_kind=exc.error_kind)

    return MechanismResult(status="ok", items=items, etag=fetch_result.etag)
