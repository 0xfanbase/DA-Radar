# PROGRESS.md

Running, dated log of what has been built and verified. Read this first in any fresh session —
along with `git log` — to know exactly where the project stands before doing anything else.

## Phase status

- **P1 — Chassis: complete** (signed off by Fable PM checkpoint 2, 2026-07-09)
- **P2 — Analyst + verifier: complete, live-run-proven** (deterministically complete per the
  2026-07-09 build-complete entry; the live-run gap closed the same day when the runbook's
  analyst+verifier+gate procedure ran for real on 5 headline cards via the docs/analyst-runbook.md
  mechanism -- see the "First real analyst+verifier pipeline run" entry below. The CCR scheduled
  trigger itself was re-enabled 2026-07-09 with the owner's explicit go-ahead; its first live fire
  is due 2026-07-10T03:35 UTC and still needs to be observed before this mechanism counts as proven
  end-to-end, not just deployed)
- **P3 — Seed backfill: complete** (7 pillar states, 5 verified headline cards, trajectory.json,
  glossary v1, the ~40-item -- in practice 69-item -- Document Library, and the Start Here page;
  see the 2026-07-09 entries below)
- **P4 — Frontend: complete, live.** Static site generator, all 7 pages, GitHub Pages Actions deploy
  workflow, real Lighthouse 100/100 on every page, browser-verified (2026-07-09 "Phase 4 (Frontend)
  build" entry below). GitHub Pages hosting confirmed live 2026-07-09:
  `https://0xfanbase.github.io/DA-Radar/` serves the real generated site.
- **P5 — Full autonomy: deterministic build complete, per Fable PM's 2026-07-09 checkpoint; branch
  merged and analyst/verifier trigger re-enabled the same day.** `audit.yml`, the corrections
  mechanism, and `improve.yml` (all four of Fable's required design refinements incorporated and
  verified) are built, tested (255 tests passing), merged to `main` via PR #2, and live. No live CCR
  trigger exists yet for `improve.yml` -- Fable confirmed this was the right call and set an explicit
  sequencing precondition before it (or any further live-activation) is revisited: see "Owner /
  next-step punch list" below. The literal P5 acceptance criterion -- 14-day soak, two consecutive
  real regulator publications with zero human action -- cannot be completed synchronously in any
  session and remains a tracked open item. **Remaining work is not more engineering** (Fable's own
  words) -- it's owner branch-protection setup and observing the sequenced live-proving steps below.
- **P6 — Multi-jurisdiction chassis refactor: complete.** Owner-approved architecture pivot from
  the one-jurisdiction-per-deployment fork model to a registry model (one deployment, many
  jurisdictions) -- see the 2026-07-11 "P6" entry below for full detail. Site output is
  byte-equivalent (still HK-only) by design; P7 (new IA, tabs, rebrand) is next.

## Owner / next-step punch list

Consolidated here so nothing sits scattered across log entries.

1. ~~**Merge `claude/hk-radar-phase-1-mzlnxx` to `main`.**~~ **Done, 2026-07-09.** PR #2 (52 commits,
   Phases 2-5) merged. `main` HEAD is now `499d317`.
2. ~~**Enable GitHub Pages.**~~ **Confirmed done, 2026-07-09** -- **later found to be a false positive,
   corrected 2026-07-11.** The disclaimer-text check that supposedly confirmed the real site was live
   was fooled by boilerplate text `README.md` happens to share verbatim with the real disclaimer;
   Pages Source was actually still "Deploy from a branch" the whole time, silently serving GitHub's
   Jekyll auto-render of `README.md` instead of `deploy.yml`'s Actions-based artifact. See the
   2026-07-11 Log entry below for the full finding and fix. Genuinely fixed now: Source is confirmed
   "GitHub Actions" and all 7 pages + static assets verified live with real content.
