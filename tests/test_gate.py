"""Tests for pipeline.verify.gate -- the final, non-bypassable verification
gate. This is the fixture-based stand-in for the Phase 2 acceptance
criterion: "inject a fabricated claim into a draft card -> verifier
strips it" (here: forces the card to status="unverified", since a
deterministic per-citation oracle can reject an inauthentic citation but
cannot itself rewrite prose -- see IMPROVEMENT_BACKLOG.md for the
citation-vs-sentence interface decision).
"""
from __future__ import annotations

from pipeline.verify.gate import enforce_verification_gate

URL = "https://example.invalid/doc"
FETCH_KWARGS = dict(user_agent="TestAgent/0.1", timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0)


def _draft_card(status="verified", quote="takes effect on 1 August 2026"):
    return {
        "id": "card-1",
        "status": status,
        "citations": [{"url": URL, "quote": quote}],
    }


def test_gate_leaves_status_when_citation_is_authentic(requests_mock, fixture_bytes):
    requests_mock.get(URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    card = _draft_card(status="verified")

    gated = enforce_verification_gate(card, **FETCH_KWARGS)

    assert gated["status"] == "verified"


def test_fabricated_claim_forces_unverified(requests_mock, fixture_bytes):
    """The literal Phase 2 acceptance criterion: a fabricated claim in a
    draft card gets stripped of its 'verified' status by the gate, even
    though the upstream LLM pass had marked the card status="verified"."""
    requests_mock.get(URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    fabricated_card = _draft_card(status="verified", quote="licence revoked with immediate effect")

    gated = enforce_verification_gate(fabricated_card, **FETCH_KWARGS)

    assert gated["status"] == "unverified"


def test_gate_ignores_llm_self_reported_status_when_citation_fails(requests_mock, fixture_bytes):
    """The gate never trusts the LLM's self-report -- even if the card
    already claims status="verified", a failing citation overrides it."""
    requests_mock.get(URL, content=fixture_bytes("sample_document_altered.html"), headers={"Content-Type": "text/html"})
    card = _draft_card(status="verified")

    gated = enforce_verification_gate(card, **FETCH_KWARGS)

    assert gated["status"] == "unverified"


def test_gate_does_not_mutate_the_input_card(requests_mock, fixture_bytes):
    requests_mock.get(URL, content=fixture_bytes("sample_document_altered.html"), headers={"Content-Type": "text/html"})
    card = _draft_card(status="verified")

    enforce_verification_gate(card, **FETCH_KWARGS)

    assert card["status"] == "verified"  # original untouched


def test_gate_forces_unverified_on_zero_citations():
    card = {"id": "card-1", "status": "verified", "citations": []}
    gated = enforce_verification_gate(card, **FETCH_KWARGS)
    assert gated["status"] == "unverified"


def test_gate_all_citations_must_be_authentic(requests_mock, fixture_bytes):
    """One bad citation among several is enough to force unverified."""
    good_url = "https://example.invalid/good"
    bad_url = "https://example.invalid/bad"
    requests_mock.get(good_url, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    requests_mock.get(bad_url, content=fixture_bytes("sample_document_altered.html"), headers={"Content-Type": "text/html"})

    card = {
        "id": "card-1",
        "status": "verified",
        "citations": [
            {"url": good_url, "quote": "takes effect on 1 August 2026"},
            {"url": bad_url, "quote": "takes effect on 1 August 2026"},
        ],
    }
    gated = enforce_verification_gate(card, **FETCH_KWARGS)
    assert gated["status"] == "unverified"
