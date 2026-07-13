"""Tests for pipeline.ci.validate_content -- the schema-validation CI gate."""
from __future__ import annotations

import json
import os

from pipeline.ci.validate_content import validate_changed_paths, validate_file

VALID_CARD = {
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
    "citations": [{"url": "https://example.invalid/doc", "quote": "a quote"}],
    "status": "verified",
    "generated_at": "2026-01-01T00:00:00Z",
    "model": "test-model",
}


def _write(repo_dir, rel_path, data):
    full = os.path.join(repo_dir, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def test_valid_card_passes(tmp_path):
    _write(tmp_path, "content/hk/cards/card-1.json", VALID_CARD)
    applicable, ok, error = validate_file("content/hk/cards/card-1.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is True
    assert error is None


def test_invalid_card_fails(tmp_path):
    bad = dict(VALID_CARD)
    del bad["citations"]
    _write(tmp_path, "content/hk/cards/card-1.json", bad)
    applicable, ok, error = validate_file("content/hk/cards/card-1.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is False
    assert error is not None


def test_path_with_no_applicable_schema_is_not_applicable():
    applicable, ok, error = validate_file("pipeline/watcher/run.py", repo_dir=".")
    assert applicable is False
    assert ok is True
    assert error is None


def test_ledger_and_queue_paths_are_schema_governed(tmp_path):
    _write(
        tmp_path,
        "data/hk/ledger.json",
        {"schema_version": 1, "jurisdiction_id": "hk", "generated_at": "x", "items": {}},
    )
    applicable, ok, error = validate_file("data/hk/ledger.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is True


def test_audit_event_path_is_schema_governed(tmp_path):
    _write(
        tmp_path,
        "data/audit/2026-07-09.json",
        {
            "schema_version": 1,
            "event_type": "link_rot_check",
            "timestamp": "2026-07-09T00:00:00Z",
            "actor": "audit.yml",
            "summary": "s",
            "details": {},
            "related_ids": [],
        },
    )
    applicable, ok, error = validate_file("data/audit/2026-07-09.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is True


def test_malformed_json_reports_error_not_crash(tmp_path):
    full = tmp_path / "content" / "hk" / "cards"
    full.mkdir(parents=True)
    (full / "broken.json").write_text("{not valid json")
    applicable, ok, error = validate_file("content/hk/cards/broken.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is False
    assert error is not None


def test_validate_changed_paths_aggregates_and_skips_non_governed_files(tmp_path):
    _write(tmp_path, "content/hk/cards/good.json", VALID_CARD)
    bad = dict(VALID_CARD, id="card-2")
    del bad["status"]
    _write(tmp_path, "content/hk/cards/bad.json", bad)

    ok, results = validate_changed_paths(
        ["content/hk/cards/good.json", "content/hk/cards/bad.json", "pipeline/watcher/run.py"],
        repo_dir=str(tmp_path),
    )
    assert ok is False
    assert len(results) == 2  # the .py file is skipped, not reported


def test_validate_changed_paths_all_valid_passes(tmp_path):
    _write(tmp_path, "content/hk/cards/good.json", VALID_CARD)
    ok, results = validate_changed_paths(["content/hk/cards/good.json"], repo_dir=str(tmp_path))
    assert ok is True
    assert len(results) == 1


def test_card_with_internal_model_identifier_is_rejected(tmp_path):
    """The 2026-07-09 correction: an internal Claude model-version
    identifier (e.g. "claude-sonnet-5") must never pass validation in a
    card's `model` field, even though card.json's schema only requires
    `minLength: 1` and has no opinion on the string's shape."""
    leaked = dict(VALID_CARD, model="claude-sonnet-5")
    _write(tmp_path, "content/hk/cards/card-1.json", leaked)
    applicable, ok, error = validate_file("content/hk/cards/card-1.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is False
    assert error is not None
    assert "content/hk/cards/card-1.json" in error
    assert "claude-sonnet-5" in error


def test_card_with_mixed_case_internal_model_identifier_is_rejected(tmp_path):
    """The detector must be case-insensitive: "Claude-Sonnet-5" is the same
    internal-identifier shape as "claude-sonnet-5" and must be caught too,
    not just the all-lowercase form."""
    leaked = dict(VALID_CARD, model="Claude-Sonnet-5")
    _write(tmp_path, "content/hk/cards/card-1.json", leaked)
    applicable, ok, error = validate_file("content/hk/cards/card-1.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is False
    assert error is not None
    assert "content/hk/cards/card-1.json" in error
    assert "Claude-Sonnet-5" in error


def test_card_with_human_readable_model_name_is_accepted(tmp_path):
    """The accepted replacement from the same correction: a human-readable
    model family name must still pass, since editorial rule 1 requires the
    model be disclosed -- this check must reject the identifier *shape*,
    not the presence of a model name at all."""
    ok_card = dict(VALID_CARD, model="Claude (Anthropic)")
    _write(tmp_path, "content/hk/cards/card-1.json", ok_card)
    applicable, ok, error = validate_file("content/hk/cards/card-1.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is True
    assert error is None


def test_real_array_shaped_corrections_file_validates(tmp_path):
    """corrections.json is an array-typed schema (matching how
    apply_correction.py's append_correction_record actually writes
    data/corrections.json to disk) -- a real latent bug found and fixed
    during the fact-check enhancement pass: the schema was originally
    typed as a single object, which would have failed this exact check
    the first time a real correction ever happened."""
    corrections = [
        {
            "schema_version": 1,
            "id": "corr-1",
            "jurisdiction": "hk",
            "card_id": "card-1",
            "corrected_at": "2026-02-01T00:00:00Z",
            "correction_note": "Fixed a wrong figure.",
            "fields_changed": ["summary"],
            "citations": [{"url": "https://example.invalid/corrected", "quote": "the actual figure"}],
        },
        {
            "schema_version": 1,
            "id": "corr-2",
            "jurisdiction": "hk",
            "card_id": "card-2",
            "corrected_at": "2026-03-01T00:00:00Z",
            "correction_note": "Fixed a date.",
            "fields_changed": ["key_dates"],
            "citations": [],
        },
    ]
    _write(tmp_path, "data/corrections.json", corrections)
    applicable, ok, error = validate_file("data/corrections.json", repo_dir=str(tmp_path))
    assert applicable is True
    assert ok is True
    assert error is None
