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

from pipeline.site.generate import REDIRECT_STUBS, build_site
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

# tests/fixtures/site/config/site.json registers exactly two jurisdictions:
# "hk" (seeded=true, live content) and "sg" (seeded=false, coming-soon
# placeholder) -- see that fixture file. Every test below that needs to
# reason about the full output set is derived from this, not a separate
# hand-maintained count, so it stays correct if the fixture registry ever
# grows.
FIXTURE_SEEDED_JURISDICTION_IDS = ["hk"]
FIXTURE_UNSEEDED_JURISDICTION_IDS = ["sg"]


def _read_all_outputs(output_dir):
    """Every *.html file anywhere under output_dir, recursively -- P7's
    output tree nests per-jurisdiction pages under <jid>/, unlike the flat
    pre-P7 layout this helper originally only needed to glob one level
    deep."""
    return {
        path: open(path, encoding="utf-8").read()
        for path in sorted(glob.glob(os.path.join(output_dir, "**", "*.html"), recursive=True))
    }


def _content_pages(output_dir):
    """Same as _read_all_outputs, minus the legacy redirect stubs (see
    REDIRECT_STUBS in pipeline/site/generate.py) -- those are minimal,
    intentionally content-free meta-refresh pages, not real site pages, so
    checks like "every page carries the disclaimer" or "every page has the
    theme toggle" must not expect them to look like one."""
    outputs = _read_all_outputs(output_dir)
    stub_paths = {os.path.join(str(output_dir), old_path) for old_path, _ in REDIRECT_STUBS}
    return {path: html for path, html in outputs.items() if path not in stub_paths}


def test_build_site_renders_expected_pages_for_the_fixture_registry(tmp_path):
    """1 global landing page + (Current State, Timeline) per registry
    entry regardless of seeded status + 3 shared pages + 3 legacy redirect
    stubs, for the fixture's 2-jurisdiction registry (see
    FIXTURE_SEEDED_JURISDICTION_IDS / FIXTURE_UNSEEDED_JURISDICTION_IDS)."""
    written = build_site(FIXTURE_ROOT, str(tmp_path))
    total_jurisdictions = len(FIXTURE_SEEDED_JURISDICTION_IDS) + len(FIXTURE_UNSEEDED_JURISDICTION_IDS)
    expected = 1 + (2 * total_jurisdictions) + 3 + len(REDIRECT_STUBS)
    assert len(written) == expected
    for path in written:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


