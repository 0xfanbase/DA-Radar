"""Deterministic numeric-claim-tracing check, sibling to authenticity.py.

Given a card's summary/why_it_matters, extracts numeric claims (currency
amounts, percentages, and counts bound to a small closed set of domain
nouns) and checks each traces to the combined text of the card's already-
fetched citation sources (see pipeline/verify/gate.py's enforce_full_gate,
which reuses authenticity.check_card_citations's own fetch rather than
fetching a second time).

Deliberately conservative, and deliberately not a semantic check: bare,
unqualified numbers and dates are NOT extracted here. Dates are the
verifier LLM prompt's job (pipeline/prompts/verifier_prompt.md instructs
re-deriving every key_dates value from source text); a bare number with
no unit/context is too noisy to check reliably here and would risk a
false downgrade against legitimate rounding or paraphrase. This module
answers exactly one bounded question -- "does this specific amount,
percentage, or count also appear, in some normalized form, in the
combined text of this card's own cited sources?" -- and nothing broader.
It cannot and does not detect cherry-picking, spin, or any other
semantic misrepresentation; that remains the adversarial verifier LLM's
job (see verifier_prompt.md), not this module's.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.verify.authenticity import normalize_for_match

# Currency: an explicit currency symbol/code immediately preceding a
# number (HK$5,000 / US$1.2 million / EUR 500) -- a bare number alone is
# never treated as a currency claim.
_CURRENCY_RE = re.compile(
    r"(?:HK\$|US\$|EUR|GBP|RMB|CNY|\$)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:million|billion|thousand))?",
    re.IGNORECASE,
)

# Percentages: "15%", "15 per cent", "15 percent".
_PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s?(?:%|per\s?cent|percent)", re.IGNORECASE)

# Counts bound to a small, closed set of domain-specific countable nouns
# already used across this project's own real content -- deliberately
# not a generic "any number + any noun" match, which would be far too
# noisy and would flag ordinary prose (including dates) as claims.
_COUNT_NOUNS = r"licen[cs]es?|licensees?|applicants?|consultations?|platforms?|regimes?"
_COUNT_RE = re.compile(rf"\d+\s+(?:{_COUNT_NOUNS})", re.IGNORECASE)


def extract_numeric_claims(text: str) -> list:
    """Returns every substring of text matching a currency amount,
    percentage, or bounded-noun count -- never bare numbers or dates."""
    if not text:
        return []
    claims = []
    for pattern in (_CURRENCY_RE, _PERCENT_RE, _COUNT_RE):
        claims.extend(match.group(0) for match in pattern.finditer(text))
    return claims


def normalize_numeric_for_match(claim: str) -> str:
    """Same normalization citation-quote matching already uses, plus:
    strip thousands-separator commas and collapse "per cent"/"percent"
    to "%", so "HK$5,000"/"HK$5000" and "15 per cent"/"15%" each compare
    equal."""
    normalized = normalize_for_match(claim).replace(",", "")
    normalized = re.sub(r"per\s?cent|percent", "%", normalized)
    return normalized.replace(" %", "%")


def numeric_claim_is_traceable(claim: str, combined_source_text: str) -> bool:
    if not claim or not combined_source_text:
        return False
    return normalize_numeric_for_match(claim) in normalize_numeric_for_match(combined_source_text)


@dataclass
class NumericClaimResult:
    claim: str
    traceable: bool


def check_card_numeric_claims(card: dict, source_texts: list) -> list:
    """Extracts numeric claims from summary + why_it_matters and checks
    each against the COMBINED text of every already-fetched citation
    source -- a claim can be supported by any one of the card's sources,
    matching how the verifier prompt already treats sentence-support.
    Returns one NumericClaimResult per extracted claim (empty list for a
    card with no numeric claims at all -- that is a legitimate,
    qualitative card, never itself a failure)."""
    combined_text = " ".join(text for text in source_texts if text)
    claims = extract_numeric_claims(card.get("summary", "")) + extract_numeric_claims(
        card.get("why_it_matters", "")
    )
    return [
        NumericClaimResult(claim=claim, traceable=numeric_claim_is_traceable(claim, combined_text))
        for claim in claims
    ]
