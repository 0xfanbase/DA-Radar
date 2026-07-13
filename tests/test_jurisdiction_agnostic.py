"""Proves the pipeline is jurisdiction-agnostic (spec §8).

Checks, in order: (1) the full watcher pipeline runs correctly against a
fabricated, non-Hong-Kong jurisdiction config; (1b) the same, run for a
SECOND, independent fabricated jurisdiction, into its own namespaced
fixture paths alongside the first, to prove the watcher doesn't leak
between jurisdictions run side by side; (2) no module under pipeline/
contains a literal Hong-Kong-specific string; (2b) the same idea, scoped
to pipeline/site/templates/*.html and pipeline/site/static/*.js, for the
site's own hardcoded identity strings; (3) the registry-model site-data
loader (pipeline/site/data.py's load_global_data() / load_jurisdiction_data(),
see that module's docstring) isolates two fabricated jurisdictions'
content with no cross-contamination. Passing (1)/(1b)/(3) without (2)/(2b)
would mean the code merely *happens* to work for a second jurisdiction
while still being HK-flavored (or site-identity-flavored) inside -- all
of these must hold together.

BANNED_LITERALS (the pipeline/ scan) is GENERATED from
config/jurisdictions/*.json and config/site.json themselves, at test-
collection time, rather than hand-maintained -- see
_collect_pipeline_banned_literals()'s docstring for exactly what is (and
is deliberately NOT) included. A future jurisdiction 9 gets its own real
config/jurisdictions/<id>.json file as part of onboarding it, which
automatically extends this scan; no test-file edit is needed.
"""
from __future__ import annotations

import glob
import json
import os
import re

from pipeline.watcher.run import run
from tests.conftest import FREEDONIA_JURISDICTION_PATH, REPO_ROOT, SYLVANIA_JURISDICTION_PATH

REGISTRY_TWO_JURISDICTIONS_FIXTURE_ROOT = os.path.join(
    REPO_ROOT, "tests", "fixtures", "registry_two_jurisdictions"
)

# Site-identity strings due to be renamed in this migration's final
# ("identity-rename") step -- kept as a small, explicit, hand-maintained
# list, deliberately NOT generated the way BANNED_LITERALS is, because
# these are not facts that live in config/jurisdictions/*.json at all;
# they're literal product-naming strings baked into templates/static
# ahead of that rename. See test_site_templates_and_static_js_contain_
# no_hardcoded_site_identity_strings's docstring for why this test is
# added now, in a currently-failing (red) state, rather than deferred.
TEMPLATE_STATIC_BANNED_LITERALS = ["hk digital asset radar", "hkdar"]


