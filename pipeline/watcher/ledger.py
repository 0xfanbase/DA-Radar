"""Ledger load/diff/upsert/save -- the watcher's idempotency memory.

data/ledger.json is keyed by item_hash -> {..., status, card_id}. Phase 1
only ever writes status="queued"; later phases move items through
drafted -> verified -> published (and corrected / suppressed / error from
there), per the lifecycle documented in IMPROVEMENT_BACKLOG.md.
"""
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Iterable

from pipeline.watcher.hashing import compute_content_hash, compute_item_hash_for_item
from pipeline.watcher.jsonio import write_if_changed

if TYPE_CHECKING:
    from pipeline.watcher.parse import NormalizedItem

SCHEMA_VERSION = 1


def load_ledger(path: str) -> dict:
    if not os.path.exists(path):
        return {"schema_version": SCHEMA_VERSION, "generated_at": None, "items": {}}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def diff_new_items(
    items: Iterable["NormalizedItem"], ledger: dict
) -> tuple[list["NormalizedItem"], list["NormalizedItem"]]:
    """Split items into (new_items, seen_items) based on ledger membership."""
    known_hashes = set(ledger.get("items", {}).keys())
    new_items = []
    seen_items = []
    for item in items:
        item_hash = compute_item_hash_for_item(item)
        if item_hash in known_hashes:
            seen_items.append(item)
        else:
            new_items.append(item)
            known_hashes.add(item_hash)  # guards against dupes within one feed/run
    return new_items, seen_items


def upsert_items(ledger: dict, new_items: Iterable["NormalizedItem"], run_ts: str) -> dict:
    """Return a new ledger dict with new_items added as status="queued".

    Never mutates an already-known entry's first_seen or status.
    """
    items = dict(ledger.get("items", {}))
    for item in new_items:
        item_hash = compute_item_hash_for_item(item)
        if item_hash in items:
            continue
        items[item_hash] = {
            "item_hash": item_hash,
            "source_id": item.source_id,
            "feed_id": item.feed_id,
            "guid": item.guid,
            "link": item.link,
            "title": item.title,
            "summary": item.summary,
            "published_at": item.published_at,
            "raw_published": item.raw_published,
            "content_hash": compute_content_hash(item.title, item.summary, item.published_at),
            "first_seen": run_ts,
            "status": "queued",
            "card_id": None,
        }
    return {"schema_version": SCHEMA_VERSION, "generated_at": run_ts, "items": items}


def save_ledger(path: str, ledger: dict) -> bool:
    return write_if_changed(path, ledger)
