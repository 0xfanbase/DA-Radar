"""Tests for pipeline.ci.promote_drafted -- deterministic ledger promotion
from "queued" to "drafted" once a card file exists."""
from __future__ import annotations

import json
import os

from pipeline.ci.promote_drafted import main, promote_drafted_items
from pipeline.watcher.ledger import upsert_items
from pipeline.watcher.parse import NormalizedItem


def _item(guid="a", **overrides):
    base = dict(
        source_id="sfc",
        feed_id="sfc_circulars",
        feed_url="https://example.invalid",
        guid=guid,
        link=None,
        title="Title",
        summary="Summary",
        published_at="2026-01-01T00:00:00Z",
        raw_published="Thu, 01 Jan 2026 00:00:00 +0000",
    )
    base.update(overrides)
    return NormalizedItem(**base)


def _queued_ledger(*guids):
    ledger = {"schema_version": 1, "generated_at": None, "items": {}}
    ledger = upsert_items(ledger, [_item(guid=g) for g in guids], "2026-01-01T00:00:00Z")
    return ledger


def test_promotes_only_items_with_a_card_file(tmp_path):
    ledger = _queued_ledger("a", "b")
    item_hashes = list(ledger["items"].keys())

    cards_dir = tmp_path / "content" / "cards"
    cards_dir.mkdir(parents=True)
    (cards_dir / f"{item_hashes[0]}.json").write_text("{}")
    # No card file written for item_hashes[1].

    new_ledger, promoted = promote_drafted_items(ledger, cards_dir=str(cards_dir), run_ts="2026-01-02T00:00:00Z")

    assert promoted == [item_hashes[0]]
    assert new_ledger["items"][item_hashes[0]]["status"] == "drafted"
    assert new_ledger["items"][item_hashes[0]]["card_id"] == item_hashes[0]
    assert new_ledger["items"][item_hashes[1]]["status"] == "queued"


def test_promote_drafted_items_is_idempotent(tmp_path):
    ledger = _queued_ledger("a")
    item_hash = next(iter(ledger["items"]))
    cards_dir = tmp_path / "content" / "cards"
    cards_dir.mkdir(parents=True)
    (cards_dir / f"{item_hash}.json").write_text("{}")

    ledger, _ = promote_drafted_items(ledger, cards_dir=str(cards_dir), run_ts="2026-01-02T00:00:00Z")
    # Running again (e.g. a re-triggered workflow) must not re-promote or error.
    ledger_again, promoted_again = promote_drafted_items(ledger, cards_dir=str(cards_dir), run_ts="2026-01-03T00:00:00Z")

    assert promoted_again == []
    assert ledger_again["items"][item_hash]["status"] == "drafted"


def test_main_updates_ledger_and_queue_files(tmp_path):
    ledger = _queued_ledger("a", "b")
    item_hashes = list(ledger["items"].keys())

    ledger_path = tmp_path / "ledger.json"
    queue_path = tmp_path / "queue.json"
    with open(ledger_path, "w") as fh:
        json.dump(ledger, fh)

    cards_dir = tmp_path / "content" / "cards"
    cards_dir.mkdir(parents=True)
    (cards_dir / f"{item_hashes[0]}.json").write_text("{}")

    exit_code = main(
        [
            "--ledger",
            str(ledger_path),
            "--queue",
            str(queue_path),
            "--cards-dir",
            str(cards_dir),
        ]
    )
    assert exit_code == 0

    with open(ledger_path) as fh:
        saved_ledger = json.load(fh)
    assert saved_ledger["items"][item_hashes[0]]["status"] == "drafted"
    assert saved_ledger["items"][item_hashes[1]]["status"] == "queued"

    with open(queue_path) as fh:
        saved_queue = json.load(fh)
    # Only the still-queued item remains in the queue.
    assert [i["item_hash"] for i in saved_queue["items"]] == [item_hashes[1]]


def test_no_cards_at_all_promotes_nothing(tmp_path):
    ledger = _queued_ledger("a")
    empty_cards_dir = tmp_path / "content" / "cards"
    empty_cards_dir.mkdir(parents=True)
    _, promoted = promote_drafted_items(ledger, cards_dir=str(empty_cards_dir), run_ts="2026-01-02T00:00:00Z")
    assert promoted == []
