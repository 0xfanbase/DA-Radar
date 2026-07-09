"""Tests for pipeline.watcher.classify -- deterministic pillar/type tagging
for the Document Library."""
from __future__ import annotations

from pipeline.watcher.classify import classify_pillars, type_for_feed

PILLAR_KEYWORDS = {
    "stablecoins": ["stablecoin"],
    "exchanges_vatp": ["trading platform", "vatp"],
}

REGULATORS = [
    {
        "id": "sfc",
        "short_name": "SFC",
        "feeds": [
            {"id": "sfc_circulars", "kind": "circulars"},
            {"id": "sfc_press_releases", "kind": "press_releases"},
        ],
    },
    {
        "id": "hkma",
        "short_name": "HKMA",
        "feeds": [{"id": "hkma_speeches", "kind": "speeches"}],
    },
]


def test_classify_pillars_matches_single_pillar():
    assert classify_pillars("New stablecoin licence granted", "", PILLAR_KEYWORDS) == ["stablecoins"]


def test_classify_pillars_matches_multiple_pillars():
    assert classify_pillars(
        "Stablecoin trading platform launches", "", PILLAR_KEYWORDS
    ) == ["exchanges_vatp", "stablecoins"]


def test_classify_pillars_returns_empty_when_no_match():
    assert classify_pillars("Unrelated banking guideline", "", PILLAR_KEYWORDS) == []


def test_classify_pillars_checks_summary_too():
    assert classify_pillars("Untitled", "mentions a trading platform here", PILLAR_KEYWORDS) == [
        "exchanges_vatp"
    ]


def test_type_for_feed_looks_up_kind():
    assert type_for_feed("sfc", "sfc_circulars", REGULATORS) == "circulars"
    assert type_for_feed("hkma", "hkma_speeches", REGULATORS) == "speeches"


def test_type_for_feed_unknown_regulator_returns_unknown():
    assert type_for_feed("fstb", "fstb_press_releases", REGULATORS) == "unknown"


def test_type_for_feed_unknown_feed_returns_unknown():
    assert type_for_feed("sfc", "sfc_nonexistent", REGULATORS) == "unknown"
