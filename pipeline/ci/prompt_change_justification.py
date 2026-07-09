"""improve.yml's second gate (Fable PM Phase 5 review, point 2):
pipeline/prompts/*.md stays legitimately editable -- it is not on
improve_scope.py's hard-deny list, and a real prompt bug has already been
found and fixed once in this project (Phase 4's model-identifier leak, via
analyst_prompt.md's original wording). But an editorial-rule-bearing
prompt is exactly the kind of file where a subtle softening reads as an
innocuous diff and gets waved through review. This does not lock the
file; it forces a spotlight: any PR whose diff touches pipeline/prompts/**
must carry an explicit "Editorial-prompt justification:" line in its PR
body, one sentence naming which CLAUDE.md rule the change relates to. A
missing or empty line fails this gate before the commit step runs, same
real-subprocess-check pattern as every other gate in this project.
"""
from __future__ import annotations

import argparse
import sys

from pipeline.ci.path_allowlist import (
    get_diff_changed_paths,
    get_uncommitted_changed_paths,
    normalize_path,
)

REQUIRED_MARKER = "Editorial-prompt justification:"


def touches_prompts(changed_paths: list) -> bool:
    return any(normalize_path(path).startswith("pipeline/prompts/") for path in changed_paths)


def extract_justification(pr_body_text: str) -> str:
    """Returns the text after the marker on its own line, or '' if the
    marker is absent or has nothing meaningful after it."""
    for line in (pr_body_text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(REQUIRED_MARKER):
            return stripped[len(REQUIRED_MARKER):].strip()
    return ""


def check_prompt_change_justification(changed_paths: list, pr_body_text: str) -> tuple:
    """Returns (ok, message). ok is True if no prompt file changed, or if
    one did and the PR body carries a non-empty justification line."""
    if not touches_prompts(changed_paths):
        return True, "no pipeline/prompts/** files changed -- not applicable"

    justification = extract_justification(pr_body_text)
    if not justification:
        return (
            False,
            f"diff touches pipeline/prompts/** but the PR body has no '{REQUIRED_MARKER}' "
            "line explaining the change against a specific CLAUDE.md rule",
        )
    return True, f"editorial-prompt justification present: {justification}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if a diff touching pipeline/prompts/** has no PR-body justification."
    )
    parser.add_argument("--mode", choices=["working-tree", "diff"], default="working-tree")
    parser.add_argument("--base", help="Base ref for --mode diff")
    parser.add_argument("--head", default="HEAD", help="Head ref for --mode diff")
    parser.add_argument("--repo-dir", default=".")
    parser.add_argument(
        "--pr-body-file",
        required=True,
        help="Path to a local file containing the AI job's proposed PR body text.",
    )
    args = parser.parse_args(argv)

    if args.mode == "diff":
        if not args.base:
            print("prompt_change_justification: --base is required in diff mode", file=sys.stderr)
            return 2
        changed = get_diff_changed_paths(args.base, args.head, repo_dir=args.repo_dir)
    else:
        changed = get_uncommitted_changed_paths(args.repo_dir)

    try:
        with open(args.pr_body_file, "r", encoding="utf-8") as fh:
            pr_body_text = fh.read()
    except FileNotFoundError:
        pr_body_text = ""

    ok, message = check_prompt_change_justification(changed, pr_body_text)
    print(f"prompt_change_justification: {'OK' if ok else 'FAIL'} -- {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
