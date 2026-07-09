"""Tests for pipeline.ci.promote_verified -- deterministic ledger
promotion from "drafted" to "verified" then "published"."""
from __future__ import annotations

import json

from pipeline.ci.promote_verified import main, promote_verified_items
from pipeline.watcher.ledger import mark_drafted, upsert_items
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


def _drafted_ledger(*guids):
    ledger = {"schema_version": 1, "generated_at": None, "items": {}}
    ledger = upsert_items(ledger, [_item(guid=g) for g in guids], "2026-01-01T00:00:00Z")
    for item_hash in list(ledger["items"]):
        ledger = mark_drafted(ledger, item_hash, item_hash, "2026-01-02T00:00:00Z")
    return ledger


def test_promotes_all_drafted_items_to_published():
    ledger = _drafted_ledger("a", "b")
    new_ledger, promoted = promote_verified_items(ledger, "2026-01-03T00:00:00Z")

    assert set(promoted) == set(ledger["items"].keys())
    for entry in new_ledger["items"].values():
        assert entry["status"] == "published"


def test_leaves_non_drafted_items_untouched():
    ledger = {"schema_version": 1, "generated_at": None, "items": {}}
    ledger = upsert_items(ledger, [_item(guid="a")], "2026-01-01T00:00:00Z")
    item_hash = next(iter(ledger["items"]))
    # still "queued", never drafted
    new_ledger, promoted = promote_verified_items(ledger, "2026-01-03T00:00:00Z")

    assert promoted == []
    assert new_ledger["items"][item_hash]["status"] == "queued"


def test_is_idempotent_on_rerun():
    ledger = _drafted_ledger("a")
    ledger, _ = promote_verified_items(ledger, "2026-01-03T00:00:00Z")
    ledger_again, promoted_again = promote_verified_items(ledger, "2026-01-04T00:00:00Z")

    assert promoted_again == []


def test_main_updates_ledger_and_queue_files(tmp_path):
    ledger = _drafted_ledger("a")
    ledger_path = tmp_path / "ledger.json"
    queue_path = tmp_path / "queue.json"
    with open(ledger_path, "w") as fh:
        json.dump(ledger, fh)

    exit_code = main(["--ledger", str(ledger_path), "--queue", str(queue_path)])
    assert exit_code == 0

    with open(ledger_path) as fh:
        saved_ledger = json.load(fh)
    for entry in saved_ledger["items"].values():
        assert entry["status"] == "published"

    with open(queue_path) as fh:
        saved_queue = json.load(fh)
    assert saved_queue["items"] == []
