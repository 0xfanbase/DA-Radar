"""Every schema under pipeline/schemas/ must be valid JSON Schema
draft 2020-12, and must correctly accept a valid instance while rejecting
an invalid one.
"""
from __future__ import annotations

import glob
import json
import os

import pytest
from jsonschema import Draft202012Validator, ValidationError

from tests.conftest import REPO_ROOT

SCHEMAS_DIR = os.path.join(REPO_ROOT, "pipeline", "schemas")


def _all_schema_paths():
    return sorted(glob.glob(os.path.join(SCHEMAS_DIR, "**", "*.json"), recursive=True))


@pytest.mark.parametrize("schema_path", _all_schema_paths())
def test_schema_is_valid_json_schema(schema_path):
    with open(schema_path) as fh:
        schema = json.load(fh)
    Draft202012Validator.check_schema(schema)


def test_ledger_schema_accepts_valid_and_rejects_invalid_instance():
    with open(os.path.join(SCHEMAS_DIR, "ledger.json")) as fh:
        schema = json.load(fh)

    valid = {
        "schema_version": 1,
        "jurisdiction_id": "hk",
        "generated_at": "2026-01-01T00:00:00Z",
        "items": {
            "abc": {
                "item_hash": "abc",
                "source_id": "x",
                "feed_id": "y",
                "guid": None,
                "link": "https://example.invalid/1",
                "title": "t",
                "summary": "s",
                "published_at": "2026-01-01T00:00:00Z",
                "raw_published": "raw",
                "content_hash": "c",
                "first_seen": "2026-01-01T00:00:00Z",
                "status": "queued",
                "card_id": None,
            }
        },
    }
    Draft202012Validator(schema).validate(valid)

    invalid = dict(valid)
    del invalid["schema_version"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)


def test_queue_schema_accepts_valid_and_rejects_invalid_instance():
    with open(os.path.join(SCHEMAS_DIR, "queue.json")) as fh:
        schema = json.load(fh)

    valid = {
        "schema_version": 1,
        "jurisdiction_id": "hk",
        "generated_at": "2026-01-01T00:00:00Z",
        "items": [
            {
                "item_hash": "abc",
                "source_id": "x",
                "feed_id": "y",
                "title": "t",
                "link": "https://example.invalid/1",
                "summary": "s",
                "published_at": "2026-01-01T00:00:00Z",
                "status": "queued",
            }
        ],
    }
    Draft202012Validator(schema).validate(valid)

    invalid = json.loads(json.dumps(valid))
    invalid["items"][0]["status"] = "not-a-real-status"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)


def test_card_schema_accepts_valid_and_rejects_missing_citation():
    with open(os.path.join(SCHEMAS_DIR, "card.json")) as fh:
        schema = json.load(fh)

    valid = {
        "schema_version": 1,
        "id": "card-1",
        "jurisdiction_id": "hk",
        "published_date": "2026-01-01",
        "regulator": "Example Regulator",
        "pillar": ["example_pillar"],
        "type": "circular",
        "title": "t",
        "summary": "s",
        "why_it_matters": "w",
        "citations": [{"url": "https://example.invalid/doc", "quote": "a short quote"}],
        "status": "verified",
        "generated_at": "2026-01-01T00:00:00Z",
        "model": "test-model",
    }
    Draft202012Validator(schema).validate(valid)

    invalid = json.loads(json.dumps(valid))
    invalid["citations"] = []
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)


def test_pillar_state_schema_accepts_valid_instance():
    with open(os.path.join(SCHEMAS_DIR, "pillar_state.json")) as fh:
        schema = json.load(fh)

    valid = {
        "schema_version": 1,
        "pillar": "example_pillar",
        "status_seal": "in_force",
        "regulator": "Example Regulator",
        "instruments": ["Example Ordinance"],
        "standing_summary": "s",
        "last_changed": "2026-01-01",
        "key_links": [{"label": "Example", "url": "https://example.invalid"}],
        "open_items": [],
        "generated_at": "2026-01-01T00:00:00Z",
        "model": "test-model",
        "status": "unverified",
    }
    Draft202012Validator(schema).validate(valid)


def test_watch_status_schema_accepts_valid_and_rejects_invalid_instance():
    with open(os.path.join(SCHEMAS_DIR, "watch_status.json")) as fh:
        schema = json.load(fh)

    valid = {
        "schema_version": 1,
        "jurisdiction_id": "hk",
        "generated_at": "2026-01-01T00:00:00Z",
        "feeds": {
            "fincen_news": {
                "source_id": "fincen",
                "mechanism": "html_diff",
                "status": "structure_error",
                "status_since": "2026-07-09T01:35:00Z",
                "last_error": "item_selector 'div.views-row' matched 0 elements (HTTP 200)",
            },
            "sfc_press_releases": {
                "source_id": "sfc",
                "mechanism": "rss",
                "status": "ok",
                "status_since": "2026-01-01T00:00:00Z",
                "last_error": None,
            },
        },
    }
    Draft202012Validator(schema).validate(valid)

    invalid = json.loads(json.dumps(valid))
    invalid["feeds"]["fincen_news"]["status"] = "not-a-real-status"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)
