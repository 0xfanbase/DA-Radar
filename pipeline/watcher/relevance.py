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

    return {
        "schema_version": SCHEMA_VERSION,
        "jurisdiction_id": ledger.get("jurisdiction_id"),
        "generated_at": run_ts,
        "items": items,
    }, changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify (or re-run classification for) ledger items lacking a "
            "'relevant' field, then re-derive the queue. Ordinary watcher runs "
            "already do this automatically; this CLI exists for one-off "
            "backfills over a ledger that predates this field."
        )
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

    with open(config_path, "r", encoding="utf-8") as fh:
        jurisdiction_config = json.load(fh)

    run_ts = utc_now_iso()
    ledger = load_ledger(ledger_path, jurisdiction_id=jurisdiction_config.get("jurisdiction_id"))
    ledger.setdefault("jurisdiction_id", jurisdiction_config.get("jurisdiction_id"))
    ledger, changed = classify_relevance(ledger, jurisdiction_config.get("relevance_keywords", []), run_ts)

    save_ledger(ledger_path, ledger)
    save_queue(queue_path, derive_queue(ledger, run_ts))

    print(f"relevance: {len(changed)} item(s) newly classified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
