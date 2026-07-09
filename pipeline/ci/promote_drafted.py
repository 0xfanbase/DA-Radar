"""Promotes ledger items from "queued" to "drafted" once the analyst has
actually written a card file for them.

Deterministic code, not the AI job, owns every ledger mutation -- the
analyst never needs (and is never granted) write access to /data at all;
this runs as a plain-shell step in the analyst job, after the AI job,
before commit.
"""
from __future__ import annotations

import argparse
import os

from pipeline.watcher.clock import utc_now_iso
from pipeline.watcher.ledger import load_ledger, mark_drafted, save_ledger
from pipeline.watcher.queue import derive_queue, save_queue


def promote_drafted_items(ledger: dict, *, cards_dir: str, run_ts: str) -> tuple:
    """For every ledger item still "queued", if content/cards/<item_hash>.json
    now exists, mark it "drafted" with that card_id.

    Returns (new_ledger, promoted_item_hashes).
    """
    promoted = []
    for item_hash, entry in ledger.get("items", {}).items():
        if entry["status"] != "queued":
            continue
        card_path = os.path.join(cards_dir, f"{item_hash}.json")
        if os.path.exists(card_path):
            ledger = mark_drafted(ledger, item_hash, item_hash, run_ts)
            promoted.append(item_hash)
    return ledger, promoted


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Promote ledger items to 'drafted' once a card file exists for them."
    )
    parser.add_argument("--ledger", default="data/ledger.json")
    parser.add_argument("--queue", default="data/queue.json")
    parser.add_argument("--cards-dir", default="content/cards")
    args = parser.parse_args(argv)

    run_ts = utc_now_iso()
    ledger = load_ledger(args.ledger)
    ledger, promoted = promote_drafted_items(ledger, cards_dir=args.cards_dir, run_ts=run_ts)

    save_ledger(args.ledger, ledger)
    save_queue(args.queue, derive_queue(ledger, run_ts))

    print(f"promote_drafted: {len(promoted)} item(s) promoted to drafted.")
    for item_hash in promoted:
        print(f"  {item_hash}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
