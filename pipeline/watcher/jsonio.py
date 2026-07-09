"""Canonical JSON serialization and change-detection for committed data files.

All files under data/ use sort_keys, 2-space indent, and a trailing newline,
so two runs with identical semantic content produce byte-identical files --
this is what makes "re-run adds nothing" a literal, checkable git diff.
"""
from __future__ import annotations

import json
import os


def dumps_canonical(data: dict) -> str:
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_if_changed(path: str, data: dict, *, ignore_keys: tuple = ("generated_at",)) -> bool:
    """Write data to path as canonical JSON.

    Returns True iff the file's content actually changed, comparing
    everything except ignore_keys -- so timestamp churn alone never
    produces a write (and therefore never a git diff) on a true no-op run.
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            try:
                existing = json.load(fh)
            except json.JSONDecodeError:
                existing = None
        if isinstance(existing, dict):
            existing_comparable = {k: v for k, v in existing.items() if k not in ignore_keys}
            new_comparable = {k: v for k, v in data.items() if k not in ignore_keys}
            if existing_comparable == new_comparable:
                return False

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(dumps_canonical(data))
    return True
