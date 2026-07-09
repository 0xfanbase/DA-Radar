"""Tests for pipeline.ci.prompt_change_justification -- improve.yml's
second gate: a diff touching pipeline/prompts/** must carry an explicit
justification in the PR body, or the gate fails before commit.
"""
from __future__ import annotations

import subprocess

from pipeline.ci.prompt_change_justification import (
    check_prompt_change_justification,
    extract_justification,
    main,
    touches_prompts,
)


def _init_repo(repo_dir):
    subprocess.run(["git", "-c", "commit.gpgsign=false", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_dir, check=True)


def _commit_all(repo_dir, message):
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo_dir, check=True)


def test_touches_prompts_true_for_prompt_file():
    assert touches_prompts(["pipeline/prompts/analyst_prompt.md"]) is True


def test_touches_prompts_false_for_unrelated_files():
    assert touches_prompts(["pipeline/watcher/fetch.py", "config/jurisdiction.json"]) is False


def test_extract_justification_finds_marker_line():
    body = "Some intro text.\n\nEditorial-prompt justification: clarifies CLAUDE.md rule 4.\n\nMore text."
    assert extract_justification(body) == "clarifies CLAUDE.md rule 4."


def test_extract_justification_empty_when_marker_absent():
    assert extract_justification("Just an ordinary PR body.") == ""


def test_extract_justification_empty_when_marker_present_but_blank():
    assert extract_justification("Editorial-prompt justification:   ") == ""


def test_ok_when_no_prompt_files_changed_regardless_of_body():
    ok, message = check_prompt_change_justification(["pipeline/watcher/fetch.py"], "")
    assert ok is True
    assert "not applicable" in message


def test_fails_when_prompt_changed_and_body_has_no_marker():
    ok, message = check_prompt_change_justification(
        ["pipeline/prompts/analyst_prompt.md"], "Fixed a typo."
    )
    assert ok is False
    assert "Editorial-prompt justification" in message


def test_fails_when_prompt_changed_and_marker_is_blank():
    ok, message = check_prompt_change_justification(
        ["pipeline/prompts/verifier_prompt.md"], "Editorial-prompt justification:\n"
    )
    assert ok is False


def test_passes_when_prompt_changed_and_marker_has_real_text():
    ok, message = check_prompt_change_justification(
        ["pipeline/prompts/analyst_prompt.md"],
        "Editorial-prompt justification: tightens the citation-quote length rule per CLAUDE.md rule 3.",
    )
    assert ok is True
    assert "tightens the citation-quote length rule" in message


def test_main_fails_on_uncommitted_prompt_change_with_no_justification_file(tmp_path):
    repo = tmp_path
    _init_repo(repo)
    (repo / "pipeline").mkdir()
    (repo / "pipeline" / "prompts").mkdir()
    (repo / "pipeline" / "prompts" / "analyst_prompt.md").write_text("original")
    _commit_all(repo, "base")

    (repo / "pipeline" / "prompts" / "analyst_prompt.md").write_text("quietly softened rule")

    exit_code = main(
        [
            "--mode",
            "working-tree",
            "--repo-dir",
            str(repo),
            "--pr-body-file",
            str(repo / "does_not_exist.md"),
        ]
    )
    assert exit_code == 1


def test_main_passes_on_uncommitted_prompt_change_with_justification_file(tmp_path):
    repo = tmp_path
    _init_repo(repo)
    (repo / "pipeline").mkdir()
    (repo / "pipeline" / "prompts").mkdir()
    (repo / "pipeline" / "prompts" / "analyst_prompt.md").write_text("original")
    _commit_all(repo, "base")

    (repo / "pipeline" / "prompts" / "analyst_prompt.md").write_text("clarified rule")
    pr_body_file = repo / "pr_body.md"
    pr_body_file.write_text("Editorial-prompt justification: clarifies CLAUDE.md rule 2 wording.\n")

    exit_code = main(
        [
            "--mode",
            "working-tree",
            "--repo-dir",
            str(repo),
            "--pr-body-file",
            str(pr_body_file),
        ]
    )
    assert exit_code == 0


def test_main_passes_when_no_prompt_file_touched_and_no_body_file_exists(tmp_path):
    repo = tmp_path
    _init_repo(repo)
    (repo / "pipeline").mkdir()
    (repo / "pipeline" / "watcher").mkdir()
    (repo / "pipeline" / "watcher" / "fetch.py").write_text("original")
    _commit_all(repo, "base")

    (repo / "pipeline" / "watcher" / "fetch.py").write_text("improved retry logic")

    exit_code = main(
        [
            "--mode",
            "working-tree",
            "--repo-dir",
            str(repo),
            "--pr-body-file",
            str(repo / "does_not_exist.md"),
        ]
    )
    assert exit_code == 0
