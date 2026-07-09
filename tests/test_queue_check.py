"""Tests for pipeline.ci.queue_check -- the analyze.yml quota gate."""
from __future__ import annotations

import json

from pipeline.ci.queue_check import main, queue_is_empty


def test_missing_queue_file_is_treated_as_empty(tmp_path):
    assert queue_is_empty(str(tmp_path / "does-not-exist.json")) is True


def test_empty_items_list_is_empty(tmp_path):
    path = tmp_path / "queue.json"
    path.write_text(json.dumps({"schema_version": 1, "generated_at": "x", "items": []}))
    assert queue_is_empty(str(path)) is True


def test_nonempty_items_list_is_not_empty(tmp_path):
    path = tmp_path / "queue.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "x",
                "items": [{"item_hash": "a", "status": "queued"}],
            }
        )
    )
    assert queue_is_empty(str(path)) is False


def test_main_writes_github_output_true_for_empty_queue(tmp_path):
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps({"schema_version": 1, "generated_at": "x", "items": []}))
    output_path = tmp_path / "github_output.txt"
    output_path.write_text("")

    exit_code = main(["--queue", str(queue_path), "--github-output", str(output_path)])

    assert exit_code == 0
    assert output_path.read_text().strip() == "empty=true"


def test_main_writes_github_output_false_for_nonempty_queue(tmp_path):
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "x",
                "items": [{"item_hash": "a", "status": "queued"}],
            }
        )
    )
    output_path = tmp_path / "github_output.txt"
    output_path.write_text("")

    exit_code = main(["--queue", str(queue_path), "--github-output", str(output_path)])

    assert exit_code == 0
    assert output_path.read_text().strip() == "empty=false"


def test_main_never_fails_even_without_github_output(tmp_path):
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps({"schema_version": 1, "generated_at": "x", "items": []}))
    exit_code = main(["--queue", str(queue_path), "--github-output", ""])
    assert exit_code == 0
