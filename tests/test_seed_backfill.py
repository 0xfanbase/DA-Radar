"""Tests for pipeline.ci.seed_backfill -- adding known historical items to
the ledger as queued, reusing the exact watcher ledger/queue machinery.
"""
from __future__ import annotations

from pipeline.ci.seed_backfill import seed_items_from_descriptors
from pipeline.watcher.ledger import load_ledger


def _empty_ledger():
    return load_ledger("/nonexistent/path/does/not/exist.json")


def test_seed_adds_new_items_as_queued():
    ledger = _empty_ledger()
    descriptors = [
        {
            "source_id": "sfc",
            "feed_id": "sfc_circulars",
            "link": "https://example.invalid/vatp",
            "title": "VATP regime in effect",
            "summary": "Dual licence regime.",
            "published_at": "2023-06-01T00:00:00Z",
        },
        {
            "source_id": "hkma",
            "feed_id": "hkma_press_release",
            "link": "https://example.invalid/stablecoins",
            "title": "First stablecoin licences granted",
        },
    ]

    new_ledger, added = seed_items_from_descriptors(ledger, descriptors, "2026-07-09T00:00:00Z")

    assert len(added) == 2
    for item_hash in added:
        entry = new_ledger["items"][item_hash]
        assert entry["status"] == "queued"
        assert entry["card_id"] is None


def test_seed_is_idempotent_on_rerun():
    ledger = _empty_ledger()
    descriptors = [
        {
            "source_id": "sfc",
            "feed_id": "sfc_circulars",
            "link": "https://example.invalid/vatp",
            "title": "VATP regime in effect",
        }
    ]

    ledger, added_first = seed_items_from_descriptors(ledger, descriptors, "2026-07-09T00:00:00Z")
    assert len(added_first) == 1

    ledger, added_second = seed_items_from_descriptors(ledger, descriptors, "2026-07-10T00:00:00Z")
    assert added_second == []
    assert len(ledger["items"]) == 1


def test_seed_defaults_missing_optional_fields():
    ledger = _empty_ledger()
    descriptors = [{"source_id": "fstb", "feed_id": "fstb_press_releases", "title": "Only a title"}]

    new_ledger, added = seed_items_from_descriptors(ledger, descriptors, "2026-07-09T00:00:00Z")

    assert len(added) == 1
    entry = new_ledger["items"][added[0]]
    assert entry["link"] is None
    assert entry["summary"] == ""
    assert entry["published_at"] is None
