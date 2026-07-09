"""Loads and manipulates data/improve_queue.json -- the bounded, human-
curated list of candidate items improve.yml's fortnightly run is allowed
to pick from.

Deliberately not the AI job's own discretion to survey the repo and pick
something worth fixing (per Fable PM directive): a bounded queue is
auditable *before* a run happens, not just reviewable after. The AI job
never edits this file itself -- it has no /data write access at all (see
pipeline/ci/improve_scope.py) -- so every status transition here is
deterministic code owned by the orchestrating workflow, the same pattern
data/ledger.json's transitions already use.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = 1


def load_queue(queue_path: str) -> dict:
    if not os.path.exists(queue_path):
        return {"schema_version": SCHEMA_VERSION, "items": []}
    with open(queue_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_queue(queue_path: str, queue: dict) -> None:
    os.makedirs(os.path.dirname(queue_path) or ".", exist_ok=True)
    with open(queue_path, "w", encoding="utf-8") as fh:
        json.dump(queue, fh, sort_keys=True, indent=2, ensure_ascii=False)
        fh.write("\n")


def pick_next_open_item(queue: dict) -> dict:
    """Returns the oldest status=='open' item (by opened_at, ties broken
    by id), or None if the queue has no open items at all -- the
    zero-cost-when-empty exit, same principle as the analyst's queue."""
    open_items = [item for item in queue.get("items", []) if item.get("status") == "open"]
    if not open_items:
        return None
    return sorted(open_items, key=lambda item: (item["opened_at"], item["id"]))[0]


def mark_item_picked(queue: dict, item_id: str, *, picked_at: str, pr_url: str) -> dict:
    """Returns a NEW queue dict (the input is never mutated) with the given
    item's status set to 'picked' and its picked_at/pr_url recorded."""
    new_items = []
    for item in queue.get("items", []):
        if item.get("id") == item_id:
            new_item = dict(item)
            new_item["status"] = "picked"
            new_item["picked_at"] = picked_at
            new_item["pr_url"] = pr_url
            new_items.append(new_item)
        else:
            new_items.append(item)
    return {**queue, "items": new_items}


def main(argv=None) -> int:
    """The "no run, no cost" quota gate for improve.yml -- same pattern as
    pipeline/ci/queue_check.py for the analyst, a separate cheap job with
    no AI and no secret needed so the expensive AI job can be skipped
    entirely via needs/if, not merely short-circuited after starting."""
    parser = argparse.ArgumentParser(description="Report the next open improve-queue item, if any.")
    parser.add_argument("--queue", default="data/improve_queue.json")
    parser.add_argument(
        "--github-output",
        default=os.environ.get("GITHUB_OUTPUT"),
        help="Path to append 'empty=true|false', 'item_id', 'item_description' to (defaults to $GITHUB_OUTPUT).",
    )
    parser.add_argument(
        "--mark-picked",
        metavar="ITEM_ID",
        help="Instead of picking, mark this item id 'picked' (requires --pr-url) and save the queue.",
    )
    parser.add_argument("--pr-url", help="PR URL to record; required with --mark-picked.")
    args = parser.parse_args(argv)

    if args.mark_picked:
        if not args.pr_url:
            print("improve_queue: --pr-url is required with --mark-picked", file=sys.stderr)
            return 2
        queue = load_queue(args.queue)
        picked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        updated = mark_item_picked(queue, args.mark_picked, picked_at=picked_at, pr_url=args.pr_url)
        save_queue(args.queue, updated)
        print(f"improve_queue: marked {args.mark_picked!r} picked -- {args.pr_url}")
        return 0

    queue = load_queue(args.queue)
    item = pick_next_open_item(queue)

    if item is None:
        print("improve_queue: no open items -- nothing to improve.")
        if args.github_output:
            with open(args.github_output, "a", encoding="utf-8") as fh:
                fh.write("empty=true\n")
        return 0

    print(f"improve_queue: picked {item['id']!r} -- {item['description']}")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as fh:
            fh.write("empty=false\n")
            fh.write(f"item_id={item['id']}\n")
            fh.write(f"item_description={item['description']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
