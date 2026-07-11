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

## Phase 2 kickoff and decisions, 2026-07-09

Fable PM reviewed Phase 2 scope (analyst + verifier + CI path-allowlist gate) before
implementation began, the same way it reviewed Phase 1. Full directive text is in PROGRESS.md.
Key decisions arising from that review and from implementation itself:

- **Citation-vs-sentence interface, resolved per Fable directive.** The deterministic module
  (`pipeline/verify/authenticity.py`) is a per-citation authenticity oracle ONLY: given
  `{url, quote}`, it re-fetches the source and checks the quote is a genuine (normalized)
  substring. It has no concept of which sentence in a card's `summary`/`why_it_matters` a
  citation is meant to support -- that is a semantic judgment only the LLM verifier pass can make
  (proposing which sentence to strip or rewrite). The deterministic module's role is narrower but
  final: `pipeline/verify/gate.py` re-checks every citation remaining in whatever the LLM
  produced, immediately before commit, and forces `status: "unverified"` on any failure --
  regardless of what the LLM's own output claims about its verification status. This is
  literally "never trust self-reported verification," implemented as code, not policy.
- **`data/queue.json`'s Phase 1 idempotency guarantee is confirmed to extend automatically to
  the new ledger states.** `derive_queue` already filters on `status == "queued"` (Phase 1
  design); once an item moves to `drafted`/`verified`/`published`, it structurally cannot
  reappear in the queue, and a watcher re-run's `upsert_items` already refuses to touch an
  already-known `item_hash` regardless of its current status. No queue.py changes were needed --
  confirmed by an explicit regression test (`test_watcher_rerun_never_resets_or_requeues_a_drafted_item`)
  rather than just asserted.
- **Ledger status lifecycle enforced as a validated state machine**, not just an unconstrained
  string field: `queued -> drafted -> verified -> published`, with `corrected`/`suppressed`
  reachable from `published`, and `error` reachable from any state (with `queued` reachable from
  `error`, for retries). Illegal transitions (e.g. `queued` straight to `published`) raise
  `InvalidStatusTransition` rather than silently corrupting the ledger.
- **`pypdf` added as a narrow, single-purpose dependency** for PDF text extraction, matching the
  `defusedxml` precedent from Phase 1 -- justified because the spec explicitly requires
  "HTML/PDF-to-text" extraction (§5) and pypdf is a focused, actively-maintained library for
  exactly this, not a general-purpose kitchen-sink dependency. HTML extraction uses stdlib
  `html.parser` (no extra dependency), consistent with Phase 1's dependency-minimalism stance.
- **Environment note (not a code decision):** this sandbox's system-installed `cryptography`
  package (used transitively by `pypdf`'s optional encrypted-PDF support) failed to import with a
  Rust-level panic due to a missing `cffi`/`_cffi_backend` module. Fixed by `pip install cffi`.
  Not a repo-code issue -- flagged here in case a fresh environment hits the same failure; the fix
  is an environment dependency, not a pinned requirement change.
- **Test isolation fix (not a repo git-config change):** `tests/test_path_allowlist.py` creates
  real scratch git repos to test `get_diff_changed_paths` end-to-end. This dev sandbox has a
  global `commit.gpgsign=true` wired to a custom SSH-signing helper that round-trips to an MCP
  server, which occasionally timed out and made a test's `git commit` fail non-deterministically
  (`fatal: failed to write commit object`). A clean CI runner (e.g. GitHub Actions) has no such
  signing setup, so this was local-only flakiness, not a CI risk -- but it was still worth fixing
  properly rather than ignoring. Fix: the test helper now disables signing inside each disposable
  scratch repo only (`git -c commit.gpgsign=false init` plus a local `git config commit.gpgsign
  false` scoped to that throwaway directory) -- this never touches the actual project repo's
  config, global or local, same category as setting a scratch repo's `user.name`/`user.email`.
- **Tool restriction for the AI jobs is enforced primarily via `claude_args`, not a settings
  *file*.** A settings *file*'s `/path`-style permission patterns anchor to *that file's own
  directory*, not the repository root -- a file at, say, `pipeline/prompts/ai_job_settings.json`
  would resolve `Write(/content/**)` to `pipeline/prompts/content/**`, silently breaking the
  intended scope. (**Correction, 2026-07-09, per Fable PM re-check of the raw `action.yml`:** an
  earlier version of this entry claimed `claude-code-action@v1` has no `settings` input at all --
  that was wrong, confirmed false by reading the action's actual source rather than a summary.
  The input exists: `"Claude Code settings as JSON string or path to settings JSON file"`. The
  path-anchoring problem is real and stands; the "input doesn't exist" reasoning was not, and is
  struck from the rationale.) Also deliberately not writing a repo-root `.claude/settings.json`
  -- that file is auto-loaded by every Claude Code session working on this project (including all
  future human/agent work in Phases 3-5), and this restriction is meant to scope two specific
  automated CI jobs, not the whole repo. Resolution: pass `--allowedTools`/`--disallowedTools`
  directly via each job's `claude_args`, using patterns with no leading slash
  (`Write(content/**)`, not `Write(/content/**)`) -- documented to anchor to the current working
  directory, which is the repository root when the action runs, and the one behavior confirmed
  unambiguous rather than inferred. The actual non-bypassable guarantee doesn't rest on this
  layer anyway -- it rests on `pipeline/ci/path_allowlist.py` running as an independent, deterministic
  post-hoc check regardless of what the AI job's own tool permissions claim to allow.
  **Deferred, not done:** the `settings` input also accepts an inline JSON string (no file, so no
  path-anchoring ambiguity), which could carry an explicit `permissions.deny` list for
  `/pipeline`, `/.github`, `/config`, `CLAUDE.md` as extra defense-in-depth (deny beats allow).
  Not added this round because it would rely on another not-yet-verified anchoring assumption
  (does an inline string anchor to cwd the same way `claude_args` patterns do?) for a layer that
  is not where the actual guarantee lives -- worth adding later if confirmed cheap, but not before
  the CI-gate-based enforcement that's already real and tested.
- **The analyst always drafts a card with `status: "unverified"`, never `"verified"`.** The
  analyst is the first pass, not an independent check on itself; only the verifier (a
  structurally separate job, fresh context) may set `"verified"`, after its own adversarial
  re-fetch. This keeps the honest default conservative: an unreviewed draft never claims
  confidence it hasn't earned, even before the deterministic gate has a chance to run.
- **"Verifier writes verification report" (spec §5) is satisfied via
  `claude-code-action`'s own `display_report: true` input**, which surfaces the verifier's
  reasoning in the GitHub Actions run's step summary. Simpler than inventing a new schema/file
  for this, and the spec doesn't define a report format -- the existing Method & Audit page
  (later phase) can link to or embed these run summaries rather than needing a parallel data
  store.
- **content/cards/, content/pillar_states/, content/glossary/ are the actual directories the
  analyst/verifier prompts instruct writing to**, matching `pipeline/ci/validate_content.py`'s
  path convention exactly -- both were designed together so the prompts and the schema-validation
  gate never drift apart.

  **The exact `claude_args` value, identical for both the analyst and verifier jobs** (defense
  layer 1 of 2 -- layer 2 is `pipeline/ci/path_allowlist.py` run as a separate plain-shell step
  in the same job, after the AI job, before any commit):
  ```
  --max-turns 30 --disallowedTools "Bash" --allowedTools "Read" "WebFetch" "Write(content/**)" "Edit(content/**)"
  ```
  `Bash` is fully removed from context (bare tool name), not merely path-scoped, since the AI
  jobs have no legitimate reason to run shell commands at all. `Read`/`WebFetch` are unscoped
  (need to read/fetch source documents and existing content anywhere). `Write`/`Edit` are scoped
  to `content/**` only.
  **Revised while designing `analyze.yml` itself (not a correction of an error reported at
  checkpoint A, a further tightening discovered once the concrete pipeline was actually laid
  out):** the original value at checkpoint A also allowed `Write(data/**)`/`Edit(data/**)`. Once
  `pipeline/ci/promote_drafted.py` and `pipeline/ci/promote_verified.py` were written --
  deterministic code that owns every `data/ledger.json`/`data/queue.json` mutation as a plain-shell
  step after the AI job -- it became clear the AI jobs never legitimately need `/data` write
  access at all. Removing it is a real reduction in the AI jobs' write surface, not just a
  restatement: the analyst/verifier LLMs cannot touch the ledger even if a prompt injection tried
  to convince them to, since the tool permission for that path no longer exists in their session.
- **Two commits per analyze.yml run, not one** (analyst drafts and commits; verifier
  independently checks out, corrects, and commits again) -- chosen over passing uncommitted state
  between jobs via artifacts because (a) GitHub Actions jobs run on fresh runners with no shared
  filesystem, so cross-job state requires either an artifact upload/download round-trip or a
  commit; a commit is simpler and (b) it produces a transparent, auditable git history showing
  the draft -> verified progression as real commits, which fits the "audited in public" goal
  better than hiding the intermediate state in an artifact. A card briefly existing on `main` with
  `status: "unverified"` between the two commits is not a content-integrity problem -- unverified
  is a real, displayable, intentionally-supported status per the spec's "fully auto-publish with
  disclaimers" decision, not a defect.
- **The verifier has no Bash access, so it cannot run its own `git diff` to discover which card
  file(s) the analyst just wrote.** A plain-shell step (`git diff --name-only HEAD~1 HEAD --
  content/cards/`, requiring `fetch-depth: 2` so the parent commit is available) computes this
  deterministically and the result is interpolated directly into the verifier's `prompt:` input.
  The canonical instructions stay in the versioned `verifier_prompt.md` (which the verifier reads
  itself via its unrestricted `Read` tool) rather than being duplicated inline in the workflow
  YAML -- only the per-run dynamic scope (which file(s)) is injected.
- **`watch.yml`'s Phase 1 no-op placeholder is now a real trigger**: on a non-empty diff, it POSTs
  a `repository_dispatch` event (`event_type: queue-updated`) to the repo using the job's own
  `GITHUB_TOKEN`, which `analyze.yml` listens for. `GITHUB_TOKEN`-triggered `repository_dispatch`
  is exempted from GitHub's "don't recursively trigger workflow runs" restriction (that
  restriction applies to push/PR-shaped events, not explicit dispatch calls), so no additional PAT
  or secret is needed for this specific chaining step -- only the analyst/verifier jobs' actual AI
  calls need the separately-provisioned `CLAUDE_CODE_OAUTH_TOKEN`.