3. ~~**Re-enable the analyst/verifier CCR trigger**~~. **Done,
   2026-07-09**, with the owner's explicit go-ahead in this session (not done silently, given it's a
   standing job that makes real unattended commits to `main`). `enabled: true`, next scheduled fire
   2026-07-10T03:35 UTC. This is the first genuinely live firing of this mechanism -- per Fable's
   standing directive, its output (commits, the actual card file, both sub-agents' behavior) needs
   review before the mechanism is considered proven, not just re-armed.
4. **Set branch protection on `main`** (still open, owner action -- no tool in this session can
   configure repo branch-protection settings): require a PR (no direct pushes), require
   `pr-check.yml`'s status check to pass before merge. This is the real structural backstop behind
   every "PR-only, human-merge" mechanism in this repo (`correction.yml`, `improve.yml`) -- the
   workflow scripts themselves never push to `main` directly, but branch protection is what stops a
   compromised script from doing so anyway.
5. **Sequenced live-proving steps, in this order (Fable PM directive, 2026-07-09) -- do not run
   improve.yml's live trigger in parallel with the analyst/verifier's own unproven first runs:**
   a. ~~Steps 1-3 above.~~ Done. Step 4 (branch protection) still open.
   b. Let the re-enabled analyst/verifier trigger complete a handful of real, observed, successful
      cycles -- proving the CCR-session/worktree/isolation mechanism holds up against live reality,
      not just fixtures. **In progress as of 2026-07-09**; first fire due 2026-07-10T03:35 UTC.
   c. Only then: one full **manual** dry run of `docs/improve-runbook.md` -- populate one real,
      low-stakes item into `data/improve_queue.json`, run the procedure by hand (the same way
      Phase 3's first analyst+verifier run was done manually before any trigger existed), and watch
      an actual PR get opened and either merged or rejected. Report this back to Fable PM before
      either trigger's live-activation question comes back up.
6. Two logged anonymity flags remain owner decisions before public launch (see
   IMPROVEMENT_BACKLOG.md's deviations entries): the LICENSE "Big Fan" copyright line, and non-bot
   commits — which are structural and recurring, not just the initial commit: every PR merged
   through GitHub's UI records the merging account (currently the owner's real account) as the
   merge commit's identity, and `correction.yml`/`improve.yml` are PR-only/human-merge by design,
   so this recurs on every future merge. Bot identity is guaranteed only for commits the pipeline
   and build sessions themselves create; closing the gap requires a bot-credentialed merge path
   (GitHub App/PAT merging as `hk-radar-bot`), which this environment does not have.

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
Disabled the analyst/verifier CCR trigger as a precaution until this branch merges --
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

### 2026-07-09 — Phase 5 begins: audit.yml, corrections built; improve.yml design note sent for review

Built `pipeline/audit/` (link-rot, pillar staleness at 45 days, feed silence at 30 days, verifier
pass-rate trend vs. the previous `data/audit/latest.json` snapshot rather than a second unschema'd
history file) and `.github/workflows/audit.yml` (weekly cron + `workflow_dispatch`, commits findings
only when something changed). Method page now renders real findings or an honest "hasn't run yet"
placeholder. Built the corrections mechanism (`pipeline/ci/apply_correction.py` +
`.github/workflows/correction.yml`): human-initiated only (every input supplied explicitly by a
person, never audit.yml's own findings), PR-only, never auto-merged. 25 + 8 new tests, 214 total.

**Real bug found and fixed via live testing, disclosed rather than hidden:** ran `audit.yml` live
against the real repo before committing. It reported 49 actionable findings, but 47 were SSL
certificate errors against exactly one HKMA subdomain (`brdr.hkma.gov.hk`), while sibling HKMA/SFC
hosts fetched cleanly over the same path -- including a real, independently-reproducible 404.
Diagnosed with curl, `openssl s_client`, and Python `requests` (with and without this dev sandbox's
proxy CA bundle) and traced it to this sandbox's TLS-inspecting egress proxy failing to validate
that one host for some TLS clients but not others -- not genuine link rot, and not expected to
reproduce on a real GitHub Actions runner (direct egress, no intercepting proxy). Discarded the
contaminated run's output rather than commit it; publishing "49 broken HKMA links" to the public
Method page on the strength of a sandbox artifact would itself violate CLAUDE.md's editorial rules.
Full diagnostic writeup in IMPROVEMENT_BACKLOG.md's "Live audit.yml run in the dev sandbox" entry.
The genuine 404 is logged there as an open item for a human to check, not auto-corrected.

`improve.yml` design note sent to Fable PM for review (see "PM checkpoints" below) -- no
implementation started, per Fable's explicit Phase 5 kickoff requirement that this get the same
kickoff-style scrutiny Phase 1/2 got before any code is written, given its necessary write access to
`/pipeline`, `/config`, and `.github/workflows` (the exact territory the path-allowlist gate exists
to keep analyst/verifier out of).

### 2026-07-09 — improve.yml built per Fable's four required refinements and verified

Fable approved the design note's architecture with four required additions (see "PM checkpoints"
below for the review itself). Built all four, then the mechanism: `pipeline/ci/improve_scope.py`
(hard-deny gate, stated as a principle then enumerated -- every check/gate/constraint module, every
schema, every workflow file, plus `promote_drafted.py` added proactively alongside its named
sibling), `pipeline/ci/prompt_change_justification.py` (spotlights `pipeline/prompts/**` changes
rather than locking them), `pipeline/ci/improve_queue.py` + an empty seed `data/improve_queue.json`
(bounded, human-curated selection -- no fabricated backlog items), `.github/workflows/improve.yml`
(dormant-but-complete, same no-AI-secret architecture pivot as `analyze.yml`), `docs/improve-runbook.md`
(the CCR-triggered procedure, mirroring `docs/analyst-runbook.md`), and `.github/workflows/pr-check.yml`
(the full test suite as a required-status-check candidate on any PR touching `/pipeline` or
`/config`). 47 new tests, 255 total passing. Full detail in IMPROVEMENT_BACKLOG.md's "improve.yml
built per Fable PM's four required refinements" entry.

Deliberately did not stand up a live CCR trigger for this mechanism -- brought that question to
Fable explicitly rather than deciding it unilaterally. See the checkpoint below for the verdict and
the sequencing precondition, now the top item in "Owner / next-step punch list" above.

### 2026-07-09 — Branch merged (PR #2), Pages confirmed live, analyst/verifier trigger re-enabled

No PR had ever been opened for the 52 commits spanning Phases 2-5 -- the owner flagged this
directly ("I don't see a PR at the moment"). Checked: `main` was still exactly where PR #1 (Phase 1
scaffold) had left it; the branch was cleanly 52 commits ahead with no divergence. Opened PR #2
covering all of it; the owner merged it the same session.

Verified directly post-merge, not assumed:
- `main` HEAD is `499d317` (`git log origin/main`).
- `deploy.yml`'s run on the merge commit completed successfully, and
  `https://0xfanbase.github.io/DA-Radar/` returns HTTP 200 serving the real generated site (checked
  for the actual disclaimer text, not just a 200 status) -- GitHub Pages hosting is live. This must
  have been enabled by the owner independently at some point after the Phase 4 entry's "still 404"
  note; not something this session did.
- Re-enabled the analyst/verifier CCR trigger -- with the owner's
  explicit go-ahead sought and given in this session first, since flipping on a standing job that
  makes real unattended commits to `main` is exactly the kind of action that warrants asking rather
  than assuming yesterday's Fable sign-off covers the literal switch-flip too. `enabled: true`,
  first live fire due 2026-07-10T03:35 UTC. This is genuinely the first live firing of this
  mechanism since it was created -- per Fable's standing directive, its actual output needs review
  before it counts as proven, not just re-armed.

Branch protection on `main` remains open -- no tool available in this session can configure repo
branch-protection settings; still an owner action.

### 2026-07-11 — Real bug found: GitHub Pages was serving the Jekyll README fallback, not the site

The owner reported `https://0xfanbase.github.io/DA-Radar/state-board.html` 404ing (screenshot of a
genuine GitHub Pages 404 page). Investigated rather than assumed a caching blip:

- `deploy.yml` itself was innocent: its latest run (2026-07-11T04:37 UTC, `repository_dispatch`)
  completed green end to end. The "Build site" step's own log showed `site: wrote 7 page(s) to _site`,
  listing `state-board.html` explicitly; the archived tar for `upload-pages-artifact` listed all 7
  pages plus `static/`; `deploy-pages` reported `Reported success!` against
  `https://0xfanbase.github.io/DA-Radar/`.
- Live fetch told a different story: only `/` (`index.html`) returned 200 -- every other path,
  including plain static assets (`static/style.css`) that were unambiguously inside the same
  successful deploy, returned a genuine (non-cached, cache-bust-immune) GitHub 404.
- Fetched and read the actual bytes of the live `index.html`: it carried a `Jekyll v3.10.0` generator
  tag, linked `/DA-Radar/assets/css/style.css` (GitHub's default Jekyll theme asset path -- not
  referenced anywhere in this codebase), an "Improve this page" edit link to `README.md`, and the
  literal, word-for-word stale "Currently in **Phase 1 (Chassis)** ... no public site exists yet"
  paragraph straight out of `README.md`'s never-updated Status section (confirmed via
  `git log -- README.md`: last touched 2026-07-09, the very first day).