def _collect_pipeline_banned_literals(repo_root: str) -> list:
    """Generates the banned-literal list for the pipeline/ scan from
    config/jurisdictions/*.json and config/site.json themselves, instead
    of a hand-maintained list -- so a future jurisdiction's real config
    file automatically extends this scan without a test-file edit.

    Included, from every config/jurisdictions/*.json file that actually
    exists on disk:
      - the jurisdiction's full name (config["jurisdiction_name"], e.g.
        "Hong Kong")
      - every regulator's id (config["regulators"][*]["id"], e.g. "sfc",
        "hkma", "fstb" -- including regulators with no live feeds yet;
        the generator does not special-case "seeded" regulators)
      - every regulator's official_domains entries verbatim (e.g.
        "www.sfc.hk"), PLUS the same domain with a leading "www." stripped
        (e.g. "sfc.hk"), so a citation that omits the "www." still trips
        the scan.
    Also included, from config/site.json's own jurisdictions[] registry:
      - the display name of every jurisdiction that has a real config
        file wired up (config != null) -- currently redundant with the
        jurisdiction_name above (both come from "hk" today) but not
        necessarily once a jurisdiction's registry entry and its config
        file's internal name ever diverge.

    Deliberately EXCLUDED:
      - each jurisdiction's own bare, short jurisdiction_id (e.g. "hk")
        in isolation. That id is legitimately used throughout /pipeline
        today as a parameterized CLI default and docstring example
        (jurisdiction="hk" argparse defaults, "config/jurisdictions/
        hk.json" / "data/hk/ledger.json" path examples, "e.g. 'hk'" help
        text) precisely BECAUSE the CLI takes --jurisdiction as a real,
        overridable parameter -- banning it would flag the
        parameterization mechanism itself, not a portability violation.
        The original hand-curated BANNED_LITERALS list made this same
        exclusion (it never included bare "hk").
      - "planned" registry entries in config/site.json that have no real
        config file (config: null, e.g. "us", "eu", "uk" as of this
        writing). They carry no real regulator/domain facts to leak, and
        several of their bare two/three-letter ids are common English
        substrings ("us" as in "US$", the pronoun "us") that would
        false-positive constantly for zero actual portability signal.
        Once a jurisdiction gets a real config file its facts are picked
        up via the config/jurisdictions/*.json glob above -- getting a
        real config file IS "being wired up" for this scan's purposes.
    """
    literals = set()

    jurisdictions_dir = os.path.join(repo_root, "config", "jurisdictions")
    configured_ids = set()
    for config_path in sorted(glob.glob(os.path.join(jurisdictions_dir, "*.json"))):
        with open(config_path, "r", encoding="utf-8") as fh:
            config = json.load(fh)
        configured_ids.add(config.get("jurisdiction_id"))
        jurisdiction_name = config.get("jurisdiction_name")
        if jurisdiction_name:
            literals.add(jurisdiction_name)
        for regulator in config.get("regulators", []):
            regulator_id = regulator.get("id")
            if regulator_id:
                literals.add(regulator_id)
            for domain in regulator.get("official_domains", []) or []:
                literals.add(domain)
                if domain.startswith("www."):
                    literals.add(domain[len("www.") :])

    site_config_path = os.path.join(repo_root, "config", "site.json")
    if os.path.exists(site_config_path):
        with open(site_config_path, "r", encoding="utf-8") as fh:
            site_config = json.load(fh)
        for jurisdiction in site_config.get("jurisdictions", []):
            if not jurisdiction.get("config"):
                continue
            name = jurisdiction.get("name")
            if name:
                literals.add(name)

    return sorted(literals)


BANNED_LITERALS = _collect_pipeline_banned_literals(REPO_ROOT)


def _find_banned_literal_hits(paths: list, literals: list) -> list:
    """Scans each file in `paths` for any of `literals` as a whole-word
    (or whole-phrase, for multi-word literals) case-insensitive match.
    Word-boundary regex so a short/generic fragment (a 3-letter regulator
    id, a bare domain label) doesn't false-positive on an innocuous
    substring inside an unrelated word. Returns (path, literal) tuples,
    one per hit; used by both the real scans below and their positive-
    control tests, so the positive controls exercise the exact same
    detection code path rather than a re-implementation of it."""
    offenders = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read().lower()
        for literal in literals:
            pattern = r"\b" + re.escape(literal.lower()) + r"\b"
            if re.search(pattern, text):
                offenders.append((path, literal))
    return offenders


