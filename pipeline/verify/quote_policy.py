"""Deterministic quote-policy check, sibling to authenticity.py and
numeric_claims.py.

CLAUDE.md editorial rule 3 requires citation quotes to be capped at 15
words, one per source -- publicly asserted as settled fact by
pipeline/site/templates/method.html ("Quotes are capped at 15 words, one
per source"). Before this module existed, that rule was enforced only by
LLM prompt compliance: card.json's own schema comment already admits the
15-word cap is "enforced by the verifier pass, not by this schema", and
the only real backstop was a 200-character maxLength (roughly 30-40
words) on the quote field. This module makes both halves of the rule a
deterministic, non-bypassable check, mirroring how authenticity.py makes
"is this quote genuine" non-bypassable: no quote may exceed 15
whitespace-split words, and no card may cite the same source URL more
than once ("one per source").
"""
from __future__ import annotations

from dataclasses import dataclass, field

MAX_QUOTE_WORDS = 15


def quote_word_count(quote: str) -> int:
    return len((quote or "").split())


def quote_within_word_limit(quote: str, max_words: int = MAX_QUOTE_WORDS) -> bool:
    return quote_word_count(quote) <= max_words


def find_duplicate_citation_urls(card: dict) -> list:
    """Returns every citation URL that appears more than once in the
    card's citations array, each listed once, in first-duplicate order."""
    seen = set()
    duplicates = []
    for citation in card.get("citations", []):
        url = citation.get("url")
        if url in seen and url not in duplicates:
            duplicates.append(url)
        seen.add(url)
    return duplicates


@dataclass
class QuotePolicyResult:
    over_limit_quotes: list = field(default_factory=list)
    duplicate_urls: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.over_limit_quotes and not self.duplicate_urls


def check_card_quote_policy(card: dict, max_words: int = MAX_QUOTE_WORDS) -> QuotePolicyResult:
    """Checks every citation in a card against the 15-word/one-per-source
    quote policy. Deliberately independent of authenticity/network
    checks -- this is pure text analysis of the card's own citations
    array, so it never needs a fetch."""
    over_limit = [
        citation["quote"]
        for citation in card.get("citations", [])
        if not quote_within_word_limit(citation.get("quote", ""), max_words)
    ]
    return QuotePolicyResult(
        over_limit_quotes=over_limit,
        duplicate_urls=find_duplicate_citation_urls(card),
    )
