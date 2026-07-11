"""Tests for pipeline.ci.path_allowlist -- the CI gate that fails if an AI
job's diff touches anything outside /content and /data.
"""
from __future__ import annotations

import subprocess

import os

from pipeline.ci.path_allowlist import (
    check_path_allowlist,
    get_diff_changed_paths,
    get_uncommitted_changed_paths,
    main,
)


def _init_repo(repo_dir):
    # -c commit.gpgsign=false is a one-off per-invocation override (never
    # touches any config file) so these disposable scratch repos don't
    # inherit the host's ambient commit-signing setup, if any.
    subprocess.run(["git", "-c", "commit.gpgsign=false", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_dir, check=True)


def _commit_all(repo_dir, message):
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo_dir, check=True)


def test_allows_content_and_data_only():
    ok, violations = check_path_allowlist(["content/cards/foo.json", "data/ledger.json"])
    assert ok is True
    assert violations == []


def test_fails_on_workflow_file():
    """The literal acceptance criterion: workflow-file diff -> CI fails."""
    ok, violations = check_path_allowlist(["content/cards/foo.json", ".github/workflows/watch.yml"])
    assert ok is False
    assert violations == [".github/workflows/watch.yml"]


def test_fails_on_pipeline_code():
    ok, violations = check_path_allowlist(["pipeline/watcher/run.py"])
    assert ok is False
    assert violations == ["pipeline/watcher/run.py"]


def test_fails_on_config_and_schemas():
    ok, violations = check_path_allowlist(["config/jurisdiction.json", "pipeline/schemas/card.json"])
    assert ok is False
    assert set(violations) == {"config/jurisdiction.json", "pipeline/schemas/card.json"}


def test_fails_on_claude_md():
    ok, violations = check_path_allowlist(["CLAUDE.md"])
    assert ok is False
    assert violations == ["CLAUDE.md"]


def test_empty_changeset_passes():
    ok, violations = check_path_allowlist([])
    assert ok is True
    assert violations == []


def test_rejects_path_traversal_tricks():
    ok, violations = check_path_allowlist(["content/../pipeline/run.py", "data/../../etc/passwd"])
    assert ok is False
    assert len(violations) == 2


def test_allowlist_is_additive_not_a_denylist():
    """A path under neither content/ nor data/ fails even though it isn't
    on any 'banned' list -- the fail-safe allowlist design, versus a
    denylist that would need updating every time a new sensitive path
    appears."""
    ok, violations = check_path_allowlist(["some/brand/new/directory/file.txt"])
    assert ok is False
    assert violations == ["some/brand/new/directory/file.txt"]


def test_get_diff_changed_paths_against_a_real_git_repo(tmp_path):
    """End-to-end against a real (scratch) git repo, not just the pure function."""
    repo = tmp_path
    _init_repo(repo)
    (repo / "data").mkdir()
    (repo / "data" / "ledger.json").write_text("{}")
    _commit_all(repo, "base")
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    (repo / ".github").mkdir()
    (repo / ".github" / "workflows.yml").write_text("bad")
    (repo / "data" / "ledger.json").write_text('{"x": 1}')
    _commit_all(repo, "ai change")

    changed = get_diff_changed_paths(base_sha, "HEAD", repo_dir=str(repo))
    ok, violations = check_path_allowlist(changed)
    assert ok is False
    assert ".github/workflows.yml" in violations
    assert "data/ledger.json" not in violations


