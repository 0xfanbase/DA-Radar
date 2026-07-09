"""Derive content/document_library.json from the ledger -- a pure,
deterministic view, same principle as pipeline/watcher/queue.py deriving
data/queue.json: regenerated in full on every run, never accumulated, so
"re-run adds nothing" holds here too.

This is the public-safe subset of the ledger (site structure item #5,
"Document Library": "every primary document the watcher has seen: title,
date, regulator, type, pillar tags, deep link") -- only relevant items,
only the fields meant for display. The ledger itself stays internal
pipeline state with more fields than should ever be public (content_hash,
raw_published, card_id, status).
"""
from __future__ import annotations

from pipeline.watcher.classify import classify_pillars, type_for_feed
from pipeline.watcher.jsonio import write_if_changed

SCHEMA_VERSION = 1


def _regulator_display_name(source_id: str, regulators: list) -> str:
    for regulator in regulators:
        if regulator.get("id") == source_id:
            return regulator.get("short_name", source_id.upper())
    return source_id.upper()


def derive_document_library(ledger: dict, config: dict, run_ts: str) -> dict:
    pillar_keywords = config.get("pillar_keywords", {})
    regulators = config.get("regulators", [])

    entries = [e for e in ledger.get("items", {}).values() if e.get("relevant", True)]
    entries.sort(key=lambda e: (e["first_seen"], e["item_hash"]))

    documents = [
        {
            "item_hash": e["item_hash"],
            "title": e["title"],
            "link": e["link"],
            "published_at": e["published_at"],
            "regulator": _regulator_display_name(e["source_id"], regulators),
            "type": type_for_feed(e["source_id"], e["feed_id"], regulators),
            "pillar": classify_pillars(e["title"], e["summary"], pillar_keywords),
        }
        for e in entries
    ]
    return {"schema_version": SCHEMA_VERSION, "generated_at": run_ts, "documents": documents}


def save_document_library(path: str, document_library_doc: dict) -> bool:
    return write_if_changed(path, document_library_doc)
