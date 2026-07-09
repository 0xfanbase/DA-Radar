"""Deterministic pillar/type classification for the Document Library.

Pure code, no AI -- same design family as pipeline/watcher/relevance.py.
Every relevant ledger item gets tagged with the pillar(s) it belongs to
(keyword match against config/jurisdiction.json's pillar_keywords) and a
"type" (the feed's own "kind" field from config/jurisdiction.json's
regulator/feeds list -- e.g. "press_releases", "circulars", "speeches" --
deliberately a SEPARATE vocabulary from card.json's analyst-assigned type
enum, which describes an analyst's editorial judgment about a drafted
card, not a document's raw feed category; conflating the two would force
every feed kind into a category it doesn't cleanly fit).
"""
from __future__ import annotations


def classify_pillars(title: str, summary: str, pillar_keywords: dict) -> list:
    """Returns the sorted list of pillar ids whose keyword list matches
    title+summary. An item can belong to more than one pillar; it can also
    match none, if pillar_keywords doesn't cover its subject."""
    haystack = f"{title} {summary}".lower()
    return sorted(
        pillar_id
        for pillar_id, keywords in pillar_keywords.items()
        if any(keyword.lower() in haystack for keyword in keywords)
    )


def type_for_feed(source_id: str, feed_id: str, regulators: list) -> str:
    """Looks up the feed's own "kind" from the jurisdiction config's
    regulators/feeds list. Returns "unknown" if the feed isn't found there
    (should not happen for any item the watcher itself produced, but a
    document-library entry from an unrecognized feed should never crash
    the classifier)."""
    for regulator in regulators:
        if regulator.get("id") != source_id:
            continue
        for feed in regulator.get("feeds", []):
            if feed.get("id") == feed_id:
                return feed.get("kind", "unknown")
    return "unknown"
