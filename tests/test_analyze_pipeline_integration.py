"""End-to-end integration test chaining the deterministic Phase 2 pipeline
stages together: promote_drafted -> (simulated LLM edit) ->
apply_verification_gate -> promote_verified.

This locks in a deliberate, easy-to-mistake-for-a-bug behavior: a card
whose citation the gate finds inauthentic still gets its LEDGER item
promoted all the way to "published". The ledger tracks PIPELINE STAGE
(did the run complete), not editorial confidence -- the card's own JSON
`status` field is what carries the "unverified" signal to readers, per
CLAUDE.md rule 1 (every card must show its verification status) and the
spec's "fully auto-publish with disclaimers" design. A future contributor
encountering this for the first time will very plausibly assume it's a
bug; this test exists so it can't be "fixed" without deliberately
breaking a passing test first.
"""
from __future__ import annotations

import json

from pipeline.ci.apply_verification_gate import apply_gate_to_file
from pipeline.ci.promote_drafted import promote_drafted_items
from pipeline.ci.promote_verified import promote_verified_items
from pipeline.watcher.ledger import upsert_items
from pipeline.watcher.parse import NormalizedItem

UA = "TestAgent/0.1"
FETCH_KWARGS = dict(
    timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0, official_domains=["example.invalid"]
)
DOC_URL = "https://example.invalid/doc"


def _draft_card(item_hash, status="unverified", quote="licence revoked with immediate effect"):
    return {
        "schema_version": 1,
        "id": item_hash,
        "published_date": "2026-01-01",
        "regulator": "Example Regulator",
        "pillar": ["example_pillar"],
        "type": "circular",
        "title": "t",
        "summary": "s",
        "why_it_matters": "w",
        "citations": [{"url": DOC_URL, "quote": quote}],
        "status": status,
        "generated_at": "2026-01-01T00:00:00Z",
        "model": "test-model",
    }


def test_fabricated_citation_still_gets_published_but_visibly_unverified(tmp_path, requests_mock, fixture_bytes):
    """The full, deliberately-surprising chain: a card whose citation is
    fabricated still reaches LEDGER status "published" -- but its own
    file-level status is forced to "unverified" by the gate, and that is
    the reader-facing signal, not the ledger."""
    requests_mock.get(
        DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"}
    )

    # 1. A queued item exists.
    item = NormalizedItem(
        source_id="sfc",
        feed_id="sfc_circulars",
        feed_url="https://example.invalid",
        guid="a",
        link=None,
        title="Title",
        summary="Summary",
        published_at="2026-01-01T00:00:00Z",
        raw_published="Thu, 01 Jan 2026 00:00:00 +0000",
    )
    ledger = upsert_items(
        {"schema_version": 1, "generated_at": None, "items": {}}, [item], "2026-01-01T00:00:00Z"
    )
    item_hash = next(iter(ledger["items"]))

    # 2. The analyst writes a draft card -- with a FABRICATED citation --
    # to content/cards/<item_hash>.json. The quote does not appear in
    # sample_document.html at all.
    cards_dir = tmp_path / "content" / "cards"
    cards_dir.mkdir(parents=True)
    card_path = cards_dir / f"{item_hash}.json"
    card_path.write_text(json.dumps(_draft_card(item_hash, status="unverified")))

    # 3. Deterministic promotion: queued -> drafted, since a card now exists.
    ledger, promoted = promote_drafted_items(ledger, cards_dir=str(cards_dir), run_ts="2026-01-02T00:00:00Z")
    assert promoted == [item_hash]
    assert ledger["items"][item_hash]["status"] == "drafted"

    # 4. Simulated verifier LLM pass: incorrectly marks the card
    # "verified" without actually fixing the fabricated quote -- exactly
    # the failure mode the deterministic gate exists to catch.
    card = json.loads(card_path.read_text())
    card["status"] = "verified"
    card_path.write_text(json.dumps(card))

    # 5. The actual non-bypassable gate: re-fetches the citation for real
    # and finds it does not match the source, overriding the LLM's
    # self-reported "verified".
    downgraded = apply_gate_to_file(str(card_path), user_agent=UA, **FETCH_KWARGS)
    assert downgraded is True
    assert json.loads(card_path.read_text())["status"] == "unverified"

    # 6. Deterministic promotion: drafted -> verified -> published,
    # REGARDLESS of the card's own (now-corrected-to-unverified) status.
    ledger, published = promote_verified_items(ledger, "2026-01-03T00:00:00Z")
    assert published == [item_hash]

    # The deliberately surprising end state: ledger says "published" --
    # the pipeline ran to completion and this card IS live -- while the
    # card file itself says "unverified" -- the reader-facing badge that
    # this content has not been independently confirmed. This is the
    # "fully auto-publish with disclaimers" design, not a bug.
    assert ledger["items"][item_hash]["status"] == "published"
    assert json.loads(card_path.read_text())["status"] == "unverified"


def test_authentic_citation_reaches_published_and_verified(tmp_path, requests_mock, fixture_bytes):
    """The mirror-image happy path, so the surprising case above is read
    against a contrasting baseline in the same file."""
    requests_mock.get(
        DOC_URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"}
    )

    item = NormalizedItem(
        source_id="sfc",
        feed_id="sfc_circulars",
        feed_url="https://example.invalid",
        guid="b",
        link=None,
        title="Title",
        summary="Summary",
        published_at="2026-01-01T00:00:00Z",
        raw_published="Thu, 01 Jan 2026 00:00:00 +0000",
    )
    ledger = upsert_items(
        {"schema_version": 1, "generated_at": None, "items": {}}, [item], "2026-01-01T00:00:00Z"
    )
    item_hash = next(iter(ledger["items"]))

    cards_dir = tmp_path / "content" / "cards"
    cards_dir.mkdir(parents=True)
    card_path = cards_dir / f"{item_hash}.json"
    card_path.write_text(
        json.dumps(_draft_card(item_hash, status="unverified", quote="takes effect on 1 August 2026"))
    )

    ledger, _ = promote_drafted_items(ledger, cards_dir=str(cards_dir), run_ts="2026-01-02T00:00:00Z")

    card = json.loads(card_path.read_text())
    card["status"] = "verified"
    card_path.write_text(json.dumps(card))

    downgraded = apply_gate_to_file(str(card_path), user_agent=UA, **FETCH_KWARGS)
    assert downgraded is False
    assert json.loads(card_path.read_text())["status"] == "verified"

    ledger, published = promote_verified_items(ledger, "2026-01-03T00:00:00Z")

    assert published == [item_hash]
    assert ledger["items"][item_hash]["status"] == "published"
    assert json.loads(card_path.read_text())["status"] == "verified"
