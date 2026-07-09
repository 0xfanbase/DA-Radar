"""The "no run, no cost" quota gate for analyze.yml.

Per CLAUDE.md's quota rules: the analyst/verifier jobs must exit
immediately if data/queue.json is empty -- no run, no cost. This is a
separate, cheap job in analyze.yml (no AI, no secret needed) so the
expensive AI jobs can be skipped entirely via `needs`/`if`, not merely
short-circuited after already starting.
"""
from __future__ import annotations

import argparse
import json
import os


def queue_is_empty(queue_path: str) -> bool:
    if not os.path.exists(queue_path):
        return True
    with open(queue_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return len(doc.get("items", [])) == 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Report whether the analyst queue is empty.")
    parser.add_argument("--queue", default="data/queue.json")
    parser.add_argument(
        "--github-output",
        default=os.environ.get("GITHUB_OUTPUT"),
        help="Path to append 'empty=true|false' to (defaults to $GITHUB_OUTPUT).",
    )
    args = parser.parse_args(argv)

    empty = queue_is_empty(args.queue)
    print(f"queue_check: {'empty -- nothing to analyze' if empty else 'has items -- proceeding'}")

    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as fh:
            fh.write(f"empty={'true' if empty else 'false'}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