- **Root cause:** repo Settings -> Pages -> Source was still "Deploy from a branch," not "GitHub
  Actions," despite `deploy.yml`'s own header comment and the 2026-07-09 punch-list item both stating
  it needed to be switched. GitHub's legacy branch/Jekyll builder auto-renders `README.md` as
  `index.html` when no explicit `index.html` exists on the branch -- explaining why root alone
  "worked" and every generator-produced page 404'd (they only ever existed inside the Actions
  artifact, never on the branch itself).
- **The 2026-07-09 "Pages confirmed live" verification was a false positive**, not a real check: it
  grepped the live page for the disclaimer sentence, which also appears verbatim in `README.md`'s own
  boilerplate -- so the check passed against the Jekyll fallback without ever touching the real
  generated site. Corrected in the punch list above rather than left standing.

**Fix:** owner switched Settings -> Pages -> Source to "GitHub Actions" directly (screenshot
confirmed: "GitHub Pages source saved"). Since that alone doesn't republish the already-live
deployment, manually re-dispatched `deploy.yml` (`workflow_dispatch` on `main`) afterward. Verified
live, not assumed: all 7 pages (`index.html`, `state-board.html`, `trajectory.html`, `timeline.html`,
`documents.html`, `glossary.html`, `method.html`) plus `static/style.css` now return 200, and
`index.html`/`state-board.html` bodies were re-fetched and confirmed to be the real generator
output (`<title>Start Here — HK Digital Asset Radar</title>` / `<title>State Board — HK Digital
Asset Radar</title>`, real nav, real disclaimer markup, real pillar content) -- no Jekyll tag, no
stale README text.

