"""Proves the pipeline is jurisdiction-agnostic (spec §8).

Two independent checks: (1) the full watcher pipeline runs correctly
against a fabricated, non-Hong-Kong jurisdiction config; (2) no module
under pipeline/ contains a literal Hong-Kong-specific string. Passing (1)
without (2) would mean the code merely *happens* to work for a second
jurisdiction while still being HK-flavored inside -- both must hold.
"""
from __future__ import annotations

import json
import os
import re

from pipeline.watcher.run import run
from tests.conftest import FREEDONIA_JURISDICTION_PATH, REPO_ROOT

BANNED_LITERALS = ["sfc", "hkma", "hong kong", "sfc.hk", "hkma.gov"]


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


def test_pipeline_source_contains_no_hardcoded_jurisdiction_strings():
    """Static scan: config/jurisdiction.json is the only place HK-specific
    facts may live. Case-insensitive; includes domain fragments, not just
    the regulator names, per Fable PM directive."""
    pipeline_dir = os.path.join(REPO_ROOT, "pipeline")
    offenders = []

    for dirpath, _dirnames, filenames in os.walk(pipeline_dir):
        if os.path.join(pipeline_dir, "schemas") in dirpath:
            # Schemas are checked in test_schemas.py for enum leakage;
            # their free-text *description* fields may legitimately mention
            # "Hong Kong" or "SFC" as documentation/examples.
            continue
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(dirpath, filename)
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read().lower()
            for literal in BANNED_LITERALS:
                if re.search(re.escape(literal), text):
                    offenders.append((path, literal))

    assert offenders == [], f"jurisdiction-specific literals found in pipeline/: {offenders}"


def test_pillar_state_schema_has_no_hardcoded_pillar_enum():
    """Baking HK's 7 pillar names into the schema itself would violate
    portability even though the scan above only checks .py files."""
    schema_path = os.path.join(REPO_ROOT, "pipeline", "schemas", "pillar_state.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    for field in ("pillar", "regulator", "status_seal"):
        prop = schema["properties"][field]
        assert "enum" not in prop, f"{field} must stay free-text, not an HK-baked enum"
