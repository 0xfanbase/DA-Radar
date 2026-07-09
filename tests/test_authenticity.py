"""Tests for pipeline.verify.authenticity -- the per-citation authenticity oracle."""
from __future__ import annotations

from pipeline.verify.authenticity import (
    check_card_citations,
    check_citation,
    normalize_for_match,
    quote_is_authentic,
)

URL = "https://example.invalid/doc"
UA = "TestAgent/0.1"
FETCH_KWARGS = dict(user_agent=UA, timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0)


def test_quote_is_authentic_exact_substring():
    assert quote_is_authentic("takes effect on 1 August 2026", "The regime takes effect on 1 August 2026 for all.")


def test_quote_is_authentic_survives_whitespace_reflow():
    quote = "takes   effect\non 1 August 2026"
    source = "The regime takes effect on 1 August 2026 for all."
    assert quote_is_authentic(quote, source)


def test_quote_is_authentic_case_insensitive():
    assert quote_is_authentic("TAKES EFFECT ON 1 AUGUST 2026", "the regime takes effect on 1 august 2026.")


def test_quote_is_not_authentic_when_absent():
    assert not quote_is_authentic("licence revoked with immediate effect", "The regime takes effect on 1 August 2026.")


def test_quote_is_not_authentic_against_altered_document(fixture_bytes):
    """The literal scenario: a fabricated/altered claim must not pass."""
    from pipeline.verify.docfetch import extract_html_text

    original_quote = "takes effect on 1 August 2026"
    altered_text = extract_html_text(fixture_bytes("sample_document_altered.html"))
    assert not quote_is_authentic(original_quote, altered_text)


def test_quote_is_not_authentic_empty_quote_or_source():
    assert not quote_is_authentic("", "some source text")
    assert not quote_is_authentic("some quote", "")


def test_normalize_for_match_collapses_whitespace_and_casefolds():
    assert normalize_for_match("  Hello\n\tWorld  ") == "hello world"


def test_normalize_for_match_treats_smart_and_straight_quotes_as_equal():
    """Real bug found live: official regulator prose consistently uses
    typographic (curly) quotes/apostrophes -- e.g. HKMA press releases --
    while an analyst/verifier's own transcription just as consistently uses
    plain ASCII ones. A quote can be entirely genuine and still fail
    authenticity on this difference alone."""
    assert normalize_for_match("stablecoin holders' requests") == normalize_for_match(
        "stablecoin holders’ requests"
    )
    assert normalize_for_match('the "regime"') == normalize_for_match("the “regime”")


def test_normalize_for_match_treats_en_and_em_dash_as_hyphen():
    assert normalize_for_match("SFC-regulated") == normalize_for_match("SFC–regulated")
    assert normalize_for_match("SFC-regulated") == normalize_for_match("SFC—regulated")


def test_quote_is_authentic_despite_source_using_smart_apostrophe():
    quote = "stablecoin holders' requests for redemption at par"
    source = "processing stablecoin holders’ requests for redemption at par value."
    assert quote_is_authentic(quote, source)


def test_check_citation_authentic_against_real_source(requests_mock, fixture_bytes):
    requests_mock.get(URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    result = check_citation(URL, "takes effect on 1 August 2026", **FETCH_KWARGS)
    assert result.authentic is True
    assert result.error is None


def test_check_citation_inauthentic_against_altered_source(requests_mock, fixture_bytes):
    requests_mock.get(URL, content=fixture_bytes("sample_document_altered.html"), headers={"Content-Type": "text/html"})
    result = check_citation(URL, "takes effect on 1 August 2026", **FETCH_KWARGS)
    assert result.authentic is False
    assert result.error is None


def test_check_citation_fetch_failure_is_not_authentic(requests_mock):
    requests_mock.get(URL, status_code=404)
    result = check_citation(URL, "any quote", **FETCH_KWARGS)
    assert result.authentic is False
    assert result.error is not None


def test_check_card_citations_checks_each_one(requests_mock, fixture_bytes):
    requests_mock.get(URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    other_url = "https://example.invalid/other-doc"
    requests_mock.get(other_url, content=fixture_bytes("sample_document_altered.html"), headers={"Content-Type": "text/html"})

    card = {
        "citations": [
            {"url": URL, "quote": "takes effect on 1 August 2026"},
            {"url": other_url, "quote": "takes effect on 1 August 2026"},
        ]
    }
    results = check_card_citations(card, **FETCH_KWARGS)
    assert len(results) == 2
    assert results[0].authentic is True
    assert results[1].authentic is False
