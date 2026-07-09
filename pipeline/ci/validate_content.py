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
import sys

from jsonschema import Draft202012Validator

_SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas")

_PREFIX_MAPPING = (
    ("content/cards/", "card.json"),
    ("content/pillar_states/", "pillar_state.json"),
    ("content/glossary/", "glossary.json"),
)

_EXACT_MAPPING = {
    "content/trajectory.json": "trajectory.json",
    "content/document_library.json": "document_library.json",
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
