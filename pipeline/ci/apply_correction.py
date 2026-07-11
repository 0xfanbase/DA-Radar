"""Applies a single correction to a previously published card.

Deterministic code, no judgment of its own about what needs correcting or
why -- that call is always a human's, supplied as explicit input (CLI
arguments here; a GitHub Actions workflow_dispatch form in
.github/workflows/correction.yml). This module only ever records and
applies a correction it is explicitly told to make; it never decides on
its own that something needs correcting (that would make the deterministic
"never trust a single pass" principle this whole project is built on cut
the other way -- a correction is a public statement that a past claim was
wrong, and getting THAT wrong is a worse integrity failure than the
original error).

Deliberately not wired to auto-trigger from audit.yml's findings: a broken
link or a stale pillar is a prompt for a human to look, not evidence that
a specific card's specific claim is actually incorrect. See
IMPROVEMENT_BACKLOG.md.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

SCHEMA_VERSION = 1


def build_correction_record(
    *,
    correction_id: str,
    card_id: str,
    corrected_at: str,
    correction_note: str,
    fields_changed: list,
    citations: list,
    jurisdiction: str = "hk",
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": correction_id,
        "jurisdiction": jurisdiction,
        "card_id": card_id,
        "corrected_at": corrected_at,
        "correction_note": correction_note,
        "fields_changed": fields_changed,
        "citations": citations,
    }


def apply_correction_to_card(card: dict, correction: dict) -> dict:
    """Returns a NEW card dict (the input is never mutated): status set to
    "corrected", correction_note set to the human-supplied explanation,
    and the correction's own supporting citations (if any) merged into
    the card's citations[] -- de-duplicated by (url, quote), so a
    correction's new citation actually becomes part of what the
    deterministic verification gate re-checks afterward (see
    .github/workflows/correction.yml), rather than being recorded in
    data/corrections.json but never itself verified. Re-applying the
    same correction is idempotent (no duplicate citation entries)."""
    new_card = dict(card)
    new_card["status"] = "corrected"
    new_card["correction_note"] = correction["correction_note"]

    correction_citations = correction.get("citations", [])
    if correction_citations:
        merged = list(card.get("citations", []))
        seen = {(c["url"], c["quote"]) for c in merged}
        for citation in correction_citations:
            key = (citation["url"], citation["quote"])
            if key not in seen:
                merged.append(citation)
                seen.add(key)
        new_card["citations"] = merged

    return new_card


def append_correction_record(corrections_path: str, correction: dict) -> list:
    """Returns the full, updated list of correction records (existing +
    this one). Does not itself write the file -- callers own that, same
    "deterministic code owns every mutation" pattern as the ledger."""
    existing = []
    if os.path.exists(corrections_path):
        with open(corrections_path, "r", encoding="utf-8") as fh:
            existing = json.load(fh)
    return existing + [correction]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply a human-supplied correction to a previously published card."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--jurisdiction",
        default="hk",
        help=(
            "Jurisdiction id (e.g. 'hk') owning the card being corrected -- resolves "
            "the card's conventional path (content/<jurisdiction>/cards/<card-id>.json) "
            "and is recorded on the correction record itself, since data/corrections.json "
            "stays a single global file with each record carrying its own jurisdiction."
        ),
    )
    parser.add_argument("--card-id", required=True)
    parser.add_argument("--correction-id", required=True)
    parser.add_argument("--corrected-at", required=True, help="ISO-8601 UTC timestamp.")
    parser.add_argument("--correction-note", required=True)
    parser.add_argument("--fields-changed", required=True, help="Comma-separated field names.")
    parser.add_argument(
        "--citation",
        action="append",
        default=[],
        metavar="URL|QUOTE",
        help="Repeatable. One '|'-separated url|quote pair per supporting citation for the correction.",
    )
    args = parser.parse_args(argv)

    card_glob = glob.glob(
        os.path.join(args.repo_root, "content", args.jurisdiction, "cards", f"{args.card_id}.json")
    )
    if not card_glob:
        print(f"apply_correction: no card found for id {args.card_id!r}", file=sys.stderr)
        return 1
    card_path = card_glob[0]

    with open(card_path, "r", encoding="utf-8") as fh:
        card = json.load(fh)

    citations = []
    for raw in args.citation:
        url, _, quote = raw.partition("|")
        citations.append({"url": url, "quote": quote})

    correction = build_correction_record(
        correction_id=args.correction_id,
        card_id=args.card_id,
        corrected_at=args.corrected_at,
        correction_note=args.correction_note,
        fields_changed=[f.strip() for f in args.fields_changed.split(",") if f.strip()],
        citations=citations,
        jurisdiction=args.jurisdiction,
    )

    corrected_card = apply_correction_to_card(card, correction)
    with open(card_path, "w", encoding="utf-8") as fh:
        json.dump(corrected_card, fh, sort_keys=True, indent=2, ensure_ascii=False)
        fh.write("\n")

    corrections_path = os.path.join(args.repo_root, "data", "corrections.json")
    updated_corrections = append_correction_record(corrections_path, correction)
    os.makedirs(os.path.dirname(corrections_path), exist_ok=True)
    with open(corrections_path, "w", encoding="utf-8") as fh:
        json.dump(updated_corrections, fh, sort_keys=True, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"apply_correction: recorded correction {args.correction_id} for card {args.card_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
