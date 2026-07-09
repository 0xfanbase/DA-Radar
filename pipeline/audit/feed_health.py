"""Feed coverage/health check: per feed, when did the watcher last see a
new item?

Pure code, no AI, no live fetch of its own (link-rot already re-checks
live URLs) -- a deterministic proxy for "did the watcher silently stop
seeing something," not a claim of certainty. A feed with no new item in a
long time might simply mean the regulator published nothing new; it might
also mean the feed quietly broke. This check surfaces the fact for a
human to look at either way -- it does not and cannot decide which case
it is, since that requires either a live comparison against the
regulator's own page (a semantic judgment, deliberately out of scope for
this deterministic audit) or a human/analyst actually reading the feed.
"""
from __future__ import annotations

from datetime import date, datetime

DEFAULT_FEED_SILENCE_THRESHOLD_DAYS = 30


def check_feed_coverage(
    ledger: dict, *, today: date, silence_threshold_days: int = DEFAULT_FEED_SILENCE_THRESHOLD_DAYS
) -> list:
    last_seen_by_feed: dict = {}
    for item in ledger.get("items", {}).values():
        key = (item["source_id"], item["feed_id"])
        first_seen = datetime.strptime(item["first_seen"][:10], "%Y-%m-%d").date()
        if key not in last_seen_by_feed or first_seen > last_seen_by_feed[key]:
            last_seen_by_feed[key] = first_seen

    events = []
    for (source_id, feed_id), last_seen in sorted(last_seen_by_feed.items()):
        silence_days = (today - last_seen).days
        if silence_days > silence_threshold_days:
            events.append(
                {
                    "event_type": "feed_silence",
                    "summary": (
                        f"{source_id}/{feed_id} has produced no new item in {silence_days} days "
                        f"(threshold {silence_threshold_days}) -- worth confirming the feed is "
                        f"still reachable, not just quiet."
                    ),
                    "details": {
                        "source_id": source_id,
                        "feed_id": feed_id,
                        "last_seen": last_seen.isoformat(),
                        "silence_days": silence_days,
                        "threshold_days": silence_threshold_days,
                    },
                    "related_ids": [f"{source_id}/{feed_id}"],
                }
            )
    return events