def test_freedonia_config_runs_through_the_real_pipeline(tmp_path, requests_mock, fixture_bytes):
    with open(FREEDONIA_JURISDICTION_PATH, "r", encoding="utf-8") as fh:
        config = json.load(fh)

    feed = config["regulators"][0]["feeds"][0]
    requests_mock.get(feed["url"], content=fixture_bytes("freedonia_feed_day1.xml"))

    ledger_path = str(tmp_path / "ledger.json")
    queue_path = str(tmp_path / "queue.json")
    cache_path = str(tmp_path / "cache" / "etags.json")
    document_library_path = str(tmp_path / "document_library.json")

    summary = run(FREEDONIA_JURISDICTION_PATH, ledger_path, queue_path, cache_path, document_library_path)

    assert summary.feeds_ok == 1
    assert summary.items_new == 2

    with open(queue_path) as fh:
        queue_doc = json.load(fh)
    assert len(queue_doc["items"]) == 2
    assert {i["source_id"] for i in queue_doc["items"]} == {"ffa"}

    # The document library is jurisdiction-portable too: Freedonia's own
    # pillar_keywords (not Hong Kong's) drive its pillar tagging, and its
    # feed "kind" (not any HK-specific type vocabulary) drives its type.
    with open(document_library_path) as fh:
        document_library_doc = json.load(fh)
    documents_by_hash = {d["item_hash"]: d for d in document_library_doc["documents"]}
    assert len(documents_by_hash) == 2
    for doc in documents_by_hash.values():
        assert doc["regulator"] == "FFA"
        assert doc["type"] == "press_releases"
    pillars_seen = {tuple(d["pillar"]) for d in documents_by_hash.values()}
    assert pillars_seen == {("freedonia_pillar_one",), ("freedonia_pillar_two",)}

    # Re-run is idempotent for this jurisdiction too.
    requests_mock.get(feed["url"], content=fixture_bytes("freedonia_feed_day1.xml"))
    summary2 = run(FREEDONIA_JURISDICTION_PATH, ledger_path, queue_path, cache_path, document_library_path)
    assert summary2.items_new == 0
    assert summary2.ledger_changed is False
    assert summary2.document_library_changed is False


