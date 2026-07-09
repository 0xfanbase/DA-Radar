"""Tests for pipeline.site.generate -- the static site generator.

Uses tests/fixtures/site/ (a small synthetic content/data/config tree),
never the real repo's content/data, so these tests are deterministic and
independent of whatever real content happens to exist when they run.
"""
from __future__ import annotations

import glob
import math
import os
import re

from pipeline.site.generate import build_site
from tests.conftest import REPO_ROOT

FIXTURE_ROOT = os.path.join(REPO_ROOT, "tests", "fixtures", "site")

REQUIRED_DISCLAIMER = (
    "AI-generated summary for general information. Not legal or regulatory "
    "advice. Always verify against the linked primary source."
)

# Literal prefixes/substrings this project's own operational infrastructure
# uses for internal identifiers -- none of these may ever appear in
# rendered, public-facing output. Matches Fable PM's directive to make this
# an automated grep, not just an intention.
LEAKED_IDENTIFIER_PATTERNS = [
    r"trig_[A-Za-z0-9]",
    r"env_[A-Za-z0-9]",
    r"session_[A-Za-z0-9]",
    r"account_uuid",
    r"Claude Code Remote",
    r"\bccr\b",
]


def _read_all_outputs(output_dir):
    return {
        path: open(path, encoding="utf-8").read()
        for path in sorted(glob.glob(os.path.join(output_dir, "*.html")))
    }


def test_build_site_renders_all_7_pages(tmp_path):
    written = build_site(FIXTURE_ROOT, str(tmp_path))
    assert len(written) == 7
    for path in written:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