def test_build_site_renders_live_current_state_and_timeline_for_seeded_jurisdictions(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    for jid in FIXTURE_SEEDED_JURISDICTION_IDS:
        current_state_html = open(os.path.join(str(tmp_path), jid, "index.html"), encoding="utf-8").read()
        timeline_html = open(os.path.join(str(tmp_path), jid, "timeline.html"), encoding="utf-8").read()
        assert "Current State" in current_state_html
        assert "Coming soon" not in current_state_html
        assert "Coming soon" not in timeline_html


def test_build_site_renders_coming_soon_placeholder_for_unseeded_jurisdictions(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    for jid in FIXTURE_UNSEEDED_JURISDICTION_IDS:
        current_state_html = open(os.path.join(str(tmp_path), jid, "index.html"), encoding="utf-8").read()
        timeline_html = open(os.path.join(str(tmp_path), jid, "timeline.html"), encoding="utf-8").read()
        assert "Coming soon" in current_state_html
        assert "Coming soon" in timeline_html
        assert os.path.getsize(os.path.join(str(tmp_path), jid, "index.html")) > 0
        assert os.path.getsize(os.path.join(str(tmp_path), jid, "timeline.html")) > 0


def test_build_site_renders_global_landing_page_with_every_registry_entry(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    index_html = open(os.path.join(str(tmp_path), "index.html"), encoding="utf-8").read()
    for jid in FIXTURE_SEEDED_JURISDICTION_IDS + FIXTURE_UNSEEDED_JURISDICTION_IDS:
        assert f'href="{jid}/index.html"' in index_html


def test_build_site_shows_page_generated_timestamp_in_footer_on_every_page(tmp_path):
    """build_generated_at (pipeline.watcher.clock.utc_now_iso(), computed
    once per build_site() call) must reach every rendered page's footer --
    a compliance reader should never be able to load a page with no visible
    signal of when this specific HTML was produced, regardless of page type
    (landing, per-jurisdiction, coming-soon, or a shared page)."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    outputs = _content_pages(tmp_path)
    for path, html in outputs.items():
        assert "Page generated " in html, f"build timestamp missing from {path}"


def test_content_last_updated_is_max_generated_at_across_content_types(tmp_path):
    """content_last_updated must be the single most-recent generated_at
    across pillar states, orientation, cards, AND trajectory -- not just
    one content type -- so it genuinely reflects "the newest AI-touched
    fact anywhere on this jurisdiction's page," not an arbitrary subset.
    The fixture's most recent generated_at is card1.json's
    2026-01-05T00:00:00Z (orientation and the other card are both earlier;
    this fixture's pillar states and trajectory entries carry no
    generated_at at all, exercising the missing-field case too)."""
    jdata = _load_hk_jurisdiction_data(FIXTURE_ROOT)
    assert jdata["content_last_updated"] == "2026-01-05T00:00:00Z"


def test_current_state_and_timeline_pages_show_content_last_updated(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    current_state_html = open(os.path.join(str(tmp_path), "hk", "index.html"), encoding="utf-8").read()
    timeline_html = open(os.path.join(str(tmp_path), "hk", "timeline.html"), encoding="utf-8").read()
    assert "Data on this page last updated 2026-01-05T00:00:00Z" in current_state_html
    assert "Data on this page last updated 2026-01-05T00:00:00Z" in timeline_html


def test_load_jurisdiction_data_flags_seed_pass_only_off_registry_status(tmp_path):
    """analyst_verifier_status / is_seed_pass_only (P8 fix) must come from
    config/site.json's own status.analyst_verifier for the jurisdiction in
    question -- never a hardcoded jurisdiction id -- so flipping the
    fixture's "hk" entry (normally "live") to "planned" changes the flag,
    and the untouched fixture stays "live" / False."""
    import json
    import shutil

    from pipeline.site.data import load_global_data, load_jurisdiction_data

    repo_copy = tmp_path / "repo_seed_pass_flag"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    site_config_path = repo_copy / "config" / "site.json"
    site_config = json.loads(site_config_path.read_text(encoding="utf-8"))
    for entry in site_config["jurisdictions"]:
        if entry["id"] == "hk":
            entry["status"]["analyst_verifier"] = "planned"
    site_config_path.write_text(json.dumps(site_config), encoding="utf-8")

    global_data = load_global_data(str(repo_copy))
    jdata = load_jurisdiction_data(str(repo_copy), "hk", global_data)
    assert jdata["analyst_verifier_status"] == "planned"
    assert jdata["is_seed_pass_only"] is True

    jdata_default = _load_hk_jurisdiction_data(FIXTURE_ROOT)
    assert jdata_default["analyst_verifier_status"] == "live"
    assert jdata_default["is_seed_pass_only"] is False


def test_seed_pass_banner_shown_when_analyst_verifier_not_live(tmp_path):
    """P8 fix: any jurisdiction whose status.analyst_verifier is not "live"
    must show a clear, non-alarming banner near the freshness line on both
    Current State and Timeline, stating the content is from a seed pass,
    not live daily monitoring -- driven off the registry, never a
    hardcoded jurisdiction id or list. Mutates the fixture's hk entry
    (normally "live") to "planned" rather than adding a new fixture
    jurisdiction, so this stays a minimal, targeted regression test."""
    import json
    import shutil

    repo_copy = tmp_path / "repo_seed_pass_only"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    site_config_path = repo_copy / "config" / "site.json"
    site_config = json.loads(site_config_path.read_text(encoding="utf-8"))
    for entry in site_config["jurisdictions"]:
        if entry["id"] == "hk":
            entry["status"]["analyst_verifier"] = "planned"
    site_config_path.write_text(json.dumps(site_config), encoding="utf-8")

    output_dir = tmp_path / "output_seed_pass_only"
    build_site(str(repo_copy), str(output_dir))
    current_state_html = open(output_dir / "hk" / "index.html", encoding="utf-8").read()
    timeline_html = open(output_dir / "hk" / "timeline.html", encoding="utf-8").read()

    for html in (current_state_html, timeline_html):
        assert "seed-pass-banner" in html
        assert "one-time seed pass" in html
        assert "Analyst/Verifier status: planned" in html


def test_seed_pass_banner_absent_for_live_analyst_verifier_jurisdiction(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    current_state_html = open(os.path.join(str(tmp_path), "hk", "index.html"), encoding="utf-8").read()
    timeline_html = open(os.path.join(str(tmp_path), "hk", "timeline.html"), encoding="utf-8").read()
    assert "seed-pass-banner" not in current_state_html
    assert "seed-pass-banner" not in timeline_html


def test_citations_link_wraps_long_unbroken_urls():
    """CSS fix: content/sg/timeline.html overflowed a 1440px viewport
    because long unbroken sgpc.gov.sg citation URL tokens had no wrap
    rule -- .card .citations li a must set overflow-wrap: anywhere."""
    css = _read_style_css()
    assert ".card .citations li a" in css
    rule_start = css.index(".card .citations li a")
    rule_chunk = css[rule_start : rule_start + 200]
    assert "overflow-wrap: anywhere" in rule_chunk


def test_landing_and_method_use_badge_live_for_jurisdiction_status(tmp_path):
    """badge-live (split from badge-verified, P8 fix) is jurisdiction
    "Live" status's own class now, distinct from a card's "Verified"
    status -- checked on both places that ever showed a jurisdiction's
    Live badge."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    index_html = open(os.path.join(str(tmp_path), "index.html"), encoding="utf-8").read()
    method_html = open(os.path.join(str(tmp_path), "method.html"), encoding="utf-8").read()
    assert '<span class="badge-live">Live</span>' in index_html
    assert '<br><span class="badge-live">Live</span>' in method_html


def test_method_page_has_badge_legend_section(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    method_html = open(os.path.join(str(tmp_path), "method.html"), encoding="utf-8").read()
    assert "What the badges mean" in method_html
    legend_chunk = method_html.split("What the badges mean")[1][:2500]
    assert "badge-verified" in legend_chunk
    assert "badge-unverified" in legend_chunk
    assert "badge-corrected" in legend_chunk


def test_landing_second_paragraph_does_not_assume_unseeded_jurisdiction_currently_exists(tmp_path):
    """Real config/site.json has every registered jurisdiction seeded as of
    this fix, so the old "a planned jurisdiction's coming-soon page"
    phrasing on the landing page falsely implied one currently exists.
    The reworded sentence must still make sense generically (for if/when
    an unseeded jurisdiction is registered later) without asserting one
    exists right now."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    index_html = open(os.path.join(str(tmp_path), "index.html"), encoding="utf-8").read()
    assert "a planned jurisdiction's coming-soon page" not in index_html
    assert "any jurisdiction registered before it is seeded shows a coming-soon page here instead" in index_html


def test_legacy_redirect_stubs_are_real_html_with_meta_refresh_and_visible_link(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    for old_path, new_path in REDIRECT_STUBS:
        stub_path = os.path.join(str(tmp_path), old_path)
        assert os.path.exists(stub_path)
        html = open(stub_path, encoding="utf-8").read()
        assert os.path.getsize(stub_path) > 0
        assert f'<meta http-equiv="refresh" content="0; url={new_path}">' in html
        # A visible, real link -- not just a meta refresh -- for crawlers,
        # no-JS clients, and clients that don't honor meta refresh.
        assert f'<a href="{new_path}">' in html
        assert "<script" not in html  # plain-HTML-first ethos, no JS redirect


def test_disclaimer_present_on_every_rendered_page(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    outputs = _content_pages(tmp_path)
    # landing + (current_state, timeline) per jurisdiction (hk, sg) + 3 shared.
    assert len(outputs) == 1 + (2 * 2) + 3
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
    timeline_html = open(os.path.join(str(tmp_path), "hk", "timeline.html"), encoding="utf-8").read()
    # card1 (verified) and card2 (unverified) both appear on the Timeline --
    # check the badge each one's own markup carries, not just presence
    # somewhere on the page. The title also appears earlier in the page's
    # timeline ribbon (a marker label and its non-JS fallback list entry),
    # so find the LAST occurrence -- the actual <article class="card">
    # block, which always renders after the ribbon in document order.
    card1_start = timeline_html.rindex("Test verified card")
    card1_chunk = timeline_html[card1_start : card1_start + 1500]
    assert "badge-verified" in card1_chunk
    assert "badge-unverified" not in card1_chunk.split("card-meta")[1][:200]


def test_unverified_card_shows_unverified_badge_with_text_label(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    timeline_html = open(os.path.join(str(tmp_path), "hk", "timeline.html"), encoding="utf-8").read()
    card2_start = timeline_html.rindex("Test unverified card")
    card2_chunk = timeline_html[card2_start : card2_start + 1500]
    assert "badge-unverified" in card2_chunk
    assert "Unverified" in card2_chunk


def test_unverified_card_from_numeric_claim_failure_shows_cause_specific_label(tmp_path):
    """Fable audit fix: enforce_full_gate downgrades a card to "unverified"
    for two independent reasons -- citation authenticity failure OR an
    unsupported numeric claim (recorded in the card's own
    numeric_claims_unsupported field) -- but the badge used to always show
    the citations-specific wording regardless of cause, which is false for
    a card whose citations are fully authentic and whose only problem is an
    untraceable figure."""
    import json
    import shutil

    repo_copy = tmp_path / "repo_numeric_claim_failure"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    card_path = repo_copy / "content" / "hk" / "cards" / "card2.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["numeric_claims_unsupported"] = ["HK$50 million"]
    card_path.write_text(json.dumps(card), encoding="utf-8")

    output_dir = tmp_path / "output_numeric_claim_failure"
    build_site(str(repo_copy), str(output_dir))
    timeline_html = open(output_dir / "hk" / "timeline.html", encoding="utf-8").read()

    card2_start = timeline_html.rindex("Test unverified card")
    card2_chunk = timeline_html[card2_start : card2_start + 1500]
    assert "badge-unverified" in card2_chunk
    assert "a stated figure could not be confirmed against the cited source" in card2_chunk
    assert "citations could not be confirmed against source" not in card2_chunk


def test_timeline_cards_use_h2_not_h3_no_heading_level_skip(tmp_path):
    """Real bug found live via an actual Lighthouse accessibility audit
    (98/100, docked for non-sequential heading order): Timeline's own <h1>
    has no intervening <h2> before the card list, so the shared card macro
    must render card titles as <h2>, not <h3> -- skipping a heading level
    is a real WCAG/Lighthouse violation, not just a style nit."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    timeline_html = open(os.path.join(str(tmp_path), "hk", "timeline.html"), encoding="utf-8").read()
    assert "<h3>" not in timeline_html
    assert timeline_html.count("<h2>") >= 2  # one per fixture card


def test_method_page_reports_three_way_verification_split_with_mixed_cards(tmp_path):
    """Fable audit fix: 'corrected' was previously unhandled on the Method
    page -- a dead verified_count variable (computed from a ledger status,
    always 0) sat above a sentence claiming 'the rest carry unverified',
    which becomes false the moment any card is corrected. Confirms the
    sentence reports all three real counts, and that the Corrected badge
    itself links through to the corrections log (rule 6 discoverability),
    distinct from the Verified badge's markup."""
    import json
    import shutil

    repo_copy = tmp_path / "repo_mixed_status"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    corrected_card = {
        "schema_version": 1,
        "id": "card3",
        "published_date": "2026-01-08",
        "regulator": "SFC",
        "pillar": ["stablecoins"],
        "type": "circular",
        "title": "Test corrected card",
        "summary": "Test summary text for a corrected card.",
        "why_it_matters": "Test why-it-matters text.",
        "citations": [{"url": "https://example.invalid/source3", "quote": "test quote three"}],
        "status": "corrected",
        "generated_at": "2026-01-08T00:00:00Z",
        "model": "test-model",
    }
    with open(repo_copy / "content" / "hk" / "cards" / "card3.json", "w", encoding="utf-8") as fh:
        json.dump(corrected_card, fh)

    output_dir = tmp_path / "output_mixed_status"
    build_site(str(repo_copy), str(output_dir))
    method_html = open(output_dir / "method.html", encoding="utf-8").read()

    assert (
        'Of 3 published cards, 1 currently carry <span class="badge-verified">verified</span> '
        'status, 1 carry <span class="badge-corrected">corrected</span> status'
        in method_html
    )
    assert (
        'and 1 carry <span class="badge-unverified">unverified</span> status.' in method_html
    )
    assert 'id="corrections-log"' in method_html

    timeline_html = open(output_dir / "hk" / "timeline.html", encoding="utf-8").read()
    card3_start = timeline_html.rindex("Test corrected card")
    card3_chunk = timeline_html[card3_start : card3_start + 1500]
    assert '<a class="badge-corrected" href="../method.html#corrections-log">' in card3_chunk
    assert "badge-verified" not in card3_chunk.split("card-meta")[1][:300]


def test_corrections_log_shows_empty_state_when_no_corrections_exist(tmp_path):
    """Fixture data has no data/corrections.json -- the Method page must
    say so honestly (a real sentence, not a stale hardcoded placeholder
    that was never actually wired to real data)."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    method_html = open(os.path.join(str(tmp_path), "method.html"), encoding="utf-8").read()
    assert "No corrections have been issued yet" in method_html


def test_corrections_log_renders_real_corrections_when_present(tmp_path):
    import json
    import shutil

    repo_copy = tmp_path / "repo_with_corrections"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    data_dir = repo_copy / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    with open(data_dir / "corrections.json", "w", encoding="utf-8") as fh:
        json.dump(
            [
                {
                    "schema_version": 1,
                    "id": "corr-1",
                    "jurisdiction": "hk",
                    "card_id": "card1",
                    "corrected_at": "2026-02-01T00:00:00Z",
                    "correction_note": "The stated capital requirement was wrong.",
                    "fields_changed": ["summary"],
                    "citations": [],
                }
            ],
            fh,
        )

    output_dir = tmp_path / "output_with_corrections"
    build_site(str(repo_copy), str(output_dir))
    method_html = open(output_dir / "method.html", encoding="utf-8").read()

    assert "2026-02-01T00:00:00Z" in method_html
    assert "The stated capital requirement was wrong." in method_html
    # Joined to the real card's title, not just the bare card_id.
    assert "Test verified card" in method_html.split("Corrections log")[1]
    assert "No corrections have been issued yet" not in method_html


def test_corrections_log_shows_reader_appropriate_label_for_unmatched_card(tmp_path):
    """When a correction's card_id matches no published card (e.g. the card
    was later removed), the Corrections Log must not leak the raw 64-char
    card_id hash to readers -- the entire purpose of this page is making
    corrections legible (CLAUDE.md rule 6). It must instead render a
    reader-appropriate label built from a short prefix of the hash."""
    import json
    import shutil

    repo_copy = tmp_path / "repo_with_orphan_correction"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    data_dir = repo_copy / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    orphan_hash = "a" * 64
    with open(data_dir / "corrections.json", "w", encoding="utf-8") as fh:
        json.dump(
            [
                {
                    "schema_version": 1,
                    "id": "corr-orphan",
                    "jurisdiction": "hk",
                    "card_id": orphan_hash,
                    "corrected_at": "2026-03-01T00:00:00Z",
                    "correction_note": "This card was later withdrawn.",
                    "fields_changed": ["summary"],
                    "citations": [],
                }
            ],
            fh,
        )

    output_dir = tmp_path / "output_with_orphan_correction"
    build_site(str(repo_copy), str(output_dir))
    method_html = open(output_dir / "method.html", encoding="utf-8").read()

    assert orphan_hash not in method_html
    assert "Card aaaaaaaa… (no longer published)" in method_html
    assert "This card was later withdrawn." in method_html


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
    empty-state text everywhere, never throw. start_here.json and
    content/trajectory.json are always-expected seed files in their own
    right (see test_raises_when_start_here_missing /
    test_raises_when_pillar_state_missing) so this fixture still supplies
    them -- trajectory.json legitimately holds zero entries here (an empty
    array is valid seed content, not a missing file)."""
    empty_root = tmp_path / "empty_repo"
    (empty_root / "config").mkdir(parents=True)
    (empty_root / "content" / "hk" / "cards").mkdir(parents=True)
    (empty_root / "content" / "hk" / "pillar_states").mkdir(parents=True)
    (empty_root / "content" / "shared" / "glossary").mkdir(parents=True)
    (empty_root / "data" / "hk").mkdir(parents=True)

    import json

    with open(empty_root / "config" / "site.json", "w") as fh:
        json.dump(
            {
                "schema_version": 1,
                "jurisdictions": [
                    {
                        "id": "hk",
                        "name": "Hong Kong",
                        "config": None,
                        "status": {"watcher": "live", "analyst_verifier": "live", "seeded": True},
                        "coverage_notes": "Test fixture jurisdiction.",
                    }
                ],
                "pillars": [],
                "seal_vocabulary": {},
            },
            fh,
        )
    with open(empty_root / "content" / "hk" / "orientation.json", "w") as fh:
        json.dump(
            {
                "schema_version": 1,
                "body": "Test intro paragraph.",
                "last_changed": "2026-01-01",
                "generated_at": "2026-01-01T00:00:00Z",
                "model": "test-model",
            },
            fh,
        )
    with open(empty_root / "content" / "hk" / "trajectory.json", "w") as fh:
        json.dump([], fh)

    output_dir = tmp_path / "empty_output"
    written = build_site(str(empty_root), str(output_dir))
    # landing(1) + hk current_state + hk timeline(2) + 3 shared + 3 redirects.
    assert len(written) == 9

    timeline_html = open(output_dir / "hk" / "timeline.html", encoding="utf-8").read()
    assert "No cards published yet" in timeline_html

    # trajectory.html is now a legacy redirect stub (see REDIRECT_STUBS),
    # not a rendered page with its own empty-state text -- the merged
    # 3-band Timeline page that will show trajectory content again is a
    # later step (see pipeline/site/templates/timeline.html's docstring).
    trajectory_stub_html = open(output_dir / "trajectory.html", encoding="utf-8").read()
    assert 'url=hk/timeline.html' in trajectory_stub_html

    documents_html = open(output_dir / "documents.html", encoding="utf-8").read()
    assert "No documents on record yet" in documents_html

    glossary_html = open(output_dir / "glossary.html", encoding="utf-8").read()
    assert "No glossary terms defined yet" in glossary_html


def _load_hk_jurisdiction_data(repo_root: str) -> dict:
    """Test helper standing in for the old single-call load_site_data() --
    P7 replaced that scaffolding with generate.py walking the registry
    itself, so a test that wants to exercise load_jurisdiction_data()'s
    own validation now composes the same two real calls build_site() makes
    for a seeded jurisdiction."""
    from pipeline.site.data import load_global_data, load_jurisdiction_data

    global_data = load_global_data(repo_root)
    return load_jurisdiction_data(repo_root, "hk", global_data)


def test_raises_when_pillar_state_missing(tmp_path):
    """Regression test for the incident this fixes: deleting one pillar's
    content/pillar_states/*.json file used to silently render 6 of 7
    pillar headings with no warning and no failing test. Post-Phase-3, a
    missing pillar state is a build error -- load_jurisdiction_data must
    raise and name the missing pillar id, not degrade gracefully."""
    import shutil

    from pipeline.site.data import SiteDataError

    repo_copy = tmp_path / "repo_missing_pillar_state"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    os.remove(repo_copy / "content" / "hk" / "pillar_states" / "exchanges_vatp.json")

    try:
        _load_hk_jurisdiction_data(str(repo_copy))
        assert False, "expected SiteDataError for a missing pillar_states file"
    except SiteDataError as exc:
        assert "exchanges_vatp" in str(exc)


def test_raises_when_start_here_missing(tmp_path):
    """Regression test: a missing content/<jurisdiction>/orientation.json
    used to degrade to a silently placeholder-only orientation page. Post-
    Phase-3, that file is always-expected seed content -- a missing file
    must fail the build loudly instead."""
    import shutil

    from pipeline.site.data import SiteDataError

    repo_copy = tmp_path / "repo_missing_start_here"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    os.remove(repo_copy / "content" / "hk" / "orientation.json")

    try:
        _load_hk_jurisdiction_data(str(repo_copy))
        assert False, "expected SiteDataError for a missing orientation.json"
    except SiteDataError as exc:
        assert "orientation.json" in str(exc)


def test_raises_when_status_seal_unmapped(tmp_path):
    """Regression test for a Fable audit finding: a status_seal id with no
    seal_vocabulary entry in config/site.json used to render as a
    raw internal id (e.g. <span class="seal">enforcement_action_pending
    </span>) right next to real seals on the State Board. load_jurisdiction_data
    must fail loudly instead, naming the offending id and the pillar state
    file it came from -- and build_site must never produce output HTML in
    that state, so the raw id can never leak into a rendered page."""
    import json
    import shutil

    from pipeline.site.data import SiteDataError

    repo_copy = tmp_path / "repo_unmapped_seal"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    state_path = repo_copy / "content" / "hk" / "pillar_states" / "stablecoins.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["status_seal"] = "enforcement_action_pending"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    try:
        _load_hk_jurisdiction_data(str(repo_copy))
        assert False, "expected SiteDataError for an unmapped status_seal id"
    except SiteDataError as exc:
        assert "enforcement_action_pending" in str(exc)
        assert "stablecoins.json" in str(exc)

    output_dir = tmp_path / "output_unmapped_seal"
    try:
        build_site(str(repo_copy), str(output_dir))
        assert False, "expected build_site to fail, not render, on an unmapped status_seal"
    except SiteDataError:
        pass
    assert not os.path.exists(output_dir), "build_site must not write output on a failed build"


def test_raises_when_card_pillar_id_unmapped(tmp_path):
    """Companion finding: a pillar id on a card with no entry in
    config/site.json's pillars used to render as a raw internal id
    (e.g. <span class="pillar-tag">aml_enforcement_typo</span>) on the
    Timeline. load_jurisdiction_data must fail loudly instead, naming the
    offending id and the card file it came from -- and build_site must
    never produce output HTML in that state, so the raw id can never leak
    into a rendered page."""
    import json
    import shutil

    from pipeline.site.data import SiteDataError

    repo_copy = tmp_path / "repo_unmapped_pillar"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    card_path = repo_copy / "content" / "hk" / "cards" / "card1.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["pillar"] = ["aml_enforcement_typo"]
    card_path.write_text(json.dumps(card), encoding="utf-8")

    try:
        _load_hk_jurisdiction_data(str(repo_copy))
        assert False, "expected SiteDataError for an unmapped card pillar id"
    except SiteDataError as exc:
        assert "aml_enforcement_typo" in str(exc)
        assert "card1.json" in str(exc)

    output_dir = tmp_path / "output_unmapped_pillar"
    try:
        build_site(str(repo_copy), str(output_dir))
        assert False, "expected build_site to fail, not render, on an unmapped card pillar id"
    except SiteDataError:
        pass
    assert not os.path.exists(output_dir), "build_site must not write output on a failed build"


def test_raises_when_card_citations_empty(tmp_path):
    """Regression test for the incident this fixes: build_timeline_events
    unconditionally indexed card["citations"][0], so a card with an empty
    or missing citations array raised an unhandled IndexError and froze
    publishing (the previously-deployed site just stops updating, with no
    notification). load_jurisdiction_data must instead raise SiteDataError,
    naming the offending card file, before any page renders."""
    import json
    import shutil

    from pipeline.site.data import SiteDataError

    repo_copy = tmp_path / "repo_empty_citations"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    card_path = repo_copy / "content" / "hk" / "cards" / "card1.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["citations"] = []
    card_path.write_text(json.dumps(card), encoding="utf-8")

    try:
        _load_hk_jurisdiction_data(str(repo_copy))
        assert False, "expected SiteDataError for a card with empty citations"
    except SiteDataError as exc:
        assert "card1.json" in str(exc)
        assert "citations" in str(exc)

    output_dir = tmp_path / "output_empty_citations"
    try:
        build_site(str(repo_copy), str(output_dir))
        assert False, "expected build_site to fail, not render, on a card with empty citations"
    except SiteDataError:
        pass
    assert not os.path.exists(output_dir), "build_site must not write output on a failed build"


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


PAPER = "#F2ECDD"
INK = "#132A43"
SEAL_RED = "#C8102E"
HARBOUR_TEAL = "#1E6E6B"
AMBER = "#B7791F"
CARD_LIGHT = "#FBF8F1"

PAPER_DARK = "#0F1E2E"
INK_DARK = "#F0E7D3"
SEAL_RED_DARK = "#F4626B"
HARBOUR_TEAL_DARK = "#3FCDB8"
AMBER_DARK = "#9A6B25"
CARD_DARK = "#16283B"


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


# --- Dark mode: same four checks, mirrored against the dark palette. ---
# Real, independently-derived hex values (not the light values re-tinted) --
# see IMPROVEMENT_BACKLOG.md's redesign entry for the full derivation and
# the dataviz skill's validate_palette.js invocations used to check them.


def test_body_text_meets_wcag_aa_contrast_on_paper_dark():
    assert _contrast_ratio(INK_DARK, PAPER_DARK) >= 4.5


def test_seal_text_meets_wcag_aa_normal_text_contrast_on_paper_dark():
    assert _contrast_ratio(SEAL_RED_DARK, PAPER_DARK) >= 4.5


def test_amber_as_text_color_fails_aa_and_is_therefore_not_used_as_text_dark():
    # Same locked-in non-text-only band as light mode, re-derived for dark.
    assert _contrast_ratio(AMBER_DARK, PAPER_DARK) < 4.5
    assert _contrast_ratio(AMBER_DARK, PAPER_DARK) >= 3.0


def test_link_color_meets_wcag_aa_contrast_on_paper_dark():
    assert _contrast_ratio(HARBOUR_TEAL_DARK, PAPER_DARK) >= 4.5


# --- Card/pillar-card surface variants -- most badges and body text
# actually render on --surface-card, not the bare page background, so
# checking only against PAPER/PAPER_DARK would miss a real near-miss
# (an earlier --seal-red-dark candidate scored 4.404 against the dark
# card surface -- below AA -- while scoring fine against the page
# background alone). ---


def test_ink_meets_wcag_aa_contrast_on_card_surfaces():
    assert _contrast_ratio(INK, CARD_LIGHT) >= 4.5
    assert _contrast_ratio(INK_DARK, CARD_DARK) >= 4.5


def test_seal_red_meets_wcag_aa_contrast_on_card_surfaces():
    assert _contrast_ratio(SEAL_RED, CARD_LIGHT) >= 4.5
    assert _contrast_ratio(SEAL_RED_DARK, CARD_DARK) >= 4.5


def test_harbour_teal_meets_wcag_aa_contrast_on_card_surfaces():
    assert _contrast_ratio(HARBOUR_TEAL, CARD_LIGHT) >= 4.5
    assert _contrast_ratio(HARBOUR_TEAL_DARK, CARD_DARK) >= 4.5


def test_amber_stays_in_non_text_band_on_card_surfaces():
    assert 3.0 <= _contrast_ratio(AMBER, CARD_LIGHT) < 4.5
    assert 3.0 <= _contrast_ratio(AMBER_DARK, CARD_DARK) < 4.5


def _read_style_css():
    css_path = os.path.join(REPO_ROOT, "pipeline", "site", "static", "style.css")
    return open(css_path, encoding="utf-8").read()


def test_style_css_defines_dark_mode_blocks():
    css = _read_style_css()
    assert "@media (prefers-color-scheme: dark)" in css
    assert '[data-theme="light"]' in css
    assert '[data-theme="dark"]' in css


def test_trajectory_board_uses_theme_invariant_tokens_not_ink_or_paper():
    """Regression lock for a real bug found during the dark-mode design:
    .trajectory-board/.trajectory-row originally hardcoded var(--ink)/
    var(--paper) to get "always-dark board, always-light text" -- which
    would have INVERTED the moment --ink/--paper became theme-reactive.
    Must use the dedicated theme-invariant tokens instead."""
    css = _read_style_css()
    board_start = css.index(".trajectory-board {")
    board_chunk = css[board_start : board_start + 600]
    assert "var(--trajectory-surface)" in board_chunk
    assert "var(--trajectory-ink)" in board_chunk
    assert "var(--ink)" not in board_chunk
    assert "var(--paper)" not in board_chunk


def test_trajectory_board_border_has_real_contrast_against_both_page_backgrounds():
    """Real finding from Fable PM's audit, not caught by the theme-invariant-
    tokens test above: the board's border originally reused
    var(--trajectory-surface) -- the same color as its own background --
    which is a no-op border by construction. That was invisible in light
    mode purely by accident (the fill itself already contrasts 12.37:1
    against the light page), but --trajectory-surface (#132A43) scores
    only 1.16:1 against the dark-mode page background (#0F1E2E) -- both
    near-black navy -- so the whole board nearly vanished into the page
    in dark mode. Fixed to use var(--amber), which independently clears
    the WCAG 1.4.11 non-text/UI-boundary 3:1 threshold against both page
    backgrounds AND against the board's own dark fill, in both themes."""
    css = _read_style_css()
    board_start = css.index(".trajectory-board {")
    board_chunk = css[board_start : board_start + 200]
    assert "border: 2px solid var(--amber)" in board_chunk
    assert "var(--trajectory-surface)" not in css[board_start : board_start + 40]  # not the border

    assert _contrast_ratio(AMBER, PAPER) >= 3.0
    assert _contrast_ratio(AMBER_DARK, PAPER_DARK) >= 3.0
    assert _contrast_ratio(AMBER, INK) >= 3.0  # AMBER vs the board's own (theme-invariant) fill, light-mode token value
    assert _contrast_ratio(AMBER_DARK, INK) >= 3.0  # dark-mode amber vs the same theme-invariant fill

    # Lock in the actual bug: the pre-fix same-color "border" scored well
    # below the 3:1 UI-boundary minimum against the dark-mode page.
    assert _contrast_ratio(INK, PAPER_DARK) < 3.0


def test_no_hardcoded_color_leaks_into_rendered_output(tmp_path):
    """Generalizes the specific #555/#fff/#4a6a4a inline-style bugs found
    during the dark-mode design into a permanent guard: no rendered page
    may hardcode a color that can't respond to a [data-theme] override."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    outputs = _read_all_outputs(tmp_path)
    offenders = []
    for path, html in outputs.items():
        for bad in ("color:#555", "color: #555", "color:#fff", "color: #fff", "#4a6a4a"):
            if bad in html:
                offenders.append((path, bad))
    assert offenders == [], f"hardcoded, non-token color(s) leaked into rendered output: {offenders}"


def test_theme_toggle_button_renders_with_correct_attributes(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    outputs = _content_pages(tmp_path)
    for path, html in outputs.items():
        assert 'id="theme-toggle"' in html, f"theme toggle missing from {path}"
        assert 'aria-pressed="false"' in html
        assert 'aria-label="Toggle dark mode"' in html


# --- Interactive timeline ribbon ---


def test_timeline_ribbon_renders_on_both_current_state_and_timeline_pages(tmp_path):
    build_site(FIXTURE_ROOT, str(tmp_path))
    outputs = _read_all_outputs(tmp_path)
    assert "data-timeline-root" in outputs[os.path.join(str(tmp_path), "hk", "index.html")]
    assert "data-timeline-root" in outputs[os.path.join(str(tmp_path), "hk", "timeline.html")]


def test_timeline_markers_carry_pillar_slot_and_date():
    from pipeline.site.data import build_timeline_events

    cards = [
        {
            "published_date": "2026-01-05",
            "title": "Card A",
            "citations": [{"url": "https://example.invalid/a", "quote": "x"}],
            "pillar": ["stablecoins"],
            "pillar_names": ["Stablecoins"],
            "regulator": "HKMA",
            "status": "verified",
        }
    ]
    events = build_timeline_events(cards, [], {"stablecoins": 0, "exchanges_vatp": 1})
    assert events[0]["pillar_color_slot"] == 0
    assert events[0]["date"] == "2026-01-05"


def test_timeline_events_assign_sentinel_slot_for_empty_pillar_card():
    """Regression test for a Fable audit finding: a card with no pillar
    classification used to get pillar_index.get(pillars[0], 0) if pillars
    else 0 -- i.e. slot 0, the FIRST configured pillar's real color --
    fabricating a classification signal that was never actually made. An
    empty pillar list must get a distinct sentinel slot instead."""
    from pipeline.site.data import build_timeline_events

    cards = [
        {
            "published_date": "2026-01-05",
            "title": "Unclassified card",
            "citations": [{"url": "https://example.invalid/unclassified", "quote": "x"}],
            "pillar": [],
            "pillar_names": [],
            "regulator": "HKMA",
            "status": "verified",
        }
    ]
    events = build_timeline_events(cards, [], {"stablecoins": 0, "exchanges_vatp": 1})
    assert events[0]["pillar_color_slot"] == -1
    assert events[0]["pillar_color_slot"] != 0


def test_timeline_events_assign_sentinel_slot_for_empty_pillar_document():
    """Same fabricated-classification bug, document call site."""
    from pipeline.site.data import build_timeline_events

    documents = [
        {
            "title": "Unclassified document",
            "link": "https://example.invalid/unclassified-doc",
            "published_at": "2026-02-01T00:00:00Z",
            "pillar": [],
            "pillar_names": [],
            "regulator": "HKMA",
        }
    ]
    events = build_timeline_events([], documents, {"stablecoins": 0, "exchanges_vatp": 1})
    assert events[0]["pillar_color_slot"] == -1
    assert events[0]["pillar_color_slot"] != 0


def test_timeline_marker_for_unclassified_card_renders_sentinel_not_pillar_zero(tmp_path):
    """Full-build regression test: card1 (real pillar "stablecoins", real
    slot 0 in the fixture config) stripped of its pillar classification
    must render data-pillar-slot="-1" on the Timeline, never
    data-pillar-slot="0" -- the two views of the same data (JS ribbon
    marker vs. no-JS fallback list) must agree that the item is
    unclassified, not silently disagree with each other."""
    import json
    import shutil

    repo_copy = tmp_path / "repo_unclassified_pillar"
    shutil.copytree(FIXTURE_ROOT, repo_copy)
    card_path = repo_copy / "content" / "hk" / "cards" / "card1.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["pillar"] = []
    card_path.write_text(json.dumps(card), encoding="utf-8")

    output_dir = tmp_path / "output_unclassified_pillar"
    build_site(str(repo_copy), str(output_dir))
    timeline_html = open(output_dir / "hk" / "timeline.html", encoding="utf-8").read()

    marker_start = timeline_html.index("Test verified card")
    marker_chunk = timeline_html[max(0, marker_start - 500) : marker_start]
    assert 'data-pillar-slot="-1"' in marker_chunk
    assert 'data-pillar-slot="0"' not in marker_chunk


def test_style_css_renders_unclassified_slot_as_neutral_not_any_pillar_color():
    """The sentinel slot's CSS rule must carry the "unclassified" styling
    hook (the data-pillar-slot="-1" selector) and must not map to any of
    the 7 real --pillar-color-N tokens -- otherwise the marker would still
    visually read as a real pillar's color."""
    css = _read_style_css()
    assert '.timeline-marker[data-pillar-slot="-1"]' in css
    rule_start = css.index('.timeline-marker[data-pillar-slot="-1"]')
    rule_chunk = css[rule_start : rule_start + 200]
    for n in range(7):
        assert f"var(--pillar-color-{n})" not in rule_chunk


def test_timeline_excludes_undated_documents():
    from pipeline.site.data import build_timeline_events

    documents = [
        {
            "title": "Undated doc",
            "link": "https://example.invalid/undated",
            "published_at": None,
            "pillar": ["stablecoins"],
            "pillar_names": ["Stablecoins"],
            "regulator": "HKMA",
        },
        {
            "title": "Dated doc",
            "link": "https://example.invalid/dated",
            "published_at": "2026-02-01T00:00:00Z",
            "pillar": ["stablecoins"],
            "pillar_names": ["Stablecoins"],
            "regulator": "HKMA",
        },
    ]
    events = build_timeline_events([], documents, {"stablecoins": 0})
    titles = [e["title"] for e in events]
    assert "Dated doc" in titles
    assert "Undated doc" not in titles


def test_timeline_events_sorted_ascending():
    from pipeline.site.data import build_timeline_events

    cards = [
        {
            "published_date": "2026-03-01",
            "title": "Newer",
            "citations": [{"url": "https://example.invalid/newer", "quote": "x"}],
            "pillar": ["stablecoins"],
            "pillar_names": [],
            "regulator": "HKMA",
            "status": "verified",
        },
        {
            "published_date": "2026-01-01",
            "title": "Older",
            "citations": [{"url": "https://example.invalid/older", "quote": "x"}],
            "pillar": ["stablecoins"],
            "pillar_names": [],
            "regulator": "HKMA",
            "status": "verified",
        },
    ]
    events = build_timeline_events(cards, [], {"stablecoins": 0})
    assert [e["title"] for e in events] == ["Older", "Newer"]


def test_current_state_timeline_is_capped_but_full_timeline_page_is_not():
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        repo_copy = os.path.join(tmp, "repo")
        shutil.copytree(FIXTURE_ROOT, repo_copy)
        # Fixture ships 2 cards + 1 dated document = 3 events total, under
        # the 40-item cap -- this test only needs to confirm the cap
        # mechanism produces a smaller-or-equal count on the Current State
        # page's hero ribbon than the uncapped Timeline page, never a
        # larger one.
        output_dir = os.path.join(tmp, "out")
        build_site(repo_copy, output_dir)
        current_state_html = open(os.path.join(output_dir, "hk", "index.html"), encoding="utf-8").read()
        timeline_html = open(os.path.join(output_dir, "hk", "timeline.html"), encoding="utf-8").read()
        assert current_state_html.count("data-pillar-slot") <= timeline_html.count("data-pillar-slot")


def test_timeline_ribbon_marker_and_fallback_carry_unverified_status(tmp_path):
    """card2 in the fixture (status "unverified") is the only card event --
    its ribbon <a class="timeline-marker"> must carry data-status, and its
    no-JS fallback <li> must show the same conditional "Unverified" label.
    Both checks look at the FIRST two occurrences of the title (the ribbon
    marker, then the fallback list entry) -- the third, later occurrence is
    the full <article class="card">, already covered by
    test_unverified_card_shows_unverified_badge_with_text_label above."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    timeline_html = open(os.path.join(str(tmp_path), "hk", "timeline.html"), encoding="utf-8").read()

    marker_start = timeline_html.index("Test unverified card")
    marker_chunk = timeline_html[max(0, marker_start - 500) : marker_start]
    assert 'data-status="unverified"' in marker_chunk

    fallback_start = timeline_html.index("Test unverified card", marker_start + 1)
    fallback_end = timeline_html.index("</li>", fallback_start)
    fallback_chunk = timeline_html[fallback_start:fallback_end]
    assert "badge-unverified" in fallback_chunk
    assert "Unverified" in fallback_chunk


def test_timeline_document_marker_and_fallback_have_no_status_badge(tmp_path):
    """doc1 in the fixture is a document event (status is always None for
    documents) -- neither its ribbon marker nor its fallback <li> should
    carry any status attribute or badge, unlike card events."""
    build_site(FIXTURE_ROOT, str(tmp_path))
    timeline_html = open(os.path.join(str(tmp_path), "hk", "timeline.html"), encoding="utf-8").read()

    marker_start = timeline_html.index("Test document title")
    marker_chunk = timeline_html[max(0, marker_start - 500) : marker_start]
    assert "data-status" not in marker_chunk

    fallback_start = timeline_html.index("Test document title", marker_start + 1)
    fallback_end = timeline_html.index("</li>", fallback_start)
    fallback_chunk = timeline_html[fallback_start:fallback_end]
    assert "badge-unverified" not in fallback_chunk


# --- window_sort_key -- trajectory's date_or_window sort key ---


def test_window_sort_key_orders_exact_dates_chronologically():
    from pipeline.site.data import window_sort_key

    keys = sorted(["2026-03-01", "2026-01-15", "2025-12-31"], key=window_sort_key)
    assert keys == ["2025-12-31", "2026-01-15", "2026-03-01"]


def test_window_sort_key_orders_year_month():
    from pipeline.site.data import window_sort_key

    keys = sorted(["2026-11", "2026-02", "2025-06"], key=window_sort_key)
    assert keys == ["2025-06", "2026-02", "2026-11"]


def test_window_sort_key_orders_quarters_both_word_orders():
    from pipeline.site.data import window_sort_key

    keys = sorted(["Q4 2026", "Q1 2026", "2026 Q2"], key=window_sort_key)
    assert keys == ["Q1 2026", "2026 Q2", "Q4 2026"]


def test_window_sort_key_orders_halves_both_word_orders():
    from pipeline.site.data import window_sort_key

    keys = sorted(["H2 2026", "2026 H1"], key=window_sort_key)
    assert keys == ["2026 H1", "H2 2026"]


def test_window_sort_key_orders_bare_years():
    from pipeline.site.data import window_sort_key

    keys = sorted(["2027", "2025", "2026"], key=window_sort_key)
    assert keys == ["2025", "2026", "2027"]


def test_window_sort_key_interleaves_mixed_precision_by_start_of_window():
    """A quarter/half/year all anchor to the FIRST day of their window, so
    e.g. an exact date early in a quarter still sorts before that same
    quarter's own coarser entry, and different granularities interleave
    into one sensible order rather than forming separate un-comparable
    bands."""
    from pipeline.site.data import window_sort_key

    items = ["2026", "H1 2026", "Q1 2026", "2026-02-01", "2026-01"]
    keys = sorted(items, key=window_sort_key)
    # 2026-01 (Jan 1) == Q1 2026 (Jan 1) == H1 2026 (Jan 1) == 2026 (Jan 1)
    # for sort purposes (stable sort keeps their relative input order), all
    # of which sort before 2026-02-01 (Feb 1).
    assert keys.index("2026-02-01") == len(items) - 1


def test_window_sort_key_unparseable_fallback_sorts_after_all_parseable_entries():
    """"mid-2026" and "TBC" match none of the recognized formats -- the
    deliberate fallback case (see window_sort_key's docstring): never
    guessed at, always sorted after every parseable entry, alphabetically
    among themselves."""
    from pipeline.site.data import window_sort_key

    items = ["2026", "TBC", "mid-2026", "2025-01-01"]
    keys = sorted(items, key=window_sort_key)
    # Unparseable entries ("TBC", "mid-2026") both sort after every
    # parseable entry, and alphabetically (case-insensitively) among
    # themselves: "mid-2026" before "TBC" ('m' < 't').
    assert keys == ["2025-01-01", "2026", "mid-2026", "TBC"]


def test_window_sort_key_is_pure_and_never_raises_on_arbitrary_input():
    from pipeline.site.data import window_sort_key

    for value in ("", "not a date at all", "2026-13-40", "  2026  ", None):
        key = window_sort_key(value)  # must not raise
        assert isinstance(key, tuple)
    # Purity: same input always produces the identical key.
    assert window_sort_key("2026-05-01") == window_sort_key("2026-05-01")
