"""The improve.yml CI gate -- structurally narrower than the analyst/
verifier's path_allowlist.py, because improve.yml's job is the opposite
shape: instead of "may only touch /content and /data", it "may touch
/pipeline and /config, EXCEPT the specific files whose job is to check,
gate, or constrain the pipeline's own output."

That is the actual principle (Fable PM directive, Phase 5 improve.yml
design review): nothing whose job is to check, gate, or constrain the
pipeline's own output may be modified by the thing being improved. The
hard-denied list below is enumerated FROM that principle, not from two
examples that happened to come to mind -- it covers every module that
renders a pass/fail verdict on AI-generated content or performs a trust-
critical ledger-state transition, plus every schema (a "diff" that
quietly loosens citations[].minItems or drops a required field reads as
an innocuous one-line change and would defeat months of gate-building in
a single merged PR), plus the gate-code files themselves and every
GitHub Actions workflow file (the widest-blast-radius, least-visible-in-
a-diff place a change could grant itself more capability -- secrets:
inherit, loosened permissions:, an altered trigger).

Deliberately NOT hard-denied: pipeline/verify/docfetch.py (a fetch/
extract utility the gates call, not itself a check -- legitimate
self-improvement territory, e.g. a real encoding-bug fix or added
content-type support) and pipeline/ci/queue_check.py / seed_backfill.py
(scheduling/one-time-seeding helpers, not correctness gates). This is a
judgment call, logged in IMPROVEMENT_BACKLOG.md, not an oversight.

Like path_allowlist.py, this is meant to run as a real subprocess check
in the SAME job as the AI job, after it runs and before any commit/push
-- it inspects the actual working tree or git diff, never trusts the AI
job's own report of what it changed.
"""
from __future__ import annotations

import argparse
import sys

from pipeline.ci.path_allowlist import (
    get_diff_changed_paths,
    get_uncommitted_changed_paths,
    normalize_path,
)

ALLOWED_PREFIXES = ("pipeline/", "config/")

# Every GitHub Actions workflow file, and every JSON schema, is denied by
# prefix -- an allowlist-of-exceptions here would need updating every time
# a new workflow or schema is added, the same fail-unsafe problem an
# allowlist (vs. denylist) avoids elsewhere in this project. Denying these
# two prefixes outright is the fail-safe direction for a hard-deny rule.
HARD_DENIED_PREFIXES = (".github/workflows/", "pipeline/schemas/")

# Every module whose job is to check, gate, or constrain AI-generated
# output, or to perform a trust-critical ledger-state transition -- plus
# the gate-code files for this very check and for path_allowlist.py.
HARD_DENIED_FILES = frozenset(
    {
        "CLAUDE.md",
        "pipeline/ci/path_allowlist.py",
        "pipeline/ci/improve_scope.py",
        "pipeline/ci/validate_content.py",
        "pipeline/ci/apply_verification_gate.py",
        "pipeline/ci/promote_verified.py",
        "pipeline/ci/promote_drafted.py",
        "pipeline/ci/apply_correction.py",
        "pipeline/verify/gate.py",
        "pipeline/verify/authenticity.py",
    }
)


def check_improve_scope(changed_paths: list) -> tuple:
    """Returns (ok, violations). ok is True iff every path in
    changed_paths is under an allowed prefix AND not hard-denied by exact
    name or hard-denied prefix."""
    violations = []
    for path in changed_paths:
        normalized = normalize_path(path)
        if normalized in HARD_DENIED_FILES:
            violations.append(path)
            continue
        if any(normalized.startswith(prefix) for prefix in HARD_DENIED_PREFIXES):
            violations.append(path)
            continue
        if not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            violations.append(path)
    return (len(violations) == 0, violations)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail if any changed path escapes improve.yml's allowlist "
            "(pipeline/, config/) or touches a hard-denied gate/schema/workflow file."
        )
    )
    parser.add_argument("--mode", choices=["working-tree", "diff"], default="working-tree")
    parser.add_argument("--base", help="Base ref for --mode diff")
    parser.add_argument("--head", default="HEAD", help="Head ref for --mode diff")
    parser.add_argument("--repo-dir", default=".")
    args = parser.parse_args(argv)

    if args.mode == "diff":
        if not args.base:
            print("improve_scope: --base is required in diff mode", file=sys.stderr)
            return 2
        changed = get_diff_changed_paths(args.base, args.head, repo_dir=args.repo_dir)
    else:
        changed = get_uncommitted_changed_paths(args.repo_dir)

    if not changed:
        print("improve_scope: no changed files -- nothing to check.")
        return 0

    ok, violations = check_improve_scope(changed)
    if ok:
        print(f"improve_scope: OK -- {len(changed)} changed file(s), all in scope.")
        return 0

    print("improve_scope: FAIL -- changed file(s) outside improve.yml's scope:", file=sys.stderr)
    for violation in violations:
        print(f"  {violation}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
