"""Seed the ledger with known historical items that predate live watcher
coverage (Phase 3 seed content: headline events, document-library backfill).

Reuses the exact same NormalizedItem -> diff_new_items -> upsert_items path
the live watcher uses (pipeline/watcher/ledger.py), so a backfilled item is
indistinguishable from a live-observed one once queued -- same idempotency
guarantee (re-running with the same descriptors adds nothing), same
lifecycle, same downstream analyst/verifier handling.
"""
from __future__ import annotations

import argparse
import json

from pipeline.watcher.clock import utc_now_iso
from pipeline.watcher.ledger import diff_new_items, load_ledger, save_ledger, upsert_items
from pipeline.watcher.parse import NormalizedItem
from pipeline.watcher.queue import derive_queue, save_queue
from pipeline.watcher.relevance import classify_relevance


def seed_items_from_descriptors(ledger: dict, descriptors: list, run_ts: str) -> tuple:
    """descriptors: list of dicts with source_id, feed_id, title, and
    optionally link, summary, published_at, raw_published, guid, feed_url.

    Returns (new_ledger, added_item_hashes). A descriptor whose computed
    item_hash already exists in the ledger is silently skipped -- the same
    idempotency guarantee a live watcher re-run gives.
    """
    items = [
        NormalizedItem(
            source_id=d["source_id"],
            feed_id=d["feed_id"],
            feed_url=d.get("feed_url", ""),
            guid=d.get("guid"),
            link=d.get("link"),
            title=d["title"],
            summary=d.get("summary", ""),
            published_at=d.get("published_at"),
            raw_published=d.get("raw_published"),
        )
        for d in descriptors
    ]
    known_hashes = set(ledger.get("items", {}).keys())
    new_items, _seen = diff_new_items(items, ledger)
    new_ledger = upsert_items(ledger, new_items, run_ts)
    added = [h for h in new_ledger["items"] if h not in known_hashes]
    return new_ledger, added


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed the ledger with known historical items (Phase 3 backfill)."
    )
    parser.add_argument(
        "--descriptors", required=True, help="Path to a JSON file: a list of item descriptors."
    )
    parser.add_argument(
        "--jurisdiction",
        default=None,
        help=(
            "Jurisdiction id (e.g. 'hk'). Resolves --ledger, --queue, and --config to "
            "their conventional paths; any of those flags passed explicitly still "
            "overrides its --jurisdiction-derived default."
        ),
    )
    parser.add_argument("--ledger", default=None)
    parser.add_argument("--queue", default=None)
    parser.add_argument("--config", default=None)
    args = parser.parse_args(argv)

    jid = args.jurisdiction
    ledger_path = args.ledger or (f"data/{jid}/ledger.json" if jid else "data/ledger.json")
    queue_path = args.queue or (f"data/{jid}/queue.json" if jid else "data/queue.json")
    config_path = args.config or (f"config/jurisdictions/{jid}.json" if jid else "config/jurisdiction.json")

    with open(args.descriptors, "r", encoding="utf-8") as fh:
        descriptors = json.load(fh)
    with open(config_path, "r", encoding="utf-8") as fh:
        jurisdiction_config = json.load(fh)

    run_ts = utc_now_iso()
    ledger = load_ledger(ledger_path, jurisdiction_id=jurisdiction_config.get("jurisdiction_id"))
    ledger.setdefault("jurisdiction_id", jurisdiction_config.get("jurisdiction_id"))
    ledger, added = seed_items_from_descriptors(ledger, descriptors, run_ts)
    ledger, _classified = classify_relevance(
        ledger, jurisdiction_config.get("relevance_keywords", []), run_ts
    )

    save_ledger(ledger_path, ledger)
    save_queue(queue_path, derive_queue(ledger, run_ts))

    print(f"seed_backfill: {len(added)} new item(s) added as queued.")
    for item_hash in added:
        print(f"  {item_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
