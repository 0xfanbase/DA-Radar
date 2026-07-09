# IMPROVEMENT_BACKLOG.md

Every place the build spec was silent and a call had to be made, logged here with the decision
and reasoning, plus known deviations from the ideal spec and open follow-ups for later phases.
Dated by the build session that made the call.

## Deviations from spec (not silence — explicit conflict with this environment)

- **2026-07-09 — Anonymous GitHub org (spec §1.5).** The spec calls for a fresh GitHub org with a
  neutral name to own the repo. This build runs inside an already-assigned repository/branch
  (`0xfanbase/DA-Radar`, `claude/hk-radar-phase-1-mzlnxx`) that could not be changed within this
  session. Honored instead: bot commit identity (`hk-radar-bot <bot@users.noreply.github.com>`
  via env vars, never git config), zero personal identifiers anywhere in code/commits/docs. Not
  honored: the literal "fresh org" mechanic. Follow-up: if/when the project is moved to a
  dedicated anonymous org, this is a pure infrastructure move, no content changes needed.
- **2026-07-09 — Pre-existing LICENSE copyright line.** The repo's LICENSE (present before this
  build started) reads "Copyright (c) 2026 Big Fan." Not touched, since it predates this build
  and wasn't part of the requested work. Flagged for the human owner to confirm this string
  doesn't function as a personal identifier before treating the anonymity rules as fully
  satisfied end-to-end.
- **2026-07-09 — Initial commit author.** The repo's pre-existing initial commit (LICENSE only)
  is authored by the owner's own account, not `hk-radar-bot`. Flagged by the Fable PM review.
  Not rewritten — rewriting a single pre-existing commit's history is a destructive, hard-to-
  reverse git operation with no build benefit, and this build was never asked to touch it. Every
  commit made *by this build*, starting with the chassis scaffold, uses the bot identity. If full
  history-level anonymity is wanted later, that is a deliberate human decision (e.g. squashing
  history when moving to a dedicated org), not something to do silently mid-build.

## Silent decisions (spec didn't specify, simplest reasonable option chosen)

- **`data/queue.json` is derived, not accumulated.** Regenerated every watcher run as every
  ledger item with `status == "queued"`, deterministically sorted by `(first_seen, item_hash)`.
  This makes "re-run adds nothing" true both logically and as a literal git diff — the P1
  acceptance criterion is satisfied by construction, not by a special-case check.
- **Item identity hash** = `sha256(source_id + feed_id + guid-or-link)`, deliberately excluding
  title/summary, so a later text correction to an already-seen item doesn't spawn a duplicate
  queue entry. A separate `content_hash` (over title+summary+published_at) is computed and stored
  but unused for diffing in Phase 1 — banked for a future correction-detection feature.
- **`save_ledger` / `save_queue` skip the write when semantic content is unchanged** (comparing
  everything except `generated_at`), so timestamp churn alone never produces a git diff on a true
  no-op re-run.
- **`watch.yml` exists in Phase 1** and runs the watcher end-to-end; the "trigger analyze.yml"
  step is a log/echo no-op since `analyze.yml` doesn't exist yet. Explicitly permitted by the
  spec's own phrasing ("runs only when queue non-empty" presupposes analyze.yml exists, which it
  doesn't yet).