## Architecture pivot: no GitHub AI secret, ever (owner decision), 2026-07-09

The owner stated plainly, after Phase 2 shipped, that `CLAUDE_CODE_OAUTH_TOKEN`/`ANTHROPIC_API_KEY`
will never be provisioned as a GitHub repo secret. This is not "not yet" -- it is a standing
decision, and it makes `.github/workflows/analyze.yml` permanently unable to authenticate in this
deployment (there is no engineering workaround for a missing credential; that is what a credential
is for). Two separate problems needed separate fixes, per Fable PM review of the pivot:

- **`analyze.yml` now fails closed, not loud.** `check-queue` gained a `credentials_available`
  output (checks both possible secret names, empty string if neither is set); `analyst`/`verifier`
  are gated on it and skip cleanly with a `::notice::` explaining why, instead of erroring on
  missing auth every single day a new item is queued. The workflow is left in the repo,
  fully documented as a **dormant, spec-literal fallback**: if a future owner ever does add either
  secret, it starts working exactly as originally designed, with no other change required.
- **Phase 3 (seed backfill) needed no automation fix at all.** It's an explicitly one-time/periodic
  research-and-write job, not the steady-state loop, so it can be (and was) performed directly in
  an interactive Claude Code session -- approved by Fable PM with four conditions, all followed:
  (1) genuine fresh-context separation for the verifier role (a separate `Agent` sub-call that
  receives only the drafted card file, never the analyst session's reasoning -- not the same
  conversation switching hats and self-grading); (2) the deterministic gates
  (`path_allowlist`/`validate_content`/`apply_verification_gate`) run as real subprocess
  invocations against the actual working tree, not a judgment call about whether the output "looks
  fine"; (3) commits still use the `hk-radar-bot` identity via env vars only, unchanged; (4) this
  paragraph -- the mechanism is disclosed plainly, not left for someone to infer.
- **Ongoing automation: the owner was asked, explicitly, not defaulted.** Fable PM flagged that
  routing ongoing analysis through a Claude Code Remote scheduled trigger (since GitHub Actions
  cannot invoke Claude without the secret the owner won't provide) is a real architectural
  tradeoff, not a pure engineering substitution, and should not be inferred from "continue
  building." Put to the owner as an explicit choice via `AskUserQuestion`:
  - *Option A (dormant):* `analyze.yml` stays inert; the site's content only updates on a manual
    run or if a secret is added later. Fully public/auditable on GitHub; a jurisdiction fork
    inherits the mechanism for free like everything else in the repo.
  - *Option B (CCR scheduled trigger):* a recurring job tied to the owner's Claude Code Remote
    account (not the repo) wakes periodically and performs the analyst+verifier role itself. It
    actually runs unattended, but lives entirely outside GitHub -- invisible to anyone auditing
    this public repo, and a jurisdiction fork does not inherit it; a new owner would need to
    separately discover and stand up their own CCR account/trigger. This is a bigger deviation
    from the portability promise ("new config + new seed pass, not touching pipeline code") than
    the anonymous-org deviation already logged above.

  **The owner chose Option B.** Documented here as an explicit, informed choice, not a default --
  see `docs/analyst-runbook.md` for the actual mechanism and PROGRESS.md for the setup record.
- **Compensating for the lost tool-restriction layer -- initially mitigated, then actually closed.**
  Phase 2's `analyze.yml` security model was two-layer: `claude_args`' `--disallowedTools`/scoped
  `Write` (structural), plus the deterministic gate (post-hoc, non-bypassable). The first version
  of the CCR runbook used a plain `Agent` call for both sub-agents, which has no fine-grained
  tool-restriction parameter of its own -- Fable PM caught this exactly (no `.claude/agents/`
  directory existed, so both sub-agents would have inherited full tool access, Bash included) and
  flagged it as worth closing properly rather than resting on mitigation alone. Fixed the same
  session: `.claude/agents/hk-radar-analyst.md` and `hk-radar-verifier.md` define real, named
  subagent types with `tools: Read, WebFetch, Write, Edit` (no Bash) and `isolation: worktree` in
  their frontmatter -- confirmed via direct research into Claude Code's actual subagent docs that
  this is real structural enforcement (the runtime removes disallowed tools from what the subagent
  can call at all), not a hint. `docs/analyst-runbook.md` now spawns both sub-agents via
  `subagent_type: "hk-radar-analyst"`/`"hk-radar-verifier"` rather than a generic `Agent` call.
  This restores genuine two-layer defense, matching Phase 2's model almost exactly (the one gap
  remaining is that `tools:` frontmatter is tool-name-level only, not path-scoped like
  `claude_args`' `Write(content/**)` syntax -- so path-level enforcement still rests on the
  deterministic gate and the orchestrator's explicit `git add content/...` staging, same as
  before). Two mitigations from the original (pre-fix) design remain as genuine additional
  layers, not just historical color: (a) both sub-agents still run with `isolation: "worktree"` --
  a disposable git worktree, not the orchestrating session's real working directory; (b) the
  orchestrating session (not either sub-agent) is the only thing that ever runs
  `git add`/`commit`/`push`, staged explicitly, never `-A`. The deterministic gate remains the
  definitive, non-bypassable backstop regardless -- unchanged from Phase 2, since it never trusted
  an LLM's self-report in the first place.

## Bug found via live gate usage: bare untracked-directory lines, 2026-07-09

While writing Phase 3's 7 `content/pillar_states/*.json` files (the first real content ever
created under a wholly-new subdirectory), running the actual deterministic gate
(`python -m pipeline.ci.path_allowlist --mode working-tree`) failed with `content/` reported as a
violation. Root cause: `git status --porcelain`'s default untracked-files mode collapses an
entirely-new, wholly-untracked directory into one bare line (`"content/"`) instead of one line per
file inside it; `_normalize()` then strips the trailing slash, so `"content/"` becomes `"content"`,
which fails a plain `.startswith("content/")` check.

First fix (commit `7f5f3cb`) special-cased this in `check_path_allowlist` only. Before committing,
re-ran the *other* real gate, `validate_content.py`, against the same still-uncommitted files and
found a more serious version of the same root cause: `validate_content`'s per-file schema mapping
has no entry for a bare `"content"` path, so it silently printed `"no schema-governed files
changed"` and skipped validating all 7 files entirely — a silent false pass, not a loud failure.
Both `path_allowlist.py` and `validate_content.py` (and `apply_verification_gate.py`) share one
underlying function, `get_uncommitted_changed_paths`, so this wasn't three separate bugs to patch
three times — it was one root cause with three blast points. Fixed properly (commit `81188aa`) by
passing `--untracked-files=all` to the underlying `git status` call so every consumer always sees
real per-file paths, and reverted the narrower first patch as unnecessary once the source data is
correct. Confirmed live: `validate_content` went from silently reporting 0 files checked to
correctly validating all 7 pillar-state files OK.

Lesson logged because it nearly slipped through: the first fix "worked" (the one gate I'd tested
against passed), but only running the *other* real gate — per this project's own standing
discipline of never trusting one green check when a second deterministic gate exists — surfaced
that the real risk (silently unvalidated content) was still live.

## Bug found starting Phase 3: no digital-asset relevance filter on the queue, 2026-07-09

