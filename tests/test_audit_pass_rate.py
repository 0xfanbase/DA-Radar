"""Tests for pipeline.audit.pass_rate."""
from __future__ import annotations

from pipeline.audit.pass_rate import check_pass_rate_regression, compute_pass_rate_snapshot


def test_compute_pass_rate_snapshot_counts_each_status():
    cards = [
        {"id": "a", "status": "verified"},
        {"id": "b", "status": "verified"},
        {"id": "c", "status": "unverified"},
        {"id": "d", "status": "corrected"},
    ]
    snapshot = compute_pass_rate_snapshot(cards)
    assert snapshot["event_type"] == "verifier_pass_rate_snapshot"
    assert snapshot["details"] == {
        "total": 4,
        "verified": 2,
        "unverified": 1,
        "corrected": 1,
        "pass_rate_pct": 50.0,
    }
    assert snapshot["related_ids"] == ["a", "b", "c", "d"]


def test_compute_pass_rate_snapshot_handles_zero_cards():
    snapshot = compute_pass_rate_snapshot([])
    assert snapshot["details"]["total"] == 0
    assert snapshot["details"]["pass_rate_pct"] is None
    assert "No published cards yet" in snapshot["summary"]


def test_check_pass_rate_regression_flags_a_real_drop():
    events = check_pass_rate_regression(60.0, 90.0, drop_threshold_pct=10.0)
    assert len(events) == 1
    assert events[0]["event_type"] == "verifier_pass_rate_regression"
    assert events[0]["details"]["drop_pct"] == 30.0


def test_check_pass_rate_regression_ignores_small_wobble():
    events = check_pass_rate_regression(88.0, 90.0, drop_threshold_pct=10.0)
    assert events == []


def test_check_pass_rate_regression_ignores_improvement():
    events = check_pass_rate_regression(95.0, 90.0, drop_threshold_pct=10.0)
    assert events == []


def test_check_pass_rate_regression_handles_no_previous_data():
    events = check_pass_rate_regression(80.0, None)
    assert events == []


def test_check_pass_rate_regression_handles_no_current_data():
    events = check_pass_rate_regression(None, 90.0)
    assert events == []
