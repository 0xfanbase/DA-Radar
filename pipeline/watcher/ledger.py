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

# Ledger status lifecycle (fixed in Phase 1, exercised starting Phase 2).
# "error" is reachable from any state; "queued" is reachable from "error"
# (a fixed item may be retried). All other transitions are one-directional
# forward progress through the pipeline.
_VALID_TRANSITIONS = {
    "queued": {"drafted"},
    "drafted": {"verified"},
    "verified": {"published"},
    "published": {"corrected", "suppressed"},
    "corrected": {"suppressed"},
    "suppressed": set(),
    "error": {"queued"},
}


class InvalidStatusTransition(Exception):
    """Raised when a ledger item's status would move somewhere the
    lifecycle doesn't allow (see _VALID_TRANSITIONS)."""


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


def set_item_status(ledger: dict, item_hash: str, new_status: str, *, run_ts: str, card_id=None) -> dict:
    """Return a NEW ledger dict with item_hash's status transitioned to
    new_status (the input ledger is never mutated).

    Raises InvalidStatusTransition if the move isn't legal from the item's
    current status, except "error" is always reachable from anywhere.
    Raises KeyError if item_hash isn't in the ledger.
    """
    items = ledger.get("items", {})
    if item_hash not in items:
        raise KeyError(f"unknown item_hash: {item_hash}")

    entry = items[item_hash]
    current_status = entry["status"]
    allowed = new_status == "error" or new_status in _VALID_TRANSITIONS.get(current_status, set())
    if not allowed:
        raise InvalidStatusTransition(
            f"cannot transition item {item_hash} from {current_status!r} to {new_status!r}"
        )

    new_entry = dict(entry)
    new_entry["status"] = new_status
    if card_id is not None:
        new_entry["card_id"] = card_id

    new_items = dict(items)
    new_items[item_hash] = new_entry

    return {"schema_version": SCHEMA_VERSION, "generated_at": run_ts, "items": new_items}


def mark_drafted(ledger: dict, item_hash: str, card_id: str, run_ts: str) -> dict:
    """The analyst has written a draft card for this item."""
    return set_item_status(ledger, item_hash, "drafted", run_ts=run_ts, card_id=card_id)


def mark_verified(ledger: dict, item_hash: str, run_ts: str) -> dict:
    """The verifier pass + the non-bypassable gate have run. Note this
    reflects pipeline STAGE, not editorial confidence -- the card itself
    may carry status="unverified" (see pipeline/verify/gate.py) while the
    ledger item is still "verified", meaning it's ready to publish with
    that visible unverified badge, per the spec's fully-auto-publish
    decision."""
    return set_item_status(ledger, item_hash, "verified", run_ts=run_ts)


def mark_published(ledger: dict, item_hash: str, run_ts: str) -> dict:
    """The card has actually been committed under /content."""
    return set_item_status(ledger, item_hash, "published", run_ts=run_ts)


def mark_error(ledger: dict, item_hash: str, run_ts: str) -> dict:
    return set_item_status(ledger, item_hash, "error", run_ts=run_ts)
