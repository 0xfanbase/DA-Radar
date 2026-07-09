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