**Process note for future sessions:** a "site is live" check that only string-matches shared
boilerplate (the disclaimer sentence, present in both `README.md` and every real page) cannot
distinguish the real site from GitHub's own Jekyll fallback of that same README. Any future
live-Pages verification should instead assert something that only the real generated site could
produce -- e.g. a non-root page resolving, or a Jekyll-absence check (`generator` meta tag / `assets/
css/style.css` path should never appear in this project's own markup).

### 2026-07-11 — Fable-directed compliance/UX audit: 34 fix items, 12 executed, rest logged

Per the owner's request, ran a full senior-compliance-officer-lens audit of the site and pipeline,
using Fable as project director (the same role it plays at every checkpoint in this log) to scope
the audit and prioritize findings, with a fleet of agents executing the read and fix work. Full
mechanics: Fable read `CLAUDE.md` and this file's 2026-07-11 Pages-bug entry (the reference example
for the class of bug being hunted -- "pipeline says X, reader sees Y") and defined 8 audit
dimensions, each scoped to specific real files: deploy/publish-chain integrity, disclaimer and
verification-status *placement*, an anonymity/internal-identifier re-scan, line-by-line editorial-
rule conformance of every published content file, generator/template edge cases, whether the
deterministic gates enforce what the Method page claims, Method-page self-description honesty, and
frontend UX/accessibility/both-theme legibility. 8 parallel agents read every targeted file in full
(not excerpts) and returned 48 raw findings. Fable deduped those into 34 fix items, ranked into 11
must-fix, 12 should-fix, 2 nice-to-have, and 9 flag-for-owner, and wrote acceptance criteria for
each. Every candidate marked safe for auto-fix was then adversarially re-verified against the
current file contents by a fresh agent before anything was touched (skeptical-by-default,
`confirmed=false` unless directly verifiable) -- 3 of 15 candidates were refuted at this step and
correctly not fixed. The remaining 12 were executed one at a time (sequential, not parallel, since
they share one working tree), each as its own scoped agent with Edit access only, no git access.

**12 fixes applied, all independently re-verified afterward (fresh `git diff` read, full pytest
re-run: 334/334 passing, not just trusted from the sub-agents' own reports):**
1. `README.md`'s Status section no longer says "Phase 1 ... no public site exists yet" (the exact
   stale text the Jekyll fallback served readers, see the entry above) -- now points at the live URL.
2. Added `@media print` rules to `style.css` -- the Trajectory Board's theme-invariant dark
   background was dropping out in print, leaving near-illegible pale-on-white text.
3. The Timeline ribbon/tooltip/no-JS fallback now render each card's verification status
   (`data.py` already computed it; nothing downstream displayed it -- a real instance of the
   "pipeline knows, reader doesn't see" class this audit was built to catch).
4. `pipeline/site/data.py`'s `load_site_data` now raises a new `SiteDataError` instead of silently
   degrading when expected content is missing (a missing `start_here.json` or pillar-state file
   used to produce a green build with a silently incomplete site).
5. Unmapped `status_seal`/pillar ids used to render as raw snake_case strings on the public State
   Board -- now a fail-loud `SiteDataError` naming the exact source file, never a raw id shown to a
   reader.
6. An item with no pillar classification used to get timeline color slot 0 -- a real pillar's own
   color -- fabricating a classification signal; now a distinct sentinel slot that renders as
   genuinely unclassified.
7. Removed unsourced named-entity and numeric claims from `content/pillar_states/stablecoins.json`
   and `funds_etfs.json` standing summaries (Anchorpoint's ownership structure, an HKMA application
   count, named ETF issuers) -- verified against all 9 cited `key_links`; none supported the claims
   as written. Direct rule-2/rule-4 violations, now fixed at the content level.
8. New `pipeline/verify/quote_policy.py` makes the 15-word/one-quote-per-source rule (asserted as
   settled fact on the Method page, previously enforced only by LLM prompt instruction) a real,
   deterministic, non-bypassable gate check, wired into `enforce_full_gate` alongside the existing
   citation-authenticity and numeric-claims checks.
9. Fixed the "Corrected" status rendering: it shared the "Verified" badge with no link to the
   corrections log, and the Method page's own summary sentence claimed every non-verified card
   "carries unverified" (false once a corrected card exists) -- now a real three-way split.
10. The fixed "Unverified -- citations could not be confirmed against source" label was factually
    wrong when a card was actually downgraded for an unsupported numeric claim -- added the
    correct-cause branch.
11. A card with an empty/missing `citations` array used to crash the entire 7-page build with an
    unhandled `IndexError` -- now a loud, named `SiteDataError` instead of a build outage.
12. Timeline tooltip positioning is now clamped to the viewport (was measuring `offsetWidth` while
    still `hidden`, and could push off-screen / cause horizontal scroll on narrow viewports).