- **pytest is fixture-only** — no test hits a live network endpoint, for CI determinism and
  speed. The literal P1 acceptance criterion ("watcher run produces a correct queue from live
  feeds; re-run adds nothing") is instead verified by a real, manual, dated pair of live
  invocations, recorded in PROGRESS.md with actual counts/timestamps.
- **Stdlib RSS parsing** (`xml.etree.ElementTree` + `email.utils.parsedate_to_datetime`) chosen
  over the `feedparser` dependency, since every known feed (SFC ×3, HKMA ×6) is clean, well-formed
  RSS 2.0. Revisit if a future jurisdiction's feed is Atom or malformed enough to need a more
  forgiving parser.
- **HKMA feed selection extended beyond the spec's literal list.** Spec §4 names "press releases,
  speeches, guidelines & circulars, LegCo issues" for HKMA. `rss_consultations.xml` was added
  because the dealing/custody/advisory/management consultations (a core Phase-1-relevant content
  stream per spec §7 item 3) live there, not in the press-release or circular feeds.
- **`corrections.json` and `audit/event.json` schemas are original designs** — the spec names
  these files without defining their fields. Corrections: `{id, card_id, corrected_at,
  correction_note, fields_changed[], citations[]}`. Audit event: generic `{event_type, timestamp,
  actor, summary, details, related_ids[]}`, extensible for later audit-loop needs.
- **`pillar_state.json`'s `pillar`, `regulator`, and `status_seal` fields are typed as free-text
  strings in the schema**, not enums baked with Hong Kong values (e.g. not `enum: ["sfc",
  "hkma"]`) — baking HK-specific values into a schema under `/pipeline` would itself violate the
  jurisdiction-portability constraint. Valid values are governed by `config/jurisdiction.json` at
  the content-authoring layer, in later phases.
- **`card.json`'s `key_dates` sub-fields** (`deadline`, `effective`, `milestone`) are plain
  ISO-8601 date strings, not nested objects.
- **`config/jurisdiction.json`'s `seal_vocabulary`** is a provisional placeholder list (in force /
  consultation open / proposed / guidance issued / enforcement action) — expected to be refined
  once real pillar-state content is authored in Phase 3, informed by actual regime states.
- **`pipeline/schemas/queue.json` schema added** even though spec §6 doesn't name a queue schema,
  since `data/queue.json` is core to the Phase 1 acceptance criterion and should be validated like
  every other pipeline data file.
