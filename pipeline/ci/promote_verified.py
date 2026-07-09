"""Promotes ledger items from "drafted" to "verified" then "published"
once the verifier pass and the non-bypassable gate have both run.

Deterministic code, not the AI job, owns every ledger mutation. Combines
verified->published into one step since this pipeline has no held-for-
manual-review state -- per the spec's locked "fully auto-publish with
disclaimers" decision, a card is published the moment it clears the
verifier + gate, in the same run.

Promotes every currently-"drafted" item (not a specific list): the
verifier always runs immediately after the analyst in the same workflow
run, so there is no scenario in this design where a "drafted" item should
linger across separate runs.
"""
from __future__ import annotations

import argparse

from pipeline.watcher.clock import utc_now_iso
from pipeline.watcher.ledger import load_ledger, mark_published, mark_verified, save_ledger
from pipeline.watcher.queue import derive_queue, save_queue


def promote_verified_items(ledger: dict, run_ts: str) -> tuple:
    """Returns (new_ledger, promoted_item_hashes)."""
    promoted = []
    for item_hash, entry in ledger.get("items", {}).items():
        if entry["status"] == "drafted":
            ledger = mark_verified(ledger, item_hash, run_ts)
            ledger = mark_published(ledger, item_hash, run_ts)
            promoted.append(item_hash)
    return ledger, promoted


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Promote 'drafted' ledger items to 'verified' then 'published'."
    )
    parser.add_argument("--ledger", default="data/ledger.json")
    parser.add_argument("--queue", default="data/queue.json")
    args = parser.parse_args(argv)

    run_ts = utc_now_iso()
    ledger = load_ledger(args.ledger)
    ledger, promoted = promote_verified_items(ledger, run_ts)

    save_ledger(args.ledger, ledger)
    save_queue(args.queue, derive_queue(ledger, run_ts))

    print(f"promote_verified: {len(promoted)} item(s) promoted to published.")
    for item_hash in promoted:
        print(f"  {item_hash}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
