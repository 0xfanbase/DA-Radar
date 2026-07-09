"""Tests for pipeline.watcher.hashing."""
from __future__ import annotations

from pipeline.watcher.hashing import (
    compute_content_hash,
    compute_item_hash,
    compute_item_hash_for_item,
)
from pipeline.watcher.parse import NormalizedItem


def _item(**overrides):
    base = dict(
        source_id="sfc",
        feed_id="sfc_circulars",
        feed_url="https://example.invalid",
        guid=None,
        link=None,
        title="Some title",
        summary="Some summary",
        published_at="2026-01-01T00:00:00Z",
        raw_published="Thu, 01 Jan 2026 00:00:00 +0000",
    )
    base.update(overrides)
    return NormalizedItem(**base)


def test_identity_hash_stable_across_calls():
    item = _item(guid="abc123")
    assert compute_item_hash_for_item(item) == compute_item_hash_for_item(item)


def test_identity_hash_uses_guid_when_present_ignoring_link():
    item1 = _item(guid="abc123", link="https://x/one")
    item2 = _item(guid="abc123", link="https://x/two")
    assert compute_item_hash_for_item(item1) == compute_item_hash_for_item(item2)


def test_same_guid_different_title_same_hash():
    """A later text correction to an already-seen item must not spawn a duplicate."""
    item1 = _item(guid="abc123", title="Original title")
    item2 = _item(guid="abc123", title="Corrected title")
    assert compute_item_hash_for_item(item1) == compute_item_hash_for_item(item2)


def test_missing_guid_falls_back_to_link_plus_title():
    """Confirmed necessary against a live feed that reuses one generic link
    across all its items (see IMPROVEMENT_BACKLOG.md)."""
    item1 = _item(guid=None, link="https://x/shared", title="Title A")
    item2 = _item(guid=None, link="https://x/shared", title="Title B")
    assert compute_item_hash_for_item(item1) != compute_item_hash_for_item(item2)


def test_same_link_and_title_is_treated_as_one_real_duplicate():
    item1 = _item(guid=None, link="https://x/shared", title="Same title")
    item2 = _item(guid=None, link="https://x/shared", title="Same title")
    assert compute_item_hash_for_item(item1) == compute_item_hash_for_item(item2)


def test_missing_guid_and_link_falls_back_to_title():
    item1 = _item(guid=None, link=None, title="Distinct title one")
    item2 = _item(guid=None, link=None, title="Distinct title two")
    assert compute_item_hash_for_item(item1) != compute_item_hash_for_item(item2)


def test_identity_hash_scoped_by_source_and_feed():
    item1 = _item(source_id="sfc", feed_id="sfc_circulars", guid="shared-guid")
    item2 = _item(source_id="hkma", feed_id="hkma_circulars", guid="shared-guid")
    assert compute_item_hash_for_item(item1) != compute_item_hash_for_item(item2)


def test_content_hash_changes_with_text():
    h1 = compute_content_hash("title", "summary", "2026-01-01T00:00:00Z")
    h2 = compute_content_hash("title changed", "summary", "2026-01-01T00:00:00Z")
    assert h1 != h2


def test_compute_item_hash_is_sha256_hex():
    h = compute_item_hash("a", "b", "c")
    assert len(h) == 64
    int(h, 16)  # raises ValueError if not valid hex
