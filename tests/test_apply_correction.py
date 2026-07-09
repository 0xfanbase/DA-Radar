"""Tests for pipeline.ci.apply_correction -- always human-initiated (CLI
args / workflow_dispatch inputs supplied by a person), never something the
audit loop or any other automated process triggers on its own.
"""
from __future__ import annotations

import json
import os

from pipeline.ci.apply_correction import (
    append_correction_record,
    apply_correction_to_card,
    build_correction_record,
    main,
)


def test_build_correction_record_matches_schema_shape():
    correction = build_correction_record(
        correction_id="corr-1",
        card_id="card1",
        corrected_at="2026-02-01T00:00:00Z",
        correction_note="The stated capital requirement was wrong; corrected per source.",
        fields_changed=["summary"],
        citations=[{"url": "https://example.invalid/source", "quote": "corrected quote"}],
    )
    assert correction["schema_version"] == 1
    assert correction["id"] == "corr-1"
    assert correction["card_id"] == "card1"
    assert correction["fields_changed"] == ["summary"]


def test_apply_correction_to_card_sets_status_and_note_without_mutating_input():
    card = {"id": "card1", "status": "verified", "summary": "old"}
    correction = {"correction_note": "Fixed a wrong figure."}

    corrected = apply_correction_to_card(card, correction)

    assert corrected["status"] == "corrected"
    assert corrected["correction_note"] == "Fixed a wrong figure."
    assert card["status"] == "verified"  # original untouched


def test_append_correction_record_to_empty_file(tmp_path):
    path = str(tmp_path / "corrections.json")
    correction = {"id": "corr-1"}
    result = append_correction_record(path, correction)
    assert result == [correction]


def test_append_correction_record_to_existing_file(tmp_path):
    path = tmp_path / "corrections.json"
    path.write_text(json.dumps([{"id": "corr-0"}]))
    result = append_correction_record(str(path), {"id": "corr-1"})
    assert result == [{"id": "corr-0"}, {"id": "corr-1"}]


def _write_card(repo_root, card_id, **overrides):
    card = {
        "schema_version": 1,
        "id": card_id,
        "published_date": "2026-01-01",
        "regulator": "HKMA",
        "pillar": ["stablecoins"],
        "type": "licence",
        "title": "Test card",
        "summary": "Original summary.",
        "why_it_matters": "Matters.",
        "citations": [{"url": "https://example.invalid/a", "quote": "x"}],
        "status": "verified",
        "generated_at": "2026-01-01T00:00:00Z",
        "model": "Claude (Anthropic)",
    }
    card.update(overrides)
    cards_dir = os.path.join(repo_root, "content", "cards")
    os.makedirs(cards_dir, exist_ok=True)
    path = os.path.join(cards_dir, f"{card_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(card, fh)
    return path


def test_main_end_to_end_updates_card_and_corrections_log(tmp_path):
    card_path = _write_card(str(tmp_path), "card1")

    exit_code = main(
        [
            "--repo-root",
            str(tmp_path),
            "--card-id",
            "card1",
            "--correction-id",
            "corr-1",
            "--corrected-at",
            "2026-02-01T00:00:00Z",
            "--correction-note",
            "The stated capital requirement was wrong; corrected per source.",
            "--fields-changed",
            "summary, why_it_matters",
            "--citation",
            "https://example.invalid/corrected|the actual figure",
        ]
    )
    assert exit_code == 0

    with open(card_path) as fh:
        card = json.load(fh)
    assert card["status"] == "corrected"
    assert "capital requirement was wrong" in card["correction_note"]

    corrections_path = tmp_path / "data" / "corrections.json"
    with open(corrections_path) as fh:
        corrections = json.load(fh)
    assert len(corrections) == 1
    assert corrections[0]["card_id"] == "card1"
    assert corrections[0]["fields_changed"] == ["summary", "why_it_matters"]
    assert corrections[0]["citations"] == [
        {"url": "https://example.invalid/corrected", "quote": "the actual figure"}
    ]


def test_main_returns_nonzero_for_unknown_card_id(tmp_path):
    exit_code = main(
        [
            "--repo-root",
            str(tmp_path),
            "--card-id",
            "does-not-exist",
            "--correction-id",
            "corr-1",
            "--corrected-at",
            "2026-02-01T00:00:00Z",
            "--correction-note",
            "x",
            "--fields-changed",
            "summary",
        ]
    )
    assert exit_code == 1


def test_main_produces_a_schema_valid_correction_record(tmp_path):
    from jsonschema import Draft202012Validator

    from tests.conftest import REPO_ROOT

    _write_card(str(tmp_path), "card1")
    main(
        [
            "--repo-root",
            str(tmp_path),
            "--card-id",
            "card1",
            "--correction-id",
            "corr-1",
            "--corrected-at",
            "2026-02-01T00:00:00Z",
            "--correction-note",
            "Fixed a figure.",
            "--fields-changed",
            "summary",
            "--citation",
            "https://example.invalid/corrected|the actual figure",
        ]
    )

    with open(tmp_path / "data" / "corrections.json") as fh:
        corrections = json.load(fh)

    schema_path = os.path.join(REPO_ROOT, "pipeline", "schemas", "corrections.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    validator = Draft202012Validator(schema)
    for correction in corrections:
        validator.validate(correction)


def test_main_produces_a_schema_valid_corrected_card(tmp_path):
    from jsonschema import Draft202012Validator

    from tests.conftest import REPO_ROOT

    card_path = _write_card(str(tmp_path), "card1")
    main(
        [
            "--repo-root",
            str(tmp_path),
            "--card-id",
            "card1",
            "--correction-id",
            "corr-1",
            "--corrected-at",
            "2026-02-01T00:00:00Z",
            "--correction-note",
            "Fixed a figure.",
            "--fields-changed",
            "summary",
        ]
    )

    with open(card_path) as fh:
        card = json.load(fh)

    schema_path = os.path.join(REPO_ROOT, "pipeline", "schemas", "card.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    Draft202012Validator(schema).validate(card)
