"""Shared contract every watcher discovery mechanism module implements.

pipeline/watcher/run.py's existing rss/atom path already has this shape
implicitly (fetch_feed -> parse_rss/parse_atom -> list[NormalizedItem],
with pipeline/watcher/parse.py's FeedParseError as the one recoverable,
per-feed error). This module makes that shape explicit and reusable so a
non-feed mechanism (html_diff first, sitemap_diff/json_api later) can
report the same three outcomes -- ok, not_modified, error -- through one
result type, and so a mechanism's internal failure can distinguish *why*
it failed without the orchestrator needing to know mechanism-specific
exception types.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pipeline.watcher.parse import NormalizedItem


class MechanismError(Exception):
    """Base class for a mechanism's own loud, distinguishable failure
    kinds. Every subclass sets error_kind so a mechanism's discover()
    can catch this one base class and map it onto
    MechanismResult(status="error", error_kind=...) without a
    mechanism-specific except clause. Never let one of these (or the
    exception it wraps) propagate out of discover() itself -- discover()
    must always return a MechanismResult, mirroring the containment
    contract pipeline/watcher/run.py already relies on for
    pipeline.watcher.parse.FeedParseError: one feed's failure is recorded
    in the run summary, never lets a single bad or hostile source abort
    the rest of a watcher run."""

    error_kind: str = "error"

    def __init__(self, message: str):
        super().__init__(message)


class MechanismFetchError(MechanismError):
    """HTTP-level failure fetching the mechanism's one configured URL.
    In practice mechanisms reuse pipeline/watcher/fetch.py's fetch_feed
    directly and map its own status=="error" result onto this error_kind
    without ever needing to raise/catch this class -- it exists so every
    mechanism's error taxonomy is expressed the same way regardless of
    whether a given mechanism ever actually raises it."""

    error_kind = "fetch"


class MechanismParseError(MechanismError):
    """The fetched content could not be parsed as the format the
    mechanism expects at all (e.g. not HTML, not XML, not JSON) --
    distinct from StructureError, which is content that parses fine but
    doesn't match the configured selectors/paths."""

    error_kind = "parse"


class MechanismStructureError(MechanismError):
    """Content parsed fine, but the configured selector/path found
    nothing (or found elements that yielded nothing usable). This is the
    "the source was redesigned out from under us" signal -- it must never
    be reachable from the same code path as a genuine "nothing new
    today," so a broken selector can never quietly masquerade as a quiet
    source."""

    error_kind = "structure"


@dataclass
class MechanismResult:
    """What every mechanism's discover() returns, always -- never raises.

    status: "ok" (items may be empty only in the sense of "0 new after
      ledger diff" -- see each mechanism's own docstring for whether it can
      ever return an empty items list from a *successful* parse), "not_modified"
      (conditional GET hit, no content to parse), or "error".
    items: parsed NormalizedItem list; only ever non-empty when status=="ok".
    etag: the ETag to persist for next run's conditional GET, when the
      fetch returned one (carries the *previous* etag forward on
      not_modified, matching fetch_feed's own contract).
    error / error_kind: populated only when status=="error"; error_kind is
      one of "fetch" | "parse" | "structure", per MechanismError's
      subclasses above.
    http_status: provenance only, populated when known.
    """

    status: str
    items: list["NormalizedItem"] = field(default_factory=list)
    etag: Optional[str] = None
    error: Optional[str] = None
    error_kind: Optional[str] = None
    http_status: Optional[int] = None