While preparing to run the real analyst+verifier pipeline on 5 headline events (Phase 3, task
"generate headline cards"), reading the actual `data/queue.json` before handing it to an analyst
sub-agent revealed it held **988 items**, not the "few items a week" CLAUDE.md's quota section
assumes. Root cause: the Phase 1 watcher queues *every* item from SFC/HKMA's chosen feeds, and
those feeds cover each regulator's full mandate (banking guidelines, generic enforcement, speeches
on quantum computing, scam alerts...), not just digital-asset content. Neither the build spec nor
CLAUDE.md's loop diagram ("new items? -> write data/queue.json") ever named a relevance-filtering
step -- it was silently assumed away, and nobody had actually looked at a full live queue.json
until now. Keyword-checking the real queue found only 69 of 988 items were genuinely digital-asset
related.

This was urgent, not just untidy: the CCR scheduled trigger (see the "Architecture pivot" entry
above) is live and due to fire against this exact queue. Handing an analyst sub-agent an unfiltered
988-item queue would have been wasteful at best and produced a nonsensical commit at worst.

**Decision (spec silent, simplest option chosen):** added `pipeline/watcher/relevance.py` -- pure,
deterministic, case-insensitive keyword matching, no AI or network call. Every watched item is
still recorded in the ledger in full (nothing is silently dropped from the audit trail); a new
optional ledger field, `relevant: bool`, is computed once per item against
`config/jurisdiction.json`'s new `relevance_keywords` list, and `derive_queue` only includes items
where `status == "queued" and relevant is not False` (so entries predating this field, which have
no `relevant` key at all, still default to included -- true fail-open, never a silent full
blackout). An empty/missing `relevance_keywords` list (e.g. a not-yet-configured jurisdiction) also
fails open -- every item is treated as relevant rather than none. `pipeline/watcher/run.py` calls
`classify_relevance` once per run, right after ingesting that run's new items, so this happens
automatically going forward with zero extra step in `watch.yml` or the CCR runbook.

Applied live: ran `python -m pipeline.watcher.relevance` once against the real
`data/ledger.json`/`data/queue.json` as a one-off backfill (the function is naturally idempotent,
so it's the same code path a live run uses, not a special migration script) -- classified all 988
pre-existing items, `data/queue.json` shrank from 988 to 69. Verified the 5 headline items seeded
for the Phase 3 headline-card task (see PROGRESS.md) all correctly classified `relevant: true`.

Also built `pipeline/ci/seed_backfill.py` in the same pass -- a small reusable module (reusing the
exact same `NormalizedItem -> diff_new_items -> upsert_items` path the live watcher uses, plus the
same `classify_relevance` call) for adding known historical items to the ledger as `queued`, needed
for this headline-card backfill and again for the planned ~40-item document library task.

**Known limitation, logged rather than fixed now:** `classify_relevance` only classifies items that
don't yet have a `relevant` field -- if `relevance_keywords` is edited later (a term added or
removed), already-classified items are never automatically reclassified against the new list. A
future deliberate reclassification would need to strip the `relevant` field first (or a dedicated
`--force` flag, not yet built) before re-running. Acceptable for now since the keyword list is
expected to be stable, not iterated on; worth revisiting if it turns out to need frequent tuning.

Test fixture note: `tests/test_run_integration.py`'s 9 real SFC/HKMA feed fixtures happen to be a
realistic relevance mix (2 of 19 unique items are genuinely digital-asset related) -- rather than
padding every fixture item with a fake keyword to preserve the old "everything gets queued"
assertion, the test's expected counts were corrected to match reality. This is a stronger test than
before: it now proves the relevance filter behaves correctly against realistic, mixed-topic sample
data, not just synthetic single-purpose fixtures (see the new `tests/test_relevance.py` for the
isolated unit-level coverage, including a portability-specific case with a non-HK keyword
vocabulary).

## First real analyst+verifier pipeline run: 5 headline cards, 2026-07-09

