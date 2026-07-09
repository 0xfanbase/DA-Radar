"""Verifier pass-rate snapshot and trend: what fraction of published cards
are actually status=="verified".

Pure arithmetic over already-published card files, no AI, no network.
Always produces exactly one snapshot event (unlike the other checks,
which only produce an event when something is wrong) -- a trend needs a
data point on every run, not just the runs where something looks off.
"""
from __future__ import annotations


def compute_pass_rate_snapshot(cards: list) -> dict:
    total = len(cards)
    verified = sum(1 for c in cards if c.get("status") == "verified")
    unverified = sum(1 for c in cards if c.get("status") == "unverified")
    corrected = sum(1 for c in cards if c.get("status") == "corrected")
    pass_rate_pct = round(100 * verified / total, 1) if total else None

    return {
        "event_type": "verifier_pass_rate_snapshot",
        "summary": (
            f"{verified}/{total} published cards verified ({pass_rate_pct}%)"
            if total
            else "No published cards yet."
        ),
        "details": {
            "total": total,
            "verified": verified,
            "unverified": unverified,
            "corrected": corrected,
            "pass_rate_pct": pass_rate_pct,
        },
        "related_ids": [c["id"] for c in cards],
    }


def check_pass_rate_regression(current_pct, previous_pct, *, drop_threshold_pct: float = 10.0) -> list:
    """Compares the current snapshot's pass rate against the most recent
    prior one. Returns a regression event only if it dropped by more than
    drop_threshold_pct -- a small run-to-run wobble (e.g. one new
    unverified card among many verified ones) is not itself a finding."""
    if current_pct is None or previous_pct is None:
        return []
    drop = previous_pct - current_pct
    if drop > drop_threshold_pct:
        return [
            {
                "event_type": "verifier_pass_rate_regression",
                "summary": (
                    f"Verifier pass rate dropped from {previous_pct}% to {current_pct}% "
                    f"(-{round(drop, 1)} points)."
                ),
                "details": {
                    "previous_pct": previous_pct,
                    "current_pct": current_pct,
                    "drop_pct": round(drop, 1),
                },
                "related_ids": [],
            }
        ]
    return []
