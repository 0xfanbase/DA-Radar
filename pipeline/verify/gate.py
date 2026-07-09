"""The final, non-bypassable verification gate.

Runs immediately before any card is committed. Re-checks every citation's
authenticity itself, via the deterministic oracle in
pipeline/verify/authenticity.py -- it never trusts a card's self-reported
status=="verified" from an upstream LLM pass. If ANY citation fails
authenticity, the card's status is forced to "unverified" here,
unconditionally, regardless of what the analyst/verifier LLM claimed.
"""
from __future__ import annotations

import copy

from pipeline.verify.authenticity import check_card_citations
from pipeline.verify.numeric_claims import check_card_numeric_claims


def enforce_verification_gate(card: dict, **fetch_kwargs) -> dict:
    """Returns a NEW card dict (the input is never mutated).

    If every citation is authentic, the card's status passes through
    unchanged. If any citation is inauthentic -- or the card has no
    citations at all, which schema validation should already have
    rejected -- status is forced to "unverified", overriding whatever the
    upstream LLM pass claimed.

    Left unchanged, alongside the newer enforce_full_gate below, so
    every existing caller/test of this exact function keeps working
    unmodified -- pipeline.ci.apply_verification_gate is the only real
    caller, and it now calls enforce_full_gate instead.
    """
    results = check_card_citations(card, **fetch_kwargs)
    gated_card = copy.deepcopy(card)

    if not results or any(not r.authentic for r in results):
        gated_card["status"] = "unverified"

    return gated_card


def enforce_full_gate(card: dict, **fetch_kwargs) -> dict:
    """Returns a NEW card dict (the input is never mutated).

    Extends enforce_verification_gate with a second, independent check:
    every numeric claim (amounts, percentages, counts) in the card's
    summary/why_it_matters must also trace to the combined text of its
    own already-fetched citation sources (pipeline/verify/numeric_claims.py).
    Reuses the SAME fetch check_card_citations already performed --
    CitationCheckResult.source_text -- rather than fetching every URL a
    second time.

    Status is forced to "unverified" if EITHER the citation-authenticity
    check or the numeric-claims check fails, extending (never replacing)
    the zero-tolerance philosophy above. A numeric-claims failure also
    records which claims didn't trace, in the optional
    numeric_claims_unsupported field -- present only when non-empty, so
    a clean card produces no extra diff noise. A card with zero numeric
    claims at all is a legitimate, purely qualitative card and is never
    penalized for that alone.
    """
    citation_results = check_card_citations(card, **fetch_kwargs)
    source_texts = [r.source_text for r in citation_results]
    numeric_results = check_card_numeric_claims(card, source_texts)

    gated_card = copy.deepcopy(card)

    citations_ok = bool(citation_results) and all(r.authentic for r in citation_results)
    unsupported_claims = [r.claim for r in numeric_results if not r.traceable]

    if not citations_ok or unsupported_claims:
        gated_card["status"] = "unverified"

    if unsupported_claims:
        gated_card["numeric_claims_unsupported"] = unsupported_claims
    else:
        gated_card.pop("numeric_claims_unsupported", None)

    return gated_card
