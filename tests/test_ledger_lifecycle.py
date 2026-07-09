"""Tests for the ledger status lifecycle (pipeline.watcher.ledger's
set_item_status and mark_* wrappers), and for the invariant that a
watcher re-run never resets or re-queues an item that has moved past
"queued" -- Phase 2's extension of Phase 1's "re-run adds nothing"
guarantee.
"""
from __future__ import annotations

import pytest

from pipeline.watcher.ledger import (
    InvalidStatusTransition,
    diff_new_items,
    mark_drafted,
    mark_error,
    mark_published,
    mark_verified,
    save_ledger,
    upsert_items,
)
from pipeline.watcher.parse import NormalizedItem
from pipeline.watcher.queue import derive_queue


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


def _queued_ledger():
    ledger = upsert_items({"schema_version": 1, "generated_at": None, "items": {}}, [_item()], "2026-01-01T00:00:00Z")
    item_hash = next(iter(ledger["items"]))
    return ledger, item_hash


def test_full_lifecycle_queued_to_published():
    ledger, item_hash = _queued_ledger()

    ledger = mark_drafted(ledger, item_hash, "card-1", "2026-01-02T00:00:00Z")
    assert ledger["items"][item_hash]["status"] == "drafted"
    assert ledger["items"][item_hash]["card_id"] == "card-1"

    ledger = mark_verified(ledger, item_hash, "2026-01-03T00:00:00Z")
    assert ledger["items"][item_hash]["status"] == "verified"

    ledger = mark_published(ledger, item_hash, "2026-01-04T00:00:00Z")
    assert ledger["items"][item_hash]["status"] == "published"
    # card_id set at drafted time survives later transitions.
    assert ledger["items"][item_hash]["card_id"] == "card-1"


def test_illegal_transition_raises():
    ledger, item_hash = _queued_ledger()
    with pytest.raises(InvalidStatusTransition):
        mark_published(ledger, item_hash, "2026-01-02T00:00:00Z")  # can't skip drafted/verified


def test_any_state_can_move_to_error():
    ledger, item_hash = _queued_ledger()
    ledger = mark_error(ledger, item_hash, "2026-01-02T00:00:00Z")
    assert ledger["items"][item_hash]["status"] == "error"

    # error -> queued (retry) -> drafted -> error again, from a different state.
    from pipeline.watcher.ledger import set_item_status

    ledger = set_item_status(ledger, item_hash, "queued", run_ts="2026-01-03T00:00:00Z")
    ledger = mark_drafted(ledger, item_hash, "card-1", "2026-01-04T00:00:00Z")
    ledger = mark_error(ledger, item_hash, "2026-01-05T00:00:00Z")
    assert ledger["items"][item_hash]["status"] == "error"


def test_error_can_be_requeued():
    ledger, item_hash = _queued_ledger()
    ledger = mark_error(ledger, item_hash, "2026-01-02T00:00:00Z")
    from pipeline.watcher.ledger import set_item_status

    ledger = set_item_status(ledger, item_hash, "queued", run_ts="2026-01-03T00:00:00Z")
    assert ledger["items"][item_hash]["status"] == "queued"


def test_set_item_status_does_not_mutate_input_ledger():
    ledger, item_hash = _queued_ledger()
    original_status = ledger["items"][item_hash]["status"]
    mark_drafted(ledger, item_hash, "card-1", "2026-01-02T00:00:00Z")
    assert ledger["items"][item_hash]["status"] == original_status


def test_unknown_item_hash_raises_keyerror():
    ledger, _ = _queued_ledger()
    with pytest.raises(KeyError):
        mark_drafted(ledger, "not-a-real-hash", "card-1", "2026-01-02T00:00:00Z")


def test_derive_queue_excludes_items_past_queued_status():
    ledger, item_hash = _queued_ledger()
    ledger = mark_drafted(ledger, item_hash, "card-1", "2026-01-02T00:00:00Z")

    queue_doc = derive_queue(ledger, "2026-01-03T00:00:00Z")
    assert queue_doc["items"] == []


def test_watcher_rerun_never_resets_or_requeues_a_drafted_item():
    """Phase 2 extension of the Phase 1 idempotency guarantee: once an
    item has moved past "queued" (e.g. the analyst has drafted a card for
    it), a later watcher run re-seeing the same upstream RSS item must
    NOT reset it back to "queued" or duplicate it."""
    ledger, item_hash = _queued_ledger()
    ledger = mark_drafted(ledger, item_hash, "card-1", "2026-01-02T00:00:00Z")

    # The watcher runs again and the same upstream item is still in the feed.
    same_item = _item()
    new_items, seen_items = diff_new_items([same_item], ledger)
    assert new_items == []
    assert len(seen_items) == 1

    ledger_after = upsert_items(ledger, new_items, "2026-01-05T00:00:00Z")
    assert ledger_after["items"][item_hash]["status"] == "drafted"
    assert ledger_after["items"][item_hash]["card_id"] == "card-1"

    # And it still doesn't show up in the queue.
    queue_doc = derive_queue(ledger_after, "2026-01-05T00:00:00Z")
    assert queue_doc["items"] == []


def test_save_ledger_after_lifecycle_transition_is_idempotent_on_rerun(tmp_path):
    ledger, item_hash = _queued_ledger()
    ledger = mark_drafted(ledger, item_hash, "card-1", "2026-01-02T00:00:00Z")

    path = str(tmp_path / "ledger.json")
    assert save_ledger(path, ledger) is True

    # Saving the identical (modulo generated_at) ledger again must be a no-op.
    ledger_again = dict(ledger, generated_at="2026-01-03T00:00:00Z")
    assert save_ledger(path, ledger_again) is False