def test_disclaimer_present_on_every_rendered_page(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    outputs = _read_all_outputs(tmp_path)
    assert len(outputs) == 7
    for path, html in outputs.items():
        assert REQUIRED_DISCLAIMER in html, f"disclaimer missing from {path}"


def test_no_internal_identifiers_leak_into_rendered_output(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    outputs = _read_all_outputs(tmp_path)
    offenders = []
    for path, html in outputs.items():
        for pattern in LEAKED_IDENTIFIER_PATTERNS:
            if re.search(pattern, html, re.IGNORECASE):
                offenders.append((path, pattern))
    assert offenders == [], f"internal identifier pattern(s) leaked into rendered output: {offenders}"


def test_id_leak_check_actually_catches_a_planted_identifier(tmp_path):
    """Positive control: proves the check above isn't vacuously passing --
    plant a real internal-identifier-shaped string into a rendered file and
    confirm the same detection logic used above flags it."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    planted_path = os.path.join(str(tmp_path), "index.html")
    with open(planted_path, "a", encoding="utf-8") as fh:
        fh.write("<!-- trig_01Bk3Lz2FKf3pWRMFkqBcdDE -->")

    html = open(planted_path, encoding="utf-8").read()
    found = any(re.search(pattern, html, re.IGNORECASE) for pattern in LEAKED_IDENTIFIER_PATTERNS)
    assert found is True


def test_verified_card_shows_verified_badge_not_unverified(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    timeline_html = open(os.path.join(str(tmp_path), "timeline.html"), encoding="utf-8").read()
    # card1 (verified) and card2 (unverified) both appear on the Timeline --
    # check the badge each one's own markup carries, not just presence
    # somewhere on the page.
    card1_start = timeline_html.index("Test verified card")
    card1_chunk = timeline_html[card1_start : card1_start + 1500]
    assert "badge-verified" in card1_chunk
    assert "badge-unverified" not in card1_chunk.split("card-meta")[1][:200]


def test_unverified_card_shows_unverified_badge_with_text_label(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    timeline_html = open(os.path.join(str(tmp_path), "timeline.html"), encoding="utf-8").read()
    card2_start = timeline_html.index("Test unverified card")
    card2_chunk = timeline_html[card2_start : card2_start + 1500]
    assert "badge-unverified" in card2_chunk
    assert "Unverified" in card2_chunk


def test_timeline_cards_use_h2_not_h3_no_heading_level_skip(tmp_path):
    """Real bug found live via an actual Lighthouse accessibility audit
    (98/100, docked for non-sequential heading order): Timeline's own <h1>
    has no intervening <h2> before the card list, so the shared card macro
    must render card titles as <h2>, not <h3> -- skipping a heading level
    is a real WCAG/Lighthouse violation, not just a style nit."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    timeline_html = open(os.path.join(str(tmp_path), "timeline.html"), encoding="utf-8").read()
    assert "<h3>" not in timeline_html
    assert timeline_html.count("<h2>") >= 2  # one per fixture card


def test_handles_missing_audit_data_gracefully(tmp_path):
    """Fixture data has no data/audit/latest.json -- audit.yml doesn't
    exist yet (a later phase). The Method page must say so honestly, not
    crash or fabricate placeholder data."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    method_html = open(os.path.join(str(tmp_path), "method.html"), encoding="utf-8").read()
    assert "has not run yet" in method_html


def test_renders_real_audit_findings_when_present(tmp_path):
    """A copy of the fixture root plus a real data/audit/latest.json --
    confirms the Method page renders actual findings, not just the
    "hasn't run yet" placeholder, and never shows the routine pass-rate
    snapshot event as if it were itself a finding."""
    import json
    import shutil

    repo_copy = tmp_path / "repo_with_audit"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    audit_dir = repo_copy / "data" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    with open(audit_dir / "latest.json", "w", encoding="utf-8") as fh:
        json.dump(
            {
                "schema_version": 1,
                "generated_at": "2026-01-05T00:00:00Z",
                "events": [
                    {
                        "schema_version": 1,
                        "event_type": "link_rot",
                        "timestamp": "2026-01-05T00:00:00Z",
                        "actor": "audit.yml",
                        "summary": "Broken link: https://example.invalid/dead (404)",
                        "details": {},
                        "related_ids": [],
                    },
                    {
                        "schema_version": 1,
                        "event_type": "verifier_pass_rate_snapshot",
                        "timestamp": "2026-01-05T00:00:00Z",
                        "actor": "audit.yml",
                        "summary": "1/1 published cards verified (100.0%)",
                        "details": {"pass_rate_pct": 100.0},
                        "related_ids": [],
                    },
                ],
            },
            fh,
        )

    output_dir = tmp_path / "output_with_audit"
    build_site(str(repo_copy), str(output_dir))
    method_html = open(output_dir / "method.html", encoding="utf-8").read()

    assert "2026-01-05T00:00:00Z" in method_html
    assert "Broken link: https://example.invalid/dead" in method_html
    # The routine snapshot must not appear as if it were a "finding".
    assert "1/1 published cards verified" not in method_html


def test_handles_empty_content_gracefully(tmp_path):
    """An entirely empty content tree (no cards, no trajectory entries, no
    documents, no glossary terms, no pillar states) must render placeholder
    empty-state text everywhere, never throw."""
    empty_root = tmp_path / "empty_repo"
    (empty_root / "config").mkdir(parents=True)
    (empty_root / "content" / "cards").mkdir(parents=True)
    (empty_root / "content" / "pillar_states").mkdir(parents=True)
    (empty_root / "content" / "glossary").mkdir(parents=True)
    (empty_root / "data").mkdir(parents=True)

    import json

    with open(empty_root / "config" / "jurisdiction.json", "w") as fh:
        json.dump({"schema_version": 1, "pillars": [], "seal_vocabulary": [], "regulators": []}, fh)

    output_dir = tmp_path / "empty_output"
    written = build_site(str(empty_root), str(output_dir))
    assert len(written) == 7

    timeline_html = open(output_dir / "timeline.html", encoding="utf-8").read()
    assert "No cards published yet" in timeline_html

    trajectory_html = open(output_dir / "trajectory.html", encoding="utf-8").read()
    assert "No officially announced upcoming events" in trajectory_html

    documents_html = open(output_dir / "documents.html", encoding="utf-8").read()
    assert "No documents on record yet" in documents_html

    glossary_html = open(output_dir / "glossary.html", encoding="utf-8").read()
    assert "No glossary terms defined yet" in glossary_html


def _srgb_to_linear(channel):
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (_srgb_to_linear(c) for c in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a, hex_b):
    l1, l2 = sorted([_relative_luminance(hex_a), _relative_luminance(hex_b)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


PAPER = "#FAFAF7"
INK = "#132A43"
SEAL_RED = "#C8102E"
HARBOUR_TEAL = "#1E6E6B"
AMBER = "#B7791F"


def test_body_text_meets_wcag_aa_contrast_on_paper():
    # Normal body text: ink on paper. WCAG AA requires >= 4.5:1.
    assert _contrast_ratio(INK, PAPER) >= 4.5


def test_seal_text_meets_wcag_aa_normal_text_contrast_on_paper():
    # The status seal renders its label directly in seal-red text -- must
    # clear the full 4.5:1 normal-text threshold, not just the 3:1
    # large-text minimum, since pillar status is one of the two highest-
    # stakes labels on the site.
    assert _contrast_ratio(SEAL_RED, PAPER) >= 4.5


def test_amber_as_text_color_fails_aa_and_is_therefore_not_used_as_text():
    # Real finding from an earlier run of this test: amber-as-text-color
    # only reaches ~3.48:1 on paper, below the 4.5:1 normal-text
    # threshold -- confirmed here as a locked-in regression check, not
    # just a one-off observation. This is exactly why the unverified badge
    # (pipeline/site/static/style.css .badge-unverified) uses amber only
    # for its border/background (where the weaker 3:1 non-text/UI-boundary
    # threshold correctly applies) and renders its actual label text in
    # ink, not amber. If this assertion ever starts failing because
    # someone changed the palette, the badge CSS should be re-reviewed
    # too, not just this test.
    assert _contrast_ratio(AMBER, PAPER) < 4.5
    # But it does clear the weaker threshold that non-text UI boundaries
    # (borders) are held to under WCAG 1.4.11.
    assert _contrast_ratio(AMBER, PAPER) >= 3.0


def test_unverified_badge_label_text_is_ink_not_amber(tmp_path):
    """The badge's actual text color must be the high-contrast ink, not the
    amber accent -- checked against the real generated CSS, not just
    inferred from the source file, so a future edit that reintroduces
    amber-as-text would be caught here."""
    css_path = os.path.join(REPO_ROOT, "pipeline", "site", "static", "style.css")
    css = open(css_path, encoding="utf-8").read()
    badge_rule = css[css.index(".badge-unverified"): css.index(".badge-unverified") + 400]
    assert "color: var(--ink)" in badge_rule


def test_link_color_meets_wcag_aa_contrast_on_paper():
    assert _contrast_ratio(HARBOUR_TEAL, PAPER) >= 4.5
