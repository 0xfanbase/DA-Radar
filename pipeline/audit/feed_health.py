"""Feed coverage/health check: per feed, when did the watcher last see a
new item -- and, as of P8's data/<jid>/watch_status.json substrate (written
by pipeline/watcher/run.py every watcher run), is the feed even reachable
and parsing correctly at all?

Pure code, no AI, no live fetch of its own (link-rot already re-checks
live URLs). Before watch_status.json existed, this module could only ever
answer "no new item in N days" and could not mechanically tell "the
regulator genuinely published nothing" apart from "the feed silently
broke" -- a feed whose fetch started 404ing, or whose listing-page
selector/sitemap url_pattern/JSON items_path stopped matching after a site
redesign, looked identical to a feed that was simply quiet: zero new items
either way. watch_status.json closes that gap, because by the mechanism
designs in pipeline/watcher/mechanisms/, a genuinely quiet source can never
produce a non-"ok" status -- a healthy quiet day is "matched N>=1 elements/
locs/results, all already known to the ledger", which is status="ok" with
0 new items after the ledger diff, not an error of any kind.

check_feed_coverage now emits three MUTUALLY EXCLUSIVE per-feed event
types -- a feed appears under at most one, so a broken feed is never
double-reported as also "silent":

  - feed_structure_error: the fetch succeeded but the configured
    selector/url_pattern/items_path matched nothing (or matched but
    yielded nothing usable) -- "the page got redesigned" is mechanically
    distinguishable from "nothing new today" here.
  - feed_fetch_failure: the fetch itself is failing (network/URL problem),
    or the fetched content won't even parse as the mechanism's expected
    format -- distinct from a structure error because the remediation
    differs (network/URL fix vs. config-selector fix).
  - feed_silence: the original check, unchanged in logic, but now gated on
    the feed's watch_status being "ok" (or absent entirely, which is the
    pre-P8/watch_status=None call path -- preserved for backward
    compatibility with ledgers that predate this substrate).

A feed with a non-"ok", non-structure/fetch-failure status (currently only
"config_error", from a feed entry naming an unrecognized "mechanism") is
deliberately reported under none of the three: it is not silently
mislabeled a false "quiet" feed, but it also doesn't fit either broken
diagnosis category -- run.py's own printed FAIL line is the actionable
surface for a config typo, which is normally caught the same day it's
introduced.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

DEFAULT_FEED_SILENCE_THRESHOLD_DAYS = 30
DEFAULT_STRUCTURE_ERROR_MIN_DAYS = 1
DEFAULT_FETCH_FAILURE_MIN_DAYS = 3

_FETCH_FAILURE_STATUSES = {"fetch_error", "parse_error"}


def _date_only(value: str) -> date:
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def check_feed_coverage(
    ledger: dict,
    *,
    today: date,
    watch_status: Optional[dict] = None,
    silence_threshold_days: int = DEFAULT_FEED_SILENCE_THRESHOLD_DAYS,
    structure_error_min_days: int = DEFAULT_STRUCTURE_ERROR_MIN_DAYS,
    fetch_failure_min_days: int = DEFAULT_FETCH_FAILURE_MIN_DAYS,
) -> list:
    last_seen_by_feed: dict = {}
    for item in ledger.get("items", {}).values():
        key = (item["source_id"], item["feed_id"])
        first_seen = _date_only(item["first_seen"])
        if key not in last_seen_by_feed or first_seen > last_seen_by_feed[key]:
            last_seen_by_feed[key] = first_seen

    watch_feeds = (watch_status or {}).get("feeds", {}) or {}

    # The feed universe is the UNION of "feeds the ledger has ever seen an
    # item from" and "feeds watch_status.json knows about" -- a feed whose
    # selector/pattern/path has been broken since its very first run would
    # never contribute a ledger item at all, so relying on the ledger alone
    # would make exactly the "broken since day one" case this check exists
    # to catch invisible.
    all_keys = set(last_seen_by_feed.keys())
    for feed_id, entry in watch_feeds.items():
        all_keys.add((entry.get("source_id"), feed_id))

    events = []
    for source_id, feed_id in sorted(all_keys, key=lambda k: (k[0] or "", k[1] or "")):
        entry = watch_feeds.get(feed_id)
        status = entry.get("status") if entry else None
        last_seen = last_seen_by_feed.get((source_id, feed_id))

        if status == "structure_error":
            days_broken = (today - _date_only(entry["status_since"])).days
            if days_broken >= structure_error_min_days:
                mechanism = entry.get("mechanism", "unknown")
                last_error = entry.get("last_error") or "no error detail recorded"
                events.append(
                    {
                        "event_type": "feed_structure_error",
                        "summary": (
                            f"{source_id}/{feed_id} ({mechanism}): {last_error} -- broken for "
                            f"{days_broken} day(s); listing page/sitemap/API structure likely "
                            "changed -- the feed is NOT merely quiet."
                        ),
                        "details": {
                            "source_id": source_id,
                            "feed_id": feed_id,
                            "mechanism": mechanism,
                            "status_since": entry["status_since"],
                            "days_broken": days_broken,
                            "last_error": entry.get("last_error"),
                        },
                        "related_ids": [f"{source_id}/{feed_id}"],
                    }
                )
            continue

        if status in _FETCH_FAILURE_STATUSES:
            days_broken = (today - _date_only(entry["status_since"])).days
            if days_broken >= fetch_failure_min_days:
                mechanism = entry.get("mechanism", "unknown")
                last_error = entry.get("last_error") or "no error detail recorded"
                events.append(
                    {
                        "event_type": "feed_fetch_failure",
                        "summary": (
                            f"{source_id}/{feed_id} ({mechanism}): {status} for {days_broken} "
                            f"day(s) -- {last_error} -- a network/URL problem, not a config-"
                            "selector problem."
                        ),
                        "details": {
                            "source_id": source_id,
                            "feed_id": feed_id,
                            "mechanism": mechanism,
                            "status": status,
                            "status_since": entry["status_since"],
                            "days_broken": days_broken,
                            "last_error": entry.get("last_error"),
                        },
                        "related_ids": [f"{source_id}/{feed_id}"],
                    }
                )
            continue

        if status is not None and status != "ok":
            # e.g. "config_error" -- not one of the three explicit event
            # types, but must never be silently folded into "just quiet"
            # either. See module docstring.
            continue

        # status == "ok", or no watch_status entry at all (pre-P8 ledger /
        # watch_status=None call path) -- the ordinary silence check.
        if last_seen is None:
            # Known to watch_status (status "ok") but has never produced a
            # ledger item -- e.g. a brand new, healthy feed that simply
            # hasn't published yet. Nothing to measure silence against.
            continue
        silence_days = (today - last_seen).days
        if silence_days > silence_threshold_days:
            events.append(
                {
                    "event_type": "feed_silence",
                    "summary": (
                        f"{source_id}/{feed_id} has produced no new item in {silence_days} days "
                        f"(threshold {silence_threshold_days}) -- worth confirming the feed is "
                        f"still reachable, not just quiet."
                    ),
                    "details": {
                        "source_id": source_id,
                        "feed_id": feed_id,
                        "last_seen": last_seen.isoformat(),
                        "silence_days": silence_days,
                        "threshold_days": silence_threshold_days,
                    },
                    "related_ids": [f"{source_id}/{feed_id}"],
                }
            )
    return events
