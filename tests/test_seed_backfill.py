"""Tests for pipeline.ci.seed_backfill -- adding known historical items to
the ledger as queued, reusing the exact watcher ledger/queue machinery.
"""
from __future__ import annotations

import json

from pipeline.ci.seed_backfill import main, seed_items_from_descriptors
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


def test_main_regenerates_document_library_from_the_full_ledger(tmp_path):
    """A real gap a P12 (Switzerland) onboarding hit: a live watcher run
    populates document_library.json once, then a *later* seed_backfill call
    adds more relevant items to the ledger but never refreshed it -- the
    file silently fell out of sync with its own source of truth. main()
    must regenerate the full derived view every time, not just touch the
    ledger/queue, exactly like pipeline/watcher/run.py already does after a
    live poll."""
    ledger_path = tmp_path / "ledger.json"
    queue_path = tmp_path / "queue.json"
    doclib_path = tmp_path / "document_library.json"
    config_path = tmp_path / "jurisdiction.json"

    config = {
        "jurisdiction_id": "test",
        "relevance_keywords": ["stablecoin"],
        "regulators": [
            {"id": "finma", "short_name": "FINMA", "feeds": [{"id": "finma_news", "kind": "press_releases"}]}
        ],
    }
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(config, fh)

    # Seed one item first (simulating an earlier live watcher run that
    # already wrote a document_library.json with just this one entry).
    first_descriptors = tmp_path / "first.json"
    first_descriptors.write_text(
        json.dumps(
            [
                {
                    "source_id": "finma",
                    "feed_id": "finma_news",
                    "link": "https://example.invalid/first",
                    "title": "First stablecoin guidance",
                }
            ]
        )
    )
    exit_code = main(
        [
            "--descriptors",
            str(first_descriptors),
            "--ledger",
            str(ledger_path),
            "--queue",
            str(queue_path),
            "--config",
            str(config_path),
            "--document-library",
            str(doclib_path),
        ]
    )
    assert exit_code == 0
    with open(doclib_path) as fh:
        first_doclib = json.load(fh)
    assert len(first_doclib["documents"]) == 1

    # A later, separate seed_backfill call adds a second relevant item.
    second_descriptors = tmp_path / "second.json"
    second_descriptors.write_text(
        json.dumps(
            [
                {
                    "source_id": "finma",
                    "feed_id": "finma_news",
                    "link": "https://example.invalid/second",
                    "title": "Second stablecoin guidance",
                }
            ]
        )
    )
    exit_code = main(
        [
            "--descriptors",
            str(second_descriptors),
            "--ledger",
            str(ledger_path),
            "--queue",
            str(queue_path),
            "--config",
            str(config_path),
            "--document-library",
            str(doclib_path),
        ]
    )
    assert exit_code == 0

    with open(doclib_path) as fh:
        second_doclib = json.load(fh)
    # Both items must now be present -- not just the second one appended,
    # and not the first one left stale from the earlier run.
    links = {d["link"] for d in second_doclib["documents"]}
    assert links == {"https://example.invalid/first", "https://example.invalid/second"}
