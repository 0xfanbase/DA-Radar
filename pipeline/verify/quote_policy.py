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

# A minimum-substance floor, symmetric with the 15-word cap above. Before
# this existed, pipeline/verify/authenticity.py's quote_is_authentic() did
# a pure substring check with no lower bound -- quote_is_authentic("the",
# <any regulator page>) returns True, since "the" is a substring of nearly
# any real prose, so a contentless or near-contentless "quote" could sail
# through the non-bypassable gate to status "verified".
#
# Character-based, not word-count-based: a first version of this floor
# used len(quote.split()) >= 3, which is NOT script-agnostic -- .split()
# treats an entire Japanese sentence as a single token, since Japanese has
# no whitespace between words, so a real MIN_QUOTE_WORDS=3 word-count
# check rejected every already-published Japanese card quote in this
# project (found live re-running this check against every published card
# across all 8 jurisdictions, not just the jurisdiction the fix touched --
# 5 genuine Japanese quotes failed). A jurisdiction-portable project
# cannot have its deterministic gate silently assume whitespace-delimited
# script. MIN_QUOTE_CHARS counts non-whitespace characters instead, which
# works the same way for any script.
MIN_QUOTE_CHARS = 6


def quote_word_count(quote: str) -> int:
    return len((quote or "").split())


def quote_within_word_limit(quote: str, max_words: int = MAX_QUOTE_WORDS) -> bool:
    return quote_word_count(quote) <= max_words


def quote_meets_minimum_substance(quote: str, min_chars: int = MIN_QUOTE_CHARS) -> bool:
    """A length floor alone is trivially gameable -- found live during the
    2026-07-13 compliance audit's adversarial re-check: '- - -', '1 2 3',
    and '. , ...' all satisfied an earlier word-count-only check while
    carrying no real evidentiary content. Two further, still-deterministic
    conditions close the classes that are unambiguously not a real quote
    under any reading, chosen to have zero false-positive cost against
    real citations: at least one character must be alphabetic (Unicode-
    aware -- this correctly treats Japanese kana/kanji as alphabetic, not
    just ASCII letters; rules out punctuation-only, digit-only, and
    emoji-only filler), and the content must not be just one distinct
    token/character repeated (rules out 'a a a' or a single character
    repeated past the length floor).

    Deliberately NOT "most tokens must be alphabetic" -- an earlier version
    of this check required most tokens to carry alphabetic content and
    broke a real, already-published citation quote, '2026 No. 102' (a
    statutory instrument number: two numeric tokens, one abbreviation),
    found live when re-verifying that exact card after that change. Short
    quotes that are mostly numbers -- instrument numbers, dates, monetary
    amounts -- are common and legitimate in regulatory citations; only the
    presence of at least one real alphabetic character is required. A
    filler quote mixing one real word with punctuation (e.g. 'crypto . ,')
    is not caught by this floor -- this is a check against clearly-
    fabricated filler, not a semantic judgment of how substantive a quote
    is, which is out of scope for a deterministic check."""
    stripped = (quote or "").strip()
    if not stripped:
        return False
    content_chars = [c for c in stripped if not c.isspace()]
    if len(content_chars) < min_chars:
        return False
    if not any(c.isalpha() for c in content_chars):
        return False
    words = stripped.split()
    if len(words) > 1:
        if len({w.casefold() for w in words}) == 1:
            return False
    else:
        if len(set(content_chars)) == 1:
            return False
    return True


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
    under_minimum_quotes: list = field(default_factory=list)
    duplicate_urls: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.over_limit_quotes and not self.under_minimum_quotes and not self.duplicate_urls


def check_card_quote_policy(
    card: dict, max_words: int = MAX_QUOTE_WORDS, min_chars: int = MIN_QUOTE_CHARS
) -> QuotePolicyResult:
    """Checks every citation in a card against the quote policy: no more
    than max_words, at least min_chars of real substance, one citation per
    source URL. Deliberately independent of authenticity/network checks --
    this is pure text analysis of the card's own citations array, so it
    never needs a fetch."""
    citations = card.get("citations", [])
    over_limit = [
        citation["quote"]
        for citation in citations
        if not quote_within_word_limit(citation.get("quote", ""), max_words)
    ]
    under_minimum = [
        citation["quote"]
        for citation in citations
        if not quote_meets_minimum_substance(citation.get("quote", ""), min_chars)
    ]
    return QuotePolicyResult(
        over_limit_quotes=over_limit,
        under_minimum_quotes=under_minimum,
        duplicate_urls=find_duplicate_citation_urls(card),
    )
