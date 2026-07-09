"""Staleness check: flag any pillar whose last_changed date is older than
a threshold.

Pure date arithmetic, no network, no AI -- deliberately does NOT attempt
to verify whether the pillar's content still matches the regulator's live
page (that would require either a live fetch-and-compare, which link-rot
already covers for the pillar's own key_links, or semantic judgment about
whether anything material changed, which is exactly the kind of call this
audit loop must NOT make on its own -- see IMPROVEMENT_BACKLOG.md). A
stale pillar is a prompt for a human (or a future analyst run) to look,
not a claim that something is actually wrong.
"""
from __future__ import annotations

from datetime import date, datetime

DEFAULT_STALENESS_THRESHOLD_DAYS = 45


def check_staleness(pillar_states: list, *, today: date, threshold_days: int = DEFAULT_STALENESS_THRESHOLD_DAYS) -> list:
    events = []
    for state in pillar_states:
        last_changed = datetime.strptime(state["last_changed"], "%Y-%m-%d").date()
        age_days = (today - last_changed).days
        if age_days > threshold_days:
            events.append(
                {
                    "event_type": "staleness",
                    "summary": (
                        f"Pillar '{state['pillar']}' last changed {age_days} days ago "
                        f"(threshold {threshold_days}) -- worth a human check against the "
                        f"regulator's own page."
                    ),
                    "details": {
                        "pillar": state["pillar"],
                        "last_changed": state["last_changed"],
                        "age_days": age_days,
                        "threshold_days": threshold_days,
                    },
                    "related_ids": [state["pillar"]],
                }
            )
    return events
