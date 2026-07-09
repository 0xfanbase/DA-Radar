"""Tests for pipeline.watcher.parse."""
from __future__ import annotations

import pytest

from pipeline.watcher.parse import FeedParseError, parse_rss


def test_parses_sfc_press_releases(fixture_bytes):
    xml = fixture_bytes("sfc_press_releases_day1.xml")
    items = parse_rss(
        xml, source_id="sfc", feed_id="sfc_press_releases", feed_url="https://example.invalid"
    )
    assert len(items) == 3
    first = items[0]
    assert first.guid == "26PR97"
    assert first.title == "SFC concludes consultation on the investor identification regime"
    assert first.published_at == "2026-06-23T09:01:09Z"
    assert first.source_id == "sfc"
    assert first.feed_id == "sfc_press_releases"


def test_parses_hkma_press_release_with_no_guid(fixture_bytes):
    xml = fixture_bytes("hkma_press_release_day1.xml")
    items = parse_rss(
        xml, source_id="hkma", feed_id="hkma_press_release", feed_url="https://example.invalid"
    )
    assert len(items) == 2
    assert items[0].guid is None
    assert items[0].link.startswith("https://www.hkma.gov.hk")


def test_missing_guid_and_link_still_parses(fixture_bytes):
    xml = fixture_bytes("missing_guid_and_link.xml")
    items = parse_rss(xml, source_id="test", feed_id="no_id", feed_url="https://example.invalid")
    assert len(items) == 2
    assert items[0].guid is None
    assert items[0].link is None
    assert items[0].title == "First item with no guid or link"


def test_empty_channel_returns_empty_list(fixture_bytes):
    xml = fixture_bytes("empty_channel.xml")
    items = parse_rss(xml, source_id="test", feed_id="empty", feed_url="https://example.invalid")
    assert items == []


def test_malformed_xml_raises_feed_parse_error(fixture_bytes):
    xml = fixture_bytes("malformed.xml")
    with pytest.raises(FeedParseError):
        parse_rss(xml, source_id="test", feed_id="malformed", feed_url="https://example.invalid")


def test_no_channel_element_raises_feed_parse_error():
    xml = b"<rss version='2.0'></rss>"
    with pytest.raises(FeedParseError):
        parse_rss(xml, source_id="test", feed_id="no_channel", feed_url="https://example.invalid")


def test_title_whitespace_and_newlines_collapsed():
    xml = (
        b'<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>'
        b"<item><title>Line one\nLine   two</title><guid>g1</guid>"
        b"<description>d</description></item></channel></rss>"
    )
    items = parse_rss(xml, source_id="test", feed_id="f", feed_url="https://example.invalid")
    assert items[0].title == "Line one Line two"


def test_title_and_summary_length_capped():
    long_title = "x" * 600
    long_summary = "y" * 3000
    xml = (
        '<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>'
        f"<item><title>{long_title}</title><guid>g1</guid>"
        f"<description>{long_summary}</description></item></channel></rss>"
    ).encode()
    items = parse_rss(xml, source_id="test", feed_id="f", feed_url="https://example.invalid")
    assert len(items[0].title) == 500
    assert len(items[0].summary) == 2000


def test_billion_laughs_is_rejected():
    """defusedxml must reject entity-expansion attacks rather than hang/crash."""
    from defusedxml.common import DefusedXmlException

    xml = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ELEMENT lolz (#PCDATA)>
 <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<rss version="2.0"><channel><title>t</title>
<item><title>&lol1;</title></item></channel></rss>"""
    with pytest.raises(FeedParseError):
        parse_rss(xml, source_id="test", feed_id="f", feed_url="https://example.invalid")
