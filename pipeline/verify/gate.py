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


def enforce_verification_gate(card: dict, **fetch_kwargs) -> dict:
    """Returns a NEW card dict (the input is never mutated).

    If every citation is authentic, the card's status passes through
    unchanged. If any citation is inauthentic -- or the card has no
    citations at all, which schema validation should already have
    rejected -- status is forced to "unverified", overriding whatever the
    upstream LLM pass claimed.
    """
    results = check_card_citations(card, **fetch_kwargs)
    gated_card = copy.deepcopy(card)

    if not results or any(not r.authentic for r in results):
        gated_card["status"] = "unverified"

    return gated_card
