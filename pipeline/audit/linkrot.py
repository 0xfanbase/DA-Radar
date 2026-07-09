"""Link-rot check: re-fetch every URL referenced anywhere in published
content and report which ones no longer resolve.

Pure code, no AI -- reuses pipeline/verify/docfetch.py's real HTTP fetch
(the same fetcher the citation-authenticity gate uses), never a semantic
judgment about content. A URL either resolves or it doesn't.
"""
from __future__ import annotations

from pipeline.verify.docfetch import fetch_document


def collect_urls(*, cards: list, pillar_states: list, trajectory: list, document_library: dict) -> dict:
    """Returns {url: [source_description, ...]} -- a URL can appear in
    more than one place, and every place it's used is worth knowing about
    if that URL later breaks."""
    urls: dict = {}

    def _add(url: str, source: str) -> None:
        if not url:
            return
        urls.setdefault(url, []).append(source)

    for card in cards:
        for citation in card.get("citations", []):
            _add(citation.get("url"), f"card:{card.get('id')}")

    for state in pillar_states:
        for link in state.get("key_links", []):
            _add(link.get("url"), f"pillar_state:{state.get('pillar')}")

    for entry in trajectory:
        _add(entry.get("source_url"), f"trajectory:{entry.get('event')}")

    for doc in document_library.get("documents", []):
        _add(doc.get("link"), f"document_library:{doc.get('item_hash')}")

    return urls


def check_link_rot(
    *, cards: list, pillar_states: list, trajectory: list, document_library: dict, **fetch_kwargs
) -> list:
    """Returns a list of audit/event.json-shaped dicts, one per broken URL.
    A URL that fetches successfully produces no event at all -- only
    genuine breakage is worth an entry."""
    urls = collect_urls(
        cards=cards, pillar_states=pillar_states, trajectory=trajectory, document_library=document_library
    )
    events = []
    for url, sources in sorted(urls.items()):
        result = fetch_document(url, **fetch_kwargs)
        if result.status != "ok":
            events.append(
                {
                    "event_type": "link_rot",
                    "summary": f"Broken link: {url} ({result.error})",
                    "details": {"url": url, "error": result.error, "referenced_by": sources},
                    "related_ids": sources,
                }
            )
    return events
