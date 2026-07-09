"""Tests for pipeline.audit.linkrot."""
from __future__ import annotations

from pipeline.audit.linkrot import check_link_rot, collect_urls

FETCH_KWARGS = dict(user_agent="TestAuditor/0.1", timeout=5, max_retries=1, backoff_base=0.01, backoff_multiplier=2.0)


def test_collect_urls_gathers_from_every_content_type():
    cards = [{"id": "c1", "citations": [{"url": "https://example.invalid/a", "quote": "x"}]}]
    pillar_states = [{"pillar": "p1", "key_links": [{"label": "l", "url": "https://example.invalid/b"}]}]
    trajectory = [{"event": "e1", "source_url": "https://example.invalid/c"}]
    document_library = {"documents": [{"item_hash": "d1", "link": "https://example.invalid/d"}]}

    urls = collect_urls(
        cards=cards, pillar_states=pillar_states, trajectory=trajectory, document_library=document_library
    )

    assert set(urls.keys()) == {
        "https://example.invalid/a",
        "https://example.invalid/b",
        "https://example.invalid/c",
        "https://example.invalid/d",
    }
    assert urls["https://example.invalid/a"] == ["card:c1"]


def test_collect_urls_tracks_multiple_sources_for_the_same_url():
    cards = [{"id": "c1", "citations": [{"url": "https://example.invalid/shared", "quote": "x"}]}]
    pillar_states = [{"pillar": "p1", "key_links": [{"label": "l", "url": "https://example.invalid/shared"}]}]

    urls = collect_urls(cards=cards, pillar_states=pillar_states, trajectory=[], document_library={"documents": []})

    assert urls["https://example.invalid/shared"] == ["card:c1", "pillar_state:p1"]


def test_check_link_rot_no_event_for_a_working_url(requests_mock, fixture_bytes):
    url = "https://example.invalid/ok"
    requests_mock.get(url, content=fixture_bytes("sample_document.html"), headers={"Content-Type": "text/html"})
    cards = [{"id": "c1", "citations": [{"url": url, "quote": "x"}]}]

    events = check_link_rot(
        cards=cards, pillar_states=[], trajectory=[], document_library={"documents": []}, **FETCH_KWARGS
    )
    assert events == []


def test_check_link_rot_reports_a_broken_url(requests_mock):
    url = "https://example.invalid/broken"
    requests_mock.get(url, status_code=404)
    cards = [{"id": "c1", "citations": [{"url": url, "quote": "x"}]}]

    events = check_link_rot(
        cards=cards, pillar_states=[], trajectory=[], document_library={"documents": []}, **FETCH_KWARGS
    )
    assert len(events) == 1
    assert events[0]["event_type"] == "link_rot"
    assert url in events[0]["summary"]
    assert events[0]["related_ids"] == ["card:c1"]
