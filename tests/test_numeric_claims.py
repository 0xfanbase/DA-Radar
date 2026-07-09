"""Tests for pipeline.verify.numeric_claims -- the deterministic
numeric-claim-tracing check (currency amounts, percentages, and bounded
domain-noun counts; deliberately not bare numbers or dates)."""
from __future__ import annotations

from pipeline.verify.numeric_claims import (
    check_card_numeric_claims,
    extract_numeric_claims,
    normalize_numeric_for_match,
    numeric_claim_is_traceable,
)


def test_extracts_currency_amount_with_symbol():
    assert extract_numeric_claims("licensees must hold HK$25 million in capital") == [
        "HK$25 million"
    ]


def test_extracts_currency_amount_with_thousands_separator():
    assert extract_numeric_claims("a fine of HK$4,000,000 was imposed") == ["HK$4,000,000"]


def test_extracts_percentage_symbol_and_written_form():
    assert extract_numeric_claims("15% of applicants") == ["15%"]
    assert extract_numeric_claims("15 per cent of applicants") == ["15 per cent"]
    assert extract_numeric_claims("15 percent of applicants") == ["15 percent"]


def test_extracts_bounded_noun_counts():
    assert extract_numeric_claims("13 platforms are licensed") == ["13 platforms"]
    assert extract_numeric_claims("36 applicants applied by the deadline") == ["36 applicants"]


def test_does_not_extract_bare_numbers():
    assert extract_numeric_claims("the regime has existed since 2023") == []


def test_does_not_extract_dates():
    assert extract_numeric_claims("effective 10 April 2026") == []
    assert extract_numeric_claims("published on 2026-01-05") == []


def test_does_not_extract_a_number_next_to_an_unrelated_noun():
    assert extract_numeric_claims("13 banks issued guidance") == []


def test_extracts_multiple_claims_from_one_string():
    claims = extract_numeric_claims("HK$25 million in capital and 13 platforms licensed, 15% growth")
    assert "HK$25 million" in claims
    assert "13 platforms" in claims
    assert "15%" in claims


def test_normalize_numeric_strips_thousands_commas():
    assert normalize_numeric_for_match("HK$5,000") == normalize_numeric_for_match("HK$5000")


def test_normalize_numeric_collapses_per_cent_phrasing():
    assert normalize_numeric_for_match("15 per cent") == normalize_numeric_for_match("15%")
    assert normalize_numeric_for_match("15 percent") == normalize_numeric_for_match("15%")


def test_numeric_claim_is_traceable_when_present_in_source():
    assert numeric_claim_is_traceable("HK$25 million", "capital of at least HK$25 million is required")


def test_numeric_claim_is_traceable_across_normalization_forms():
    assert numeric_claim_is_traceable("15%", "a rate of 15 per cent applies")


def test_numeric_claim_is_not_traceable_when_absent():
    assert not numeric_claim_is_traceable("HK$25 million", "capital of at least HK$50 million is required")


def test_numeric_claim_is_not_traceable_empty_claim_or_source():
    assert not numeric_claim_is_traceable("", "some source text")
    assert not numeric_claim_is_traceable("HK$5", "")


def test_check_card_numeric_claims_all_traceable():
    card = {
        "summary": "Licensees must hold HK$25 million in capital.",
        "why_it_matters": "13 platforms are already licensed.",
    }
    source_texts = ["capital of at least HK$25 million is required.", "13 platforms are licensed today."]
    results = check_card_numeric_claims(card, source_texts)
    assert len(results) == 2
    assert all(r.traceable for r in results)


def test_check_card_numeric_claims_flags_untraceable_claim():
    card = {"summary": "The fine was HK$9,000,000.", "why_it_matters": ""}
    source_texts = ["The fine was HK$4,000,000."]
    results = check_card_numeric_claims(card, source_texts)
    assert len(results) == 1
    assert results[0].traceable is False
    assert results[0].claim == "HK$9,000,000"


def test_check_card_numeric_claims_empty_for_purely_qualitative_card():
    """A card with no numeric claims at all is legitimate and must not be
    treated as a failure -- an empty list, not an error."""
    card = {"summary": "The regime took effect as scheduled.", "why_it_matters": "This matters."}
    results = check_card_numeric_claims(card, ["some unrelated source text"])
    assert results == []


def test_check_card_numeric_claims_traceable_if_supported_by_any_one_source():
    """A claim can be supported by any one of the card's several sources,
    matching how the verifier prompt already treats sentence-support."""
    card = {"summary": "A total of HK$25 million was required.", "why_it_matters": ""}
    source_texts = ["unrelated text with no numbers", "capital of at least HK$25 million is required"]
    results = check_card_numeric_claims(card, source_texts)
    assert results[0].traceable is True
