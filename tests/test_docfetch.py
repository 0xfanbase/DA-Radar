"""Tests for pipeline.verify.docfetch -- document fetch + text extraction."""
from __future__ import annotations

from pipeline.verify.docfetch import extract_html_text, extract_pdf_text, extract_text, fetch_document

URL = "https://example.invalid/doc"
UA = "TestAgent/0.1"


def test_extract_html_text_strips_tags_script_and_style(fixture_bytes):
    html = fixture_bytes("sample_document.html")
    text = extract_html_text(html)
    assert "SFC concludes consultation on the investor identification regime" in text
    assert "takes effect on 1 August 2026" in text
    assert "console.log" not in text
    assert "font-family" not in text


def test_extract_pdf_text_reads_real_pdf(fixture_bytes):
    pdf = fixture_bytes("sample_document.pdf")
    text = extract_pdf_text(pdf)
    assert "HKMA licence granted 10 April 2026." in text


def test_extract_text_dispatches_by_content_type(fixture_bytes):
    html = fixture_bytes("sample_document.html")
    text = extract_text(html, content_type="text/html; charset=utf-8", url=URL)
    assert "SFC concludes consultation" in text


def test_extract_text_dispatches_pdf_by_url_extension(fixture_bytes):
    pdf = fixture_bytes("sample_document.pdf")
    text = extract_text(pdf, content_type=None, url="https://example.invalid/doc.pdf")
    assert "HKMA licence granted" in text


def test_extract_text_dispatches_pdf_by_magic_bytes(fixture_bytes):
    pdf = fixture_bytes("sample_document.pdf")
    text = extract_text(pdf, content_type=None, url=None)
    assert "HKMA licence granted" in text


def test_fetch_document_ok(requests_mock, fixture_bytes):
    requests_mock.get(URL, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    result = fetch_document(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0
    )
    assert result.status == "ok"
    assert "SFC concludes consultation" in result.text


def test_fetch_document_404_returns_error(requests_mock):
    requests_mock.get(URL, status_code=404)
    result = fetch_document(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0
    )
    assert result.status == "error"
    assert result.text is None
    assert result.http_status == 404


def test_fetch_document_malformed_pdf_does_not_crash(requests_mock):
    requests_mock.get(
        URL, content=b"%PDF-not actually a valid pdf", headers={"Content-Type": "application/pdf"}
    )
    result = fetch_document(
        URL, user_agent=UA, timeout=5, max_retries=3, backoff_base=0.01, backoff_multiplier=2.0
    )
    assert result.status == "error"
    assert "text extraction failed" in result.error
