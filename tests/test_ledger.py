"""Tests for pipeline.watcher.ledger."""
from __future__ import annotations

import os

from pipeline.watcher.ledger import diff_new_items, load_ledger, save_ledger, upsert_items
from pipeline.watcher.parse import NormalizedItem


def _item(guid, title="Title", **overrides):
    base = dict(
        source_id="sfc",
        feed_id="sfc_circulars",
        feed_url="https://example.invalid",
        guid=guid,
        link=None,
        title=title,
        summary="Summary",
        published_at="2026-01-01T00:00:00Z",
        raw_published="Thu, 01 Jan 2026 00:00:00 +0000",
    )
    base.update(overrides)
    return NormalizedItem(**base)


def _empty_ledger():
    return {"schema_version": 1, "generated_at": None, "items": {}}


def test_load_ledger_missing_file_returns_empty_structure(tmp_path):
    ledger = load_ledger(str(tmp_path / "does-not-exist.json"))
    assert ledger["items"] == {}
    assert ledger["schema_version"] == 1


def test_diff_new_items_all_new_on_empty_ledger():
    items = [_item("a"), _item("b")]
    new_items, seen_items = diff_new_items(items, _empty_ledger())
    assert len(new_items) == 2
    assert seen_items == []


def test_diff_new_items_skips_already_known():
    item_a = _item("a")
    ledger = upsert_items(_empty_ledger(), [item_a], "2026-01-01T00:00:00Z")
    new_items, seen_items = diff_new_items([item_a, _item("b")], ledger)
    assert [i.guid for i in new_items] == ["b"]
    assert [i.guid for i in seen_items] == ["a"]


def test_upsert_items_does_not_clobber_first_seen_on_already_known_item():
    ledger = upsert_items(_empty_ledger(), [_item("a")], "2026-01-01T00:00:00Z")
    # Re-upserting the same item on a later run must not change its first_seen.
    ledger = upsert_items(ledger, [_item("a")], "2026-06-01T00:00:00Z")
    entry = next(iter(ledger["items"].values()))
    assert entry["first_seen"] == "2026-01-01T00:00:00Z"


def test_upsert_items_sets_status_queued_and_null_card_id():
    ledger = upsert_items(_empty_ledger(), [_item("a")], "2026-01-01T00:00:00Z")
    entry = next(iter(ledger["items"].values()))
    assert entry["status"] == "queued"
    assert entry["card_id"] is None


def test_save_ledger_roundtrip(tmp_path):
    path = str(tmp_path / "ledger.json")
    ledger = upsert_items(_empty_ledger(), [_item("a")], "2026-01-01T00:00:00Z")
    assert save_ledger(path, ledger) is True
    loaded = load_ledger(path)
    assert loaded["items"].keys() == ledger["items"].keys()


def test_save_ledger_skips_write_when_only_generated_at_differs(tmp_path):
    path = str(tmp_path / "ledger.json")
    ledger = upsert_items(_empty_ledger(), [_item("a")], "2026-01-01T00:00:00Z")
    save_ledger(path, ledger)
    mtime_before = os.path.getmtime(path)

    ledger_again = dict(ledger, generated_at="2026-02-01T00:00:00Z")
    changed = save_ledger(path, ledger_again)
    assert changed is False
    assert os.path.getmtime(path) == mtime_before


def test_save_ledger_writes_when_items_actually_change(tmp_path):
    path = str(tmp_path / "ledger.json")
    ledger = upsert_items(_empty_ledger(), [_item("a")], "2026-01-01T00:00:00Z")
    save_ledger(path, ledger)

    ledger2 = upsert_items(ledger, [_item("b")], "2026-01-02T00:00:00Z")
    assert save_ledger(path, ledger2) is True
