"""Weekly audit orchestrator + CLI (pipeline.audit.run).

Pure deterministic code, no AI, mirroring watch.yml's own category exactly
-- every check here is mechanically decidable (a URL either resolves or it
doesn't; a date either exceeds a threshold or it doesn't; a pass-rate
either dropped or it didn't). Four checks: link-rot, pillar staleness,
feed coverage/silence, verifier pass-rate trend. Writes data/audit/latest.json
(schema-governed, renders on the Method & Audit page) and appends an
IMPROVEMENT_BACKLOG.md entry -- but only when there is an actual finding to
report, never for a routine clean run (a clean week leaves no trace beyond
the routine pass-rate snapshot, same "no run, no cost" spirit as the
watcher's own empty-queue fast exit).

Trend comparison deliberately reads the *previous* data/audit/latest.json
(before it gets overwritten this run) rather than maintaining a separate
running-history file -- avoids introducing a second, ungoverned data file
with no schema of its own. This means the pass-rate trend is only ever a
one-run-back comparison, not a full time series; a real trend chart is a
reasonable future enhancement, not something this v1 claims to provide.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime

from pipeline.audit.feed_health import check_feed_coverage
from pipeline.audit.linkrot import check_link_rot
from pipeline.audit.pass_rate import check_pass_rate_regression, compute_pass_rate_snapshot
from pipeline.audit.staleness import check_staleness
from pipeline.watcher.clock import utc_now_iso
from pipeline.watcher.jsonio import write_if_changed

SCHEMA_VERSION = 1
DEFAULT_FETCH_KWARGS = dict(timeout=15, max_retries=3, backoff_base=1.0, backoff_multiplier=2.0)
DEFAULT_USER_AGENT = (
    "GlobalDigitalAssetRadarAuditor/0.1 (contact: da-radar-bot@users.noreply.github.com; purpose: link-rot/staleness audit)"
)

# event_types that represent an actionable problem worth logging to
# IMPROVEMENT_BACKLOG.md -- verifier_pass_rate_snapshot is a routine metric
# point, not itself a finding, so it is excluded here.
ACTIONABLE_EVENT_TYPES = {"link_rot", "staleness", "feed_silence", "verifier_pass_rate_regression"}


def _load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_json_glob(pattern: str) -> list:
    return [_load_json(path) for path in sorted(glob.glob(pattern))]


def _finalize_event(event: dict, *, run_ts: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "event_type": event["event_type"],
        "timestamp": run_ts,
        "actor": "audit.yml",
        "summary": event["summary"],
        "details": event["details"],
        "related_ids": event["related_ids"],
    }


def _previous_pass_rate_pct(previous_latest: dict):
    if not previous_latest:
        return None
    for event in previous_latest.get("events", []):
        if event.get("event_type") == "verifier_pass_rate_snapshot":
            return event["details"]["pass_rate_pct"]
    return None


def run_audit(
    repo_root: str,
    *,
    run_ts: str,
    jurisdiction: str | None = None,
    previous_latest: dict = None,
    user_agent: str = DEFAULT_USER_AGENT,
    **fetch_kwargs,
) -> list:
    """Runs all four checks against real repo content. Returns the full
    list of finalized (schema-shaped) events for this run.

    jurisdiction, when given, scopes the content/data read to
    content/<jurisdiction>/... and data/<jurisdiction>/ledger.json (the
    registry-model pivot's per-jurisdiction layout). Omitting it preserves
    this module's original flat content/*, data/ledger.json paths --
    wiring this up to walk every jurisdiction in config/site.json is
    deliberately deferred to a later step, same as pipeline/site/data.py."""
    fetch_kwargs = fetch_kwargs or DEFAULT_FETCH_KWARGS
    today = datetime.fromisoformat(run_ts.replace("Z", "+00:00")).date()

    content_root = os.path.join(repo_root, "content", jurisdiction) if jurisdiction else os.path.join(
        repo_root, "content"
    )
    data_root = os.path.join(repo_root, "data", jurisdiction) if jurisdiction else os.path.join(repo_root, "data")

    cards = [c for c in _load_json_glob(os.path.join(content_root, "cards", "*.json")) if c]
    pillar_states = [p for p in _load_json_glob(os.path.join(content_root, "pillar_states", "*.json")) if p]
    trajectory = _load_json(os.path.join(content_root, "trajectory.json"), [])
    document_library = _load_json(os.path.join(content_root, "document_library.json"), {"documents": []})
    ledger = _load_json(os.path.join(data_root, "ledger.json"), {"items": {}})

    events = []
    events += check_link_rot(
        cards=cards,
        pillar_states=pillar_states,
        trajectory=trajectory,
        document_library=document_library,
        user_agent=user_agent,
        **fetch_kwargs,
    )
    events += check_staleness(pillar_states, today=today)
    events += check_feed_coverage(ledger, today=today)

    snapshot = compute_pass_rate_snapshot(cards)
    previous_pct = _previous_pass_rate_pct(previous_latest)
    events.append(snapshot)
    events += check_pass_rate_regression(snapshot["details"]["pass_rate_pct"], previous_pct)

    return [_finalize_event(e, run_ts=run_ts) for e in events]


def _append_backlog_entry(backlog_path: str, actionable_events: list, *, run_ts: str) -> None:
    if not actionable_events:
        return
    lines = [f"\n## Audit findings, {run_ts[:10]}\n\n"]
    for event in actionable_events:
        lines.append(f"- **{event['event_type']}**: {event['summary']}\n")
    with open(backlog_path, "a", encoding="utf-8") as fh:
        fh.writelines(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the weekly HK Digital Asset Radar audit.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--jurisdiction",
        default=None,
        help=(
            "Jurisdiction id (e.g. 'hk'). Scopes the content/data read to "
            "content/<id>/... and data/<id>/ledger.json; omitting it preserves the "
            "original flat content/*, data/ledger.json paths."
        ),
    )
    args = parser.parse_args(argv)

    run_ts = utc_now_iso()
    # data/audit/latest.json and IMPROVEMENT_BACKLOG.md stay single, global
    # files regardless of --jurisdiction -- pipeline/schemas/audit/event.json
    # carries no jurisdiction_id field, matching CLAUDE.md's own accounting
    # of the audit loop as not yet a fully-built, jurisdiction-aware phase.
    latest_path = os.path.join(args.repo_root, "data", "audit", "latest.json")
    previous_latest = _load_json(latest_path)

    events = run_audit(
        args.repo_root, run_ts=run_ts, jurisdiction=args.jurisdiction, previous_latest=previous_latest
    )

    write_if_changed(latest_path, {"schema_version": SCHEMA_VERSION, "generated_at": run_ts, "events": events})

    actionable = [e for e in events if e["event_type"] in ACTIONABLE_EVENT_TYPES]
    backlog_path = os.path.join(args.repo_root, "IMPROVEMENT_BACKLOG.md")
    _append_backlog_entry(backlog_path, actionable, run_ts=run_ts)

    print(f"audit: {len(events)} event(s), {len(actionable)} actionable finding(s).")
    for event in events:
        print(f"  [{event['event_type']}] {event['summary']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
