"""Tests for pipeline.verify.quote_policy -- the deterministic
15-word/one-per-source citation quote policy check."""
from __future__ import annotations

import glob
import json
import os

from pipeline.verify.quote_policy import (
    MIN_QUOTE_CHARS,
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


def test_short_quote_fails_minimum_substance():
    """Real gap found live during the 2026-07-13 compliance audit: before
    this floor existed, pipeline/verify/authenticity.py's
    quote_is_authentic("the", <any regulator page>) returned True, since
    "the" is a substring of nearly any real prose -- a contentless
    "quote" could sail through the non-bypassable gate to status
    "verified". No live card currently exploits this; the floor closes
    the gap regardless."""
    assert quote_meets_minimum_substance("the") is False
    assert quote_meets_minimum_substance("no") is False


def test_quote_at_or_above_char_floor_meets_minimum_substance():
    assert quote_meets_minimum_substance("crypto is regulated") is True
    assert quote_meets_minimum_substance("crypto is") is True


def test_contentless_tokens_still_fail_minimum_substance():
    """Real gap found live during the 2026-07-13 compliance audit's own
    adversarial re-check of an earlier word-count-based floor: any 3
    tokens satisfied a raw word count regardless of whether they carried
    real content. Punctuation-only, digit-only, and emoji-only "quotes"
    are caught by the length and alphabetic-content checks; a repeated
    single word is caught by the distinct-token check."""
    assert quote_meets_minimum_substance("... . ,") is False
    assert quote_meets_minimum_substance("- - -") is False
    assert quote_meets_minimum_substance("1 2 3") is False
    assert quote_meets_minimum_substance("\U0001F600 \U0001F601 \U0001F602") is False
    assert quote_meets_minimum_substance("a a a") is False
    assert quote_meets_minimum_substance("aaaaaa aaaaaa") is False


def test_japanese_quote_with_no_internal_whitespace_meets_minimum_substance():
    """Real gap found live during the 2026-07-13 compliance audit: an
    earlier version of this floor used len(quote.split()) >= 3, which
    silently broke every already-published Japanese card quote in this
    project -- .split() treats an entire Japanese sentence as ONE token,
    since Japanese has no whitespace between words, so a word-count-based
    floor is not script-agnostic. Found by re-running this check against
    every published card across all 8 jurisdictions, not just the
    jurisdiction the original fix touched. The character-based floor
    below must keep passing genuine non-whitespace-delimited quotes."""
    assert quote_meets_minimum_substance("その結果、一般の方からのご意見はございませんでした。") is True
    assert quote_meets_minimum_substance("本日公布されており、令和５年６月１日（木曜）から施行されます") is True


def test_repeated_single_japanese_character_fails_minimum_substance():
    """The distinct-content guard must still work for a single
    non-whitespace-delimited token, not just multi-word input."""
    assert quote_meets_minimum_substance("ああああああああ") is False


def test_mostly_numeric_legitimate_citation_still_passes_minimum_substance():
    """Regression for a real false positive: an earlier version of this
    check required min_words alphabetic tokens (not just one), which broke
    an already-published citation quote, '2026 No. 102' (a statutory
    instrument number -- two numeric tokens, one abbreviation), found live
    when re-verifying that exact card after the hardening pass. Short
    quotes that are mostly numbers -- instrument numbers, dates, monetary
    amounts -- are common and legitimate in regulatory citations."""
    assert quote_meets_minimum_substance("2026 No. 102") is True


def test_one_real_word_with_punctuation_filler_passes_minimum_substance():
    """Documents a known, accepted residual gap (not a regression): a
    quote mixing one real word with punctuation filler is not caught by
    this floor, since the check is against clearly-fabricated filler (all
    tokens non-alphabetic, or all tokens identical), not a semantic
    judgment of how substantive a quote is."""
    assert quote_meets_minimum_substance("crypto . ,") is True


def test_three_distinct_stopwords_still_pass_minimum_substance():
    """A floor against fabricated filler, not a semantic judgment of how
    substantive a quote is -- three distinct ordinary (if weak) words
    still pass, same as before this hardening pass."""
    assert quote_meets_minimum_substance("of the act") is True
    assert quote_meets_minimum_substance("and or but") is True


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
    already published under content/<jurisdiction>/cards/ must still
    pass. If this ever fails, stop and report -- do not silently
    downgrade published content to make the check pass.

    Deliberately globs content/*/cards/ (every jurisdiction), not just
    content/hk/cards/ -- an earlier, hk-only version of this test passed
    even while a word-count-based predecessor of this same check silently
    broke 5 real, already-published Japanese card quotes elsewhere in the
    repo (found only by a manual cross-jurisdiction sweep during the
    2026-07-13 compliance audit). A per-jurisdiction glob here would have
    caught that regression itself."""
    card_paths = sorted(glob.glob(os.path.join(REPO_ROOT, "content", "*", "cards", "*.json")))
    assert card_paths, "expected at least one published card fixture"
    assert len({os.path.basename(os.path.dirname(os.path.dirname(p))) for p in card_paths}) > 1, (
        "expected published cards from more than one jurisdiction -- if this ever fails because "
        "only one jurisdiction has cards, that's fine, but confirm it's not silently only globbing one"
    )
    for path in card_paths:
        with open(path, "r", encoding="utf-8") as fh:
            card = json.load(fh)
        result = check_card_quote_policy(card)
        assert result.ok, f"{path} fails quote policy: {result}"
