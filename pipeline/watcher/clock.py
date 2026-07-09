"""Single source of truth for "current time" across the watcher.

Centralized so tests can monkeypatch one function instead of patching
datetime.now() calls scattered across modules.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
