"""Tests for pipeline.watcher.queue."""
from __future__ import annotations

import os

from pipeline.watcher.queue import derive_queue, save_queue


def _entry(item_hash, first_seen, status="queued", **overrides):
    base = dict(
        item_hash=item_hash,
        source_id="sfc",
        feed_id="sfc_circulars",
        guid=None,
        link=None,
        title="Title",
        summary="Summary",
        published_at="2026-01-01T00:00:00Z",
        raw_published="x",
        content_hash="c",
        first_seen=first_seen,
        status=status,
        card_id=None,
    )
    base.update(overrides)
    return base


def test_derive_queue_empty_ledger_is_empty_queue():
    ledger = {"schema_version": 1, "generated_at": None, "items": {}}
    queue_doc = derive_queue(ledger, "2026-01-01T00:00:00Z")
    assert queue_doc["items"] == []


def test_derive_queue_only_includes_queued_status():
    ledger = {
        "schema_version": 1,
        "generated_at": None,
        "items": {
            "h1": _entry("h1", "2026-01-01T00:00:00Z", status="queued"),
            "h2": _entry("h2", "2026-01-02T00:00:00Z", status="published"),
        },
    }
    queue_doc = derive_queue(ledger, "2026-01-03T00:00:00Z")
    assert [i["item_hash"] for i in queue_doc["items"]] == ["h1"]


def test_derive_queue_deterministic_order_by_first_seen_then_hash():
    ledger = {
        "schema_version": 1,
        "generated_at": None,
        "items": {
            "hz": _entry("hz", "2026-01-01T00:00:00Z"),
            "ha": _entry("ha", "2026-01-01T00:00:00Z"),
            "hb": _entry("hb", "2025-12-01T00:00:00Z"),
        },
    }
    queue_doc = derive_queue(ledger, "2026-01-03T00:00:00Z")
    assert [i["item_hash"] for i in queue_doc["items"]] == ["hb", "ha", "hz"]


def test_derive_queue_is_a_pure_function_of_ledger():
    ledger = {
        "schema_version": 1,
        "generated_at": None,
        "items": {"h1": _entry("h1", "2026-01-01T00:00:00Z")},
    }
    q1 = derive_queue(ledger, "2026-01-03T00:00:00Z")
    q2 = derive_queue(ledger, "2026-01-04T00:00:00Z")
    assert q1["items"] == q2["items"]


def test_save_queue_skips_write_when_only_generated_at_differs(tmp_path):
    path = str(tmp_path / "queue.json")
    ledger = {
        "schema_version": 1,
        "generated_at": None,
        "items": {"h1": _entry("h1", "2026-01-01T00:00:00Z")},
    }
    save_queue(path, derive_queue(ledger, "2026-01-03T00:00:00Z"))
    mtime_before = os.path.getmtime(path)

    changed = save_queue(path, derive_queue(ledger, "2026-01-04T00:00:00Z"))
    assert changed is False
    assert os.path.getmtime(path) == mtime_before
