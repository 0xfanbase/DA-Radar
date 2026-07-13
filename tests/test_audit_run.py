"""Integration tests for pipeline.audit.run -- the weekly audit
orchestrator, against a small real (temp-directory) repo tree, never the
real repo's content/data.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

from pipeline.audit.run import ACTIONABLE_EVENT_TYPES, _append_backlog_entry, main, run_audit
from pipeline.watcher.clock import utc_now_iso


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def _days_ago_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_repo(root, *, card_status="verified", pillar_age_days=5, link_ok=True):
    """pillar_age_days: how many days ago the pillar/feed were last touched,
    relative to whenever the test actually runs -- deliberately not a
    hardcoded date, so this test doesn't quietly go stale itself."""
    pillar_last_changed = _days_ago_iso(pillar_age_days)[:10]
    _write_json(
        os.path.join(root, "content", "cards", "c1.json"),
        {
            "id": "c1",
            "status": card_status,
            "citations": [{"url": "https://example.invalid/source", "quote": "x"}],
        },
    )
    _write_json(
        os.path.join(root, "content", "pillar_states", "p1.json"),
        {"pillar": "stablecoins", "last_changed": pillar_last_changed, "key_links": []},
    )
    _write_json(os.path.join(root, "content", "trajectory.json"), [])
    _write_json(os.path.join(root, "content", "document_library.json"), {"documents": []})
    _write_json(
        os.path.join(root, "data", "ledger.json"),
        {
            "items": {
                "c1": {
                    "source_id": "hkma",
                    "feed_id": "hkma_press_release",
                    "first_seen": _days_ago_iso(pillar_age_days),
                }
            }
        },
    )


def test_run_audit_produces_a_pass_rate_snapshot_always(tmp_path, requests_mock, fixture_bytes):
    _build_repo(tmp_path)
    requests_mock.get(
        "https://example.invalid/source",
        content=fixture_bytes("sample_document.html"),
        headers={"Content-Type": "text/html"},
    )
    events = run_audit(str(tmp_path), run_ts=utc_now_iso())
    types = [e["event_type"] for e in events]
    assert "verifier_pass_rate_snapshot" in types
    # A working link and a fresh pillar/feed produce no other findings.
    assert not (set(types) & ACTIONABLE_EVENT_TYPES)


def test_run_audit_flags_broken_link_stale_pillar_and_silent_feed(tmp_path, requests_mock):
    _build_repo(tmp_path, pillar_age_days=200)
    requests_mock.get("https://example.invalid/source", status_code=404)
    events = run_audit(str(tmp_path), run_ts=utc_now_iso())
    types = {e["event_type"] for e in events}
    assert "link_rot" in types
    assert "staleness" in types
    assert "feed_silence" in types


def test_run_audit_uses_previous_latest_for_regression_detection(tmp_path, requests_mock, fixture_bytes):
    _build_repo(tmp_path, card_status="unverified")
    requests_mock.get(
        "https://example.invalid/source",
        content=fixture_bytes("sample_document.html"),
        headers={"Content-Type": "text/html"},
    )
    previous_latest = {
        "events": [
            {
                "event_type": "verifier_pass_rate_snapshot",
                "details": {"pass_rate_pct": 100.0},
            }
        ]
    }
    events = run_audit(str(tmp_path), run_ts=utc_now_iso(), previous_latest=previous_latest)
    types = [e["event_type"] for e in events]
    assert "verifier_pass_rate_regression" in types


def test_every_event_conforms_to_the_audit_event_schema(tmp_path, requests_mock, fixture_bytes):
    from jsonschema import Draft202012Validator

    from tests.conftest import REPO_ROOT

    _build_repo(tmp_path, pillar_age_days=200)
    requests_mock.get("https://example.invalid/source", status_code=404)
    events = run_audit(str(tmp_path), run_ts=utc_now_iso())

    schema_path = os.path.join(REPO_ROOT, "pipeline", "schemas", "audit", "event.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    validator = Draft202012Validator(schema)
    for event in events:
        validator.validate(event)


def test_main_writes_latest_json_and_appends_backlog_only_when_actionable(tmp_path, requests_mock):
    _build_repo(tmp_path, pillar_age_days=200)
    requests_mock.get("https://example.invalid/source", status_code=404)
    backlog_path = tmp_path / "IMPROVEMENT_BACKLOG.md"
    backlog_path.write_text("# IMPROVEMENT_BACKLOG.md\n")

    exit_code = main(["--repo-root", str(tmp_path)])
    assert exit_code == 0

    latest_path = tmp_path / "data" / "audit" / "latest.json"
    assert latest_path.exists()
    latest = json.loads(latest_path.read_text())
    assert latest["schema_version"] == 1
    assert len(latest["events"]) > 0

    backlog_text = backlog_path.read_text()
    assert "Audit findings" in backlog_text
    assert "link_rot" in backlog_text


def test_main_does_not_touch_backlog_on_a_fully_clean_run(tmp_path, requests_mock, fixture_bytes):
    _build_repo(tmp_path)
    requests_mock.get(
        "https://example.invalid/source",
        content=fixture_bytes("sample_document.html"),
        headers={"Content-Type": "text/html"},
    )
    backlog_path = tmp_path / "IMPROVEMENT_BACKLOG.md"
    original_text = "# IMPROVEMENT_BACKLOG.md\n"
    backlog_path.write_text(original_text)

    exit_code = main(["--repo-root", str(tmp_path)])
    assert exit_code == 0
    assert backlog_path.read_text() == original_text


def test_append_backlog_entry_is_idempotent_for_identical_same_day_events(tmp_path, capsys):
    backlog_path = tmp_path / "IMPROVEMENT_BACKLOG.md"
    backlog_path.write_text("# IMPROVEMENT_BACKLOG.md\n")

    actionable_events = [
        {"event_type": "link_rot", "summary": "https://example.invalid/source returned 404"},
        {"event_type": "staleness", "summary": "stablecoins pillar last changed 200 days ago"},
    ]
    run_ts = utc_now_iso()

    _append_backlog_entry(str(backlog_path), actionable_events, run_ts=run_ts)
    text_after_first = backlog_path.read_text()
    assert text_after_first.count("## Audit findings,") == 1
    assert "link_rot" in text_after_first
    assert "staleness" in text_after_first

    # Re-run with the exact same events on the same day: must not duplicate
    # the block, and must say so rather than doing nothing unexplained.
    _append_backlog_entry(str(backlog_path), actionable_events, run_ts=run_ts)
    text_after_second = backlog_path.read_text()
    assert text_after_second == text_after_first
    assert text_after_second.count("## Audit findings,") == 1

    captured = capsys.readouterr()
    assert "skipping backlog append" in captured.out
