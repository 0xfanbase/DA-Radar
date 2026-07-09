"""Deterministic subject-matter relevance classification for watched items.

A regulator's RSS feeds cover its full mandate, not just this project's
subject -- most items on a general regulator feed are unrelated to what
this deployment tracks. Every observed item is still recorded in the
ledger (full watcher history); only relevance-matching items are ever
queued for the analyst. Pure code, no AI or network access -- deterministic
substring matching against a jurisdiction-supplied keyword list, so a
human can read config/jurisdiction.json's relevance_keywords and know
exactly why an item was or wasn't queued. Jurisdiction-portable: this
module holds no literal keywords itself, only the matching logic.
"""
from __future__ import annotations

import argparse
import json

from pipeline.watcher.clock import utc_now_iso
from pipeline.watcher.ledger import SCHEMA_VERSION, load_ledger, save_ledger
from pipeline.watcher.queue import derive_queue, save_queue


def is_relevant(title: str, summary: str, keywords: list) -> bool:
    """Fails open: an empty/missing keyword list means every item is
    relevant, since that is far more likely to be a not-yet-configured
    jurisdiction than an intentional "nothing here is ever relevant."""
    if not keywords:
        return True
    haystack = f"{title} {summary}".lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def classify_relevance(ledger: dict, keywords: list, run_ts: str) -> tuple:
    """Return (new_ledger, newly_classified_item_hashes).

    Computes and stores a "relevant" boolean on every ledger item that
    doesn't have one yet. Idempotent -- an already-classified item is left
    untouched, so this is safe to call on every watcher run (classifying
    only that run's new items) as well as once, as a one-off backfill over
    an existing ledger that predates this field.
    """
    items = dict(ledger.get("items", {}))
    changed = []
    for item_hash, entry in items.items():
        if "relevant" in entry:
            continue
        new_entry = dict(entry)
        new_entry["relevant"] = is_relevant(entry.get("title", ""), entry.get("summary", ""), keywords)
        items[item_hash] = new_entry
        changed.append(item_hash)

    if not changed:
        return ledger, []

    return {"schema_version": SCHEMA_VERSION, "generated_at": run_ts, "items": items}, changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify (or re-run classification for) ledger items lacking a "
            "'relevant' field, then re-derive the queue. Ordinary watcher runs "
            "already do this automatically; this CLI exists for one-off "
            "backfills over a ledger that predates this field."
        )
    )
    parser.add_argument("--ledger", default="data/ledger.json")
    parser.add_argument("--queue", default="data/queue.json")
    parser.add_argument("--config", default="config/jurisdiction.json")
    args = parser.parse_args(argv)

    with open(args.config, "r", encoding="utf-8") as fh:
        jurisdiction_config = json.load(fh)

    run_ts = utc_now_iso()
    ledger = load_ledger(args.ledger)
    ledger, changed = classify_relevance(ledger, jurisdiction_config.get("relevance_keywords", []), run_ts)

    save_ledger(args.ledger, ledger)
    save_queue(args.queue, derive_queue(ledger, run_ts))

    print(f"relevance: {len(changed)} item(s) newly classified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
