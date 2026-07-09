"""Watcher orchestrator + CLI entrypoint.

    python -m pipeline.watcher.run --config config/jurisdiction.json \\
        --ledger data/ledger.json --queue data/queue.json --cache-dir data/cache

Every regulator/feed/User-Agent string is read from the jurisdiction config
-- nothing in this module hardcodes a jurisdiction-specific value. One
feed's failure (timeout, malformed XML) never aborts the run for the
others; failures are recorded in the run summary.
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
) -> RunSummary:
    config = load_jurisdiction(config_path)
    run_ts = utc_now_iso()
    ledger = load_ledger(ledger_path)
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
    _save_etag_cache(cache_path, etag_cache)

    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="HK Digital Asset Radar watcher")
    parser.add_argument("--config", default="config/jurisdiction.json")
    parser.add_argument("--ledger", default="data/ledger.json")
    parser.add_argument("--queue", default="data/queue.json")
    parser.add_argument("--cache-dir", default="data/cache")
    args = parser.parse_args(argv)

    cache_path = os.path.join(args.cache_dir, "etags.json") if args.cache_dir else None

    try:
        summary = run(args.config, args.ledger, args.queue, cache_path)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"watcher: invalid or missing config: {exc}", file=sys.stderr)
        return 1

    print(
        f"feeds attempted={summary.feeds_attempted} ok={summary.feeds_ok} "
        f"failed={summary.feeds_failed} items_seen={summary.items_seen_total} "
        f"items_new={summary.items_new} ledger_changed={summary.ledger_changed} "
        f"queue_changed={summary.queue_changed}"
    )
    for fr in summary.feed_results:
        status = "OK" if fr.ok else f"FAIL ({fr.error})"
        print(f"  [{fr.source_id}/{fr.feed_id}] {status} seen={fr.items_seen} new={fr.items_new}")

    if summary.feeds_attempted > 0 and summary.feeds_ok == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