def test_freedonia_output_validates_against_the_same_schemas(tmp_path, requests_mock, fixture_bytes):
    from jsonschema import Draft202012Validator

    with open(FREEDONIA_JURISDICTION_PATH, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    feed = config["regulators"][0]["feeds"][0]
    requests_mock.get(feed["url"], content=fixture_bytes("freedonia_feed_day1.xml"))

    ledger_path = str(tmp_path / "ledger.json")
    queue_path = str(tmp_path / "queue.json")
    document_library_path = str(tmp_path / "document_library.json")
    run(
        FREEDONIA_JURISDICTION_PATH,
        ledger_path,
        queue_path,
        str(tmp_path / "cache" / "etags.json"),
        document_library_path,
    )

    schemas_dir = os.path.join(REPO_ROOT, "pipeline", "schemas")
    with open(os.path.join(schemas_dir, "ledger.json")) as fh:
        ledger_schema = json.load(fh)
    with open(os.path.join(schemas_dir, "queue.json")) as fh:
        queue_schema = json.load(fh)
    with open(os.path.join(schemas_dir, "document_library.json")) as fh:
        document_library_schema = json.load(fh)

    with open(ledger_path) as fh:
        Draft202012Validator(ledger_schema).validate(json.load(fh))
    with open(queue_path) as fh:
        Draft202012Validator(queue_schema).validate(json.load(fh))
    with open(document_library_path) as fh:
        Draft202012Validator(document_library_schema).validate(json.load(fh))


def test_two_fabricated_jurisdictions_run_through_the_watcher_without_cross_contamination(
    tmp_path, requests_mock, fixture_bytes
):
    """Freedonia and Sylvania -- two independent fabricated jurisdictions --
    run through the SAME real watcher entrypoint, one right after the
    other, into their own namespaced fixture paths (tmp_path/freedonia/...
    and tmp_path/sylvania/...), the same layout the real repo uses
    (data/<jurisdiction_id>/...). Proves the watcher's per-jurisdiction
    isolation isn't an accident of only ever running one jurisdiction at a
    time in these tests: neither run's queue or document library contains
    so much as a trace of the other's regulator id or pillar ids."""
    with open(FREEDONIA_JURISDICTION_PATH, "r", encoding="utf-8") as fh:
        freedonia_config = json.load(fh)
    with open(SYLVANIA_JURISDICTION_PATH, "r", encoding="utf-8") as fh:
        sylvania_config = json.load(fh)

    freedonia_feed = freedonia_config["regulators"][0]["feeds"][0]
    sylvania_feed = sylvania_config["regulators"][0]["feeds"][0]
    requests_mock.get(freedonia_feed["url"], content=fixture_bytes("freedonia_feed_day1.xml"))
    requests_mock.get(sylvania_feed["url"], content=fixture_bytes("sylvania_feed_day1.xml"))

    freedonia_root = tmp_path / "freedonia"
    sylvania_root = tmp_path / "sylvania"

    freedonia_summary = run(
        FREEDONIA_JURISDICTION_PATH,
        str(freedonia_root / "ledger.json"),
        str(freedonia_root / "queue.json"),
        str(freedonia_root / "cache" / "etags.json"),
        str(freedonia_root / "document_library.json"),
    )
    sylvania_summary = run(
        SYLVANIA_JURISDICTION_PATH,
        str(sylvania_root / "ledger.json"),
        str(sylvania_root / "queue.json"),
        str(sylvania_root / "cache" / "etags.json"),
        str(sylvania_root / "document_library.json"),
    )

    assert freedonia_summary.items_new == 2
    assert sylvania_summary.items_new == 2

    with open(freedonia_root / "queue.json") as fh:
        freedonia_queue = json.load(fh)
    with open(sylvania_root / "queue.json") as fh:
        sylvania_queue = json.load(fh)

    assert {i["source_id"] for i in freedonia_queue["items"]} == {"ffa"}
    assert {i["source_id"] for i in sylvania_queue["items"]} == {"sfa"}
    # Cross-contamination guard: neither jurisdiction's namespaced output
    # contains a trace of the OTHER's regulator id.
    assert "sfa" not in json.dumps(freedonia_queue)
    assert "ffa" not in json.dumps(sylvania_queue)

    with open(freedonia_root / "document_library.json") as fh:
        freedonia_docs = json.load(fh)
    with open(sylvania_root / "document_library.json") as fh:
        sylvania_docs = json.load(fh)
    freedonia_pillars = {tuple(d["pillar"]) for d in freedonia_docs["documents"]}
    sylvania_pillars = {tuple(d["pillar"]) for d in sylvania_docs["documents"]}
    assert freedonia_pillars == {("freedonia_pillar_one",), ("freedonia_pillar_two",)}
    assert sylvania_pillars == {("sylvania_pillar_one",), ("sylvania_pillar_two",)}
    assert freedonia_pillars.isdisjoint(sylvania_pillars)


def test_load_jurisdiction_data_isolates_two_fabricated_jurisdictions_with_no_cross_contamination():
    """P6 scope note: pipeline/site/generate.py's build_site() still calls
    the single-jurisdiction load_site_data() scaffolding (see that
    function's own docstring in pipeline/site/data.py) for exactly one
    hardcoded jurisdiction id at a time -- real multi-jurisdiction PAGE
    rendering doesn't exist until P7. So this test does NOT build_site()
    and diff rendered HTML across jurisdictions (there is no such HTML to
    diff yet); it targets what P6 actually shipped: the split of
    pipeline/site/data.py into load_global_data() (the site-wide registry:
    config/site.json, the unified pillar/seal vocabulary) and
    load_jurisdiction_data() (everything scoped to one jurisdiction id,
    content/<id>/... and data/<id>/..., validated against that SAME
    global_data). It runs a fixture repo
    (tests/fixtures/registry_two_jurisdictions/) that registers ONLY two
    fabricated jurisdictions -- Freedonia and Sylvania -- loads each one's
    data independently off the one shared global_data, and asserts each
    jurisdiction's own per-jurisdiction data loads correctly AND that
    neither jurisdiction's cards/pillar-states/trajectory/documents/
    orientation text ever appears in the other's loaded result -- proving
    the loader is genuinely registry-driven (keyed strictly off the
    jurisdiction_id argument) rather than accidentally reading ambient or
    leftover state."""
    from pipeline.site.data import load_global_data, load_jurisdiction_data

    global_data = load_global_data(REGISTRY_TWO_JURISDICTIONS_FIXTURE_ROOT)
    assert {j["id"] for j in global_data["site_config"]["jurisdictions"]} == {"freedonia", "sylvania"}

    freedonia = load_jurisdiction_data(REGISTRY_TWO_JURISDICTIONS_FIXTURE_ROOT, "freedonia", global_data)
    sylvania = load_jurisdiction_data(REGISTRY_TWO_JURISDICTIONS_FIXTURE_ROOT, "sylvania", global_data)

    # Each jurisdiction's own content actually loaded.
    assert [c["title"] for c in freedonia["cards"]] == ["Freedonia Financial Authority issues first notice"]
    assert [c["title"] for c in sylvania["cards"]] == ["Sylvania Financial Authority issues first bulletin"]
    assert [d["title"] for d in freedonia["documents"]] == ["Freedonia document title"]
    assert [d["title"] for d in sylvania["documents"]] == ["Sylvania document title"]

    # Both validated against the SAME unified pillar vocabulary (proving
    # isolation is about content *scoping*, not two independent
    # vocabularies that simply never happened to collide).
    assert freedonia["pillar_states"][0]["pillar_name"] == "Test Pillar Alpha"
    assert sylvania["pillar_states"][0]["pillar_name"] == "Test Pillar Alpha"

    # Cross-contamination guard, both directions: dump each loaded result
    # to text and confirm the OTHER jurisdiction's identifying strings
    # never appear in it.
    freedonia_text = json.dumps(freedonia)
    sylvania_text = json.dumps(sylvania)

    freedonia_markers = ["Freedonia", "FFA", "freedonia-card1", "freedonia-doc1"]
    sylvania_markers = ["Sylvania", "SFA", "sylvania-card1", "sylvania-doc1"]

    for marker in sylvania_markers:
        assert marker not in freedonia_text, f"Sylvania marker {marker!r} leaked into Freedonia's loaded data"
    for marker in freedonia_markers:
        assert marker not in sylvania_text, f"Freedonia marker {marker!r} leaked into Sylvania's loaded data"


def test_pipeline_source_contains_no_hardcoded_jurisdiction_strings():
    """Static scan: config/jurisdictions/*.json is the only place a real
    jurisdiction's facts may live. Case-insensitive, word-boundary
    matched; includes domain fragments, not just regulator names, per
    Fable PM directive. See BANNED_LITERALS / _collect_pipeline_banned_
    literals() at module scope for exactly what's generated and why."""
    pipeline_dir = os.path.join(REPO_ROOT, "pipeline")
    paths = []
    for dirpath, _dirnames, filenames in os.walk(pipeline_dir):
        if os.path.join(pipeline_dir, "schemas") in dirpath:
            # Schemas are checked in test_schemas.py for enum leakage;
            # their free-text *description* fields may legitimately mention
            # "Hong Kong" or "SFC" as documentation/examples.
            continue
        for filename in filenames:
            if filename.endswith(".py"):
                paths.append(os.path.join(dirpath, filename))

    offenders = _find_banned_literal_hits(paths, BANNED_LITERALS)
    assert offenders == [], f"jurisdiction-specific literals found in pipeline/: {offenders}"


def test_pipeline_scan_actually_catches_a_planted_literal(tmp_path):
    """Positive control: proves the scan above isn't vacuously passing --
    plant a real HK-specific-shaped literal into a throwaway file and
    confirm the same detection helper the real scan uses flags it."""
    planted = tmp_path / "planted.py"
    planted.write_text('HOMEPAGE = "https://www.sfc.hk/en"\n', encoding="utf-8")

    offenders = _find_banned_literal_hits([str(planted)], BANNED_LITERALS)

    assert offenders != []
    assert any(literal in ("sfc", "sfc.hk", "www.sfc.hk") for _, literal in offenders)


def test_banned_literals_are_generated_not_vacuous():
    """Sanity-checks the generator itself: real regulator ids, a
    multi-word jurisdiction name, and a domain fragment are all present
    (proving generation actually walked config/jurisdictions/*.json and
    config/site.json, not silently produced an empty/trivial list), and
    the bare 2-letter jurisdiction id is deliberately absent (see
    _collect_pipeline_banned_literals's docstring for why)."""
    assert "sfc" in BANNED_LITERALS
    assert "hkma" in BANNED_LITERALS
    assert "Hong Kong" in BANNED_LITERALS
    assert "www.sfc.hk" in BANNED_LITERALS
    assert "sfc.hk" in BANNED_LITERALS
    # fstb has no live feeds yet -- the generator doesn't special-case
    # "seeded" regulators, it reads every regulator id in the config.
    assert "fstb" in BANNED_LITERALS
    assert "hk" not in BANNED_LITERALS


def test_site_templates_and_static_js_contain_no_hardcoded_site_identity_strings():
    """Extends the banned-literal scan to pipeline/site/templates/*.html
    and pipeline/site/static/*.js, where the site's own product-identity
    string ("HK Digital Asset Radar") and an abbreviation of it baked into
    a client-side localStorage key ("hkdar-theme") are currently
    hardcoded -- separately from, and for a different reason than, the
    pipeline/ scan above (that scan is about jurisdiction FACTS leaking
    outside config/; this one is about the site's own NAME not yet being
    jurisdiction/deployment-portable, which is a distinct, later step of
    this same migration: the "identity-rename").

    THIS TEST IS EXPECTED TO FAIL RIGHT NOW, and is deliberately not
    marked xfail/skip. Two ways existed to add it: (a) scope its own
    small, explicit banned-literal list to just the specific strings due
    to be renamed (TEMPLATE_STATIC_BANNED_LITERALS) and add it now, red,
    as a concrete signal that self-resolves the moment the identity-rename
    step lands; or (b) hold off adding it at all until after confirming
    that rename step will land before this workflow's Final Check phase.
    (a) was chosen: (b) would mean either doing the identity-rename here
    (out of scope -- it's a separate, later step of this migration, not
    part of the registry-model test upgrade this task covers) or silently
    not fulfilling this instruction in this session at all, and it makes
    the test's existence depend on cross-session timing/coordination this
    test file can't verify for itself. A currently-red, narrowly-scoped,
    non-xfail'd test is a known, intentional pattern already used
    elsewhere in this suite for "not yet fixed, must not be silently
    forgotten" states -- e.g. test_id_leak_check_actually_catches_a_
    planted_identifier in test_site_generate.py is a positive control for
    exactly the same kind of leak-detection logic. Whoever runs the
    identity-rename step will see this go green as a direct confirmation
    it actually reached every file, not just the ones a human happened to
    remember."""
    templates_dir = os.path.join(REPO_ROOT, "pipeline", "site", "templates")
    static_dir = os.path.join(REPO_ROOT, "pipeline", "site", "static")

    paths = sorted(glob.glob(os.path.join(templates_dir, "*.html")))
    paths += sorted(glob.glob(os.path.join(static_dir, "*.js")))
    assert paths, "expected at least one template and one static .js file to scan"

    offenders = _find_banned_literal_hits(paths, TEMPLATE_STATIC_BANNED_LITERALS)
    assert offenders == [], (
        "site-identity literal(s) due to be renamed still found in templates/static: "
        f"{offenders} -- expected until the identity-rename step of this migration lands"
    )


def test_template_static_scan_actually_catches_a_planted_literal(tmp_path):
    """Positive control for the scan above, same pattern as
    test_pipeline_scan_actually_catches_a_planted_literal."""
    planted = tmp_path / "planted.html"
    planted.write_text("<title>HK Digital Asset Radar</title>\n", encoding="utf-8")

    offenders = _find_banned_literal_hits([str(planted)], TEMPLATE_STATIC_BANNED_LITERALS)

    assert offenders != []
    assert any(literal == "hk digital asset radar" for _, literal in offenders)


def test_pillar_state_schema_has_no_hardcoded_pillar_enum():
    """Baking HK's 7 pillar names into the schema itself would violate
    portability even though the scan above only checks .py files."""
    schema_path = os.path.join(REPO_ROOT, "pipeline", "schemas", "pillar_state.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    for field in ("pillar", "regulator", "status_seal"):
        prop = schema["properties"][field]
        assert "enum" not in prop, f"{field} must stay free-text, not an HK-baked enum"