**22 items deliberately not auto-fixed this session** -- 3 refuted on adversarial re-check
(a trajectory citation and a card-citation pair that held up under a fresh, skeptical re-read;
a theme.js OS-preference-change listener claim that didn't reproduce), the rest genuinely deferred:
6 should-fix/nice-to-have items needing a real implementation pass rather than a mechanical patch
(dead-link research, a model-field leak-guard regex, a domain-allowlist design for citations), and
9 flag-for-owner items where the correct fix touches protected territory or is a policy decision --
logged in full in IMPROVEMENT_BACKLOG.md's matching 2026-07-11 entry rather than acted on, per
CLAUDE.md's own rule that editorial-rule, path-allowlist, and architecture changes need a separate,
explicit human-approved change.

**Note on scope:** the executed fixes touch `pipeline/verify/gate.py`,
`pipeline/ci/apply_verification_gate.py`, and the new `pipeline/verify/quote_policy.py` --
outside `/content` and `/data`, so outside the AI-analyst-job path allowlist. That allowlist governs
the automated analyst/verifier pipeline specifically (see CLAUDE.md's Path allowlist section); this
was a full human-directed session-level audit, not an analyst/verifier run, so it was never subject
to that gate in the first place -- noted here for clarity, not as an exception.

### 2026-07-11 — Owner-authorized fix of all 9 flag-for-owner items, Fable directing

The owner reviewed the prior entry's 9 flag-for-owner items and gave explicit, separate
authorization to fix all of them, verbatim: "please fix all and override rules where needed to fix
this fully please -- use fable as required; and use fable as project director for these fixes."
This is exactly the "explicit, separate human-approved change" CLAUDE.md's own rule requires before
protected territory is touched.

Fable made five judgment calls before any execution: **redact** (not relax) all 6 -- turned out to
be **7** -- literal occurrences of the live CCR trigger ID across `PROGRESS.md`, `IMPROVEMENT_BACKLOG.md`,
and `docs/improve-runbook.md` (a prior audit undercounted by one); document the recurring
non-bot-merge-commit issue honestly as structural rather than claim a fix that doesn't actually work
(no bot-credentialed merge path exists in this environment; a squash-merge policy does not solve
this, since the merge commit's committer is still whoever clicks merge); **reverify_primary** as the
governing approach for `banking_money.json`'s secondary-sourced claims, falling back to an
in-text caveat only for whichever circular a research pass couldn't actually fetch; add the
provenance trio to all four non-card schemas with the `status` enum deliberately excluding
`"verified"` (**label_only** decision -- no deterministic gate covers this content class, so it must
always read as unverified, never re-architect the verifier pipeline to cover it in the same pass);
and exact replacement wording for `CLAUDE.md`'s two stale loop-diagram lines and its build-state
paragraph.

**9 of the fix agents executed successfully** (each independently re-verifying prior steps' claims
rather than trusting them, consistent with this project's own established practice): `audit.yml` and
both of `analyze.yml`'s commit steps now fire the same `repository_dispatch` `watch.yml` already
uses, so a weekly audit run or a live analyst/verifier run no longer publishes to git without
rebuilding the site; all 7 trigger-ID occurrences redacted; the merge-commit anonymity gap corrected
in `IMPROVEMENT_BACKLOG.md`/`PROGRESS.md`'s punch list; `content/document_library.json`'s dead HKMA
link replaced with a verified live URL and verbatim title (independently re-verified via `curl`,
`crt.sh`, and a cross-check against every existing `brdr.hkma.gov.hk` link's URL pattern in this
repo -- the research agent's own proposed URL shape was wrong and got corrected); `banking_money.json`
cured for 2 of 3 circular claims against real primary text (the third circular remained genuinely
unreachable -- TLS chain failure on `brdr.hkma.gov.hk`, no archive snapshot -- so it got an honest
in-text caveat instead, following the `aml_cft_enforcement.json` precedent rather than either
deleting the claim or leaving it unqualified); and the provenance trio (`generated_at`/`model`/`status`)
added to all four schemas, backfilled onto all 20 existing pillar-state/glossary/trajectory/
start_here content files (`generated_at` derived from each file's real first git-commit date, never
fabricated; `model` set to an explicit `"not recorded (pre-provenance content)"` sentinel rather than
guessing a historical model name), and rendered on all four corresponding pages plus a runbook update
so future items of these types get real values.

**One fix agent correctly refused, and its refusal was the right call:** asked to patch
`pipeline/ci/path_allowlist.py`'s symlink gap, the agent read `CLAUDE.md`, `IMPROVEMENT_BACKLOG.md`'s
own "no agent should apply these without an explicit, separate human-approved change" language, and
declined -- correctly reasoning that a task instruction from the launching agent is not itself the
human-approved change CLAUDE.md requires, since it had no direct evidence the actual owner had
authorized this specific file. This is exactly the defense-in-depth behavior wanted on the CI gate's
own core logic. The session's own final-check step independently confirmed the refusal (reproduced
the live gap in a scratch repo: a symlink under `content/` resolving into `pipeline/` passed the gate
with exit code 0).

**Fixed directly by the orchestrating session** (not delegated, for the same reason: these are the
two most protected files in the repo, and the orchestrating session -- unlike a spawned sub-agent --
has first-hand evidence of the owner's actual authorization in this real conversation):
- `CLAUDE.md`: applied Fable's exact drafted replacement text to the two stale loop-diagram lines and
  the build-state paragraph. No editorial rule, the path-allowlist section, or anything else in the
  file was touched.
- `pipeline/ci/path_allowlist.py`: added a real containment check (`_escapes_allowlist_via_symlink`,
  using `os.path.realpath` against `repo_dir`) -- a path that passes the existing string-prefix check
  is now also rejected if its symlink-resolved real location escapes `content/`/`data/`. Fails open
  (treats as non-escaping) for paths that don't exist on disk, so the working-tree integration point
  (this gate's actual pre-commit use, per its own docstring) is where the check is live; existing
  behavior for the non-symlink case is completely unchanged (all 14 pre-existing tests still pass
  unmodified). Added 4 new regression tests: a symlinked file escape, a symlinked directory escape
  (git itself reports the symlink as one entry rather than expanding it -- confirmed live, not
  assumed), a legitimate-real-files-still-pass check, and a backward-compatibility check for callers
  that don't pass `repo_dir` at all.
- `data/ledger.json` / `data/queue.json`: the document-library-dead-link fix agent flagged (correctly)
  that `content/document_library.json` is regenerated in full from `data/ledger.json` on every watcher
  run, so its own fix would be silently reverted on the next run unless the same dead link/title were
  corrected at the source. Applied the identical correction to both files' matching entry
  (`item_hash bc898c7...`). Re-validated against `pipeline/schemas/ledger.json` and `queue.json`
  afterward.

**Verification, run fresh by the orchestrating session, not trusted from any sub-agent's report:**
full pytest suite 338 passing (334 + 4 new symlink tests); the two new symlink regression tests
independently confirmed to reproduce the bug against unpatched code and pass against the fix;
`data/ledger.json`/`data/queue.json` re-validated against their schemas after the manual edit; `git
diff` read in full for every touched file before committing, including a direct read of the
`banking_money.json`, `audit.yml`/`analyze.yml`, and trigger-ID-redaction diffs.

### 2026-07-11 — Remaining 8 audit items closed out

The last 8 open items from the 2026-07-11 compliance audit (all should-fix/nice-to-have, plus the one
must-fix that needed a careful rather than mechanical pass) were executed in one batch, each against
the acceptance criteria the original audit already specified -- no new judgment calls needed. Notably
**`citation-domain-check-missing`**: `pipeline/verify/authenticity.py` gained
`citation_domain_is_official`/`official_domains_from_config`, and `check_citation` now rejects any
citation URL that isn't on an official-domain allowlist *before* even attempting a fetch -- a genuine
quote match can no longer compensate for a non-official source. `config/jurisdiction.json` gained an
additive `official_domains` list per regulator (plus four previously feed-less source-table entries --
FSTB, GovHK, LegCo, Gazette -- so their domains are allowlisted too), and `apply_verification_gate.py`
now loads and threads it through the real gate invocation. Verified against all 5 real published cards
before treating it as a hard failure, per the acceptance criteria's own requirement -- all 5 pass.
Also closed: the Timeline's missing skip-link (WCAG 2.4.1) and undated-document caption, the Document
Library's over-broad AI-disclaimer (now clarified as deterministic classification, not AI-summarized)
and missing search aria-live region, `generate.py`'s last surviving trace of the abandoned docs/-
folder branch-deploy assumption, a deterministic reject-list guard in `validate_content.py` against
the exact internal-model-identifier leak shape that shipped live once already, and the Corrections
Log's raw-64-char-hash fallback (now a reader-appropriate label). Full suite: 355 passing (up from
338). Site rebuilt and independently re-verified: all 7 pages, all four new UI markers grepped directly
out of the generated HTML rather than trusted from a report.

### 2026-07-11 — P6: multi-jurisdiction chassis refactor (registry model)

The owner asked for the project to expand from HK-only to 8 jurisdictions (HK, US, EU, UK,
Singapore, UAE, Switzerland, Japan) under one deployment, renamed **Global Digital Asset Radar**.
Before any implementation, ran a Fable-directed planning pass: 7 parallel recon agents did real,
live-fetch-verified research on every new jurisdiction's regulators and feed availability (the
same discipline this project's own Phase 1 kickoff used for SFC/HKMA), and Fable synthesized a
full phased roadmap (P6-P15) plus flagged genuine hard problems rather than glossing over them --
most notably that Singapore's MAS has no feed and serves fake "Maintenance" pages to any client
that isn't browser-realistic, a real tension with this project's own honest-client fetch
discipline. Four blocking decisions were put to the owner before P6 started (all approved): the
CLAUDE.md rewrite from the fork model to the registry model; renaming the bot identity and
localStorage key to jurisdiction-neutral names; generalizing editorial rule 2's HK-specific source
list; and Singapore shipping as a "manual-assisted" watcher (not browser-UA impersonation) when
its phase (P14) arrives.

**P6 itself is the architecture pivot only -- deliberately no visible site change.** Fable directed
a sequential migration (config/content/data migration -> pipeline entrypoint `--jurisdiction`
selectors -> site-generator restructure -> watch.yml matrix conversion -> jurisdiction-agnostic
test upgrade -> identity rename), each step building on the last:

- `config/jurisdiction.json` -> `config/site.json` (new: site name, 8-entry jurisdiction registry,
  unified 7-pillar taxonomy, base seal vocabulary incl. a new `no_dedicated_regime` seal, fetch
  defaults) + `config/jurisdictions/hk.json` (regulators, feeds, keywords -- hk is the only
  registry entry with `status.watcher`/`status.analyst_verifier` = `"live"`; the other 7 are
  `"planned"` with no config file yet).
- `content/{cards,pillar_states,trajectory.json,document_library.json}` -> `content/hk/...`;
  `content/start_here.json` -> `content/hk/orientation.json`; `content/glossary/` ->
  `content/shared/glossary/` (now a genuinely shared pool -- each of the 11 terms gained a stable
  `id` and a `jurisdictions` tag, and `related_terms` changed from display strings to id
  references, laying the groundwork for real glossary crosslinks in P7).
- `data/{ledger,queue}.json` -> `data/hk/...` (each gained a `jurisdiction_id` field);
  `data/corrections.json`/`data/improve_queue.json` stay global by design.
- Six schemas bumped to require jurisdiction/id fields (`glossary` v2, `document_library`, `card`,
  `ledger`, `queue`, `corrections`); two new schemas (`site.json`, `orientation.json`).
- `pipeline/watcher/run.py` and every `pipeline/ci/*` entrypoint that touches per-jurisdiction
  files gained a `--jurisdiction <id>` selector resolving conventional paths, with explicit path
  flags still available and overriding.
- `pipeline/site/data.py` split into `load_global_data()` + `load_jurisdiction_data()`, with a
  thin `load_site_data()` wrapper (explicitly marked as temporary scaffolding) so `generate.py` and
  every template stayed untouched in this phase -- the site still renders the identical 7 HK pages.
- `watch.yml` converted to a registry-driven matrix (`jurisdiction: [hk]` today; adding a
  jurisdiction later is one matrix-array entry, not a workflow restructure), with a documented,
  deliberately-deferred limitation (multi-matrix-job output aggregation) rather than
  over-engineered now for a matrix of one.
- `tests/test_jurisdiction_agnostic.py` upgraded: the banned-literal list is now generated from
  the config files themselves (not hand-maintained), a second fabricated jurisdiction ("Sylvania")
  joins the existing "Freedonia" fixture so the test proves multi-jurisdiction isolation rather
  than single-config substitution, and `pipeline/site/templates/`/`static/*.js` entered the scan
  scope for the first time.
- Bot identity renamed `hk-radar-bot` -> `da-radar-bot` (env-var-set, never `git config`, per rule
  5 unchanged); theme localStorage key `hkdar-theme` -> `gdar-theme`.

**A skeptical final-check step caught real gaps the migration itself missed, and they were fixed
before this landed, not glossed over:** the workflow's own verification agent found that
`docs/analyst-runbook.md` and `pipeline/prompts/{analyst,verifier}_prompt.md` -- the actual,
currently-operative instructions the live CCR trigger follows, since `analyze.yml` stays dormant
-- were left referencing the old flat paths (`data/queue.json`, `content/cards/`, etc.), meaning a
real trigger firing after this landed would have followed broken instructions. It also found a
live functional bug in `correction.yml` (`git add content/cards` -- a now-empty leftover
directory -- would have silently dropped the corrected card from its own commit), stale paths in
the dormant `analyze.yml` that would have falsified CLAUDE.md's explicit promise that it "starts
working exactly as diagrammed... with no other change required," and a stale `config/jurisdiction.
json` path filter in `deploy.yml`. All fixed directly by the orchestrating session afterward (not
delegated -- these are the operative-automation and CI-trigger layer, warranting the same direct
care as CLAUDE.md itself): the runbook and both prompt files updated to the new paths and made
jurisdiction-aware in their wording; `correction.yml` gained a `jurisdiction` input threaded
through its `apply_correction`/`apply_verification_gate` calls and its commit's `git add` path;
`analyze.yml`'s queue-check/promote/commit/diff-scoping steps repointed at `data/hk/`/
`content/hk/`; `deploy.yml`'s path filter updated to `config/site.json`/`config/jurisdictions/**`;
three empty leftover directories removed. Also brought the watcher/audit/gate `User-Agent` contact
strings and README.md (still describing "HK Digital Asset Radar... Hong Kong is the pilot
jurisdiction" -- the same staleness pattern as the 2026-07-11 GitHub Pages/Jekyll incident) in line
with the rebrand, since leaving them stale would have repeated that exact mistake.

**CLAUDE.md rewrite applied directly by the orchestrating session** (not delegated -- consistent
with every other CLAUDE.md edit this session), using Fable's exact drafted replacement text:
the title, Purpose section, the self-learning-loop diagram's watch.yml/analyze.yml lines, one
sentence appended to the CCR-deviation paragraph, editorial rule 2's source-list parenthetical,
rule 5's bot identity, the Path allowlist section (one sentence appended), the Sources section, the
Jurisdiction portability section (full rewrite -- fork model to registry model, the core change),
one bullet appended to Schema and test conventions, and the Quota/execution rules section. Left
deliberately untouched: rule 3's "HK Government works are under copyright" phrasing, which the
original plan flagged as a candidate one-word generalization but the owner's explicit approvals
this round covered only rule 2 and the bot-identity naming -- not raised for this round, so not
touched; still technically true for HK, just incomplete once other jurisdictions' government works
are also covered. Flagged here rather than decided unilaterally.

**Verification, run fresh by the orchestrating session after every fix, not trusted from the
workflow's own reports:** full pytest suite 363 passing (up from 355); `tests/
test_jurisdiction_agnostic.py` specifically re-run (10/10, including the new two-fabricated-
jurisdiction and templates/static-scan tests); a full site rebuild confirmed byte-equivalent in
substance (same 7 pages, real HK pillar content grepped directly out of the generated HTML, not
assumed); `config/site.json` and `config/jurisdictions/hk.json` re-validated against their new
schemas with real `jsonschema.validate()` calls; every workflow YAML file re-parsed after each
edit; a full `grep` sweep for every remaining `hk-radar-bot`/old-contact-email occurrence,
confirming the only survivors are historical log entries in `PROGRESS.md`/`IMPROVEMENT_BACKLOG.md`
describing what was true at the time, correctly left untouched.

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
- A live CCR trigger ("HK Radar — Analyst/Verifier daily run"),
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

### 2026-07-09 — Phase 5 kickoff: audit.yml/corrections/improve.yml scoping directive

Brought Phase 5 to Fable before building: the literal P5 acceptance criterion (14-day soak, two
consecutive real publications) can't be completed synchronously in any session. Fable's direction:
track that as an explicit open item (same pattern as the CCR trigger's unfired status), get the
owner's merge/Pages/trigger-reenable punch list moving in parallel, build `audit.yml` and
corrections now under specific conditions (human-initiated, PR-reviewed, never auto-triggered from
audit findings), and bring a design note for `improve.yml` for review before writing any code, given
its necessary write access to `/pipeline`, `/config`, and `.github/workflows`.

### 2026-07-09 — improve.yml design note: approved with four required additions

Reviewed the design note (file scope, structural PR-only enforcement, prompt-injection exposure via
audit data) before any implementation. Verdict: core architecture approved --
"defense doesn't depend on the model behaving, it depends on the gate" is exactly right. Four
required additions before building: (1) state the hard-deny list as a principle ("nothing whose job
is to check, gate, or constrain the pipeline's own output may be modified by the thing being
improved"), not two example files, and enumerate every gate/schema/workflow from that principle;
(2) `pipeline/prompts/*.md` should stay editable but needs a PR-body spotlight requirement, not a
lock; (3) prefer a bounded, human-curated selection queue over open-ended discretion to survey the
repo; (4) `improve_scope.py` needs the same real-scratch-git-repo test rigor `path_allowlist.py`
got, including a named stress case (a diff touching `pipeline/verify/gate.py` must fail even though
nominally under the allowed `pipeline/` root).

### 2026-07-09 — improve.yml checkpoint: verified and signed off, live-activation sequenced

Independently verified the built mechanism directly: pulled the branch, ran the suite (255/255),
read `improve_scope.py`, `prompt_change_justification.py`, `improve_queue.py`,
`data/improve_queue.json` (confirmed empty), `improve.yml`, and `pr-check.yml` in full, confirmed via
`list_triggers` that no live CCR trigger exists for this mechanism. All four required additions
verified as real and correctly implemented, not just described -- specifically confirmed the named
stress test exists verbatim and correctly proves deny-wins-over-allow. The proactive addition of
`promote_drafted.py` alongside its named sibling was called out as the correct catch. The three
deliberate hard-deny exclusions (`docfetch.py`, `queue_check.py`, `seed_backfill.py`,
`pipeline/audit/**`) have sound reasoning and no changes were requested.

**Verdict on not standing up a live CCR trigger yet: confirmed as the right call**, with an explicit
sequencing precondition for revisiting it (now recorded as item 5 in "Owner / next-step punch list"
above): don't run `improve.yml`'s live trigger in parallel with the analyst/verifier trigger's own
unproven first runs. Sequence strictly: (1) merge, Pages, trigger re-enable, branch protection; (2)
let the re-enabled analyst/verifier trigger complete a handful of real, observed, successful cycles;
(3) only then, one full manual dry run of `docs/improve-runbook.md` against one real, low-stakes
queued item, reported back to Fable before either trigger's live-activation question comes back up.
Reasoning given: every gate built so far in this project has caught at least one real bug the
moment it was actually run against live reality rather than fixtures alone, and compounding two
newly-live autonomous mechanisms at once would make any incident far harder to attribute.

**Fable's summary verdict:** "Phase 5's deterministic build (audit, corrections, improve) is in
good shape. The remaining work is the owner's punch list ... and the sequenced live-proving steps
... -- not more engineering."
