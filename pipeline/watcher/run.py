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
from pipeline.watcher.fetch import fetch_feed
from pipeline.watcher.ledger import diff_new_items, load_ledger, save_ledger, upsert_items
from pipeline.watcher.parse import FeedParseError, parse_rss
from pipeline.watcher.queue import derive_queue, save_queue
from pipeline.watcher.relevance import classify_relevance


@dataclass
class FeedRunResult:
    feed_id: str
    source_id: str
    url: str
    ok: bool
    items_seen: int = 0
    items_new: int = 0
    error: Optional[str] = None


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


def run(
    config_path: str,
    ledger_path: str,
    queue_path: str,
    cache_path: Optional[str] = None,
    document_library_path: Optional[str] = None,
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

    summary = RunSummary()

    with requests.Session() as session:
        for regulator in config.get("regulators", []):
            source_id = regulator["id"]
            for feed in regulator.get("feeds", []):
                feed_id = feed["id"]
                url = feed["url"]
                summary.feeds_attempted += 1

                fetch_result = fetch_feed(
                    url,
                    user_agent=config["user_agent"],
                    timeout=config["fetch"]["timeout_seconds"],
                    max_retries=config["fetch"]["max_retries"],
                    backoff_base=config["fetch"]["backoff_base_seconds"],
                    backoff_multiplier=config["fetch"]["backoff_multiplier"],
                    etag=etag_cache.get(feed_id),
                    session=session,
                )

                if fetch_result.status == "error":
                    summary.feeds_failed += 1
                    summary.feed_results.append(
                        FeedRunResult(feed_id, source_id, url, ok=False, error=fetch_result.error)
                    )
                    continue

                if fetch_result.status == "not_modified":
                    summary.feeds_ok += 1
                    summary.feed_results.append(
                        FeedRunResult(feed_id, source_id, url, ok=True, items_seen=0, items_new=0)
                    )
                    continue

                if fetch_result.etag:
                    etag_cache[feed_id] = fetch_result.etag

                try:
                    items = parse_rss(
                        fetch_result.content, source_id=source_id, feed_id=feed_id, feed_url=url
                    )
                except FeedParseError as exc:
                    summary.feeds_failed += 1
                    summary.feed_results.append(
                        FeedRunResult(feed_id, source_id, url, ok=False, error=str(exc))
                    )
                    continue

                new_items, _seen_items = diff_new_items(items, ledger)
                ledger = upsert_items(ledger, new_items, run_ts)

                summary.feeds_ok += 1
                summary.items_seen_total += len(items)
                summary.items_new += len(new_items)
                summary.feed_results.append(
                    FeedRunResult(
                        feed_id, source_id, url, ok=True, items_seen=len(items), items_new=len(new_items)
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
    args = parser.parse_args(argv)

    jid = args.jurisdiction
    config_path = args.config or (f"config/jurisdictions/{jid}.json" if jid else "config/jurisdiction.json")
    ledger_path = args.ledger or (f"data/{jid}/ledger.json" if jid else "data/ledger.json")
    queue_path = args.queue or (f"data/{jid}/queue.json" if jid else "data/queue.json")
    cache_dir = args.cache_dir or (f"data/{jid}/cache" if jid else "data/cache")
    document_library_path = args.document_library or (
        f"content/{jid}/document_library.json" if jid else "content/document_library.json"
    )

    cache_path = os.path.join(cache_dir, "etags.json") if cache_dir else None

    try:
        summary = run(config_path, ledger_path, queue_path, cache_path, document_library_path)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"watcher: invalid or missing config: {exc}", file=sys.stderr)
        return 1

    print(
        f"feeds attempted={summary.feeds_attempted} ok={summary.feeds_ok} "
        f"failed={summary.feeds_failed} items_seen={summary.items_seen_total} "
        f"items_new={summary.items_new} ledger_changed={summary.ledger_changed} "
        f"queue_changed={summary.queue_changed} "
        f"document_library_changed={summary.document_library_changed}"
    )
    for fr in summary.feed_results:
        status = "OK" if fr.ok else f"FAIL ({fr.error})"
        print(f"  [{fr.source_id}/{fr.feed_id}] {status} seen={fr.items_seen} new={fr.items_new}")

    if summary.feeds_attempted > 0 and summary.feeds_ok == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
