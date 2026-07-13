"""Pluggable watcher discovery mechanisms (P8).

pipeline/watcher/run.py's rss/atom path fetches a feed the regulator
publishes for machine consumption and parses it with pipeline/watcher/
parse.py. Not every regulator publishes one -- some only maintain an HTML
listing page (html_diff), an XML sitemap (sitemap_diff, not yet built), or
a JSON API (json_api, not yet built). Each mechanism module under this
package implements the same `discover(feed, *, source_id, user_agent,
fetch_cfg, etag, session) -> MechanismResult` contract (see
pipeline/watcher/mechanisms/base.py) so the orchestrator can dispatch on a
feed entry's "mechanism" field without knowing anything about how any one
mechanism actually gets its items.

Every mechanism module in this package holds no jurisdiction- or
regulator-specific literal (no site name, domain, or selector) -- all of
that comes from the feed's own config object, per CLAUDE.md's portability
rule. tests/test_jurisdiction_agnostic.py's banned-literal scan walks all
of pipeline/, which already covers this package with no test-file change
needed.

DISPATCH is the one table pipeline.watcher.run's per-feed loop reads to go
from a feed entry's "mechanism" string (default "rss", for backward
compatibility with every pre-P8 config that has no such field) to the
discover() callable that knows how to fetch and parse it. Adding mechanism
#6 is one new module (implementing the discover() contract in base.py)
plus one new line here plus one new enum value in
pipeline/schemas/jurisdiction.json -- never a growing if/elif chain in
run.py itself.
"""
from __future__ import annotations

from typing import Callable

from pipeline.watcher.mechanisms import atom, html_diff, json_api, rss, sitemap_diff
from pipeline.watcher.mechanisms.base import MechanismResult

DiscoverFn = Callable[..., MechanismResult]

DISPATCH: "dict[str, DiscoverFn]" = {
    "rss": rss.discover,
    "atom": atom.discover,
    "html_diff": html_diff.discover,
    "sitemap_diff": sitemap_diff.discover,
    "json_api": json_api.discover,
}