def test_main_returns_nonzero_on_workflow_diff(tmp_path, capsys):
    repo = tmp_path
    _init_repo(repo)
    (repo / "content").mkdir()
    (repo / "content" / "a.json").write_text("{}")
    _commit_all(repo, "base")
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    (repo / ".github").mkdir()
    (repo / ".github" / "workflows.yml").write_text("malicious")
    _commit_all(repo, "ai change")

    exit_code = main(["--mode", "diff", "--base", base_sha, "--repo-dir", str(repo)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert ".github/workflows.yml" in captured.err


def test_main_returns_zero_on_content_only_diff(tmp_path):
    repo = tmp_path
    _init_repo(repo)
    (repo / "content").mkdir()
    (repo / "content" / "a.json").write_text("{}")
    _commit_all(repo, "base")
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    (repo / "content" / "b.json").write_text("{}")
    _commit_all(repo, "ai change")

    exit_code = main(["--mode", "diff", "--base", base_sha, "--repo-dir", str(repo)])
    assert exit_code == 0


def test_main_working_tree_mode_catches_uncommitted_ai_change(tmp_path):
    """The realistic integration point: the AI job has written files but
    not committed yet -- the gate inspects the uncommitted working tree."""
    repo = tmp_path
    _init_repo(repo)
    (repo / "content").mkdir()
    (repo / "content" / "a.json").write_text("{}")
    _commit_all(repo, "base")

    # Simulate a prompt-injected AI job "helpfully" editing a workflow file,
    # without committing.
    (repo / ".github").mkdir()
    (repo / ".github" / "workflows.yml").write_text("malicious, uncommitted")
    (repo / "content" / "b.json").write_text("{}")

    exit_code = main(["--mode", "working-tree", "--repo-dir", str(repo)])
    assert exit_code == 1


def test_main_no_changes_at_all_passes(tmp_path):
    repo = tmp_path
    _init_repo(repo)
    (repo / "content").mkdir()
    (repo / "content" / "a.json").write_text("{}")
    _commit_all(repo, "base")

    exit_code = main(["--mode", "working-tree", "--repo-dir", str(repo)])
    assert exit_code == 0


def test_get_uncommitted_changed_paths_expands_bare_untracked_directory(tmp_path):
    """Real bug found live: with git's default untracked-files mode,
    `git status --porcelain` reports an entirely new, wholly-untracked
    directory as a single bare line (e.g. "content/"), not one line per file
    inside it. That broke more than the allowlist check -- validate_content's
    per-file schema mapping has no schema for a bare "content" path, so it
    would silently skip validating a brand-new content subdirectory
    entirely. Fixed at the source via --untracked-files=all so every
    downstream consumer of get_uncommitted_changed_paths always sees real
    per-file paths."""
    repo = tmp_path
    _init_repo(repo)
    (repo / "data").mkdir()
    (repo / "data" / "ledger.json").write_text("{}")
    _commit_all(repo, "base")

    # A brand-new, entirely untracked directory -- no files inside it are
    # tracked yet, so git's default mode would emit one bare "content/" line
    # instead of per-file lines.
    (repo / "content").mkdir()
    (repo / "content" / "pillar_states").mkdir()
    (repo / "content" / "pillar_states" / "stablecoins.json").write_text("{}")

    default_status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert default_status.strip() == "?? content/"

    changed = get_uncommitted_changed_paths(str(repo))
    assert changed == ["content/pillar_states/stablecoins.json"]

    exit_code = main(["--mode", "working-tree", "--repo-dir", str(repo)])
    assert exit_code == 0


def test_symlink_under_content_resolving_into_pipeline_is_rejected(tmp_path):
    """Real gap found live during the 2026-07-11 compliance audit: a symlink
    placed under content/ that resolves to a file under pipeline/ used to
    pass check_path_allowlist's pure string-prefix check, since the check
    never looked at the filesystem. A prompt-injected AI job with Write
    access to content/ (but no Bash, so no direct edit to pipeline/) could
    still stage such a symlink -- os.symlink is a plain filesystem write, not
    a shell command."""
    repo = tmp_path
    _init_repo(repo)
    (repo / "content").mkdir()
    (repo / "pipeline").mkdir()
    (repo / "pipeline" / "secret.py").write_text("# real pipeline code")
    _commit_all(repo, "base")

    os.symlink(
        os.path.join("..", "pipeline", "secret.py"),
        repo / "content" / "evil_link.py",
    )

    changed = get_uncommitted_changed_paths(str(repo))
    assert changed == ["content/evil_link.py"]

    ok, violations = check_path_allowlist(changed, repo_dir=str(repo))
    assert ok is False
    assert violations == ["content/evil_link.py"]

    exit_code = main(["--mode", "working-tree", "--repo-dir", str(repo)])
    assert exit_code == 1


def test_symlinked_directory_under_content_is_rejected(tmp_path):
    """Same gap, one level up: a symlinked *directory* under content/ whose
    real target is outside the allowlist. git itself reports the symlink as
    a single untracked entry (it does not follow the symlink to list files
    inside it), so the gate only ever needs to resolve that one reported
    path -- which _escapes_allowlist_via_symlink does via os.path.realpath."""
    repo = tmp_path
    _init_repo(repo)
    (repo / "content").mkdir()
    (repo / "escape_target").mkdir()
    (repo / "escape_target" / "payload.json").write_text("{}")
    _commit_all(repo, "base")

    os.symlink(
        os.path.join("..", "escape_target"),
        repo / "content" / "linked_dir",
    )

    changed = get_uncommitted_changed_paths(str(repo))
    assert changed == ["content/linked_dir"]

    ok, violations = check_path_allowlist(changed, repo_dir=str(repo))
    assert ok is False
    assert violations == ["content/linked_dir"]


def test_legitimate_real_files_still_pass_with_repo_dir_set(tmp_path):
    """The new filesystem-resolution check must not false-positive on
    ordinary, non-symlinked content/data files -- confirms the fix is
    additive, not a regression on the common case."""
    repo = tmp_path
    _init_repo(repo)
    (repo / "content").mkdir()
    (repo / "data").mkdir()
    (repo / "content" / "a.json").write_text("{}")
    (repo / "data" / "ledger.json").write_text("{}")
    _commit_all(repo, "base")

    (repo / "content" / "b.json").write_text("{}")

    changed = get_uncommitted_changed_paths(str(repo))
    ok, violations = check_path_allowlist(changed, repo_dir=str(repo))
    assert ok is True
    assert violations == []


def test_check_path_allowlist_without_repo_dir_still_works_as_pure_function():
    """Backward compatibility: existing callers that pass plain path strings
    with no real filesystem behind them (repo_dir defaults to ".") must
    behave exactly as before the symlink fix -- the filesystem check
    fail-opens (treats as "not escaping") for a path that doesn't exist on
    disk relative to the current working directory."""
    ok, violations = check_path_allowlist(["content/cards/foo.json", "data/ledger.json"])
    assert ok is True
    assert violations == []
