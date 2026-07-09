"""The citation-authenticity oracle: a narrow, deterministic per-citation check.

Given {url, quote}, re-fetch the source and check that quote is a genuine
(normalized) substring of the fetched text. This module answers exactly
one question -- "does this quote actually appear in this source?" -- and
nothing more. It deliberately does NOT know which sentence in a card's
summary/why_it_matters a citation is meant to support; that is a semantic
judgment only the LLM verifier can make. See pipeline/verify/gate.py for
how this oracle's answer becomes non-bypassable before a card is
committed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import requests

from pipeline.verify.docfetch import fetch_document

_WHITESPACE_RE = re.compile(r"\s+")

# Official regulator prose consistently uses typographic (curly) quotes
# and apostrophes; an analyst/verifier transcribing a quote by hand (or an
# LLM's own text generation) just as consistently uses the plain ASCII
# equivalents. A quote that is otherwise perfectly genuine would otherwise
# fail authenticity on this typographic difference alone -- found live via
# the real verification gate rejecting an accurate quote of real regulator
# prose containing "holders'" (source used "holders’", U+2019 right single
# quotation mark). Mapped to ASCII before comparison, not before storage --
# published cards keep whatever punctuation the analyst/verifier wrote.
_PUNCTUATION_NORMALIZE = str.maketrans(
    {
        "‘": "'",  # left single quotation mark
        "’": "'",  # right single quotation mark / apostrophe
        "‚": "'",  # single low-9 quotation mark
        "‛": "'",  # single high-reversed-9 quotation mark
        "“": '"',  # left double quotation mark
        "”": '"',  # right double quotation mark
        "„": '"',  # double low-9 quotation mark
        "‟": '"',  # double high-reversed-9 quotation mark
        "–": "-",  # en dash
        "—": "-",  # em dash
    }
)


def normalize_for_match(text: str) -> str:
    """Casefold + collapse whitespace + normalize smart quotes/dashes to
    their ASCII equivalents, so a quote survives incidental reflow,
    whitespace, and typographic-punctuation differences between the
    analyst's copy and a fresh re-fetch, without being so lenient it
    accepts a materially different claim."""
    normalized = text.translate(_PUNCTUATION_NORMALIZE)
    return _WHITESPACE_RE.sub(" ", normalized).strip().casefold()


def quote_is_authentic(quote: str, source_text: str) -> bool:
    if not quote or not source_text:
        return False
    return normalize_for_match(quote) in normalize_for_match(source_text)


@dataclass
class CitationCheckResult:
    url: str
    quote: str
    authentic: bool
    error: Optional[str] = None
    # The fetched source's extracted text, kept so a later, separate check
    # (pipeline/verify/numeric_claims.py) can re-use this same fetch
    # rather than re-fetching every citation a second time. Empty string
    # on any fetch/extraction failure, never None, so callers can always
    # safely join/concatenate it.
    source_text: str = ""


def check_citation(
    url: str,
    quote: str,
    *,
    user_agent: str,
    timeout: float,
    max_retries: int,
    backoff_base: float,
    backoff_multiplier: float,
    session: Optional[requests.Session] = None,
) -> CitationCheckResult:
    """Re-fetch url and check whether quote genuinely appears in it.

    A fetch or extraction failure counts as NOT authentic -- fail closed,
    since an uncheckable citation cannot be treated as verified.
    """
    doc = fetch_document(
        url,
        user_agent=user_agent,
        timeout=timeout,
        max_retries=max_retries,
        backoff_base=backoff_base,
        backoff_multiplier=backoff_multiplier,
        session=session,
    )
    if doc.status != "ok":
        return CitationCheckResult(url=url, quote=quote, authentic=False, error=doc.error)

    return CitationCheckResult(
        url=url,
        quote=quote,
        authentic=quote_is_authentic(quote, doc.text),
        source_text=doc.text,
    )


def check_card_citations(card: dict, **fetch_kwargs) -> list:
    """Check every citation in a card. Returns one CitationCheckResult per
    citation, in the card's citation order."""
    session = fetch_kwargs.pop("session", None) or requests.Session()
    return [
        check_citation(citation["url"], citation["quote"], session=session, **fetch_kwargs)
        for citation in card.get("citations", [])
    ]
