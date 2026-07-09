"""Tests for pipeline.ci.improve_scope -- the CI gate that fails if
improve.yml's proposed diff touches anything outside /pipeline and
/config, or touches one of the hard-denied gate/schema/workflow files
even though it's nominally under an allowed root.
"""
from __future__ import annotations

import subprocess

from pipeline.ci.improve_scope import check_improve_scope, main


def _init_repo(repo_dir):
    subprocess.run(["git", "-c", "commit.gpgsign=false", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_dir, check=True)


def _commit_all(repo_dir, message):
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo_dir, check=True)


def test_allows_ordinary_pipeline_and_config_files():
    ok, violations = check_improve_scope(["pipeline/watcher/fetch.py", "config/jurisdiction.json"])
    assert ok is True
    assert violations == []


def test_fails_on_content_and_data():
    """improve.yml has no legitimate reason to touch published content or
    ledger/queue data -- that's analyst/verifier/corrections territory."""
    ok, violations = check_improve_scope(["content/cards/foo.json", "data/ledger.json"])
    assert ok is False
    assert set(violations) == {"content/cards/foo.json", "data/ledger.json"}


def test_fails_on_any_workflow_file_even_a_new_one():
    """Denied by prefix, not by name -- a brand-new workflow file the AI
    job invents is caught exactly like an existing one."""
    ok, violations = check_improve_scope([".github/workflows/brand-new-thing.yml"])
    assert ok is False
    assert violations == [".github/workflows/brand-new-thing.yml"]


def test_fails_on_any_schema_even_a_new_one():
    ok, violations = check_improve_scope(["pipeline/schemas/card.json", "pipeline/schemas/new_thing.json"])
    assert ok is False
    assert set(violations) == {"pipeline/schemas/card.json", "pipeline/schemas/new_thing.json"}


def test_fails_on_claude_md():
    ok, violations = check_improve_scope(["CLAUDE.md"])
    assert ok is False
    assert violations == ["CLAUDE.md"]


def test_fails_on_gate_code_files_named_by_fable_pm_review():
    """The specific enumeration Fable PM's Phase 5 review required: every
    module whose job is to check, gate, or constrain the pipeline's own
    output, named individually since Fable asked to verify this list is
    real and tested, not just described."""
    gate_files = [
        "pipeline/ci/path_allowlist.py",
        "pipeline/ci/improve_scope.py",
        "pipeline/ci/validate_content.py",
        "pipeline/ci/apply_verification_gate.py",
        "pipeline/ci/promote_verified.py",
        "pipeline/ci/promote_drafted.py",
        "pipeline/ci/apply_correction.py",
        "pipeline/verify/gate.py",
        "pipeline/verify/authenticity.py",
    ]
    for path in gate_files:
        ok, violations = check_improve_scope([path])
        assert ok is False, f"{path} should be hard-denied"
        assert violations == [path]


def test_fails_on_gate_file_even_though_nominally_under_the_allowed_pipeline_root():
    """The exact case Fable PM's review flagged: pipeline/verify/gate.py
    is technically under the allowed pipeline/ prefix, but must still fail
    because it's on the hard-deny list -- the deny rule must be checked
    and win regardless of the allow rule, not just happen to agree with it
    for files that also fail some other unrelated check."""
    ok, violations = check_improve_scope(["pipeline/verify/gate.py", "pipeline/watcher/fetch.py"])
    assert ok is False
    assert violations == ["pipeline/verify/gate.py"]


def test_docfetch_is_deliberately_not_hard_denied():
    """pipeline/verify/docfetch.py is a fetch/extract utility the gates
    call, not itself a check -- legitimate self-improvement territory
    (logged as a deliberate judgment call in IMPROVEMENT_BACKLOG.md, not
    an oversight). Locked in here so a future edit doesn't silently widen
    or narrow the hard-deny list without a matching test update."""
    ok, violations = check_improve_scope(["pipeline/verify/docfetch.py"])
    assert ok is True
    assert violations == []


def test_empty_changeset_passes():
    ok, violations = check_improve_scope([])
    assert ok is True
    assert violations == []


def test_rejects_path_traversal_tricks():
    ok, violations = check_improve_scope(["pipeline/../.github/workflows/watch.yml"])
    assert ok is False
    assert len(violations) == 1


def test_get_diff_changed_paths_against_a_real_git_repo_catches_gate_file(tmp_path):
    """End-to-end against a real (scratch) git repo, not just the pure
    function -- mirrors path_allowlist.py's own end-to-end rigor."""
    repo = tmp_path
    _init_repo(repo)
    (repo / "pipeline").mkdir()
    (repo / "pipeline" / "watcher").mkdir()
    (repo / "pipeline" / "watcher" / "fetch.py").write_text("# original")
    (repo / "pipeline" / "verify").mkdir()
    (repo / "pipeline" / "verify" / "gate.py").write_text("# original gate")
    _commit_all(repo, "base")
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    (repo / "pipeline" / "watcher" / "fetch.py").write_text("# legit improvement")
    (repo / "pipeline" / "verify" / "gate.py").write_text("# quietly weakened gate")
    _commit_all(repo, "improve.yml proposal")

    from pipeline.ci.improve_scope import check_improve_scope
    from pipeline.ci.path_allowlist import get_diff_changed_paths

    changed = get_diff_changed_paths(base_sha, "HEAD", repo_dir=str(repo))
    ok, violations = check_improve_scope(changed)
    assert ok is False
    assert "pipeline/verify/gate.py" in violations
    assert "pipeline/watcher/fetch.py" not in violations


def test_main_returns_nonzero_on_schema_diff(tmp_path, capsys):
    repo = tmp_path
    _init_repo(repo)
    (repo / "pipeline").mkdir()
    (repo / "pipeline" / "watcher").mkdir()
    (repo / "pipeline" / "watcher" / "fetch.py").write_text("# original")
    _commit_all(repo, "base")

    (repo / "pipeline" / "schemas").mkdir()
    (repo / "pipeline" / "schemas" / "card.json").write_text("{}")

    exit_code = main(["--mode", "working-tree", "--repo-dir", str(repo)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "pipeline/schemas/card.json" in captured.err


def test_main_returns_zero_on_in_scope_diff(tmp_path):
    repo = tmp_path
    _init_repo(repo)
    (repo / "pipeline").mkdir()
    (repo / "pipeline" / "watcher").mkdir()
    (repo / "pipeline" / "watcher" / "fetch.py").write_text("# original")
    _commit_all(repo, "base")

    (repo / "pipeline" / "watcher" / "fetch.py").write_text("# improved retry logic")
    (repo / "config").mkdir()
    (repo / "config" / "jurisdiction.json").write_text("{}")

    exit_code = main(["--mode", "working-tree", "--repo-dir", str(repo)])
    assert exit_code == 0
