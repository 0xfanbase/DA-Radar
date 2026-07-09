# PROGRESS.md

Running, dated log of what has been built and verified. Read this first in any fresh session —
along with `git log` — to know exactly where the project stands before doing anything else.

## Phase status

- **P1 — Chassis: complete** (signed off by Fable PM checkpoint 2, 2026-07-09)
- **P2 — Analyst + verifier: complete, live-run-proven** (deterministically complete per the
  2026-07-09 build-complete entry; the live-run gap closed the same day when the runbook's
  analyst+verifier+gate procedure ran for real on 5 headline cards via the docs/analyst-runbook.md
  mechanism -- see the "First real analyst+verifier pipeline run" entry below. The CCR scheduled
  trigger itself, as opposed to the mechanism it runs, remains unfired as of this writing -- see
  that entry's operational note)
- **P3 — Seed backfill: complete** (7 pillar states, 5 verified headline cards, trajectory.json,
  glossary v1, the ~40-item -- in practice 69-item -- Document Library, and the Start Here page;
  see the 2026-07-09 entries below)
- P4 — Frontend: not started
- P5 — Full autonomy: not started

## Log

### 2026-07-09 — Phase 1 kickoff

- Read `HK_REG_RADAR_BUILD_SPEC.md` in full.
- Confirmed repo state: one commit, MIT LICENSE only, branch `claude/hk-radar-phase-1-mzlnxx`.
- Verified live, by direct fetch, that all target RSS feeds are valid RSS 2.0:
  - SFC: `Press-releases`, `Circulars`, `Consultations-and-Conclusions` (all at
    `https://www.sfc.hk/en/RSS-Feeds/...`, no `.xml` suffix).
  - HKMA: `rss_press-release.xml`, `rss_circulars.xml`, `rss_speeches.xml`, `rss_guidelines.xml`,
    `rss_legislative-council-issues.xml`, `rss_consultations.xml` (all at
    `https://www.hkma.gov.hk/eng/other-information/rss/...`).
- Spawned a Fable-model agent as project-manager reviewer for scope/risk sign-off at kickoff and
  at two build checkpoints (see "PM checkpoints" below).
- Scaffolded repo structure, `pyproject.toml`, `.gitignore`, empty schema-conformant
  `data/ledger.json` / `data/queue.json` (commit `chore: scaffold repo structure...`).
- Wrote `CLAUDE.md` (this phase's governance doc, per spec §11) and this file.

### 2026-07-09 — Phase 1 build complete

- Applied all Fable PM kickoff directives (see "PM checkpoints" below and IMPROVEMENT_BACKLOG.md).
- Built `config/jurisdiction.json` (HK: SFC ×3 feeds, HKMA ×6 feeds) and a fictitious
  `tests/fixtures/second_jurisdiction.json` ("Freedonia") side by side, before any watcher code.
- Implemented `pipeline/watcher/{clock,fetch,parse,hashing,jsonio,ledger,queue,run}.py` — stdlib +
  `defusedxml` RSS 2.0 parsing, retry/backoff + ETag-aware fetch, sha256 identity hashing, a
  derived (not accumulated) queue, canonical JSON serialization with write-if-changed.
- Authored all 8 schemas (`card`, `pillar_state`, `trajectory`, `glossary`, `ledger`, `queue`,
  `corrections`, `audit/event`) — all valid JSON Schema draft 2020-12.
- Live smoke-testing against all 9 real feeds (scratch dir, before touching committed `data/`)
  surfaced two real findings that changed the design — see IMPROVEMENT_BACKLOG.md's "Findings from
  live smoke-testing" section: the identity-hash fallback (`guid -> link -> title` was insufficient
  because one HKMA feed reuses a single generic `<link>` for every item; fixed to
  `guid -> (link + title)`), and neither SFC nor HKMA send `ETag`/`Last-Modified` on any feed (our
  conditional-GET support is correct but currently unexercised — a server-side fact, not a gap).
- Wrote 61 pytest tests (fetch, parse, hashing, ledger, queue, integration, jurisdiction-
  agnosticism, schemas) — all fixture-based, no live network in CI (an autouse fixture blocks real
  sockets structurally). **61/61 passing.**
- Added `.github/workflows/watch.yml` (daily cron 09:30 HKT + `workflow_dispatch`, bot-identity
  commit, path-scoped `git add`, GitHub Actions pinned to verified commit SHAs via `git ls-remote`).

**Live acceptance-criterion verification** ("watcher run produces a correct queue from live feeds;
re-run adds nothing"):

| Run | Timestamp (UTC) | Feeds ok | Items seen | Items new | ledger_changed | queue_changed |
|---|---|---|---|---|---|---|
| 1 | 2026-07-09T02:43:00Z | 9/9 | 984 | 983 | True | True |
| 2 | 2026-07-09T02:43:29Z | 9/9 | 984 | 0 | False | False |

Run 2 (29 seconds after run 1) touched zero files — `git status` after run 2 is completely empty,
and the local (git-ignored) ETag cache confirms neither SFC nor HKMA returned an `ETag` to cache,
consistent with the live-smoke-test finding above. Both `data/ledger.json` (983 items) and
`data/queue.json` (983 items, all `status: "queued"`) validate against their schemas.

### 2026-07-09 — Phase 2 build complete (deterministically; live LLM run still blocked)

Built in full, per Fable PM kickoff/checkpoint-A/checkpoint-B review (see "PM checkpoints" below):

- `pipeline/http.py`: shared retry/backoff core, refactored out of the Phase 1 watcher so the new
  document fetcher reuses it instead of duplicating.
- `pipeline/ci/path_allowlist.py`: the CI path-allowlist gate. Allowlist-based (fail unless every
  changed path is under `content/` or `data/`), not a denylist. Two integration points:
  working-tree mode (`git status --porcelain` — the real pre-commit use case) and diff mode
  (between two refs).
- `pipeline/verify/docfetch.py`, `authenticity.py`, `gate.py`: the deterministic
  citation-authenticity oracle and the non-bypassable pre-commit gate. The oracle only ever
  answers "is this quote a genuine substring of this source" — never which sentence a citation
  supports (that's the LLM verifier's job). The gate re-checks every citation itself and forces
  `status: "unverified"` on any failure, never trusting a card's self-reported status.
- `pipeline/watcher/ledger.py` extended with a real status-transition state machine (`queued ->
  drafted -> verified -> published`, `corrected`/`suppressed` from `published`, `error` from
  anywhere) — `InvalidStatusTransition` raised on illegal moves.
- `pipeline/ci/queue_check.py`, `validate_content.py`, `apply_verification_gate.py`,
  `promote_drafted.py`, `promote_verified.py`: the deterministic CI-job wiring — quota gate,
  schema validation of changed content/data files, the gate applied to real card files on disk,
  and the ledger-mutation scripts that the AI jobs never touch themselves.
- `pipeline/prompts/analyst_prompt.md`, `verifier_prompt.md`: the actual instructions the two AI
  jobs will run under, encoding CLAUDE.md's hard rules (data-not-instructions is rule 1 in both),
  the card schema shape, and the `content/` path convention.
- `.github/workflows/analyze.yml`: three jobs — `check-queue` (no AI, no cost when the queue is
  empty), `analyst` (`claude-code-action`, drafts under `content/cards/`), `verifier` (`needs:
  analyst`, a genuinely separate job/runner = fresh context, not a continued conversation).
  `claude_args` identical for both, tightened during design to drop `/data` access entirely once
  the promotion scripts took over every ledger mutation.
- `.github/workflows/watch.yml`'s Phase 1 no-op placeholder replaced with a real
  `repository_dispatch` POST using the job's own `GITHUB_TOKEN`.
- 28 new tests (136 total), all fixture-based, no live network.

**The one behavior every future session must know without digging for it** (Fable PM flagged
that this needs proactive, prominent disclosure, not something found by reading a docstring):
**a card whose only citation the deterministic gate finds fabricated still gets PUBLISHED** —
its ledger item reaches `status: "published"`, meaning the pipeline ran to completion and the
card is live on the site — but the card's own JSON carries `status: "unverified"`, which is the
actual reader-facing signal, displayed as a visible badge per CLAUDE.md rule 1 ("every card must
show ... verification status"). This is the spec's locked "fully auto-publish with disclaimers"
decision working as intended, not a bug: the ledger tracks *pipeline stage* (did analyst+verifier
finish), never *editorial confidence* — that lives entirely in the card's own `status` field.
Locked in by `tests/test_analyze_pipeline_integration.py`, which chains the real deterministic
functions end-to-end (`promote_drafted` -> simulated verifier pass -> `apply_verification_gate`
-> `promote_verified`) and asserts this exact, easy-to-mistake-for-a-bug end state explicitly, so
it can't be silently "fixed" without breaking a passing test first.

**Two residual gaps, named plainly, not papered over (same shape as Phase 1's pre-merge gap):**
1. No `CLAUDE_CODE_OAUTH_TOKEN`/`ANTHROPIC_API_KEY` secret exists yet, so no real analyst/verifier
   LLM pass has ever run. Every deterministic gate is tested; whether a real Claude Code agent
   actually resists a hostile fetched document the way the prompts instruct is fixture-unprovable
   by construction — the gates are the backstop for when it doesn't, not proof that it won't.
2. The `analyze.yml`/`watch.yml` chain (the `repository_dispatch` trigger firing, `fetch-depth: 2`
   giving the verifier job `HEAD~1`, the AI job's environment) has never executed on GitHub's
   actual infrastructure — YAML-validated and unit-tested piece by piece, not dry-run as a whole.

Per Fable PM directive: the first real live run's output (both commits, the actual card file, and
both jobs' `display_report` output) must be reviewed before Phase 2 is called operationally
closed — mirroring how Phase 1's live `workflow_dispatch` run, not just green tests, was the
actual closing evidence.

### 2026-07-09 — Phase 3 begins: 7 pillar states seeded, relevance-filter bug found and fixed

Researched the current state of all 7 pillars (exchanges/VATP, stablecoins, dealing/custody/
advisory/management, tokenization/RWA, funds/ETFs, banking/money, AML/CFT/enforcement) against
live primary sources (SFC, HKMA, FSTB, LegCo, gov.hk), via 5 parallel research passes. Wrote
`content/pillar_states/*.json` for all 7, validated against `pillar_state.json` and the real
`validate_content`/`path_allowlist` gates, committed.

While preparing to run the analyst+verifier pipeline on the spec's 5 headline events (VATP regime,
stablecoins licences, dealing/custody consultations, Policy Statement 2.0, enforcement), found that
`data/queue.json` held 988 items, not the "few per week" CLAUDE.md assumes — the Phase 1 watcher
queues every SFC/HKMA feed item with no digital-asset relevance filter, and the live CCR trigger
was due to fire against this exact queue within roughly a day. Built and shipped
`pipeline/watcher/relevance.py` (deterministic keyword classification, jurisdiction-configurable via
`config/jurisdiction.json`'s new `relevance_keywords`, fail-open on missing config) and wired it
into `pipeline/watcher/run.py` and `derive_queue`. Ran it live against the real ledger: `data/
queue.json` went from 988 to 69 genuinely relevant items. Full reasoning and the fixture-test
correction this required in `tests/test_run_integration.py` are logged in IMPROVEMENT_BACKLOG.md.

Also fixed a real bug in `pipeline/ci/path_allowlist.py`/`validate_content.py` (found by running
the actual deterministic gates against the newly-created `content/pillar_states/` directory): a
wholly-untracked new directory collapses to one bare `git status --porcelain` line by default,
which broke `validate_content`'s per-file schema mapping silently (it reported "no schema-governed
files changed" instead of validating anything). Fixed at the root — `get_uncommitted_changed_paths`
now passes `--untracked-files=all`. Full detail in IMPROVEMENT_BACKLOG.md.

Built `pipeline/ci/seed_backfill.py` (reuses the watcher's own `NormalizedItem -> diff_new_items ->
upsert_items -> classify_relevance` path) and used it to add the 5 headline events as `queued`
ledger items, ready for the analyst+verifier pipeline.

Test suite: 148 passing (up from 137 at the last Phase 2 checkpoint).

**Operational note:** all of the above (7 pillar states, the relevance-filter fix, the 5 seeded
headline events) lives on the feature branch (`claude/hk-radar-phase-1-mzlnxx`), not yet merged to
`main`. The CCR analyst/verifier trigger operates against `main` (`git pull origin main`), so it
would have fired tomorrow (2026-07-10T03:31 UTC) against the *old*, unfiltered, pre-fix state.
Disabled the trigger (`trig_01Bk3Lz2FKf3pWRMFkqBcdDE`) as a precaution until this branch merges --
re-enable once merged, then it will correctly see the fixed pipeline and the (much smaller,
relevance-filtered) real queue.

### 2026-07-09 — First real analyst+verifier run: 5 headline cards drafted, verified, published

Ran the full analyst+verifier+gate pipeline for real for the first time (previously only
deterministically tested against fixtures). One `hk-radar-analyst` sub-agent drafted cards for all
5 of the build spec's headline events (VATP dual-licence regime, first Stablecoins Ordinance
licences, dealing/custodian consultation conclusions, Policy Statement 2.0, an SFC enforcement
action against Saxo Capital Markets HK Limited), plus `trajectory.json`'s first entry and 6
glossary terms. 5 separate, worktree-isolated `hk-radar-verifier` sub-agents (one per card, each
given only the drafted card file, never the analyst's reasoning) then adversarially re-checked
every citation. **All 5 verifier passes found and corrected at least one real problem** in the
analyst's draft — see IMPROVEMENT_BACKLOG.md for the full list (a fabricated/spliced quote, a wrong
statutory-basis description, unsupported date/comparative claims, and several claims needing
better-sourced citations).

Running the real deterministic gate afterward caught two further problems the LLM verifiers had
missed — a smart-quote/straight-quote mismatch and a PDF-extraction whitespace artifact — both real
bugs in `pipeline/verify/authenticity.py`, now fixed with regression tests (151 tests passing, up
from 148). Also found and worked around a real infrastructure issue: spawning 5 worktree-isolated
verifier sub-agents concurrently in one batch left 4 of the 5 worktrees pinned to a stale commit
(hours old, predating the card files entirely) rather than the current branch tip — full detail and
the recovery approach in IMPROVEMENT_BACKLOG.md.

End state: all 5 cards `status: "verified"`, all 5 ledger items `published`, gates re-confirmed
passing before each commit. Committed in three parts (analyst draft, the authenticity-oracle fix,
verifier corrections + promotion), all pushed to the feature branch.

### 2026-07-09 — Phase 3 complete: seed backfill checkpoint

All five remaining Phase 3 deliverables landed today: 5 verified headline cards (see above), 4
real-source-verified `trajectory.json` entries, glossary v1 (11 terms total), the Document Library
(`content/document_library.json`, `pipeline/watcher/classify.py` -- deterministic pillar/type
tagging wired into every watcher run, 69 real relevant documents, all correctly pillar-tagged after
iterating the keyword lists against live output), and the Start Here orientation page
(`content/start_here.json`, ~780 words).

Closing verification for this checkpoint, run fresh just now rather than trusted from earlier in
the session: full pytest suite (166 passing), a full schema-validation sweep of every file currently
under `content/` and `data/` against its schema (28 files, 0 failures -- not just the "changed files
since last commit" check the CI gate itself uses), a fresh live re-run of the citation-authenticity
gate against all 5 published cards (all citations still authentic, all still `status: "verified"`),
and a clean `git status` (nothing uncommitted). `pipeline.ci.path_allowlist` and
`pipeline.ci.validate_content` both report nothing to check against a clean tree, as expected.

Two real bugs were found and fixed along the way by directly inspecting live output rather than
trusting a first green result: the path-allowlist/validate_content bare-directory bug, the
smart-quote/PDF-artifact authenticity-oracle bugs, the digital-asset relevance-filter gap (988 ->
69 items), the `git diff --quiet` untracked-file blind spot in `watch.yml`'s planned commit-scope
check, and a test-hygiene bug where two tests calling the watcher's `main()` without the new
`--document-library` flag briefly overwrote the real document library during a routine `pytest`
run. Full detail on every one of these is in IMPROVEMENT_BACKLOG.md, dated 2026-07-09.

P2's live-LLM-run gap is also now closed: the analyst+verifier+gate mechanism ran for real (via the
CCR runbook procedure, manually invoked rather than trigger-fired) on all 5 headline cards. The CCR
scheduled trigger itself has still never fired (disabled pending this branch's merge to `main`) --
that remains the one genuinely unproven piece of live automation, tracked separately from Phase 2/3
content completeness.

**Standing operational note, unresolved:** everything above lives on the feature branch
(`claude/hk-radar-phase-1-mzlnxx`), not yet merged to `main`. The CCR trigger stays disabled until
that merge happens; re-enabling it is a manual follow-up once the owner merges this branch.

### 2026-07-09 — Phase 4 (Frontend) build: static site generator, all 7 pages

Built `pipeline/site/` -- a plain-Python, Jinja2-templated static site generator (no JS framework,
no npm toolchain), rendering all 7 site structure pages (Start Here, State Board, Trajectory Board,
Timeline, Document Library, Glossary, Method & Audit) from `content/*.json` and `data/*.json`. New
`.github/workflows/deploy.yml` builds and publishes via GitHub's official Actions-based Pages
deployment.

Real problems found and fixed by actually running and looking at the output, not by trusting the
plan:
- **Directory collision:** the originally planned `docs/` output target already holds
  `docs/analyst-runbook.md`. Switched to GitHub's Actions-based Pages deployment (`_site/`,
  gitignored, never committed) instead of committing rendered HTML to a branch -- also sidesteps
  the `GITHUB_TOKEN`-doesn't-trigger-`on:push` question entirely.
- **Accessibility:** a real WCAG contrast-ratio test (not eyeballed) found the design spec's fixed
  amber (#B7791F) only reaches ~3.48:1 on the paper background -- below the 4.5:1 normal-text
  threshold. Fixed by using amber only as the unverified-badge border/background accent (where the
  weaker 3:1 non-text threshold applies) and rendering the label text in ink instead.
- **Misleading data:** the Method page's ledger status table originally counted all 988 observed
  items rather than the 69 relevant ones (919 permanently-irrelevant items never leave "queued"
  status) -- corrected to show both figures with an explanation.
- **Serious: internal model identifier leaking publicly.** Caught by looking at an actual rendered
  screenshot during browser verification: every card and the Start Here page displayed the literal
  internal model-version identifier in their `model` field (restricted to this session's own chat
  replies, never repository artifacts, per this session's own operating constraints). Fixed across
  all 6 affected content files (`"Claude (Anthropic)"` instead) and updated `analyst_prompt.md` so
  future analyst runs don't reintroduce it.

Verification, in order: 179 tests passing (13 new for the site generator, including an automated
grep for internal-identifier patterns with a positive-control test proving the check actually
catches a planted identifier, and real WCAG contrast-ratio checks -- not just disclaimer-presence
assertions); a real local browser check via Playwright against the actual generated `_site/` output
-- all 7 pages screenshotted (desktop and a 375px mobile view), the client-side document-library
search verified interactively (69 -> 8 rows filtering on "stablecoin"), and the Trajectory Board's
flap-animation attribute confirmed applied on load.

**Still open:** GitHub Pages hosting is not yet enabled for this repository (confirmed:
`https://0xfanbase.github.io/DA-Radar/` returns 404) -- needs a human with repo admin access to set
Settings -> Pages -> Source: "GitHub Actions", not something available via this session's tools.
`deploy.yml` also cannot be live-dispatched for a real end-to-end run until this branch merges to
`main` (GitHub's `workflow_dispatch` API only recognizes a workflow once it exists on the default
branch -- the same situation `watch.yml` was in before its own Phase 1 merge).

*(Further entries appended as Phase 4+ work lands.)*

## PM checkpoints (Fable)

### 2026-07-09 — Kickoff review: approved with directives

Fable reviewed the scope, sequencing, and engineering plan before implementation began.
**Verdict: approved for kickoff**, with directives treated as blocking before the acceptance
criteria can be considered met:

1. Byte-level idempotency: canonical JSON serialization, no per-run-mutated ledger fields
   (dropped `last_seen`), ETag cache moved out of version control entirely.
2. Jurisdiction portability enforced at the schema layer too, not just in pipeline code —
   Freedonia test fixture must validate against the same schemas as HK.
3. Ledger status lifecycle fixed now as a documented enum (`queued → drafted → verified →
   published`, plus `corrected`/`suppressed`/`error`), even though Phase 1 only writes `queued`.
4. Two anonymity findings logged (LICENSE copyright line, initial-commit author) — not fixed,
   since both predate this build and touching either would be a separate, deliberate human call.
5. Per-feed failure isolation, tested with a fixture — one bad feed must never abort a run.
6. `requests` calls always pass an explicit timeout; static jurisdiction-agnosticism scan is a
   pytest test (not a standalone script), case-insensitive, with domain-fragment bans; no-network
   enforced structurally via an autouse fixture; XML parsing hardened with `defusedxml`; feed text
   sanitized (control-char strip + length cap) before entering the ledger.

All directives incorporated into the design — see IMPROVEMENT_BACKLOG.md's "Decisions from Fable
(PM) kickoff review" section for the specifics of each.

### 2026-07-09 — Checkpoint 2: Phase 1 signed off

Two independent Fable review passes (one continuing the kickoff agent with full context, one a
fresh instance given a self-contained report — both a genuine second opinion) each independently
re-executed the evidence rather than trusting the report: re-ran the full pytest suite, read the
actual test bodies for the tests named at kickoff, ran the live watcher themselves and diffed
sha256 of the output files, grepped `pipeline/` for banned jurisdiction strings, and verified the
pinned GitHub Actions commit SHAs against the real upstream repos via `git ls-remote`. Both also
hit the GitHub API directly and confirmed `list_workflows` returns zero registered workflows for
this repo, corroborating that the missing green Actions run is a genuine "not on the default
branch yet" platform constraint, not a shortcut.

**Verdict from both: Phase 1 signed off, complete.**

Directives logged for Phase 2 kickoff (non-blocking for Phase 1, carried into IMPROVEMENT_BACKLOG.md):
1. Once this branch merges to `main`, trigger one real `workflow_dispatch` run of `watch.yml`
   before trusting the daily cron — Phase 1 doesn't require it, but the workflow is not yet
   *operationally* proven on GitHub's actual infrastructure.
2. Resolve the two logged anonymity flags (LICENSE "Big Fan" copyright line, non-bot initial
   commit) with the human owner before public launch — correctly left as owner decisions.
3. Phase 2 must implement the CI path-allowlist gate (currently only documented in CLAUDE.md)
   before any AI analyst/verifier job is wired in — first item on that phase's list, not an
   afterthought.

### 2026-07-09 — PR #1 merged; watch.yml verified live on GitHub Actions

`claude/hk-radar-phase-1-mzlnxx` merged into `main` (merge commit `02d5a40`). Branch restarted from
the new `main` per standard post-merge handling. Immediately closed out directive 1 above:

- `list_workflows` now shows `Watcher` registered (it wasn't, pre-merge).
- Triggered a real `workflow_dispatch` run on `main` (run id `28991034262`).
- **Result: `completed` / `success`, 21 seconds end-to-end.** All steps green: checkout, Python
  3.12 setup, `pip install -e .`, run watcher, check-for-changes. Watcher log shows all 9 feeds
  `OK ... new=0` (zero new items in the ~20 minutes since the last manual live run — the
  idempotency guarantee holding in production, not just locally). "Commit ledger/queue updates"
  and "Note next step" both show `conclusion: skipped`, exactly as designed, since
  `steps.changes.outputs.changed` was `false`. No new commit landed on `main`, as expected.
- Minor non-blocking note: the job log shows a GitHub-side deprecation warning that
  `actions/checkout`/`actions/setup-python` target Node 20 internally and are being forced onto
  Node 24 by the runner. This is GitHub's own forward-compat shim, not a failure — no action
  needed now, but worth bumping the pinned SHAs next time either action cuts a Node-24-native
  release.

**Phase 1 is now both criterion-verified locally and operationally proven on real GitHub Actions
infrastructure.** Proceeding to Phase 2 (analyst + verifier + CI path-allowlist gate) per the
user's instruction to continue building.

### 2026-07-09 — Kickoff review: approved, split and sequencing adjusted

Fable reviewed Phase 2 scope before implementation began. Approved, with the analyst/deterministic
split sharpened: the deterministic module is a per-citation authenticity oracle ONLY (never judges
which sentence a citation supports); the gate is the final, non-bypassable check before commit,
never trusting a card's self-reported status. Directives: build the path-allowlist gate first,
standalone, before any prompt-writing; enforce the AI jobs' tool restriction at two independent
layers (their own `claude_args` plus a separate deterministic post-hoc check); the verifier must be
a structurally separate job, fresh context, not a continued conversation; log the citation-vs-
sentence interface decision explicitly. Full directive text and all resulting decisions are in
IMPROVEMENT_BACKLOG.md's "Phase 2 kickoff and decisions" section.

### 2026-07-09 — Checkpoint A: deterministic scaffolding verified

Fable independently re-ran the full suite, read `path_allowlist.py`/`gate.py`/`authenticity.py`/
`docfetch.py`/`ledger.py` directly, and confirmed every named test does what was claimed. Caught
one factual error in the report (a claim that `claude-code-action@v1` has no `settings` input —
false; the input exists, though the path-anchoring problem that ruled out a settings-*file*
approach was and is real) — corrected in IMPROVEMENT_BACKLOG.md rather than left standing.
Approved proceeding to `analyze.yml` + prompts.

### 2026-07-09 — Checkpoint B: signed off, with one gap closed

Fable independently re-ran the suite, read `analyze.yml`/`watch.yml` and both prompt files in
full, and verified the `repository_dispatch`-exemption claim against GitHub's own docs. Found one
real, non-blocking gap: `promote_verified.py` promotes a ledger item to `"published"` regardless of
the card file's own (possibly gate-downgraded) `status` — a deliberate design, not a bug, but one
that needed (a) proactive disclosure in the checkpoint report itself, not something found by
reading a docstring, and (b) an explicit integration test locking in the exact end state, since a
future contributor would very plausibly "fix" it as a bug otherwise. Both addressed: see the
prominent callout in the Phase 2 build-complete log entry above, and
`tests/test_analyze_pipeline_integration.py`. **Verdict: Phase 2 signed off as
designed-and-deterministically-verified**, with the live-LLM-behavior and live-YAML-execution gaps
named as pending the same secret-provisioning blocker as Phase 1's pre-merge gap — Fable's
directive is that the first real live run's output (both commits, the card file, both jobs'
`display_report`) comes back for review before Phase 2 is called operationally closed, mirroring
Phase 1's live `workflow_dispatch` run being the actual closing evidence, not just green tests.

### 2026-07-09 — Owner confirms: no AI secret, ever; CCR scheduled trigger stood up instead

The owner stated plainly that `CLAUDE_CODE_OAUTH_TOKEN`/`ANTHROPIC_API_KEY` will never be
provisioned as a GitHub secret. Fable PM reviewed the pivot (see IMPROVEMENT_BACKLOG.md's
"Architecture pivot" entry for the full reasoning) and required the ongoing-automation question be
put to the owner explicitly rather than defaulted — done via `AskUserQuestion`, framed as: leave
`analyze.yml` dormant (fully auditable on GitHub, portable to jurisdiction forks, but the loop
doesn't actually run unattended) vs. a Claude Code Remote (CCR) scheduled trigger (actually runs
unattended, but invisible to a GitHub-based repo audit and doesn't port to forks the way everything
else does). **The owner chose the CCR trigger.**

Built:
- `.github/workflows/analyze.yml` updated with a real credential check (`check-queue` job) so it
  skips cleanly, with a clear `::notice::`, instead of failing daily — left in the repo as a
  documented, dormant, spec-literal fallback that activates automatically if a secret is ever added.
- `docs/analyst-runbook.md`: the exact procedure a CCR-fired session follows in place of
  `analyze.yml` — worktree-isolated analyst sub-agent, a genuinely *separate* worktree-isolated
  verifier sub-agent (receives only the drafted card file, never the analyst's reasoning — the
  same fresh-context separation Phase 2's `needs: analyst` job split enforced), the same
  deterministic gates (`path_allowlist`, `validate_content`, `apply_verification_gate`) run as real
  subprocess calls, same bot commit identity, dated `PROGRESS.md` logging every run.
- A live CCR trigger, `trig_01Bk3Lz2FKf3pWRMFkqBcdDE` ("HK Radar — Analyst/Verifier daily run"),
  cron `30 3 * * *` (03:30 UTC / 11:30 HKT — ~2 hours after `watch.yml`'s 09:30 HKT run, so the
  queue is current), `create_new_session_on_fire: true` so each firing starts from a clean slate
  rather than accumulating context across days. First scheduled run: 2026-07-10T03:31 UTC.

**Compensating for the lost tool-restriction layer** (the `Agent` tool has no equivalent to
`claude_args`' `--disallowedTools`/scoped `Write`): both sub-agents run with `isolation: "worktree"`
so a hostile fetched-document prompt injection can only damage a disposable checkout, never the
real branch; only the orchestrating session ever runs `git add`/`commit`/`push`, and it stages
explicitly (never `-A`). The deterministic gate remains the definitive, non-bypassable backstop
either way — unchanged from Phase 2, since it never trusted an LLM's self-report in the first
place.

Still unverified: the first actual CCR-triggered run hasn't fired yet (scheduled for tomorrow).
Per Fable's standing directive, that first run's output — both commits, the actual card file, both
sub-agents' behavior — needs review before this mechanism is considered proven, not just deployed.
