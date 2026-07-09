"""Derive data/queue.json from the ledger -- a pure, deterministic view.

queue.json is regenerated in full on every run (all ledger items with
status=="queued"), never accumulated -- so "re-run adds nothing" is true
both logically and as a literal git diff.
"""
from __future__ import annotations

from pipeline.watcher.jsonio import write_if_changed

SCHEMA_VERSION = 1


def derive_queue(ledger: dict, run_ts: str) -> dict:
    entries = [e for e in ledger.get("items", {}).values() if e.get("status") == "queued"]
    entries.sort(key=lambda e: (e["first_seen"], e["item_hash"]))

    items = [
        {
            "item_hash": e["item_hash"],
            "source_id": e["source_id"],
            "feed_id": e["feed_id"],
            "title": e["title"],
            "link": e["link"],
            "summary": e["summary"],
            "published_at": e["published_at"],
            "status": "queued",
        }
        for e in entries
    ]
    return {"schema_version": SCHEMA_VERSION, "generated_at": run_ts, "items": items}


def save_queue(path: str, queue_doc: dict) -> bool:
    return write_if_changed(path, queue_doc)
