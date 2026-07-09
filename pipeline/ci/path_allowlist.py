"""The path-allowlist CI gate.

Automated AI jobs (the analyst and verifier) may only modify files under
/content and /data (see CLAUDE.md). This is deliberately an ALLOWLIST ("fail
unless every changed path is under content/ or data/"), not a denylist
enumerating banned paths -- an allowlist is fail-safe if a new sensitive
path is added later (e.g. a future secrets/ directory); a denylist is not.

Intended use (per Fable PM directive): a plain-shell step in the SAME job
as the AI job, run AFTER the AI job and BEFORE any git commit/push. This
module holds no trust in the AI job's own report of what it changed -- it
inspects the actual working tree (or an actual git diff) itself.
"""
from __future__ import annotations

import argparse
import posixpath
import subprocess
import sys

DEFAULT_ALLOWED_PREFIXES = ("content/", "data/")


def normalize_path(path: str) -> str:
    """Shared by every CI gate that needs to compare a changed path against
    prefix rules (see also pipeline/ci/improve_scope.py)."""
    return posixpath.normpath(path.replace("\\", "/")).lstrip("/")


def check_path_allowlist(
    changed_paths: list, *, allowed_prefixes: tuple = DEFAULT_ALLOWED_PREFIXES
) -> tuple:
    """Returns (ok, violations). ok is True iff every path in changed_paths
    normalizes to somewhere under one of allowed_prefixes."""
    violations = [
        path
        for path in changed_paths
        if not any(normalize_path(path).startswith(prefix) for prefix in allowed_prefixes)
    ]
    return (len(violations) == 0, violations)


def get_uncommitted_changed_paths(repo_dir: str = ".") -> list:
    """Paths changed in the working tree (staged, unstaged, or untracked),
    via `git status --porcelain` -- the pre-commit view of what an AI job
    just wrote.

    Uses `--untracked-files=all` rather than git's default: the default
    collapses an entirely-new, wholly-untracked directory into a single
    bare line (e.g. "content/" instead of "content/pillar_states/x.json").
    That bare-directory line breaks every path-based consumer downstream --
    not just this allowlist check, but validate_content.py's per-file
    schema mapping, which would silently skip validating any brand-new
    content subdirectory entirely (no schema maps to a bare "content"
    path, so it's treated as "not schema-governed" instead of "unvalidated
    new file"). Listing real per-file paths is the actual fix; every
    downstream consumer works correctly once it never sees a bare
    directory line.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    paths = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path_part = line[3:]
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        paths.append(path_part.strip())
    return paths


def get_diff_changed_paths(base_ref: str, head_ref: str = "HEAD", repo_dir: str = ".") -> list:
    """Paths changed between two commits, via `git diff --name-only`."""
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, head_ref],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if any changed path escapes the AI-job allowlist (content/, data/)."
    )
    parser.add_argument("--mode", choices=["working-tree", "diff"], default="working-tree")
    parser.add_argument("--base", help="Base ref for --mode diff")
    parser.add_argument("--head", default="HEAD", help="Head ref for --mode diff")
    parser.add_argument("--repo-dir", default=".")
    args = parser.parse_args(argv)

    if args.mode == "diff":
        if not args.base:
            print("path_allowlist: --base is required in diff mode", file=sys.stderr)
            return 2
        changed = get_diff_changed_paths(args.base, args.head, repo_dir=args.repo_dir)
    else:
        changed = get_uncommitted_changed_paths(args.repo_dir)

    if not changed:
        print("path_allowlist: no changed files -- nothing to check.")
        return 0

    ok, violations = check_path_allowlist(changed)
    if ok:
        print(f"path_allowlist: OK -- {len(changed)} changed file(s), all under content/ or data/.")
        return 0

    print("path_allowlist: FAIL -- changed file(s) outside the allowlist:", file=sys.stderr)
    for violation in violations:
        print(f"  {violation}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