Ran the full analyst+verifier+gate pipeline for real for the first time, on the build spec's 5
seed-content headline events (VATP regime, stablecoins licences, dealing/custody consultation
conclusions, Policy Statement 2.0, an SFC enforcement action). One `hk-radar-analyst` sub-agent
drafted all 5 cards plus `trajectory.json`'s first entry and 6 glossary terms; 5 separate,
worktree-isolated `hk-radar-verifier` sub-agents (one per card, each given only the drafted card
file, never the analyst's reasoning) then adversarially re-checked them. Every single one of the 5
verifier passes found and fixed at least one real problem: a fabricated/spliced quote (two distinct
bullet headings stitched together with a semicolon), a wrong statutory-basis description (the draft
said the AMLO licence applies "regardless of what a platform trades" -- the source actually ties the
AMLO/SFO split to token classification), an unsupported commencement-date claim with no source
support, an unsupported "for the first time" comparative claim, and (for the stablecoin-licences
card) several factual claims that needed additional citations located and re-fetched to genuinely
support them. This is exactly the fresh-context adversarial design paying for itself on the first
live run, not merely passing tests against fixtures.

**Real infrastructure bug found: concurrent `isolation: worktree` agent spawns can get a stale
worktree.** Spawning all 5 verifier sub-agents in one batch (same message, 5 parallel `Agent` calls)
resulted in 4 of the 5 worktrees being created pinned to `main`'s original Phase 1 merge commit
(`02d5a40`) -- a commit from hours earlier, missing every Phase 2/3 change including the very card
files and `pipeline/prompts/verifier_prompt.md` the sub-agents needed -- rather than the current
feature branch tip. The 5th (spawned alone, earlier, as the analyst) correctly got the live branch
tip. This looks like a race in the harness's worktree-creation path under concurrent load, not
anything this build's own git state caused. One sub-agent, faced with its own worktree missing the
target files entirely, correctly stopped and reported rather than fabricate a "verification" of a
file it couldn't find -- exactly the right call, and worth noting as evidence the anti-fabrication
instruction in `verifier_prompt.md`/`hk-radar-verifier.md` holds even under a genuinely confusing
environment fault. The other 3 discovered (independently, each in its own run) that their `Read`
tool was not actually confined to their own worktree -- it could see the shared main checkout too,
even though `Edit`/`Write` were correctly sandboxed to the worktree -- and used that to read the
real card + prompt from the shared checkout while writing their corrected output to their own
worktree path. Recovered the one that stopped by resuming it with explicit absolute paths into the
shared checkout, pointing out the same Read/Edit asymmetry its siblings had already found; it then
completed the same adversarial check successfully. **Follow-up, not fixed now:** if `isolation:
worktree` is used again for a batch of concurrent sub-agents, verify each resulting worktree's `git
log` actually matches the intended branch tip before trusting its output -- don't assume concurrent
spawns are independently reliable just because a single spawn was.

**Real bugs found in the deterministic authenticity gate itself**, by running it for real against
all 5 verifier-approved cards rather than stopping at the LLM verifier's own "verified" verdict (the
entire point of the gate being non-bypassable): it downgraded 2 of the 5 cards despite both having
just been marked `verified`. Investigated rather than assumed-correct:
1. **Smart-quote/straight-quote mismatch.** The stablecoin-licences card's quote used a plain ASCII
   apostrophe in `"holders' requests"`; the actual HKMA source page uses a typographic right single
   quotation mark, `"holders’ requests"` (U+2019). The quote was completely genuine -- only the
   punctuation character class differed. Fixed at the root: `normalize_for_match` in
   `pipeline/verify/authenticity.py` now maps common smart quotes/apostrophes/dashes to their ASCII
   equivalents before comparison (comparison-time only; stored card text is untouched). This will
   recur constantly on real regulator prose, which consistently uses proper typographic punctuation,
   so this is a durable fix, not a one-off patch.
2. **PDF text-extraction whitespace artifact.** The consultation-conclusions card's PDF citation
   quoted `"SFC-regulated"`; the pipeline's own PDF extraction of that exact document yields
   `"SFC -regulated"` (an extra space before the hyphen, evidently introduced by the PDF's own
   internal text layout/kerning, confirmed by directly re-running the deterministic fetcher and
   inspecting the raw extracted text). This is a source-specific extraction quirk, not a general
   punctuation-class problem, so fixed narrowly: corrected that one quote to match the actual
   extracted text exactly, rather than loosening the general matcher to ignore all
   whitespace-around-hyphen differences (too great a risk of masking a genuinely different quote
   elsewhere). Logged here in case the same PDF-kerning artifact recurs on a future document from the
   same source.

Both fixes are covered by new regression tests in `tests/test_authenticity.py`. Full test suite: 151
passing (up from 148).

## Document Library (task #44) built, 2026-07-09 -- design approved by Fable PM

Built per Fable's approved design (site structure item #5, distinct from item #4's analyst-authored
Timeline cards): `pipeline/watcher/classify.py` (deterministic pillar tagging via
`config/jurisdiction.json`'s new `pillar_keywords`, plus `type` derived from each feed's own
existing `kind` field -- a separate vocabulary from `card.json`'s analyst-assigned type enum, since
a raw watched document's feed category and an analyst's editorial judgment of a drafted card are
different concepts and forcing one enum to cover both would misclassify press releases with no
analyst verdict yet) and `pipeline/watcher/document_library.py` (derives
`content/document_library.json` from the ledger's `relevant: true` items, same "derived view,
regenerated in full, never accumulated" principle as `queue.py`). New schema:
`pipeline/schemas/document_library.json`. Wired into `pipeline/watcher/run.py`'s normal run (not a
standalone script), and into `watch.yml`'s commit step.

**Bug found while wiring the commit-scope check, same category as the earlier bare-directory bug:**
`watch.yml`'s existing `git diff --quiet -- data/ledger.json data/queue.json` check would have
silently missed `content/document_library.json` on its very first run -- plain `git diff` (without
`--cached`) only shows differences for already-tracked files; a brand-new untracked file produces no
diff output at all, so the "did anything change" check would have reported `false` even though a
genuinely new file existed, and it would never get committed. Confirmed live (`git status
--porcelain` showed the untracked file; `git diff --quiet` returned success/no-diff for the exact
same paths). Fixed by switching the check to `git status --porcelain`, which correctly covers both
modified and untracked files -- this only mattered because `content/document_library.json` is
committed by this same PR alongside the workflow change, so the gap never actually bit in practice,
but would have for anyone reasoning about this workflow from a truly clean slate.

Full test suite: 165 passing (up from 151) -- new `tests/test_classify.py`,
`tests/test_document_library.py`, plus Freedonia-jurisdiction and real-HK-fixture coverage added to
`tests/test_jurisdiction_agnostic.py` and `tests/test_run_integration.py` per Fable's directive that
every new deterministic subsystem needs the same portability proof as the rest of the pipeline.

**Known, explainable edge case (flagged at Fable PM's Phase 3 checkpoint, not a bug):** 2 of the 69
real `document_library.json` entries carry `type: "unknown"`. Both are FSTB documents (Policy
Statement 2.0 and the dealing/custodian consultation conclusions, seeded via
`pipeline/ci/seed_backfill.py` -- see that section above), and `type_for_feed()` looks up a feed's
`kind` from `config/jurisdiction.json`'s `regulators` list, which only wires SFC and HKMA today;
FSTB is a named source in CLAUDE.md's source table but explicitly "not yet wired into the watcher
(out of Phase 1 scope)." `"unknown"` is the honest, correct answer for a source the watcher doesn't
actually poll -- not a misclassification. Resolves itself automatically whenever FSTB is wired into
the watcher in a future phase; no action needed before then.

**Follow-up bug found immediately after, by noticing an unexpected `git status` diff rather than
assuming the commit was clean:** adding `main()`'s new `--document-library` CLI flag (defaulting to
the real relative path `content/document_library.json`, matching how `--ledger`/`--queue` already
default) meant any test calling `main()` without explicitly overriding that flag would run the real
watcher logic against the REAL repo's `content/document_library.json`, not a `tmp_path` fixture.
Two tests in `tests/test_run_integration.py`
(`test_all_feeds_failing_returns_nonzero_exit`, `test_partial_failure_still_returns_success_exit_code`)
called `main()` directly with only `--ledger`/`--queue`/`--cache-dir` overridden -- pre-dating the
new flag, so nobody had reason to add it. Concretely: running the full suite silently overwrote the
real, 69-document `content/document_library.json` with a single-item file derived from
`test_partial_failure_...`'s own broken-feed fixture state. Caught by noticing `content/
document_library.json` in `git status` when I hadn't intentionally touched it, not by any test
failure (both tests still legitimately passed -- the bug was a scope leak, not incorrect behavior
in what was actually being tested). Fixed by adding `--document-library <tmp_path>` to both call
sites, matching the pattern the other path flags already follow, and reconfirmed by regenerating
the real file and re-running the full suite to prove it now survives untouched. Lesson: any new CLI
flag with a real-path default needs an audit of every existing test that calls that CLI's `main()`
directly, not just the tests written alongside the new flag.

## Deploy workflow: why it needs two trigger paths, not one (2026-07-09)

Per Fable PM's explicit deployment constraint: whatever rebuilds and commits the static site must
push using the workflow's own `GITHUB_TOKEN`, never a personal access token, because GitHub does
not trigger `on: push` workflows from a `GITHUB_TOKEN`-authored push (the exact mechanism this
project already relies on for `watch.yml`'s `repository_dispatch` call to `analyze.yml`, verified
against GitHub's own docs back in Phase 2). Working through what this means for `deploy.yml`
specifically: if it were a plain `on: push`-triggered workflow, it would correctly fire from the
CCR-triggered analyst/verifier runbook's commits (those push with real git credentials, not
`GITHUB_TOKEN`) and from any manual push -- but it would **never** fire from `watch.yml`'s own
commit, since that push uses the default `GITHUB_TOKEN` precisely to avoid other unwanted
recursive triggers. A `document_library.json`-only update from a routine watcher run would
silently never redeploy.

Fixed by giving `deploy.yml` two trigger paths: `on: push` (paths: `content/**`, `data/**`,
`config/jurisdiction.json`, `pipeline/site/**`) for the CCR/manual case, plus
`repository_dispatch: types: [site-rebuild-needed]`, explicitly fired by a new step in `watch.yml`
right after its existing `queue-updated` dispatch to `analyze.yml` -- same pattern, different
event type, same underlying reason.

**Superseding revision, same day:** the first version of this workflow committed the rendered
output to `docs/` (the common "deploy from branch, /docs folder" GitHub Pages convention) using the
default `GITHUB_TOKEN`, matching every other generated-artifact commit in this project. Building the
site for real (not just reading the YAML) immediately surfaced a real collision: `docs/` already
holds `docs/analyst-runbook.md` (Phase 2's operational runbook), so the generated `index.html`,
`static/`, etc. would land in the same directory as an unrelated operational document -- confirmed
live by actually running the generator against `--output-dir docs` and seeing both side by side.
Renaming the runbook instead would have required updating every reference to it, including the
literal path already baked into the live CCR trigger's stored prompt text
(`trig_01Bk3Lz2FKf3pWRMFkqBcdDE`) -- a riskier, wider-blast-radius change than switching the site's
own output location.

Switched instead to GitHub's official Actions-based Pages deployment
(`actions/upload-pages-artifact` + `actions/deploy-pages`, both pinned to verified commit SHAs via
`git ls-remote`): the site builds into `_site/` (gitignored, an ordinary workflow-run artifact, never
committed to git at all) and is uploaded directly to GitHub's Pages hosting infrastructure. This is
also the more modern, currently-recommended approach generally, not just a workaround for the
naming collision -- it avoids polluting git history with rendered HTML/CSS on every content change,
and sidesteps the `GITHUB_TOKEN`-doesn't-trigger-`on:push` commit-recursion question entirely, since
this workflow no longer commits anything back to the repository. The dual-trigger design (`on: push`
+ `repository_dispatch` from `watch.yml`) is unchanged and still necessary for the same underlying
reason. **Owner action still required, mechanism just changed:** Settings -> Pages -> Source:
"GitHub Actions" (not "Deploy from a branch" as originally planned).

## Phase 5 kickoff: scoping audit.yml, corrections, and improve.yml (Fable PM, 2026-07-09)

Phase 5 per spec is "watch->analyze->verify->publish untouched for 14 days with correct output;
audit + corrections + improve loop live," acceptance criterion "two consecutive real regulator
publications flow to the site with zero human action." Brought this to Fable PM before building:
the 14-day soak and "two consecutive real publications" parts of that criterion cannot be completed
synchronously in any session, since they require elapsed real-world time and the CCR trigger firing
on its own schedule (currently disabled pending this branch's merge). Fable's direction: treat that
as an explicitly-tracked open item (same pattern as the CCR trigger's own unfired status), get the
owner's merge/Pages/trigger-reenable punch list moving in parallel since that's the true long pole,
build `audit.yml` and the corrections plumbing now under specific conditions, and bring a design note
for `improve.yml` for review before writing any code (its blast radius -- potential write access to
`/pipeline`, `/config`, `/.github/workflows`, the prompts themselves -- is categorically different
from the other two, and deserves the same kickoff-style scrutiny Phase 1/2 got before implementation).

## Corrections mechanism built (task from Phase 5 kickoff), 2026-07-09

Built per Fable's explicit condition: **human-initiated and PR-reviewed by design, never
autonomous.** `pipeline/ci/apply_correction.py` is pure, deterministic code with zero judgment of
its own about what needs correcting or why -- every input (which card, what changed, the
correction's own supporting citation) is supplied explicitly by a human, via CLI arguments locally
or `.github/workflows/correction.yml`'s `workflow_dispatch` form inputs. Deliberately **not** wired
to auto-trigger from `audit.yml`'s findings: a broken link or a stale pillar is a prompt for a human
to look, not evidence that a specific claim on a specific card is actually wrong -- conflating "the
audit noticed something" with "therefore auto-correct it" would be exactly the kind of unsupervised
autonomy Fable's condition was meant to prevent.

`correction.yml` never commits to `main` directly: it creates a branch, applies the correction (also
re-running `path_allowlist` and `validate_content` as real subprocess gates, same as every other
content-touching workflow in this project), commits under the `hk-radar-bot` identity, pushes the
branch, and opens a PR via the pre-installed `gh` CLI -- a human must review and merge it. No new
third-party GitHub Action was added for PR creation (e.g. `peter-evans/create-pull-request`); reused
the runner's built-in `gh` CLI instead, consistent with this project's preference for pinned
`actions/*` officials over third-party marketplace actions wherever avoidable.

**Security note, applied deliberately:** `workflow_dispatch` input values are assigned to `env:`
variables and referenced as `$CARD_ID`/`$CORRECTION_NOTE`/etc. in every `run:` step, never
interpolated directly via `${{ github.event.inputs.* }}` inside a shell script body -- this follows
GitHub's own guidance against script injection from untrusted input text. `workflow_dispatch` can
only be triggered by a repo collaborator with write access, so the practical risk here is lower than
for a PR-triggered workflow reacting to arbitrary external input, but the same safe-by-construction
pattern costs nothing to apply and removes the question entirely rather than relying on who-can-
trigger-this as the only safeguard.

`card.json`'s existing (already-defined, previously-unused) optional `correction_note` field and the
`"corrected"` status enum value are exactly what this wires into -- no schema change needed.
`data/corrections.json`'s schema also already existed from Phase 1, unused until now. 8 new tests in
`tests/test_apply_correction.py`, including schema-validation of both the correction record and the
corrected card. 214 tests passing.

## Real Lighthouse accessibility audit against the literal P4 acceptance criterion (2026-07-09)

Spec §10's Phase 4 acceptance criterion literally names "Lighthouse ≥90 a11y," not just a manual
contrast check -- re-read the spec after Fable's Phase 4 sign-off and realized the WCAG contrast-
ratio test built earlier only covers one narrow slice of what an actual Lighthouse accessibility
audit checks. Ran the real tool: installed via `npx lighthouse` (network access permitted this;
needed `CHROME_PATH` pointed at the pre-installed Playwright Chromium, since no system Chrome
exists in this environment), served the real generated `_site/` locally, and ran a real audit
against all 7 pages.

First real run found a genuine, legitimate issue on the Timeline page: **98/100**, docked for
"Heading elements are not in a sequentially-descending order" -- the shared card macro
(`pipeline/site/templates/_macros.html`) used `<h3>` for every card title unconditionally, but
Timeline's own page structure goes straight from its `<h1>` to the cards with no intervening `<h2>`,
skipping a level. Fixed by making the heading macro parameterized (`heading_level="h2"` default),
correct for Timeline's actual nesting depth; a future page that embeds a card one level deeper
(e.g. a pillar page's "recent activity" section) can pass `heading_level="h3"` explicitly rather
than the macro silently assuming one fixed depth everywhere.

All 7 pages re-audited after the fix: **100/100 on every single page** (Start Here, State Board,
Trajectory Board, Timeline, Document Library, Glossary, Method & Audit), well clear of the spec's
≥90 threshold. This is a genuinely separate, more thorough check than the earlier WCAG
contrast-ratio unit test -- that test only proves the palette's specific hex values behave
correctly in isolation; this proves the actual rendered DOM structure of every real page passes an
industry-standard automated accessibility audit, catching a real structural defect the narrower
test could never have found.

## Correction: internal model identifier was leaking into public content (2026-07-09)

Found by actually looking at a rendered screenshot of the Start Here page during Phase 4's browser
verification pass, not by any automated check: the page's footer displayed `generated ... ·
claude-sonnet-5`. `analyst_prompt.md`'s original instruction for the card schema's `model` field
said "the actual model you are running as, not a placeholder" -- every one of the 5 published cards
and `content/start_here.json` had accordingly written the literal internal model-version identifier
string (`claude-sonnet-5`), which is explicitly restricted to this session's own chat replies, never
to be included in any artifact pushed to a repository.

CLAUDE.md rule 1 genuinely does require a "model name" on every card, for transparency -- that
requirement stands. The fix is in what counts as satisfying it: changed all 6 affected files'
`model` field from `"claude-sonnet-5"` to `"Claude (Anthropic)"` -- a human-readable statement that
an AI (and which one) produced the content, without the specific internal version identifier.
Updated `analyst_prompt.md`'s instruction to match, so future analyst runs don't reintroduce this:
"a human-readable name for the model family... never the exact internal model-version identifier
string (no version numbers/dates/internal IDs)."

Re-validated all 6 files against their schemas and re-ran the full test suite after the fix; no
other content field was touched (citations/quotes untouched, so the deterministic authenticity gate
result is unaffected).

## Phase 4 gate item, flagged now so it isn't lost (Fable PM, 2026-07-09)

CLAUDE.md rule 1 requires every card to carry the "AI-generated summary... not legal or regulatory
advice... always verify against the linked primary source" disclaimer, plus a visible generation
timestamp, model name, and verification status. It is correctly absent from `card.json`'s schema
and from every generated card today -- there is no frontend yet, and duplicating that boilerplate
into every JSON record would be the wrong place for it (it's a rendering concern, not a data
concern). **Explicit Phase 4 requirement, not optional:** no frontend page may render a card,
pillar state, or trajectory entry without this disclaimer appearing alongside it. Do not let this
slip between now and Phase 4 kickoff.

## Follow-ups for later phases (not decisions, just noted so they aren't lost)

- Phase 2 must add the actual CI path-allowlist gate (today it's a documented rule in CLAUDE.md,
  not yet a machine-enforced check, since there are no AI jobs to restrict yet). Per Fable PM
  checkpoint 2, this should be the first thing built in Phase 2, before any analyst/verifier job
  is wired in — not an afterthought.
- `content/` directory (cards, pillar states, trajectory, glossary data) doesn't exist yet —
  correctly out of scope per the kickoff instruction, but noted so no one mistakes its absence
  for an oversight.
- ~~Once this branch merges to `main`, trigger one real `workflow_dispatch` run of `watch.yml`~~
  **Resolved 2026-07-09.** PR #1 merged; `list_workflows` immediately showed `Watcher` registered.
  Triggered `workflow_dispatch` on `main` (run `28991034262`): completed/success in 21s, all 9
  feeds `OK ... new=0` (idempotency held live, ~20 min after the manual run), commit step
  correctly `skipped` (no diff). See PROGRESS.md's 2026-07-09 "PR #1 merged" entry. Non-blocking
  note from the job log: GitHub is deprecating Node 20 for actions and force-runs our pinned
  `actions/checkout`/`actions/setup-python` on Node 24 in the meantime (their own compat shim, not
  a failure) — worth bumping the pins next time either action ships a Node-24-native release.
- The two logged anonymity flags (LICENSE "Big Fan" copyright line, non-bot initial commit) should
  be resolved with the human owner before public launch — deliberately left as owner decisions,
  not made unilaterally during this build.

## Live audit.yml run in the dev sandbox: real bug, discarded contaminated output (2026-07-09)

Before committing `audit.yml`, ran `pipeline.audit.run` live against the real repo content as a
final check beyond the 25-test fixture suite. It returned 50 events, 49 flagged actionable -- but
47 of those "link_rot" findings were not genuine dead links, and the contaminated output (including
an auto-appended backlog section this same run wrote to this file) was deleted rather than
committed, for reasons recorded here rather than silently.

Every one of the 47 failed with `SSLCertVerificationError: unable to get local issuer certificate`,
and every single one was against one specific subdomain: `brdr.hkma.gov.hk` (HKMA's document-ledger
host, used for circular/guideline PDF links). Diagnosed before trusting the numbers:

- Reproduced independently outside the audit pipeline: `curl` and Python `requests` failed
  identically and deterministically against *every* `brdr.hkma.gov.hk` URL tried, including ones
  never mentioned in the findings list, even with the sandbox's own proxy CA bundle
  (`/root/.ccr/ca-bundle.crt`) passed explicitly via `--cacert`.
- Sibling HKMA hosts on the same domain (`www.hkma.gov.hk`) and SFC's site verified and fetched
  cleanly over the same network path -- including a real, independently-reproducible `404` on
  `https://www.hkma.gov.hk/eng/regulatory-resources/consultations/20250113-1/` (see below).
- `openssl s_client`'s default trust store completed the TLS handshake to `brdr.hkma.gov.hk`
  successfully through this sandbox's TLS-inspecting egress proxy (`verify return:1` at every
  depth), while `curl`/`requests` failed even when pointed at that same proxy's own CA bundle.

This sandbox's outbound HTTPS goes through a policy-enforcing egress proxy that re-terminates TLS
and re-signs a fresh per-host certificate; one host verifying for one TLS client's trust path but
not another's, while every other host on the same domain is unaffected, points at a sandbox-local
proxy/cert-chain quirk specific to this dev container -- not evidence that ~47 real HKMA documents
went dead simultaneously. `audit.yml`'s real execution environment is a normal GitHub Actions
runner with direct internet egress and no intercepting proxy, so this should not reproduce there.

**Decision:** discarded this run's `data/audit/latest.json` rather than commit it -- publishing
"49 broken links, mostly HKMA circulars" to the public Method page on the strength of a sandbox
TLS artifact would be exactly the kind of fabricated/misleading claim the editorial rules in
CLAUDE.md exist to prevent, and worse than the honest "audit hasn't produced real data yet" state
`method.html` already renders gracefully. The `audit.yml` code itself is not in question -- it is
proven correct by the 25 fixture-based tests, which don't touch the network at all. The genuine,
authoritative first run happens when `audit.yml` executes for real via its GitHub Actions cron,
post-merge.

**One finding in the 49 was real and independently reproducible, not a proxy artifact:** the plain
HTTP 404 on `https://www.hkma.gov.hk/eng/regulatory-resources/consultations/20250113-1/` (this URL
is not on `brdr.hkma.gov.hk` and returned a genuine 404, no SSL error, confirmed with a fresh `curl`
run outside the audit pipeline). Flagged here as a known open item for a human to check against the
regulator's current page structure -- not auto-corrected, consistent with the corrections
mechanism's human-initiated-only design immediately below.

## improve.yml built per Fable PM's four required refinements, 2026-07-09

Fable approved the design note's core architecture ("defense doesn't depend on the model behaving,
it depends on the gate") with four required additions before implementation. Built all four, then
the mechanism itself.

**1. Hard-deny list stated as a principle, then enumerated from it.** Fable's exact framing:
"nothing whose job is to check, gate, or constrain the pipeline's own output may be modified by the
thing being improved." `pipeline/ci/improve_scope.py` enumerates from that principle, not from the
two example files (`path_allowlist.py`, itself) that came up in the original design note:
`pipeline/verify/gate.py`, `pipeline/verify/authenticity.py`, `pipeline/ci/validate_content.py`,
`pipeline/ci/apply_verification_gate.py`, `pipeline/ci/promote_verified.py`,
`pipeline/ci/apply_correction.py`, plus `pipeline/ci/path_allowlist.py` and
`pipeline/ci/improve_scope.py` themselves, plus every file under `pipeline/schemas/` and every file
under `.github/workflows/` (both denied by prefix, not individually, since an allowlist-of-
exceptions would need updating every time a new workflow or schema is added -- the same fail-unsafe
problem an allowlist avoids elsewhere in this project, just applied to a deny rule this time).

**Added one file to the list Fable didn't name, applying the stated principle rather than copying
the list verbatim:** `pipeline/ci/promote_drafted.py`. Fable named its sibling,
`promote_verified.py`, as an example; `promote_drafted.py` performs the exact same category of
trust-critical ledger-state mutation and would be an inconsistent gap if left editable.

**Deliberately NOT hard-denied, a judgment call, not an oversight:** `pipeline/verify/docfetch.py`
(a fetch/extract utility the gates call, not itself a check -- legitimate self-improvement
territory, e.g. today's own sandbox investigation would motivate a real retry-on-transient-TLS-
error improvement here) and `pipeline/ci/queue_check.py`/`pipeline/ci/seed_backfill.py` (a
scheduling helper and a one-time historical seeding script, neither a correctness gate over
AI-generated content). Locked in with an explicit test
(`test_docfetch_is_deliberately_not_hard_denied`) so a future edit can't silently widen or narrow
the list without a matching test update. `pipeline/audit/**` is likewise left editable -- it reports
findings, it doesn't gate or grant trust to published content.

**2. `pipeline/prompts/*.md` stays editable, but spotlighted, not locked.** Built
`pipeline/ci/prompt_change_justification.py`: a real subprocess gate, not a review-etiquette norm --
if the diff touches `pipeline/prompts/**`, the PR body must carry an explicit
`Editorial-prompt justification:` line naming the specific CLAUDE.md rule the change relates to, or
the gate fails before commit. The AI job writes its PR title/body to a scratch file
(`.improve-pr-body.md`) that the orchestrating workflow reads and then deletes before it can ever
become part of the proposed diff itself.

**3. Bounded selection via a dedicated queue, not open-ended discretion.** Built
`pipeline/schemas/improve_queue.json` + `pipeline/ci/improve_queue.py`
(`load_queue`/`save_queue`/`pick_next_open_item`/`mark_item_picked`, same "deterministic code owns
every mutation" pattern as `data/ledger.json`). The real, committed `data/improve_queue.json` ships
**empty** -- manufacturing "candidate improvements" without a genuinely validated, independent
reason would itself be a form of fabrication. improve.yml exits immediately, no run, when the queue
has no `status: "open"` item, same zero-cost-when-empty principle as the analyst's
`data/queue.json`. The queue is meant to be populated by a human (or a future producer) over time;
this build does not decide what goes in it. The AI job is handed only the one picked item's `id`
and `description` as task input -- it never reads the queue file itself, and has no `/data` write
access at all to mark its own item picked; that transition is deterministic code the orchestrating
workflow runs after a PR is opened, the same trust class as a ledger-status transition.

**4. `improve_scope.py` tested with the same rigor `path_allowlist.py` got, both directions, plus
the specific case Fable named.** `tests/test_improve_scope.py` mirrors `test_path_allowlist.py`'s
structure exactly (pure-function cases, a real scratch-git-repo end-to-end case, `main()` CLI
cases) and includes, verbatim, the case Fable said they'd verify:
`test_fails_on_gate_file_even_though_nominally_under_the_allowed_pipeline_root` -- a diff touching
`pipeline/verify/gate.py` fails even though it is nominally under the allowed `pipeline/` prefix,
because the hard-deny check runs and wins regardless of the allow check.

**Also built, agreed overdue independent of improve.yml:** `.github/workflows/pr-check.yml` -- runs
the full test suite (including the jurisdiction-agnosticism scan) on any PR touching `/pipeline` or
`/config`, human-authored or improve.yml's own. This is a required-status-check *candidate*; actual
branch-protection enforcement (require this check to pass, require a PR, disallow direct pushes to
`main`) is a GitHub admin setting outside this session's tools -- added to the owner punch-list
alongside GitHub Pages enablement and the analyst/verifier CCR trigger re-enablement.

**Architecture pivot applied identically to `improve.yml` as it already was to `analyze.yml`, found
before it became a silent gap:** a literal `improve.yml` invoking `anthropics/claude-code-action@v1`
needs the same `CLAUDE_CODE_OAUTH_TOKEN`/`ANTHROPIC_API_KEY` secret this deployment will never
provision. Built `.github/workflows/improve.yml` as the same kind of complete, correct,
spec-literal-but-dormant fallback `analyze.yml` already is (credential-checked, skips cleanly), and
`docs/improve-runbook.md` as the CCR-triggered procedure a fired session would follow instead,
mirroring `docs/analyst-runbook.md`.

**Deliberately not done in this build: no live CCR trigger was created for `improve-runbook.md`,**
unlike the analyst/verifier's `trig_01Bk3Lz2FKf3pWRMFkqBcdDE`. This mechanism's blast radius (write
access to `/pipeline` and `/config`) earned it a kickoff-style design review before any code was
written; standing up a live recurring trigger for it is a further, separate decision for the
owner/Fable PM to make explicitly once the built mechanism itself has been reviewed, not something
to bundle into the same build step that produced it.

**Cron schedule note:** GitHub Actions cron cannot express a literal 14-day interval; approximated
"fortnightly" with two fixed calendar dates a month apart (`0 4 1,15 * *`) -- simplest reasonable
reading of the spec's "cron, fortnightly," logged here per this project's standing practice for
silent decisions.

47 new tests across `improve_scope`, `improve_queue`, and `prompt_change_justification`. 255 tests
passing total.

**Update: independently verified and signed off by Fable PM the same day** (pulled the branch, ran
the suite, read every file named above in full, confirmed via `list_triggers` no live CCR trigger
exists). All four required additions confirmed real and correctly implemented; no changes
requested. Not standing up a live trigger yet was confirmed as the right call, with an explicit
sequencing precondition recorded in PROGRESS.md's "Owner / next-step punch list": re-enabled
analyst/verifier trigger must complete several real successful cycles, and one full manual dry run
of `docs/improve-runbook.md` must happen and be reported back, before either trigger's
live-activation question is revisited. Full checkpoint text in PROGRESS.md's "PM checkpoints"
section.

## Visual redesign (light cream + dark mode + interactive timeline) and fact-check enhancement, 2026-07-09

Owner-requested, out of the normal phase sequence: the live site's UI read as visually plain (near-
white `#FAFAF7`, no dark mode, zero elevation, "Timeline" page was a flat card list with no actual
timeline), plus an explicit ask to confirm — and if needed strengthen — the anti-misrepresentation
logic. Owner's own condition attached: a Fable PM audit of UI/UX, every interactive control, and the
fact-check/data-source methodology, work only reported as done once that audit passes.

**Color tokens, independently verified twice.** Only `--paper` changed in light mode
(`#FAFAF7` -> `#F2ECDD`, a genuine warm cream, not the "just less white" trap); `--ink`/`--seal-red`/
`--harbour-teal`/`--amber` kept their existing light-mode hex values unchanged. New tokens added:
`--surface-card`, `--ink-muted` (replaces every hardcoded `#555`), `--verified-green` (replaces
hardcoded `#4a6a4a`), `--hairline`, `--shadow-elevation`, and a full dark-mode value for every one of
the above. Every contrast figure (ink/seal-red/harbour-teal/verified-green against both the page
background and the card surface, in both themes) was computed with real WCAG relative-luminance
math and re-checked independently by a second pass before implementation — all clear >=4.5:1 where
normal text requires it; `--amber` deliberately sits in the 3.0-4.5 band in both themes (border/
background accent only, never text color — enforced by a dedicated regression test,
`test_amber_as_text_color_fails_aa_and_is_therefore_not_used_as_text[_dark]`). One dark-mode
candidate for `--seal-red` was rejected during design because it scored 4.404 against the dark card
surface (just under AA) before the shipped value was chosen instead.

**Theme switching: OS preference + explicit toggle, owner's own choice between the two options
offered.** `prefers-color-scheme: dark` sets the automatic default; an explicit `#theme-toggle`
button (persisted to `localStorage`) always wins via `[data-theme]` selector specificity, regardless
of source order. A synchronous inline script is the first thing in `<head>`, before any stylesheet,
so the stored choice applies before first paint — no flash of the wrong theme.

**Interactive timeline, both placements the owner asked for.** A new `build_timeline_events()`
merges cards and documents onto one real, ascending-sorted date axis; documents with no
`published_at` are excluded rather than guessed at, since a timeline axis has no honest way to place
an undated point. The Trajectory Board's loose `date_or_window` strings (`"2026"`, `"H1 2026"`) are
deliberately kept in a visually separate "officially indicated" rail alongside the precise axis,
never merged onto it — merging them would fabricate a precision the source data doesn't have. The
same `timeline_ribbon()` macro renders capped (`limit=40`) as a homepage hero and uncapped at the top
of the dedicated Timeline page. Built JS-optional throughout: every marker is a real `<a href>`
(works with JS disabled), a `<details>` fallback lists the same events as plain text, and the hover/
focus tooltip enhances rather than gates — the same information is reachable by keyboard focus alone.
The categorical 7-color pillar palette (position in `config.pillars[]` is the primary identity
channel, color reinforces it) was validated with the `dataviz` skill's own `validate_palette.js`
against this project's real surface colors, not eyeballed: worst adjacent-pair separation 76.9 (light
mode) / 70.4 (dark mode), all 7 slots >=3:1 contrast against both page and card surfaces in both
themes.

**Two real pre-existing bugs found and fixed while doing this, not just noted:**
1. Hardcoded `#555`/`#fff`/`#4a6a4a` colors scattered across several templates' inline `style="..."`
   attributes and `style.css` itself couldn't respond to a `[data-theme]` override by construction —
   replaced with token-referencing classes (e.g. `.meta-line`). Generalized into a permanent
   regression guard, `test_no_hardcoded_color_leaks_into_rendered_output`, rather than just fixed
   once.
2. `.trajectory-board`/`.trajectory-row` hardcoded `var(--ink)`/`var(--paper)` to get their
   permanently-dark-board/light-text look — which would have silently *inverted* the instant those
   two tokens became theme-reactive. Fixed with two new, genuinely theme-invariant tokens,
   `--trajectory-surface`/`--trajectory-ink`, that never respond to `prefers-color-scheme` or
   `[data-theme]` at all. (See below — this fix was real but incomplete; Fable's audit found the
   remainder.)

**Fact-check layer: what already existed, confirmed by full-file reads, not assumed.** The
deterministic, non-bypassable citation-authenticity gate (`pipeline/verify/gate.py`'s
`enforce_verification_gate`, live re-fetching every citation URL on every run) was already real and
was left untouched. Confirmed gaps: nothing checked for cherry-picking/out-of-context quoting
(inherently a semantic judgment, not something a deterministic check can do honestly), and nothing
checked numeric claims (amounts/percentages) beyond citation-quote substring matching.

- `verifier_prompt.md`/`analyst_prompt.md` gained explicit cherry-picking language: an accurate,
  verbatim quote used in a way that omits an adjacent caveat the source itself makes must be
  rewritten or dropped, not waved through because the substring technically matches. This stays a
  prompt-level instruction on purpose — deliberately not oversold as a deterministic check, since
  semantic misrepresentation genuinely cannot be caught by regex.
- New `pipeline/verify/numeric_claims.py`: bounded, conservative regex extraction of currency
  amounts/percentages/counts (deliberately not bare numbers or dates, to avoid false positives
  against legitimate paraphrase), checked against the same already-fetched source text. Its own
  docstring states plainly what it does *not* do — cannot and does not detect cherry-picking, spin,
  or semantic misrepresentation — so the honesty-of-scope principle lives in the code, not just in
  this log. Wired into a new `enforce_full_gate()` alongside (not replacing) the untouched
  `enforce_verification_gate`.
- Two more real, previously-undiscovered bugs in the corrections mechanism, found while wiring the
  gate onto it: `pipeline/schemas/corrections.json` was typed as a single object while
  `data/corrections.json` is actually written as an array (would have broken schema validation the
  first time a real correction ever happened); and `apply_correction_to_card` never merged a
  correction's own supplied citation into the card's `citations[]` at all, which would have made the
  new gate-on-correction step check nothing. Both fixed; `correction.yml` now runs the full
  verification gate on the correction's own citation before schema validation, and real corrections
  data is now surfaced in a table on the Method page instead of a static placeholder sentence.

Full suite: 303 tests passing at this point (up from 255 in the last logged entry above). Verified
directly in a real headless browser (Playwright): both themes, the toggle persisting across reload
and fresh navigation, the timeline's hover/keyboard/click-through/no-JS-fallback behavior, and all 7
pages in both themes — 35/35 checks passing.

### Fable PM audit finding, same day: trajectory board lost its identity in dark mode specifically

Per the owner's own condition, this work was not reported as done until Fable's audit passed. Fable
independently reproduced the test count, re-ran the Playwright script itself against a fresh build,
and re-ran `validate_palette.js` itself against the live hex values — all matched. It also computed a
contrast ratio nobody had checked: **`--trajectory-surface` (#132A43) against the dark-mode page
background (#0F1E2E) is only 1.16:1** — both are near-black navy. The board's own border was set to
`var(--trajectory-surface)`, i.e. the same color as its own background, which is a no-op border by
construction; this had been invisible in light mode purely by accident, since the board's fill
already contrasts 12.37:1 against the light page there. In dark mode, with no independent border
color and almost no fill-vs-page contrast, the board — the site's signature "departures board"
component, and the exact thing the theme-invariant-token fix above was built to preserve — nearly
disappeared into the surrounding page.

**Fix:** `.trajectory-board`'s border now uses `var(--amber)` instead of `var(--trajectory-surface)`,
plus a `box-shadow: var(--shadow-elevation)` for additional depth. `--amber` is already validated and
already reserved in this codebase for exactly this role (border/background accent, never text — see
`.badge-unverified` above) and independently clears the WCAG 1.4.11 non-text/UI-boundary 3:1
threshold against **both** page backgrounds in both themes (3.09 light / 3.62 dark) and against the
board's own dark fill in both themes (4.01 light / 3.13 dark) — so the border reads as a real frame
whether viewed from the page side or the board's own interior, in either theme. Confirmed visually
(zoomed dark-mode screenshot of the board, and the full page) after the fix: the board now reads as a
distinct, framed panel against the dark page, matching the light-mode look's intent. Locked in with a
new regression test, `test_trajectory_board_border_has_real_contrast_against_both_page_backgrounds`,
which asserts the actual bug (a same-color border scores under 3:1 against the dark page) as well as
the fix. Full suite: 304 tests passing. Re-verified with Playwright: 35/35.

**Process gap Fable also flagged, fixed by this section existing:** none of this work — the palette/
CVD derivation, the two pre-existing CSS bugs, the fact-check gaps closed, or (until now) the
trajectory-board finding — had a durable log entry here, only two commit messages. Every phase before
this one got one; this is the corrected record.

### 2026-07-11 — GitHub Pages was silently serving the Jekyll README fallback, not the real site

Full finding and fix are logged in `PROGRESS.md`'s 2026-07-11 Log entry (not duplicated here in
full to avoid drift between the two files). Backlog-relevant angle: this is a second instance of the
same shape of mistake `PROGRESS.md`'s Phase 1/2/3 entries already flag repeatedly in this project —
**trusting a first green/200 result instead of inspecting the actual output.** The 2026-07-09
"Pages confirmed live" check technically executed (an HTTP 200, a disclaimer-text grep hit) but never
actually distinguished the real generated site from GitHub's own Jekyll fallback of `README.md`,
because both legitimately contain the same disclaimer sentence. The check was not wrong on its own
terms; it was checking the wrong thing.

**Standing lesson for any future "is X actually live" verification in this project:** prefer an
assertion that only the real artifact could satisfy (a page that doesn't exist anywhere else, an
absence check for a marker the fallback *would* produce) over a substring match on content that might
legitimately appear in more than one place. Everywhere else in this project's own history (the
path-allowlist bare-directory bug, the smart-quote/PDF-artifact authenticity bugs, the relevance-
filter gap, the trajectory-board contrast bug above) the fix was the same pattern: read the actual
rendered/served output byte-for-byte rather than trusting that a check passing means the thing it's
supposed to guard against didn't happen.

### 2026-07-11 — Fable-directed compliance/UX audit: full findings, deferred and owner-flagged items

Mechanics and the 12 executed fixes are logged in `PROGRESS.md`'s matching 2026-07-11 entry. This
entry is the durable record of everything that survived triage but was **not** applied this session,
so none of it gets lost the way ungoverned findings tend to. 22 of 34 fix items were not executed: 3
were refuted by a fresh, skeptical re-read of the actual current files (correctly not fixed -- a
citation-URL/quote pair and a trajectory-source claim that held up, and a theme.js
OS-preference-listener claim that didn't reproduce), 2 must-fix items need a real implementation pass
rather than a mechanical patch, 6 should-fix/nice-to-have items likewise, and 9 are flag-for-owner:
items where the correct fix touches protected territory (`CLAUDE.md` itself, `pipeline/schemas/**`,
`.github/workflows/**`, `pipeline/ci/path_allowlist.py`'s core deny logic) or is a genuine policy
judgment call, per CLAUDE.md's own rule that those require "an explicit, separate human-approved
change." Full detail on each (files, description, acceptance criteria) lives in the audit
workflow's own transcript; the summary below is enough for the owner to decide next steps without
digging for it.

**Needs a real implementation pass (not owner-gated, just not mechanical enough for a same-session
auto-fix):**
1. `document-library-dead-link` -- one Document Library entry links to a 404'd HKMA URL with a
   paraphrase-style title unlike its 68 siblings; needs the current live URL located before fixing.
2. `timeline-skip-link` -- up to 77 individually-focusable timeline markers with no skip-link,
   a real WCAG 2.4.1 gap.
3. `generate-docstring-stale` -- `generate.py`'s module docstring still describes the abandoned
   `docs/`-folder branch-deploy model its own code no longer uses -- the last surviving trace of
   the exact assumption that caused the 2026-07-11 Pages outage.
4. `model-field-leak-guard` -- no deterministic guard exists against the internal-model-identifier
   leak recurring in a card's `model` field (the 2026-07-09 fix was prompt-text only, the same
   enforcement class that caused the leak); needs a carefully-designed reject-list regex in
   `validate_content.py`, not a blanket pattern that could false-positive a legitimate display name.
5. `documents-page-disclaimer-clarification` -- the Document Library carries the identical
   AI-generated-summary disclaimer over rows that are deterministic watcher output, which is
   over-warning that risks banner-blindness on the pages where the disclaimer genuinely matters.
6. `corrections-log-hash-fallback` -- if a corrected card is ever removed, the Corrections Log
   (the one page whose entire purpose is rule 6) falls back to rendering a bare 64-character sha256
   hash as the card title.
7. `banking-money-secondary-source-basis` -- `content/pillar_states/banking_money.json`'s own
   `open_items` admits its HKMA-circular claims rest solely on secondary legal commentary because
   the primary circulars couldn't be fetched during research -- needs either a real primary-source
   re-verification pass or an explicit in-text caveat, the same pattern `aml_cft_enforcement.json`
   already uses for its own unconfirmed figure.
8. `citation-domain-check-missing` -- the citation-authenticity gate checks that a quote is genuine
   but never that the URL is an official regulator domain, so a law-firm blog with an accurate quote
   passes cleanly; rule 2 (primary sources only) is enforced by prompt instruction alone today.

**Nice-to-have, not urgent:**
9. `timeline-undated-docs-caption` -- nothing on-page explains that undated documents are excluded
   from the Timeline ribbon (invisible today since every current document has a date; will produce a
   silent count mismatch the first time it doesn't).
10. `doc-search-aria-live` -- the Document Library's live search gives screen-reader users no
    feedback on filter results.

**Flag-for-owner (protected territory or a policy decision -- report-only, no agent should apply
these without an explicit, separate human-approved change):**
11. `provenance-trio-non-card-content` -- pillar summaries, glossary definitions, trajectory
    entries, and Start Here are all AI-analyst-authored but render with no generation timestamp,
    model, or verification-status trio, and their schemas (`pillar_state.json`, `glossary.json`,
    `trajectory.json`, `start_here.json`) have no fields to hold them -- only cards currently pass
    through the verifier at all. Needs an owner decision on two questions: approve the schema
    extensions, and decide whether non-card content should be verifier-gated or explicitly labeled
    "Not independently verified."
12. `workflow-dispatch-missing` -- `audit.yml` and `analyze.yml` push to `main` with `GITHUB_TOKEN`
    but, unlike `watch.yml`, never fire the `repository_dispatch` that actually triggers
    `deploy.yml` -- live consequence: Method & Audit page findings go stale indefinitely after every
    weekly audit run. Also falsifies CLAUDE.md's own claim that `analyze.yml` "starts working
    exactly as diagrammed... with no other change required" if a secret is ever added -- today it
    would silently break at the publish step on first activation.
13. `deploy-post-verification-missing` -- `deploy.yml` has no post-deploy check that the live site
    is actually the real generator output (exactly the gap that let the Jekyll-fallback bug persist
    for two days across multiple all-green deploy runs) and never re-runs `validate_content.py`/
    `path_allowlist.py` before `generate.py`, trusting `main` unconditionally.
14. `claude-md-stale-build-state` -- `CLAUDE.md`'s own loop diagram and "Current build state"
    paragraph still say the audit loop is "not yet built," though Phase 5 shipped it on 2026-07-09.
    The project's governing self-description being stale about a shipped phase is a real
    trust-undermining finding, but `CLAUDE.md` is read-only to every AI agent in this repo without
    exception -- only a human may edit it, even for a pure factual-staleness fix.
15. `recurring-non-bot-merge-commits` -- `git log` shows 5 non-bot-identity commits, not the 1 the
    backlog previously disclosed: beyond the logged initial commit, four PR-merge commits are
    authored under the owner's real GitHub handle. Because `correction.yml`/`improve.yml` are
    PR-only/human-merge by design, this recurs on every future merge, contradicting rule 5's
    anonymity guarantee and this file's own prior "single, contained, already-fixed"
    characterization of the issue -- corrected here rather than left standing. Three legitimate
    resolution paths exist (squash-merge policy, a bot-credentialed merge via the GitHub API, or an
    accepted-tradeoff note); the choice is the owner's.
16. `trigger-id-disclosure` -- `docs/analyst-runbook.md` states verbatim that internal trigger/
    session IDs "don't belong in commit messages or PROGRESS.md entries," yet the live CCR trigger
    ID is spelled out 6 times across `PROGRESS.md`/`IMPROVEMENT_BACKLOG.md` (including this file).
    Not a credential leak, but a verified contradiction between written policy and actual practice.
    Two legitimate resolutions: relax the runbook rule to match practice, or redact the six literal
    occurrences to match the rule -- owner's call.
17. `footer-license-scoping` -- the site footer's blanket "content CC BY 4.0" claim doesn't scope
    out HK-Government-copyright quoted excerpts; a downstream re-user could misread it as licensing
    quoted regulator text under CC BY when it remains Government copyright used under
    quotation/attribution. Rewording a public licensing claim is reserved to the owner (rule 7).
18. `google-fonts-third-party` -- `fonts.googleapis.com` is the site's only third-party runtime
    call; every page view sends visitor IP/user-agent to a Google domain. Not a bug (fallback font
    stacks mean a blocked request only degrades typography), but a real privacy-posture choice,
    increasingly relevant ahead of any EU/UK jurisdiction fork -- keep as-is or self-host, owner's
    call.
19. `path-allowlist-symlink-gap` -- verified by direct test: `pipeline/ci/path_allowlist.py`
    evaluates changed-path *strings*, not resolved targets, so a symlink placed under `content/`
    pointing into `pipeline/` passes the gate's prefix check without being resolved. Mitigated today
    only by the analyst/verifier sub-agents' own no-Bash tool grants -- the gate itself does not
    structurally deliver the "inspects the actual working tree" guarantee CLAUDE.md and the Method
    page both describe it as providing. `path_allowlist.py`'s core allow/deny logic is explicitly
    protected territory, so even this genuine gate bug must be escalated rather than patched by an
    agent under any framing.
