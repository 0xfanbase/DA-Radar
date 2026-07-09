"""Tests for pipeline.watcher.document_library -- deriving the public
document-library view from the ledger."""
from __future__ import annotations

from pipeline.watcher.document_library import derive_document_library

CONFIG = {
    "pillar_keywords": {"stablecoins": ["stablecoin"]},
    "regulators": [
        {
            "id": "hkma",
            "short_name": "HKMA",
            "feeds": [{"id": "hkma_press_release", "kind": "press_releases"}],
        }
    ],
}


def _ledger(items: dict) -> dict:
    return {"schema_version": 1, "generated_at": None, "items": items}


def _item(**overrides):
    base = {
        "item_hash": "h1",
        "source_id": "hkma",
        "feed_id": "hkma_press_release",
        "guid": None,
        "link": "https://example.invalid/a",
        "title": "New stablecoin licence",
        "summary": "",
        "published_at": "2026-01-01T00:00:00Z",
        "raw_published": None,
        "content_hash": "c1",
        "first_seen": "2026-01-01T00:00:00Z",
        "status": "queued",
        "card_id": None,
        "relevant": True,
    }
    base.update(overrides)
    return base


def test_derive_document_library_includes_relevant_items_only():
    ledger = _ledger(
        {
            "h1": _item(item_hash="h1", relevant=True),
            "h2": _item(item_hash="h2", relevant=False, title="Unrelated"),
        }
    )
    doc = derive_document_library(ledger, CONFIG, "2026-01-02T00:00:00Z")
    hashes = [d["item_hash"] for d in doc["documents"]]
    assert hashes == ["h1"]


def test_derive_document_library_tags_pillar_and_type():
    ledger = _ledger({"h1": _item()})
    doc = derive_document_library(ledger, CONFIG, "2026-01-02T00:00:00Z")
    entry = doc["documents"][0]
    assert entry["pillar"] == ["stablecoins"]
    assert entry["type"] == "press_releases"
    assert entry["regulator"] == "HKMA"
    assert entry["link"] == "https://example.invalid/a"
    assert entry["title"] == "New stablecoin licence"


def test_derive_document_library_missing_relevant_field_defaults_included():
    """An item predating the relevance field (no "relevant" key at all)
    must still default to included, same fail-open rule as derive_queue."""
    item = _item()
    del item["relevant"]
    ledger = _ledger({"h1": item})
    doc = derive_document_library(ledger, CONFIG, "2026-01-02T00:00:00Z")
    assert len(doc["documents"]) == 1


def test_derive_document_library_sorted_by_first_seen_then_hash():
    ledger = _ledger(
        {
            "b": _item(item_hash="b", first_seen="2026-01-02T00:00:00Z"),
            "a": _item(item_hash="a", first_seen="2026-01-01T00:00:00Z"),
        }
    )
    doc = derive_document_library(ledger, CONFIG, "2026-01-03T00:00:00Z")
    assert [d["item_hash"] for d in doc["documents"]] == ["a", "b"]


def test_derive_document_library_unknown_regulator_uppercases_source_id():
    ledger = _ledger({"h1": _item(source_id="fstb", feed_id="fstb_press_releases")})
    doc = derive_document_library(ledger, CONFIG, "2026-01-02T00:00:00Z")
    assert doc["documents"][0]["regulator"] == "FSTB"
    assert doc["documents"][0]["type"] == "unknown"


def test_derive_document_library_is_a_pure_function_of_ledger():
    ledger = _ledger({"h1": _item()})
    doc1 = derive_document_library(ledger, CONFIG, "2026-01-02T00:00:00Z")
    doc2 = derive_document_library(ledger, CONFIG, "2026-01-03T00:00:00Z")
    assert doc1["documents"] == doc2["documents"]
