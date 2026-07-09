"""Applies the non-bypassable verification gate (pipeline/verify/gate.py)
to real card files on disk -- the actual CI-job wiring of that gate into
the file-based pipeline, not just in-memory dicts.

Run as the final step of the verifier job in analyze.yml, after the
verifier LLM pass and before any commit: re-checks every citation in
every changed card file for real (live re-fetch), and rewrites the file
if the gate downgrades its status. This is what makes "never trust the
LLM's self-report" real for files on disk.
"""
from __future__ import annotations

import argparse
import json
import os

from pipeline.ci.path_allowlist import get_uncommitted_changed_paths
from pipeline.verify.gate import enforce_verification_gate

DEFAULT_FETCH_KWARGS = dict(timeout=15, max_retries=3, backoff_base=1.0, backoff_multiplier=2.0)
DEFAULT_USER_AGENT = (
    "HKDigitalAssetRadarVerifier/0.1 "
    "(contact: bot@users.noreply.github.com; purpose: citation re-verification)"
)


def apply_gate_to_file(path: str, *, user_agent: str, **fetch_kwargs) -> bool:
    """Re-checks and possibly rewrites one card file in place.

    Returns True iff the file's status was changed (downgraded to
    "unverified" by the gate).
    """
    with open(path, "r", encoding="utf-8") as fh:
        card = json.load(fh)

    gated = enforce_verification_gate(card, user_agent=user_agent, **fetch_kwargs)

    if gated["status"] != card.get("status"):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(gated, fh, sort_keys=True, indent=2, ensure_ascii=False)
            fh.write("\n")
        return True
    return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-check every changed card's citations for real; downgrade to unverified on failure."
    )
    parser.add_argument("--repo-dir", default=".")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    args = parser.parse_args(argv)

    changed = get_uncommitted_changed_paths(args.repo_dir)
    card_paths = [p for p in changed if p.startswith("content/cards/") and p.endswith(".json")]

    if not card_paths:
        print("apply_verification_gate: no changed card files.")
        return 0

    for rel_path in card_paths:
        full_path = os.path.join(args.repo_dir, rel_path)
        downgraded = apply_gate_to_file(full_path, user_agent=args.user_agent, **DEFAULT_FETCH_KWARGS)
        note = "downgraded to unverified" if downgraded else "citations OK"
        print(f"  [{rel_path}] {note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
