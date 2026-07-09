"""Tests for pipeline.ci.improve_queue -- the bounded, human-curated
candidate list improve.yml picks from. The AI job never edits this file
itself (no /data write access, see improve_scope.py), so every status
transition here is deterministic code, tested the same way ledger.py's
transitions are.
"""
from __future__ import annotations

import json
import os

from pipeline.ci.improve_queue import (
    load_queue,
    main,
    mark_item_picked,
    pick_next_open_item,
    save_queue,
)


def _item(item_id, opened_at, status="open", **overrides):
    item = {
        "id": item_id,
        "opened_at": opened_at,
        "source": "test",
        "description": "A candidate improvement.",
        "status": status,
        "picked_at": None,
        "pr_url": None,
    }
    item.update(overrides)
    return item


def test_load_queue_missing_file_returns_empty_queue(tmp_path):
    queue = load_queue(str(tmp_path / "does_not_exist.json"))
    assert queue == {"schema_version": 1, "items": []}


def test_pick_next_open_item_returns_none_when_empty():
    assert pick_next_open_item({"schema_version": 1, "items": []}) is None


def test_pick_next_open_item_ignores_picked_and_resolved():
    queue = {
        "schema_version": 1,
        "items": [
            _item("a", "2026-01-01T00:00:00Z", status="picked"),
            _item("b", "2026-01-02T00:00:00Z", status="resolved"),
        ],
    }
    assert pick_next_open_item(queue) is None


def test_pick_next_open_item_returns_oldest_by_opened_at():
    queue = {
        "schema_version": 1,
        "items": [
            _item("newer", "2026-02-01T00:00:00Z"),
            _item("older", "2026-01-01T00:00:00Z"),
        ],
    }
    picked = pick_next_open_item(queue)
    assert picked["id"] == "older"


def test_pick_next_open_item_breaks_ties_by_id():
    queue = {
        "schema_version": 1,
        "items": [
            _item("b-item", "2026-01-01T00:00:00Z"),
            _item("a-item", "2026-01-01T00:00:00Z"),
        ],
    }
    picked = pick_next_open_item(queue)
    assert picked["id"] == "a-item"


def test_mark_item_picked_does_not_mutate_input():
    queue = {"schema_version": 1, "items": [_item("a", "2026-01-01T00:00:00Z")]}
    updated = mark_item_picked(
        queue, "a", picked_at="2026-01-05T00:00:00Z", pr_url="https://example.invalid/pr/1"
    )
    assert queue["items"][0]["status"] == "open"
    assert updated["items"][0]["status"] == "picked"
    assert updated["items"][0]["picked_at"] == "2026-01-05T00:00:00Z"
    assert updated["items"][0]["pr_url"] == "https://example.invalid/pr/1"


def test_mark_item_picked_leaves_other_items_untouched():
    queue = {
        "schema_version": 1,
        "items": [_item("a", "2026-01-01T00:00:00Z"), _item("b", "2026-01-02T00:00:00Z")],
    }
    updated = mark_item_picked(queue, "a", picked_at="2026-01-05T00:00:00Z", pr_url="https://example.invalid/pr/1")
    assert updated["items"][1] == queue["items"][1]


def test_save_then_load_round_trips(tmp_path):
    path = str(tmp_path / "nested" / "improve_queue.json")
    queue = {"schema_version": 1, "items": [_item("a", "2026-01-01T00:00:00Z")]}
    save_queue(path, queue)
    assert os.path.exists(path)
    assert load_queue(path) == queue


def test_saved_queue_is_schema_valid(tmp_path):
    from jsonschema import Draft202012Validator

    from tests.conftest import REPO_ROOT

    path = str(tmp_path / "improve_queue.json")
    queue = {
        "schema_version": 1,
        "items": [_item("a", "2026-01-01T00:00:00Z", status="picked", picked_at="2026-01-05T00:00:00Z", pr_url="https://example.invalid/pr/1")],
    }
    save_queue(path, queue)

    schema_path = os.path.join(REPO_ROOT, "pipeline", "schemas", "improve_queue.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    Draft202012Validator(schema).validate(load_queue(path))


def test_real_seed_data_file_is_schema_valid_and_empty():
    """The real, committed data/improve_queue.json ships empty -- a
    deliberate choice (see IMPROVEMENT_BACKLOG.md): manufacturing
    "candidate improvements" without a genuinely validated, independent
    reason would be exactly the kind of fabrication this project's
    editorial rules exist to prevent. improve.yml exits immediately, no
    run, when this queue has no open items -- same zero-cost-when-empty
    principle as the analyst's data/queue.json."""
    from jsonschema import Draft202012Validator

    from tests.conftest import REPO_ROOT

    real_path = os.path.join(REPO_ROOT, "data", "improve_queue.json")
    queue = load_queue(real_path)
    assert queue["items"] == []

    schema_path = os.path.join(REPO_ROOT, "pipeline", "schemas", "improve_queue.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    Draft202012Validator(schema).validate(queue)


def test_main_reports_empty_true_when_no_open_items(tmp_path):
    queue_path = tmp_path / "improve_queue.json"
    save_queue(str(queue_path), {"schema_version": 1, "items": []})
    output_path = tmp_path / "github_output"

    exit_code = main(["--queue", str(queue_path), "--github-output", str(output_path)])
    assert exit_code == 0
    assert output_path.read_text() == "empty=true\n"


def test_main_reports_picked_item_when_one_is_open(tmp_path):
    queue_path = tmp_path / "improve_queue.json"
    save_queue(
        str(queue_path),
        {"schema_version": 1, "items": [_item("only-open", "2026-01-01T00:00:00Z", description="Fix the retry backoff.")]},
    )
    output_path = tmp_path / "github_output"

    exit_code = main(["--queue", str(queue_path), "--github-output", str(output_path)])
    assert exit_code == 0
    output = output_path.read_text()
    assert "empty=false" in output
    assert "item_id=only-open" in output
    assert "item_description=Fix the retry backoff." in output


def test_main_missing_queue_file_reports_empty(tmp_path):
    output_path = tmp_path / "github_output"
    exit_code = main(
        ["--queue", str(tmp_path / "does_not_exist.json"), "--github-output", str(output_path)]
    )
    assert exit_code == 0
    assert output_path.read_text() == "empty=true\n"


def test_main_mark_picked_updates_the_real_queue_file(tmp_path):
    queue_path = tmp_path / "improve_queue.json"
    save_queue(str(queue_path), {"schema_version": 1, "items": [_item("item-a", "2026-01-01T00:00:00Z")]})

    exit_code = main(
        ["--queue", str(queue_path), "--mark-picked", "item-a", "--pr-url", "https://example.invalid/pr/9"]
    )
    assert exit_code == 0

    updated = load_queue(str(queue_path))
    assert updated["items"][0]["status"] == "picked"
    assert updated["items"][0]["pr_url"] == "https://example.invalid/pr/9"
    assert updated["items"][0]["picked_at"] is not None


def test_main_mark_picked_requires_pr_url(tmp_path):
    queue_path = tmp_path / "improve_queue.json"
    save_queue(str(queue_path), {"schema_version": 1, "items": [_item("item-a", "2026-01-01T00:00:00Z")]})

    exit_code = main(["--queue", str(queue_path), "--mark-picked", "item-a"])
    assert exit_code == 2
