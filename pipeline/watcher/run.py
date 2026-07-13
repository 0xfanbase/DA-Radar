"""Watcher orchestrator + CLI entrypoint.

    python -m pipeline.watcher.run --jurisdiction hk

    -- or, spelling out the conventional paths --jurisdiction resolves --

    python -m pipeline.watcher.run --config config/jurisdictions/hk.json \\
        --ledger data/hk/ledger.json --queue data/hk/queue.json \\
        --cache-dir data/hk/cache --document-library content/hk/document_library.json

Every regulator/feed/User-Agent string is read from the jurisdiction config
-- nothing in this module hardcodes a jurisdiction-specific value. One
feed's failure (timeout, malformed XML) never aborts the run for the
others; failures are recorded in the run summary.

--jurisdiction is purely a convenience for resolving the conventional
per-jurisdiction paths below; it is never required, and any explicit path
flag (--config, --ledger, --queue, --cache-dir, --document-library) always
overrides the corresponding --jurisdiction-derived default. Passing
neither --jurisdiction nor an explicit flag falls back to this module's
own long-standing bare defaults, unchanged from before the registry-model
pivot -- they no longer point at real content on disk post-pivot, but
removing them would be a breaking change for any caller (test or script)
that relies on argparse's own defaults rather than passing paths.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

import requests

from pipeline.watcher.clock import utc_now_iso
from pipeline.watcher.document_library import derive_document_library, save_document_library
from pipeline.watcher.jsonio import write_if_changed
from pipeline.watcher.ledger import diff_new_items, load_ledger, save_ledger, upsert_items
from pipeline.watcher.mechanisms import DISPATCH
from pipeline.watcher.parse import parse_rss  # noqa: F401 -- kept for run_module.parse_rss (tests/test_run_integration.py)
from pipeline.watcher.queue import derive_queue, save_queue
from pipeline.watcher.relevance import classify_relevance

# Maps a mechanism's MechanismResult.error_kind onto the persisted
# watch_status.json "status" value (see _build_watch_status_doc below).
# "config" is run.py's own error_kind for a feed entry naming a mechanism
# absent from DISPATCH (a config typo) -- not one of MechanismResult's own
# "fetch" | "parse" | "structure" kinds, but it needs a status just the
# same. An unrecognized/missing error_kind falls back to "fetch_error"
# rather than being silently dropped from watch_status.json.
_WATCH_STATUS_BY_ERROR_KIND = {
    "fetch": "fetch_error",
    "parse": "parse_error",
    "structure": "structure_error",
    "config": "config_error",
}


@dataclass
class FeedRunResult:
    feed_id: str
    source_id: str
    url: str
    ok: bool
    items_seen: int = 0
    items_new: int = 0
    error: Optional[str] = None
    mechanism: str = "rss"
    error_kind: Optional[str] = None


@dataclass
class RunSummary:
    feeds_attempted: int = 0
    feeds_ok: int = 0
    feeds_failed: int = 0
    items_seen_total: int = 0
    items_new: int = 0
    ledger_changed: bool = False
    queue_changed: bool = False
    document_library_changed: bool = False
    watch_status_changed: bool = False
    feed_results: list = field(default_factory=list)


def load_jurisdiction(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_etag_cache(cache_path: Optional[str]) -> dict:
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _save_etag_cache(cache_path: Optional[str], cache: dict) -> None:
    if not cache_path:
        return
    directory = os.path.dirname(cache_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, sort_keys=True, indent=2)
        fh.write("\n")


def _load_watch_status(path: Optional[str]) -> dict:
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _watch_status_value(fr: "FeedRunResult") -> str:
    if fr.ok:
        return "ok"
    return _WATCH_STATUS_BY_ERROR_KIND.get(fr.error_kind, "fetch_error")


def _build_watch_status_doc(
    feed_results: list, previous: dict, *, jurisdiction_id: Optional[str], run_ts: str
) -> dict:
    """Builds data/<jid>/watch_status.json's content from this run's
    FeedRunResults, carrying status_since forward from `previous` whenever
    a feed's status is unchanged run-to-run -- transition-keyed fields
    only (status + status_since, no per-run counters), per jsonio.py's
    write_if_changed contract: a stretch of identical daily outcomes
    produces zero git churn.
    """
    previous_feeds = previous.get("feeds", {}) if previous else {}
    feeds: dict = {}
    for fr in feed_results:
        status = _watch_status_value(fr)
        prev_entry = previous_feeds.get(fr.feed_id)
        if prev_entry and prev_entry.get("status") == status:
            status_since = prev_entry.get("status_since", run_ts)
        else:
            status_since = run_ts
        feeds[fr.feed_id] = {
            "source_id": fr.source_id,
            "mechanism": fr.mechanism,
            "status": status,
            "status_since": status_since,
            "last_error": fr.error,
        }
    return {
        "schema_version": 1,
        "jurisdiction_id": jurisdiction_id,
        "generated_at": run_ts,
        "feeds": feeds,
    }


def run(
    config_path: str,
    ledger_path: str,
    queue_path: str,
    cache_path: Optional[str] = None,
    document_library_path: Optional[str] = None,
    watch_status_path: Optional[str] = None,
) -> RunSummary:
    config = load_jurisdiction(config_path)
    run_ts = utc_now_iso()
    ledger = load_ledger(ledger_path, jurisdiction_id=config.get("jurisdiction_id"))
    # An existing ledger file always keeps its own on-disk jurisdiction_id
    # (load_ledger's contract above); this only fills in the field for a
    # pre-registry-pivot ledger that predates it, so a ledger written by an
    # old run still round-trips through save_ledger as schema-valid.
    ledger.setdefault("jurisdiction_id", config.get("jurisdiction_id"))
    etag_cache = _load_etag_cache(cache_path)
    previous_watch_status = _load_watch_status(watch_status_path)

    summary = RunSummary()

    with requests.Session() as session:
        for regulator in config.get("regulators", []):
            source_id = regulator["id"]
            for feed in regulator.get("feeds", []):
                feed_id = feed["id"]
                url = feed["url"]
                # "rss" is the default mechanism -- backward compatible
                # with every pre-P8 feed entry (e.g. hk.json) that has no
                # explicit "mechanism" field.
                mechanism = feed.get("mechanism", "rss")
                summary.feeds_attempted += 1

                discover = DISPATCH.get(mechanism)
                if discover is None:
                    # A config typo (unknown mechanism) is a per-feed
                    # failure, not a run-aborting one -- the run continues
                    # exactly as it does for a fetch/parse failure.
                    summary.feeds_failed += 1
                    summary.feed_results.append(
                        FeedRunResult(
                            feed_id,
                            source_id,
                            url,
                            ok=False,
                            error=f"unknown mechanism {mechanism!r}",
                            mechanism=mechanism,
                            error_kind="config",
                        )
                    )
                    continue

                result = discover(
                    feed,
                    source_id=source_id,
                    user_agent=config["user_agent"],
                    fetch_cfg=config["fetch"],
                    etag=etag_cache.get(feed_id),
                    session=session,
                )

                # Shared tail, identical for every mechanism -- the
                # convergence point is the NormalizedItem list, exactly as
                # the mechanism contract requires.
                if result.status == "error":
                    summary.feeds_failed += 1
                    summary.feed_results.append(
                        FeedRunResult(
                            feed_id,
                            source_id,
                            url,
                            ok=False,
                            error=result.error,
                            mechanism=mechanism,
                            error_kind=result.error_kind,
                        )
                    )
                    continue

                if result.status == "not_modified":
                    summary.feeds_ok += 1
                    summary.feed_results.append(
                        FeedRunResult(
                            feed_id, source_id, url, ok=True, items_seen=0, items_new=0, mechanism=mechanism
                        )
                    )
                    continue

                if result.etag:
                    etag_cache[feed_id] = result.etag

                new_items, _seen_items = diff_new_items(result.items, ledger)
                ledger = upsert_items(ledger, new_items, run_ts)

                summary.feeds_ok += 1
                summary.items_seen_total += len(result.items)
                summary.items_new += len(new_items)
                summary.feed_results.append(
                    FeedRunResult(
                        feed_id,
                        source_id,
                        url,
                        ok=True,
                        items_seen=len(result.items),
                        items_new=len(new_items),
                        mechanism=mechanism,
                    )
                )

    ledger, _classified = classify_relevance(ledger, config.get("relevance_keywords", []), run_ts)

    summary.ledger_changed = save_ledger(ledger_path, ledger)
    queue_doc = derive_queue(ledger, run_ts)
    summary.queue_changed = save_queue(queue_path, queue_doc)

    if document_library_path:
        document_library_doc = derive_document_library(ledger, config, run_ts)
        summary.document_library_changed = save_document_library(
            document_library_path, document_library_doc
        )

    if watch_status_path:
        watch_status_doc = _build_watch_status_doc(
            summary.feed_results,
            previous_watch_status,
            jurisdiction_id=ledger.get("jurisdiction_id"),
            run_ts=run_ts,
        )
        summary.watch_status_changed = write_if_changed(watch_status_path, watch_status_doc)

    _save_etag_cache(cache_path, etag_cache)

    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="HK Digital Asset Radar watcher")
    parser.add_argument(
        "--jurisdiction",
        default=None,
        help=(
            "Jurisdiction id (e.g. 'hk'). Resolves --config, --ledger, --queue, "
            "--cache-dir, and --document-library to their conventional paths under "
            "config/jurisdictions/, data/<id>/, and content/<id>/ -- any of those "
            "flags passed explicitly still overrides its --jurisdiction-derived default."
        ),
    )
    parser.add_argument("--config", default=None)
    parser.add_argument("--ledger", default=None)
    parser.add_argument("--queue", default=None)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--document-library", default=None)
    parser.add_argument(
        "--watch-status",
        default=None,
        help=(
            "Path to write watch_status.json (the per-feed health substrate the "
            "audit reads). Defaults to data/<jurisdiction>/watch_status.json when "
            "--jurisdiction is given, else data/watch_status.json."
        ),
    )
    args = parser.parse_args(argv)

    jid = args.jurisdiction
    config_path = args.config or (f"config/jurisdictions/{jid}.json" if jid else "config/jurisdiction.json")
    ledger_path = args.ledger or (f"data/{jid}/ledger.json" if jid else "data/ledger.json")
    queue_path = args.queue or (f"data/{jid}/queue.json" if jid else "data/queue.json")
    cache_dir = args.cache_dir or (f"data/{jid}/cache" if jid else "data/cache")
    document_library_path = args.document_library or (
        f"content/{jid}/document_library.json" if jid else "content/document_library.json"
    )
    watch_status_path = args.watch_status or (
        f"data/{jid}/watch_status.json" if jid else "data/watch_status.json"
    )

    cache_path = os.path.join(cache_dir, "etags.json") if cache_dir else None

    try:
        summary = run(
            config_path, ledger_path, queue_path, cache_path, document_library_path, watch_status_path
        )
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"watcher: invalid or missing config: {exc}", file=sys.stderr)
        return 1

    print(
        f"feeds attempted={summary.feeds_attempted} ok={summary.feeds_ok} "
        f"failed={summary.feeds_failed} items_seen={summary.items_seen_total} "
        f"items_new={summary.items_new} ledger_changed={summary.ledger_changed} "
        f"queue_changed={summary.queue_changed} "
        f"document_library_changed={summary.document_library_changed} "
        f"watch_status_changed={summary.watch_status_changed}"
    )
    for fr in summary.feed_results:
        if fr.ok:
            status = "OK"
        elif fr.error_kind:
            status = f"FAIL[{fr.error_kind}] ({fr.error})"
        else:
            status = f"FAIL ({fr.error})"
        print(f"  [{fr.source_id}/{fr.feed_id}] {status} seen={fr.items_seen} new={fr.items_new}")

    if summary.feeds_attempted > 0 and summary.feeds_ok == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
