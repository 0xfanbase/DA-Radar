"""Schema-validation CI gate: every changed file under content/ or data/
must validate against its corresponding JSON schema (the spec's
"jsonschema validation of all changed files"), run alongside the
path-allowlist gate before any AI-job commit.

The content/ path convention below is this build's own design -- the spec
names the content directory and the schemas but does not define a file
layout within content/ (see IMPROVEMENT_BACKLOG.md). No real content
exists yet (that's Phase 3); this module just needs to know where future
content WILL live so it can validate it.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys

from jsonschema import Draft202012Validator

_SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas")

# Guards against the 2026-07-09 correction recurring: an internal Claude
# model-version identifier (e.g. "claude-sonnet-5") was written into the
# `model` field of 5 cards + start_here.json and published live. The fix
# at the time was prompt-text-only (analyst_prompt.md wording) -- the same
# enforcement class that let the leak happen in the first place, since a
# prompt instruction is not a gate. This is the deterministic backstop:
# every schema-governed content file's `model` field (wherever the schema
# defines one -- card.json, glossary.json, pillar_state.json,
# start_here.json, trajectory.json's per-item `model`) is checked against
# reject patterns for internal-identifier *shapes*, not a denylist of
# specific strings, so it also catches future model names we haven't seen.
#
# Deliberately narrow, per IMPROVEMENT_BACKLOG.md's own warning against "a
# blanket pattern that could false-positive a legitimate display name":
# human-readable names ("Claude (Anthropic)", "GPT-4 (OpenAI)", "not
# recorded (pre-provenance content)") use capitalization, spaces, and/or
# parentheses, none of which these patterns match.
_INTERNAL_MODEL_ID_PATTERNS = (
    # Lowercase-hyphenated "claude-<family>-<tier>" tokens, with or without
    # a trailing dated version suffix -- e.g. "claude-sonnet-5",
    # "claude-opus-4-1", "claude-opus-4-5-20251101",
    # "claude-3-7-sonnet-20250219", "claude-haiku-4-5-20251001".
    re.compile(r"^claude[-_][a-z0-9][a-z0-9.\-]*$"),
    # A bare dated version suffix on its own, or trailing on any
    # lowercase-hyphenated token regardless of family word -- an 8-digit
    # YYYYMMDD is not a human-readable name under any circumstance.
    re.compile(r"(?:^|-)\d{8}$"),
    # Bare version numbers with no descriptive name at all -- e.g. "4.5",
    # "4-1", "v5", "5.2.1" -- conveys no human-readable information and is
    # the shape of an internal version tag, not a display name.
    re.compile(r"^v?\d+(?:[.\-]\d+)*$"),
)


def _internal_model_id_reason(value: str) -> str | None:
    """Returns a human-readable reason if `value` has the shape of an
    internal model-version identifier, or None if it looks like an
    acceptable human-readable display name."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    for pattern in _INTERNAL_MODEL_ID_PATTERNS:
        if pattern.match(candidate):
            return (
                f"model field {value!r} looks like an internal model-version "
                "identifier, not a human-readable display name (e.g. "
                '"Claude (Anthropic)") -- see the 2026-07-09 correction in '
                "IMPROVEMENT_BACKLOG.md"
            )
    return None


def _model_field_values(data):
    """Yields every `model` field value present in a parsed content file,
    handling both single-object content types (card/glossary/pillar_state/
    start_here) and trajectory.json's array-of-objects shape."""
    records = data if isinstance(data, list) else [data]
    for record in records:
        if isinstance(record, dict) and "model" in record:
            yield record["model"]


def check_model_field_leak(data) -> str | None:
    """Returns an error message if any `model` field in `data` has the
    shape of an internal model-version identifier, else None."""
    for value in _model_field_values(data):
        reason = _internal_model_id_reason(value)
        if reason is not None:
            return reason
    return None


_PREFIX_MAPPING = (
    ("content/cards/", "card.json"),
    ("content/pillar_states/", "pillar_state.json"),
    ("content/glossary/", "glossary.json"),
)

_EXACT_MAPPING = {
    "content/trajectory.json": "trajectory.json",
    "content/document_library.json": "document_library.json",
    "content/start_here.json": "start_here.json",
    "data/ledger.json": "ledger.json",
    "data/queue.json": "queue.json",
    "data/corrections.json": "corrections.json",
}


def _schema_path_for(changed_path: str):
    """Map a changed file's repo-relative path to its schema file's path,
    or None if no schema governs this path."""
    normalized = posixpath.normpath(changed_path.replace("\\", "/")).lstrip("/")

    for prefix, schema_name in _PREFIX_MAPPING:
        if normalized.startswith(prefix) and normalized.endswith(".json"):
            return os.path.join(_SCHEMAS_DIR, schema_name)

    if normalized in _EXACT_MAPPING:
        return os.path.join(_SCHEMAS_DIR, _EXACT_MAPPING[normalized])

    if normalized.startswith("data/audit/") and normalized.endswith(".json"):
        return os.path.join(_SCHEMAS_DIR, "audit", "event.json")

    return None


def validate_file(changed_path: str, *, repo_dir: str = ".") -> tuple:
    """Returns (schema_applicable, ok, error)."""
    schema_path = _schema_path_for(changed_path)
    if schema_path is None:
        return (False, True, None)

    full_path = os.path.join(repo_dir, changed_path)
    try:
        with open(full_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return (True, False, f"could not read/parse {changed_path}: {exc}")

    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=str)
    if errors:
        message = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:5])
        return (True, False, message)

    leak_reason = check_model_field_leak(data)
    if leak_reason is not None:
        return (True, False, f"{changed_path}: {leak_reason}")

    return (True, True, None)


def validate_changed_paths(changed_paths, *, repo_dir: str = ".") -> tuple:
    """Returns (ok, results) where results is [(path, ok, error), ...] for
    every changed path that had an applicable schema (paths with no
    applicable schema are silently skipped, not reported)."""
    results = [
        (path, ok, error)
        for path in changed_paths
        for applicable, ok, error in [validate_file(path, repo_dir=repo_dir)]
        if applicable
    ]
    return all(ok for _, ok, _ in results), results


def main(argv=None) -> int:
    from pipeline.ci.path_allowlist import get_uncommitted_changed_paths

    parser = argparse.ArgumentParser(
        description="Validate changed content/data files against their JSON schemas."
    )
    parser.add_argument("--repo-dir", default=".")
    args = parser.parse_args(argv)

    changed = get_uncommitted_changed_paths(args.repo_dir)
    ok, results = validate_changed_paths(changed, repo_dir=args.repo_dir)

    if not results:
        print("validate_content: no schema-governed files changed.")
        return 0

    for path, file_ok, error in results:
        status = "OK" if file_ok else f"FAIL ({error})"
        print(f"  [{path}] {status}")

    if ok:
        print(f"validate_content: OK -- {len(results)} file(s) validated.")
        return 0

    print("validate_content: FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
