"""Applies the non-bypassable verification gate (pipeline/verify/gate.py)
to real card files on disk -- the actual CI-job wiring of that gate into
the file-based pipeline, not just in-memory dicts.

Run as the final step of the verifier job in analyze.yml, after the
verifier LLM pass and before any commit: re-checks every citation in
every changed card file for real (live re-fetch), enforces the
15-word/one-per-source quote policy (pipeline/verify/quote_policy.py),
and rewrites the file if the gate downgrades its status. This is what
makes "never trust the LLM's self-report" real for files on disk.
"""
from __future__ import annotations

import argparse
import json
import os
import re

from pipeline.ci.path_allowlist import get_uncommitted_changed_paths
from pipeline.verify.authenticity import official_domains_from_config
from pipeline.verify.gate import enforce_full_gate
from pipeline.watcher.run import load_jurisdiction

DEFAULT_FETCH_KWARGS = dict(timeout=15, max_retries=3, backoff_base=1.0, backoff_multiplier=2.0)
DEFAULT_USER_AGENT = (
    "GlobalDigitalAssetRadarVerifier/0.1 "
    "(contact: da-radar-bot@users.noreply.github.com; purpose: citation re-verification)"
)

# Matches content/<jurisdiction_id>/cards/<id>.json for any jurisdiction id
# (registry-model pivot) -- deliberately not scoped to a single jurisdiction
# here, since a changed-paths list from one CI run can in principle span
# more than one jurisdiction's cards. The jurisdiction id is captured so
# callers can verify a card's own path against an expected --jurisdiction.
_CARD_PATH_RE = re.compile(r"^content/(?P<jurisdiction>[^/]+)/cards/[^/]+\.json$")


class JurisdictionMismatchError(Exception):
    """Raised when --jurisdiction=X is given but one or more matched card
    paths belong to a different jurisdiction's content/<jid>/cards/ tree.

    Applying X's official-domain allowlist to a card from another
    jurisdiction would silently validate (or invalidate) citations against
    the wrong regulator list -- a correctness gap that must fail loudly
    rather than be papered over, once a CI run's diff can span more than
    one jurisdiction (P9 onward)."""


def _assert_single_jurisdiction(card_paths: list, expected_jurisdiction: str) -> None:
    """Fails loudly if any card path's own jurisdiction segment differs
    from --jurisdiction. No-op when --jurisdiction wasn't given."""
    if not expected_jurisdiction:
        return
    mismatched = []
    for rel_path in card_paths:
        match = _CARD_PATH_RE.match(rel_path)
        if match and match.group("jurisdiction") != expected_jurisdiction:
            mismatched.append(rel_path)
    if mismatched:
        listing = ", ".join(sorted(mismatched))
        raise JurisdictionMismatchError(
            f"apply_verification_gate: --jurisdiction={expected_jurisdiction!r} was given, but the "
            f"changed-files diff also contains card(s) belonging to a different jurisdiction: "
            f"{listing}. Refusing to apply {expected_jurisdiction!r}'s official-domain allowlist to "
            f"card(s) outside that jurisdiction. Run apply_verification_gate.py separately per "
            f"jurisdiction, or split the diff so each run's changed files belong to one jurisdiction."
        )


def _load_official_domains(config_path: str) -> list:
    """Derives the official-domain allowlist from the jurisdiction config.

    A missing config file fails closed (empty allowlist -- every citation
    is then rejected by the domain check) rather than raising, so a
    caller that hasn't wired a config path yet gets a safe default, not a
    crash."""
    if not os.path.isfile(config_path):
        return []
    return official_domains_from_config(load_jurisdiction(config_path))


def apply_gate_to_file(path: str, *, user_agent: str, official_domains: list, **fetch_kwargs) -> bool:
    """Re-checks and possibly rewrites one card file in place.

    Returns True iff the file changed -- either the status was
    downgraded to "unverified" (citation or numeric-claim failure), or
    the set of unsupported numeric claims changed while status stayed
    the same. Compares the whole card, not just status, since
    numeric_claims_unsupported can change independently of status only
    in the direction "was unsupported, now traceable" -- which still
    needs writing back so a stale finding doesn't linger in the file.
    """
    with open(path, "r", encoding="utf-8") as fh:
        card = json.load(fh)

    gated = enforce_full_gate(card, user_agent=user_agent, official_domains=official_domains, **fetch_kwargs)

    if gated != card:
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
    parser.add_argument(
        "--jurisdiction",
        default=None,
        help=(
            "Jurisdiction id (e.g. 'hk'). Resolves --config-path to its conventional "
            "path; --config-path passed explicitly still overrides that default."
        ),
    )
    parser.add_argument(
        "--config-path",
        default=None,
        help=(
            "Path to the jurisdiction config. Defaults to "
            "<repo-dir>/config/jurisdictions/<jurisdiction>.json when --jurisdiction "
            "is given, else <repo-dir>/config/jurisdiction.json."
        ),
    )
    args = parser.parse_args(argv)

    changed = get_uncommitted_changed_paths(args.repo_dir)
    card_paths = [p for p in changed if _CARD_PATH_RE.match(p)]

    if not card_paths:
        print("apply_verification_gate: no changed card files.")
        return 0

    _assert_single_jurisdiction(card_paths, args.jurisdiction)

    if args.config_path:
        config_path = args.config_path
    elif args.jurisdiction:
        config_path = os.path.join(args.repo_dir, "config", "jurisdictions", f"{args.jurisdiction}.json")
    else:
        config_path = os.path.join(args.repo_dir, "config", "jurisdiction.json")
    official_domains = _load_official_domains(config_path)

    for rel_path in card_paths:
        full_path = os.path.join(args.repo_dir, rel_path)
        downgraded = apply_gate_to_file(
            full_path, user_agent=args.user_agent, official_domains=official_domains, **DEFAULT_FETCH_KWARGS
        )
        note = "downgraded to unverified" if downgraded else "citations OK"
        print(f"  [{rel_path}] {note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