- **Watcher exit-code convention:** `0` unless every feed fails or the jurisdiction config is
  missing/invalid; a partial feed failure (e.g. one regulator's site down) is a warning in the run
  summary, not a run failure — the point of a daily watcher is to keep going and catch up
  tomorrow, not to block on a single flaky endpoint.
- **`pyproject.toml`** chosen as the single dependency/tooling manifest over separate
  `requirements*.txt` files.
- **Watcher User-Agent contact address** reuses the bot's noreply email
  (`bot@users.noreply.github.com`) rather than a separately monitored project inbox. Fine for a
  low-volume Phase 1 chassis; recommend a real monitored contact address before sustained
  production polling once the site is live and publicly indexed.

## Findings from live smoke-testing against real feeds, 2026-07-09

Before writing the pytest fixtures, `fetch.py`/`parse.py`/`hashing.py`/`ledger.py`/`queue.py`/
`run.py` were smoke-tested directly against all 9 real live SFC+HKMA feeds (against a scratch
directory, not the committed `data/` files). Two things surfaced that changed the design:

- **Identity-key fallback changed from `guid -> link -> title` to `guid -> (link + title)`.**
  HKMA's `hkma_legislative_council_issues` feed gives every `<item>` the *same* generic
  landing-page `<link>` (no per-item URL) and no `<guid>` — only the title differs between items.
  Falling back to `link` alone collapsed genuinely distinct items into one ledger entry. Combining
  link+title fixed it, while still correctly collapsing HKMA's `hkma_circulars` feed's occasional
  *literal* duplicate `<item>` (identical link and identical title, confirmed by inspection) down
  to one ledger entry — that one is a real duplicate, not a false collision.
- **Neither SFC nor HKMA serve `ETag` or `Last-Modified` on any of the 9 feeds** (confirmed by
  inspecting response headers directly; SFC even sends `Cache-Control: no-cache, no-store`). The
  watcher's conditional-GET support (`If-None-Match`) is implemented correctly and will engage
  automatically the moment a source does send a validator (e.g. a future non-HK jurisdiction's
  feed), but it is currently inert for both HK regulators — there is nothing further the client
  side can do here; this is a server-side limitation, not a gap in the watcher. Not implementing
  `If-Modified-Since`/`Last-Modified` support for now, since no known feed would exercise it
  (revisit if a future source sends `Last-Modified`).

## Decisions from Fable (PM) kickoff review, 2026-07-09

A Fable-model agent acting as project manager reviewed the kickoff plan before implementation
began and required the following be pinned down (see PROGRESS.md for the full checkpoint record):

- **ETag/HTTP cache state moved out of version control.** Originally scaffolded at
  `data/cache/etags.json` and committed; corrected to a git-ignored path (`/data/cache/` added to
  `.gitignore`, file untracked) before any watcher code was written. Reasoning: ETags change
  whenever a feed republishes anything, independent of whether there are new items — a committed
  ETag file would produce a git diff on every run even when the ledger/queue are unchanged,
  breaking the "re-run adds nothing" acceptance criterion at the byte level.
- **Ledger `last_seen` field dropped.** An earlier draft tracked both `first_seen` and
  `last_seen` per item; `last_seen` would update to the current run's timestamp on every re-run
  even with zero new items, which would break byte-identical re-runs. Only `first_seen` is
  tracked. If "last confirmed still live" tracking is wanted later, it belongs in `audit/*.json`
  (a weekly, not daily, artifact), not the ledger.
- **Canonical JSON serialization for all committed data files.** `sort_keys=True`, 2-space indent,
  trailing newline, UTC ISO-8601 timestamps only (`Z` suffix, no offsets) — applied uniformly so
  two runs with identical semantic content always produce byte-identical files.
- **`schema_version` (not `version`) is the field name used consistently across all 8 schemas**
  and their data files, for naming consistency across the whole content model.
- **Ledger status lifecycle finalized as an enum, documented now even though Phase 1 only ever
  writes `queued`:** `queued → drafted → verified → published`, with `corrected` and `suppressed`
  as later-reachable states from `published`, and `error` reachable from any state. This is the
  contract the Phase 2 analyst/verifier will consume, so it's fixed now rather than migrated
  later.
- **Per-feed failure isolation.** One feed timing out or returning malformed XML must not abort
  the other eight; the watcher records a per-feed status in its run summary and continues. Exit
  code stays 0 unless every feed failed or the config itself is invalid (restates the earlier
  exit-code decision, now with an explicit fixture-backed test).
- **XML parsing hardened with `defusedxml`.** Added as a small, single-purpose runtime dependency
  (`defusedxml.ElementTree.fromstring` instead of stdlib `xml.etree.ElementTree.fromstring`) to
  guard against XXE / entity-expansion issues in fetched feed XML. This is a narrow, deliberate
  exception to the "minimize dependencies" preference — the library exists specifically for this
  threat model, on external-source XML, which is exactly what the watcher processes.
- **Feed text sanitized on ingest.** Titles/summaries have control characters stripped and are
  length-capped (title 500 chars, summary 2000 chars) before entering the ledger — defense in
  depth, since this text will later be handed to an AI analyst per the "fetched documents are
  data, not instructions" rule.
- **Cross-feed duplicates are accepted, not deduplicated, in Phase 1.** If the same item appears
  in two different feeds (e.g. a circular cross-posted to both a regulator's circulars feed and
  its press-release feed), it produces two separate ledger entries, since identity is keyed by
  `(source_id, feed_id, guid-or-link)`. Noted as a known limitation, not solved now — true content
  dedup is an analyst-phase concern (comparing summaries/citations), not a watcher concern.
- **User-Agent does not include the current repo's URL.** Kept generic
  (`HKDigitalAssetRadarWatcher/<version> (contact: bot@users.noreply.github.com; purpose: public
  RSS regulatory monitoring)`) rather than pointing at `0xfanbase/DA-Radar` specifically, since
  that repo location is itself a temporary deviation (see the anonymous-org entry above) that is
  expected to change — baking today's infra location into an external-facing header would need
  updating the moment the project moves to its intended dedicated org.
- **No-live-network enforced structurally in tests**, not just by convention: an autouse pytest
  fixture in `tests/conftest.py` monkeypatches `socket.socket.connect` to raise inside every test,
  so a future test cannot silently start hitting a live feed in CI. Mocked tests (via
  `requests-mock`) never touch real sockets in the first place, so this is a zero-cost guardrail.

## Follow-ups for later phases (not decisions, just noted so they aren't lost)

- Phase 2 must add the actual CI path-allowlist gate (today it's a documented rule in CLAUDE.md,
  not yet a machine-enforced check, since there are no AI jobs to restrict yet).
- `content/` directory (cards, pillar states, trajectory, glossary data) doesn't exist yet —
  correctly out of scope per the kickoff instruction, but noted so no one mistakes its absence
  for an oversight.
