"""Item identity/content hashing for the ledger.

Identity hash deliberately excludes title/summary so a later text
correction to an already-seen item doesn't spawn a duplicate queue entry.
content_hash is computed and stored but unused for diffing in Phase 1 --
banked as a building block for a future correction-detection feature.
"""
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pipeline.watcher.parse import NormalizedItem


def compute_item_hash(source_id: str, feed_id: str, identity_key: str) -> str:
    key = f"{source_id}\x1f{feed_id}\x1f{identity_key}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def compute_content_hash(title: str, summary: str, published_at: Optional[str]) -> str:
    key = f"{title}\x1f{summary}\x1f{published_at or ''}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def identity_key_for_item(item: "NormalizedItem") -> str:
    """Uses guid when present. Otherwise combines link + title, not link
    alone -- confirmed necessary against a live feed (HKMA's legislative-
    council-issues feed reuses one generic landing-page <link> for every
    item, with only the title distinguishing them; see
    IMPROVEMENT_BACKLOG.md). Two items with the same link AND the same
    title are treated as one real duplicate (also observed live, in HKMA's
    circulars feed, which occasionally lists one item twice)."""
    if item.guid:
        return item.guid
    return f"{item.link or ''}\x1e{item.title or ''}"


def compute_item_hash_for_item(item: "NormalizedItem") -> str:
    return compute_item_hash(item.source_id, item.feed_id, identity_key_for_item(item))
