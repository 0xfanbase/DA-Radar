"""Tests for pipeline.verify.quote_policy -- the deterministic
15-word/one-per-source citation quote policy check."""
from __future__ import annotations

import glob
import json
import os

from pipeline.verify.quote_policy import (
    MIN_QUOTE_WORDS,
    check_card_quote_policy,
    find_duplicate_citation_urls,
    quote_meets_minimum_substance,
    quote_within_word_limit,
    quote_word_count,
)

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))


def test_quote_word_count():
    assert quote_word_count("takes effect on 1 August 2026") == 6


def test_fifteen_word_quote_passes():
    quote = " ".join(f"word{i}" for i in range(15))
    assert quote_word_count(quote) == 15
    assert quote_within_word_limit(quote) is True


def test_sixteen_word_quote_fails():
    quote = " ".join(f"word{i}" for i in range(16))
    assert quote_word_count(quote) == 16
    assert quote_within_word_limit(quote) is False


def test_find_duplicate_citation_urls_none_when_all_distinct():
    card = {
        "citations": [
            {"url": "https://example.invalid/a", "quote": "q1"},
            {"url": "https://example.invalid/b", "quote": "q2"},
        ]
    }
    assert find_duplicate_citation_urls(card) == []


def test_find_duplicate_citation_urls_flags_repeated_url():
    card = {
        "citations": [
            {"url": "https://example.invalid/a", "quote": "q1"},
            {"url": "https://example.invalid/a", "quote": "q2 different wording"},
        ]
    }
    assert find_duplicate_citation_urls(card) == ["https://example.invalid/a"]


def test_two_word_quote_fails_minimum_substance():
    """Real gap found live during the 2026-07-13 compliance audit: before
    this floor existed, pipeline/verify/authenticity.py's
    quote_is_authentic("the", <any regulator page>) returned True, since
    "the" is a substring of nearly any real prose -- a contentless
    "quote" could sail through the non-bypassable gate to status
    "verified". No live card currently exploits this; the floor closes
    the gap regardless."""
    assert quote_meets_minimum_substance("the") is False
    assert quote_meets_minimum_substance("crypto is") is False


def test_three_word_quote_meets_minimum_substance():
    assert quote_word_count("crypto is regulated") == MIN_QUOTE_WORDS
    assert quote_meets_minimum_substance("crypto is regulated") is True


def test_check_card_quote_policy_flags_under_minimum_quote():
    card = {"citations": [{"url": "https://example.invalid/a", "quote": "the"}]}
    result = check_card_quote_policy(card)
    assert result.ok is False
    assert result.under_minimum_quotes == ["the"]
    assert result.over_limit_quotes == []


def test_check_card_quote_policy_passes_clean_card():
    card = {
        "citations": [
            {"url": "https://example.invalid/a", "quote": "a short quote"},
            {"url": "https://example.invalid/b", "quote": "another short quote"},
        ]
    }
    result = check_card_quote_policy(card)
    assert result.ok is True
    assert result.over_limit_quotes == []
    assert result.duplicate_urls == []


def test_check_card_quote_policy_flags_over_limit_quote():
    long_quote = " ".join(f"word{i}" for i in range(16))
    card = {"citations": [{"url": "https://example.invalid/a", "quote": long_quote}]}
    result = check_card_quote_policy(card)
    assert result.ok is False
    assert result.over_limit_quotes == [long_quote]
    assert result.duplicate_urls == []


def test_check_card_quote_policy_flags_duplicate_urls():
    card = {
        "citations": [
            {"url": "https://example.invalid/a", "quote": "first quote"},
            {"url": "https://example.invalid/a", "quote": "second quote"},
        ]
    }
    result = check_card_quote_policy(card)
    assert result.ok is False
    assert result.duplicate_urls == ["https://example.invalid/a"]


def test_check_card_quote_policy_distinct_urls_pass():
    card = {
        "citations": [
            {"url": "https://example.invalid/a", "quote": "first real quote"},
            {"url": "https://example.invalid/b", "quote": "second real quote"},
        ]
    }
    result = check_card_quote_policy(card)
    assert result.ok is True


def test_check_card_quote_policy_no_citations_is_trivially_ok():
    """An empty citations array is not this check's job to reject --
    that's authenticity.py's zero-citations check in gate.py."""
    result = check_card_quote_policy({"citations": []})
    assert result.ok is True


def test_all_published_cards_pass_quote_policy():
    """The acceptance criterion for wiring this check in: every card
    already published under content/cards/ must still pass. If this
    ever fails, stop and report -- do not silently downgrade published
    content to make the check pass."""
    card_paths = sorted(glob.glob(os.path.join(REPO_ROOT, "content", "hk", "cards", "*.json")))
    assert card_paths, "expected at least one published card fixture"
    for path in card_paths:
        with open(path, "r", encoding="utf-8") as fh:
            card = json.load(fh)
        result = check_card_quote_policy(card)
        assert result.ok, f"{path} fails quote policy: {result}"
