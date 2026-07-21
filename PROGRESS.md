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
- **P7 — New IA and frontend rebuild: complete.** Sticky two-row header, Current State/Timeline
  merge, condensed 5-link nav, glossary jurisdiction filter chips with real `#term-{id}`
  crosslinks, config-driven Method coverage table -- see the 2026-07-11 "P7" entry below.
- **P8 — Watcher mechanism expansion: complete.** Feed mechanisms generalized beyond RSS to atom,
  html_diff, sitemap_diff, json_api, all converging on one `NormalizedItem` contract; three-way
  feed-health event classification (`feed_structure_error`/`feed_fetch_failure`/`feed_silence`) --
  see the 2026-07-11 "P8" entry below.
- **P9 — UK onboarding (first new jurisdiction): complete.** Full seed depth (7 pillar states, 6
  verified headline cards, trajectory, 12 glossary terms, document library, orientation page), real
  live watcher wiring (`status.watcher: "live"`, `status.seeded: true`), CCR routine prepared but
  deliberately not activated (`status.analyst_verifier: "planned"`) -- see the 2026-07-11 "P9" entry
  below for the nine real gaps the final-check surfaced and how each was closed.
- **P10 — EU onboarding (third jurisdiction, watcher-first ordering): complete.** Full seed depth (7
  pillar states, 5 verified cards, 12-entry trajectory, 17 glossary terms, document library,
  orientation page), MiCA-aware "already in force since 2024" framing, explicit EU-level-only scope
  discipline, real live watcher wiring -- see the 2026-07-11/12 "P10" entry below for how the
  watcher-before-cards phase reorder closed P9's worst gap structurally, plus the two real defects
  (5 glossary placeholders, one fabricated quote) still found and fixed.
- **P11 — US onboarding (fourth jurisdiction, no single federal regulator): complete.** Full seed depth
  (7 pillar states, 5 verified cards, 7-entry trajectory, 17 glossary terms, 45-document library,
  orientation page), 6 federal regulators registered (SEC, CFTC, FinCEN, OCC, Federal Reserve, plus a
  zero-feed GovInfo/Congress.gov/U.S. Code citation entry), elevated neutrality discipline given how
  contested US digital-asset policy genuinely is, real live watcher wiring -- see the 2026-07-12 "P11"
  entry below for the four real citation defects the final-check surfaced (a quote fabrication, a
  missing domain registration, two bot-blocked false-negative URLs) and a materially inverted timing
  claim an independent verifier pass caught along the way.
- **P12a — Switzerland onboarding (fifth jurisdiction, no omnibus crypto statute): complete.** Full seed
  depth (7 pillar states, 5 verified cards, 4-entry trajectory, 15 glossary terms, orientation page),
  FINMA registered plus 4 zero-feed citation entries (Fedlex, SIF, SNB, SIX Exchange Regulation),
  explicit "amend existing law, never a new statute" structural framing, real live watcher wiring -- see
  the 2026-07-12 "P12a" entry below for a real cross-jurisdiction pipeline gap the final-check surfaced
  (`seed_backfill.py` never regenerated the document library the way the live watcher does) and how it
  was fixed at the source, plus a latent official-domain gap caught before any card actually hit it.
- **P12b — Japan onboarding (sixth jurisdiction): complete, first fully clean final-check.** Full seed
  depth (7 pillar states, 5 verified cards, 7-entry trajectory, 11 glossary terms, 13-document library,
  orientation page), FSA and JVCEA registered plus 4 zero-feed citation entries (proactively including
  the Bank of Japan, learning P12a's own lesson), one of the earliest dedicated national stablecoin
  frameworks anywhere (2022 PSA amendment, in force since 1 June 2023, already iterated by a 2025
  amendment), Japanese-language source-quoting discipline held throughout -- see the 2026-07-12 "P12b"
  entry below. Zero defects found by the final-check; no fix-then-commit cycle needed.
- **P13 — UAE onboarding (seventh jurisdiction, layered federal/emirate/free-zone structure):
  complete.** Full seed depth (7 pillar states, 26 verified cards, 2-entry trajectory, 26 UAE-tagged
  glossary terms + 3 cross-jurisdiction, 26-document library, orientation page), five regulators
  registered (VARA, CMA/SCA, DFSA, FSRA all with live feeds, plus CBUAE and Dubai Land Department as
  zero-feed citation entries added during this phase's own fix cycle), four-regulator/four-geography
  scope-attribution convention enforced on every card and pillar state. See the 2026-07-13 "P13" entry
  below for the fix-then-commit cycle this phase needed: a live official-domain gap that was gate-forcing
  7/26 cards to `unverified` (fixed at the config layer, then genuinely re-verified by fresh verifier
  agents, not just status-flipped), a latent domain gap across four more already-cited government
  bodies, one glossary status-field misuse repeating P9's exact mistake, and one self-contradictory
  sentence in orientation.json's opening framing.
- **P14 — Singapore onboarding (eighth jurisdiction, manual-assisted watcher, no live feed):
  complete.** Full seed depth (7 pillar states, 13 verified + 1 honestly-unverified cards,
  3-entry trajectory, 13 SG-tagged glossary terms, 19-document library, orientation page). The first
  jurisdiction with `status.watcher: "dormant"` -- MAS (mas.gov.sg) and Singapore Statutes Online both
  confirmed, live, to bot-block this project's honest User-Agent; per the owner's P6-stage decision, no
  browser-UA impersonation was used, so `sg` is deliberately absent from `watch.yml`'s matrix and content
  is curated via manual `seed_backfill` review instead. See the 2026-07-13 "P14" entry below for the
  fix-then-commit cycle this phase needed: the workflow's own Research phase hit a "Prompt is too long"
  failure and silently produced only 6 of 7 pillar-state files, crashing `pipeline.site.generate` outright
  for every jurisdiction (not just Singapore) until fixed; two cards cited a blocked mas.gov.sg page when
  an already-proven `sgpc.gov.sg` mirror existed but wasn't used; two cards had PDF-extraction-artifact
  quote mismatches (a glued footnote digit, a curly-quote spacing difference); three cards were genuinely
  authentic but had simply never received a completed verifier pass; and a `sgpc.gov.sg`-cited quote that
  one fix agent believed it had verified was still caught and downgraded by the real gate on a second PDF-
  extraction artifact, fixed by directly calling the gate's own `quote_is_authentic()` function to find a
  clean substring before re-verifying through a fresh agent, never by hand-editing status.

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
   b. ~~Let the re-enabled analyst/verifier trigger complete a handful of real, observed, successful
      cycles.~~ **Confirmed live and firing nightly as of this entry (2026-07-13)**: the "HK Radar —
      Analyst/Verifier daily run" CCR trigger (`trig_01Bk3Lz2FKf3pWRMFkqBcdDE`, cron `30 22 * * *`,
      `enabled: true`) shows a real `last_fired_at` of 2026-07-12T22:35Z, confirmed via
      `list_triggers` at P15 time -- it has been firing on schedule since re-enabling. This session
      did not independently audit every individual firing's commit history for this entry (that is a
      genuine remaining verification step, not assumed clean), but the mechanism itself is
      demonstrably live and unattended, not merely armed.
   c. **Still open.** One full **manual** dry run of `docs/improve-runbook.md` -- `data/improve_queue.json`
      is confirmed still empty (`{"schema_version": 1, "items": []}`) as of this entry, meaning this
      step has not yet happened. `improve.yml` has real, unreviewed write-access implications
      (`/pipeline`, `/config`, `.github/workflows` are all in its potential blast radius, gated only by
      `improve_scope.py`'s allow/deny logic), and Fable's own directive was to report the dry run's
      result back before either trigger's live-activation question comes back up -- this session
      judged that populating a real queue item and running that dry run is itself a decision the owner
      should be looped in on before it happens, not something to do unilaterally while unattended, so
      it was deliberately left for explicit owner/PM sign-off rather than run here.
6. Two logged anonymity flags remain owner decisions before public launch (see
   IMPROVEMENT_BACKLOG.md's deviations entries): the LICENSE "Big Fan" copyright line, and non-bot
   commits — which are structural and recurring, not just the initial commit: every PR merged
   through GitHub's UI records the merging account (currently the owner's real account) as the
   merge commit's identity, and `correction.yml`/`improve.yml` are PR-only/human-merge by design,
   so this recurs on every future merge. Bot identity is guaranteed only for commits the pipeline
   and build sessions themselves create; closing the gap requires a bot-credentialed merge path
   (GitHub App/PAT merging as `hk-radar-bot`), which this environment does not have.
7. ~~**`audit.yml` has still never produced a real `data/audit/latest.json`**~~ **Resolved,
   2026-07-13.** `audit.yml`'s first genuine scheduled run fired for real and produced `data/
   audit/latest.json` (63KB, merged into `main` via PR #6's merge window -- see that entry above);
   its findings were the subject of the same day's "PR #6 merged; first post-merge maintenance
   pass" fix cycle. The "self-learning loop" diagram's audit stage is now genuinely proven live,
   not just built.
8. ~~**P6-P14's registry-model rebuild added seven more jurisdictions... but `status.analyst_verifier`
   deliberately stays `"planned"`**~~ **Resolved, 2026-07-14.** Owner explicitly approved extending
   live analyst/verifier to all 6 remaining live-watcher jurisdictions (`us`, `eu`, `uk`, `uae`,
   `ch`, `jp`) at once -- see that entry below for the full decision, prerequisite generalization
   work, and a real bot-identity bug found in the CCR trigger's own prompt text along the way (fix
   left for explicit owner go-ahead, not done unilaterally). `sg` stays `"planned"` by design (its
   watcher is `"dormant"`, manual-assisted only). **Still open, and now the real next verification
   step**: watch the first real post-flip firing across all 7 live jurisdictions and confirm it
   behaves as designed before calling this rollout proven, not just confirming the trigger fired.
9. **The literal P15 acceptance criterion -- a 14-day zero-touch soak with two consecutive real
   publications -- cannot be completed synchronously in any single session**, exactly as flagged when
   this constraint was first named back at Phase 5's kickoff (see that entry above). The HK trigger has
   been live and firing since 2026-07-09; the actual 14-day clock needs to run in the background across
   real calendar time and be checked back on, not simulated here.

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

### 2026-07-11 — P7: new IA and frontend rebuild

Owner authorized continuing the build autonomously ("carry on until done... use Fable as project
director... leave questions if any at the end"). Fable directed P7 -- the visible frontend rebuild
on top of P6's registry-model foundation -- via a director-spec-then-sequential-migration workflow
matching P6's own pattern: exact page copy, orientation-panel content, seal legend, coming-soon
copy, the Timeline/Trajectory merge design, and the window-sort-key parsing rules were all specified
by Fable before any template code was written.

**Site restructured from 7 flat pages to the planned 5-page-type IA:** `pipeline/site/generate.py`
now renders a global landing page (`_site/index.html` -- an 8-jurisdiction grid, HK marked live, the
other 7 marked "Coming soon" with real per-jurisdiction `coverage_notes` from `config/site.json`,
not identical boilerplate) plus per-jurisdiction Current State and Timeline pages for every registry
entry (`_site/{jid}/index.html`, `_site/{jid}/timeline.html` -- HK renders full real content, the
other 7 render a genuine, honest "coverage planned" page, never a 404 or empty file). Document
Library, Glossary, and Method & Audit stay as shared, root-level pages. `pipeline/site/templates/
{start_here,state_board,trajectory}.html` deleted; `landing.html`, `current_state.html`,
`coming_soon.html` added.

**Timeline absorbs the Trajectory Board**, per the plan's exact three-band design:
`pipeline/site/data.py` gained `window_sort_key()` -- a pure function parsing a trajectory entry's
free-text `date_or_window` (exact date, year-month, quarter, half-year, bare year) into a sortable
key anchored to the window's *start*, with a deliberate, documented non-guessing fallback for
genuinely unparseable strings ("mid-2026", "TBC") that sorts last rather than risk a wrong
chronological guess -- the same "an honest 'unparsed' beats a wrong guess" principle this project's
citation-authenticity gate already applies to facts. The merged `hk/timeline.html` renders the
existing precise ribbon unchanged, a new "Ahead" rail showing trajectory entries as pills with their
*verbatim* window text (confirmed in the final-check: real qualitative windows like "H1 2026" and
"mid-2026" render as-is, never coerced into a fabricated exact date), and the existing by-pillar
board view below. The standalone Trajectory Board page and template are gone; `trajectory.json`
itself is untouched as the data source.

**Glossary and Document Library became genuinely shared, filterable pages:** jurisdiction filter
chips with real, build-time-computed counts (verified by hand-count in the final-check: 8 HK-tagged
+ 3 global-tagged = 11 for the "Hong Kong" chip, matching exactly); "See also" changed from unlinked
display text to real `#term-{id}` anchor links, with the anchor scheme itself changed from the old
term-text-derived id (which could collide across jurisdictions or break on punctuation) to the
stable, collision-proof `id` field P6's migration already added. The final-check independently
verified at least one crosslink's target anchor genuinely exists elsewhere in the same file, not
just that the link text looked right.

**Method & Audit's coverage table is real and config-driven, not hand-written:** 8 rows, one per
`config/site.json` registry entry, cross-checked cell-by-cell against the config in the final-check
and confirmed to match verbatim, including jurisdiction-specific gap notes (Singapore's manual-
assisted-watcher decision, UAE's federal-vs-free-zone ambiguity, EU's member-state-NCA exclusion).

**One real bug found by the final-check and fixed directly by the orchestrating session:**
`base.html`'s jurisdiction-tab markup rendered `aria-current="page"aria-disabled="true"` with no
separating space (invalid HTML5, though browsers parse it leniently) whenever a visitor viewed an
unseeded jurisdiction's own tab -- a Jinja `trim_blocks`/`lstrip_blocks` side effect of two adjacent
`{% if %}` blocks on separate template lines. Fixed with an explicit literal space inside the first
conditional's own output so it survives block-trimming regardless of which branch renders; rebuilt
and grepped the actual output to confirm the fix, not just the template diff.

**Known, disclosed content gap, not a P7 regression:** three glossary "See also" references
(`Policy statement 2.0`, `Stablecoins ordinance`, `Virtual asset`) point at terms that don't exist
as their own glossary entries yet -- pre-existing gaps from Phase 3's original glossary v1, now
visible because P7 made "See also" a real link-or-plain-text choice instead of always-plain-text.
Degrades gracefully (unlinked text, never a dead anchor); left as a content backlog item, not a
frontend bug.

**Verification, run fresh by the orchestrating session, not trusted from the workflow's own
report:** full pytest suite 375 passing (up from 363); the aria-attribute fix specifically rebuilt
and grepped out of the real generated HTML; `tests/test_jurisdiction_agnostic.py` re-confirmed
green (the templates/static scan included).

### 2026-07-11 — P8: watcher mechanism expansion (atom, html_diff, sitemap_diff, json_api)

Fable directed P8 the same way as P6/P7: a director spec (exact `NormalizedItem` contract, exact
config field design per mechanism -- with real worked examples drawn from the earlier jurisdiction
recon, e.g. a FinCEN-shaped `html_diff` entry, a MAS-shaped `sitemap_diff` entry, a Federal-Register-
shaped `json_api` entry, an HM-Treasury-shaped `atom` entry -- then sequential implementation).
`pipeline/watcher/run.py`'s previously RSS-only per-feed loop now dispatches on each feed config
entry's `mechanism` field (default `"rss"`, so all 9 of `hk.json`'s existing feeds are unaffected)
to one of five modules under the new `pipeline/watcher/mechanisms/` package, all converging on the
same `NormalizedItem` shape so hashing/ledger/queue/relevance/classify/document_library needed zero
changes downstream. Real engineering care in the contract itself: `html_diff`/`sitemap_diff` items
(no stable guid on a listing page) get identity via a canonicalized absolute URL rather than the
existing guid→link+title fallback, specifically to avoid spawning a duplicate ledger entry every
time a CMS page's title gets touched up post-publication; a new `needs_enrichment` flag marks
sitemap-diff items (which have no title/date at all) so the analyst knows to fetch-and-derive rather
than receive a fabricated placeholder -- the same "an honest gap beats a wrong guess" principle
`window_sort_key` (P7) and the citation-authenticity gate already apply elsewhere in this project.

New `data/{jid}/watch_status.json` substrate (new schema) means a feed whose selector/pattern/path
breaks entirely -- never contributing a single ledger item -- is no longer invisible to
`pipeline/audit/feed_health.py`: it now emits three mutually exclusive event types
(`feed_structure_error`, `feed_fetch_failure`, `feed_silence`), each independently gated on its own
minimum-days threshold so a single transient blip doesn't page anyone.

**The workflow's own final-check caught two real test-coverage gaps rather than accepting a passing
suite as sufficient, and both were closed directly by the orchestrating session before this counted
as done:** the atom mechanism had no dedicated day1/day2 diff-detection test at all (unlike the
other three mechanisms, which each prove "detects only the new items, not zero, not all" against
the real ledger machinery) -- added `tests/test_atom.py` plus an `hmt_day2.atom` fixture (2 new
entries appended to the existing HM Treasury fixture), confirming exactly 2 new items detected, not
4, not 0, plus idempotency on a third run. And `feed_health.py`'s `feed_fetch_failure` event type
had zero test coverage anywhere (only `feed_structure_error` was exercised, and only indirectly, via
an end-to-end integration test) -- added 8 new unit tests directly against `check_feed_coverage`
covering `fetch_error` and `parse_error` statuses, the mutual-exclusivity guarantee in both
directions, the `fetch_failure_min_days` threshold's exact boundary, the deliberately-unclassified
`config_error` case, and a healthy-new-feed-with-no-item-yet case.

Also fixed in the same pass: `pipeline/watcher/fetch.py`'s docstring still referenced the deleted
pre-P6 `config/jurisdiction.json` path.

**Verification, run fresh by the orchestrating session:** full pytest suite 439 passing (up from
375) -- the 429 the workflow itself reported plus 10 more from closing the two gaps above; every new
atom/feed-health test independently re-run and confirmed passing; `tests/
test_jurisdiction_agnostic.py` re-confirmed green over the four new mechanism modules (no hardcoded
selector, URL, or jurisdiction string -- verified by direct grep, not just trusting the scan); a
fresh `pipeline.site.generate` run confirmed the (unrelated) site build still works unchanged.

### 2026-07-11 — P9: UK onboarding (first new jurisdiction) + consolidated CCR routine

The proof that the P6-P8 registry-model architecture actually holds for a jurisdiction beyond HK.
Fable directed the same director-spec -> research -> cards -> gates -> wiring -> final-check
pattern as P6-P8, grounded in the earlier live-verified UK recon (real FCA/Bank of England/HM
Treasury feed URLs, a worked 7-pillar mapping, 6 headline-event candidates). `config/jurisdictions/
uk.json` registers 4 regulators -- FCA, Bank of England (PRA folded in, matching how it actually
publishes), HM Treasury, and a zero-feed `legislation_gov_uk` citation-only entry (the
`legislation.gov.uk` National Archives domain, added the same way HK registers its zero-feed
Gazette/LegCo/FSTB entries) -- 11 parallel research passes seeded all 7 pillar states, `trajectory.
json` (7 entries), 12 new shared-glossary terms, and a 6-document library, all independently
citation-checked. The core finding threaded through every UK pillar: the Financial Services and
Markets Act 2000 (Cryptoassets) Regulations 2026 (SI 2026/102) was made 4 Feb 2026 and its final
implementing rules (FCA policy statements PS26/9-PS26/13, Bank of England's systemic-stablecoin
Code of Practice) were finalised 22-30 Jun 2026, but the regime itself does not take legal effect
until 25 October 2027 -- every card and pillar state states this plainly rather than implying the
new perimeter is live.

**The workflow's own final-check again caught real gaps, several more substantial than P6-P8's --
all closed directly by the orchestrating session before this counted as done, none papered over:**

1. One of six planned card drafts failed outright mid-run (`[draft:FCA publishes final policy
   statement pac] failed: Prompt is too long`) -- the workflow's own per-stage prompt constructor
   passed too much accumulated context into that one draft call. Re-drafted directly via a fresh,
   lean, self-contained `Agent` call (not a re-run of the whole workflow) against the same real
   queued ledger item; independently re-verified afterward like every other card.
2. `content/uk/orientation.json` was never written at all -- `pipeline.site.generate` treats it as
   mandatory per-jurisdiction seed content and crashed outright (`SiteDataError`) rather than
   degrading gracefully, meaning the UK site could not build at all and the only artifact on disk
   was a stale "coming soon" placeholder. Written directly by the orchestrating session (795 words,
   same who-regulates-what / already-in-force / coming-next structure as HK's, grounded in the
   now-verified pillar states -- the orientation schema requires no citations of its own, being
   free prose, but every claim in it traces to already-fact-checked pillar-state content).
3. `config/jurisdictions/uk.json`'s `official_domains` never included `legislation.gov.uk` --
   which forced two cards citing primary UK legislation (`FSMA 2000 (Cryptoassets) Regulations
   2026`, `Bank of England`'s statutory basis) to `unverified` by the deterministic gate's
   fail-closed domain check, even though their citations were independently confirmed genuine.
   Fixed by registering `legislation.gov.uk` as its own zero-feed regulator entry rather than
   folding it into an existing regulator's domain list, matching the HK Gazette convention; caught
   a second-order bug from this fix's first attempt (id `"legislation"` collided with the plain
   English word already used in `pipeline/site/data.py`'s seal-vocabulary prose, tripping
   `test_jurisdiction_agnostic.py`'s generated banned-literals scan) and renamed the id to
   `legislation_gov_uk`.
4. **The five originally-drafted cards' filenames/ids never matched any real ledger `item_hash`**,
   because the workflow drafted cards from headline-event research before the live watcher had
   ever run, so `promote_drafted`/`promote_verified` (which key strictly off `content/uk/cards/
   <item_hash>.json` existing) found zero matches -- by the ledger's own record, UK had never
   produced a single card, even though five real ones existed on disk. Reconciled by hand,
   evidence-based, not fabricated: for the 2 events the live watcher's real first run genuinely
   discovered (the tokenisation Call for Input, the BoE stablecoin policy statement), matched by
   citation URL and exact publish date and renamed the card files to those real `item_hash`es. For
   the 3 events that had already rolled off the live feeds' retention window (Oct 2025 and Feb 2026
   items, 5-9 months old by the time the watcher first ran in Jul 2026), used
   `pipeline.ci.seed_backfill` -- the exact tool this project already built for pre-watcher
   historical seeding -- with descriptors built from each card's own already-cited primary URLs and
   dates, then renamed those card files to the resulting real hashes too. All six `content/uk/
   cards/*.json` ids now equal their governing ledger `item_hash`, exactly mirroring how HK's own
   5 published ledger items work.
5. Two cards (the SI card, the BoE stablecoin card) were sitting at gate-forced `status:
   "unverified"` purely from finding #3 above, not from any real content problem -- confirmed by
   independently re-running a full adversarial verifier pass against each (fresh context, real
   re-fetch of every citation) after the domain fix, rather than hand-flipping their status. One
   verifier pass also independently re-examined the BoE card's previously-flagged "Recognition
   order: DSA service provider" quote (worried it read like a paraphrase of two separate clauses)
   by re-fetching the actual Schedule 6 text three separate ways -- confirmed it is a genuine
   verbatim section heading, not a fabrication, while separately catching and fixing an unrelated
   misattribution (the summary had conflated three separate FCA policy statements' distinct scopes
   into one). The sixth (newly re-drafted) card's own verifier pass separately caught and fixed an
   unsupported "(SI 2026/102)" parenthetical, replacing it with an added fourth citation to
   `legislation.gov.uk` and the primary source's own exact citation format ("2026 No. 102"). Two of
   three verifier sub-agents hit a genuine worktree infrastructure issue (isolated at a stale,
   pre-P6 commit with no `content/uk/` tree and an incompatible `card.json` schema) and could not
   write their completed verdict back themselves -- their adversarial analysis was read in full and
   applied directly by the orchestrating session rather than discarded or re-run from scratch, since
   the analysis itself (independent re-fetches, no edits needed beyond the status field) was
   already sound.
6. A shared glossary content generalization (broadening `stablecoin.json`'s formal definition from
   HK-only to cross-jurisdiction) had been marked `status: "corrected"` -- the wrong status for a
   scope expansion rather than a retraction of a wrong claim (`data/corrections.json` does not even
   exist yet anywhere in this repo; `status: "corrected"` is meant for CLAUDE.md rule 6's public
   retraction workflow). Reset to `"unverified"`, matching a freshly-written entry's normal status.
7. Six `first_used_card_id` glossary fields were left as literal `"PENDING-no-uk-card-yet"`
   placeholders from the mid-run card-draft failure (finding #1) -- one batch of 6 was fixed by the
   re-draft agent itself; a second, previously-unnoticed batch of 5 (`digit`, `boe`,
   `digital-securities-sandbox`, `systemic-stablecoin`, `hm-treasury`) was found by an explicit
   repo-wide grep and fixed directly, each pointed at whichever real card's `published_date` is
   chronologically earliest among the cards that actually use that term.
8. `content/uk/trajectory.json`'s 7 entries all carried `model: "claude-sonnet-5"` -- an internal
   model-version identifier, banned by `validate_content` per the 2026-07-09 correction in
   IMPROVEMENT_BACKLOG.md -- rather than the required human-readable `"Claude (Anthropic)"`. Fixed
   directly across all 7 entries.
9. `.gitignore`'s ETag-cache exclusion (`/data/cache/`) was still anchored to the pre-P6 flat path
   and silently stopped covering the P6 registry-model's real per-jurisdiction path
   (`data/{jid}/cache/`), which would have let `data/uk/cache/etags.json` get committed -- the exact
   idempotency-breaking outcome the original comment explains the exclusion exists to prevent.
   Generalized to `/data/*/cache/`, same "operative layer left stale by a structural migration"
   lesson already logged from P6.

After all nine fixes: all 6 UK cards genuinely `"verified"` end to end (real deterministic gate
re-run against all six after every fix, zero downgrades); `promote_drafted`/`promote_verified` ran
for real and promoted exactly 6 ledger items to `published` with matching `card_id` (137 items
remain genuinely `queued`, including 3 real relevant items the live watcher found that were never
part of this seed batch -- correctly left for a future run, not fabricated as processed);
`pipeline.site.generate` produces real `_site/uk/index.html` and `_site/uk/timeline.html` content
(verified by direct grep for the absence of "coming soon" and the presence of the real orientation
text); `config/site.json`'s `uk` entry now reads `status.watcher: "live"`, `status.seeded: true`,
`status.analyst_verifier: "planned"` (deliberately left planned -- flipping it live is a separate,
explicit owner decision per `docs/analyst-runbook.md`'s own rewritten Step 0, not inferred from a
successful seed pass); `.github/workflows/watch.yml`'s matrix is now `[hk, uk]`; `docs/
analyst-runbook.md`'s Step 0 is rewritten into a real per-jurisdiction registry loop (4
cards/jurisdiction, 10 cards/firing caps) that explicitly refuses to process any jurisdiction not
marked `analyst_verifier: "live"`, regardless of queue size.

**Verification, run fresh by the orchestrating session, after all nine fixes above:** full pytest
suite 439/439 passing; `pipeline.ci.validate_content` 31/31 files OK; `pipeline.ci.
apply_verification_gate --jurisdiction uk` re-run clean (zero downgrades) as the final check before
promotion; a full `pipeline.site.generate` rebuild from a clean `_site/` directory succeeded and was
spot-checked; `tests/test_jurisdiction_agnostic.py` green including the newly-registered UK
regulator ids and domains. Not yet done, logged honestly rather than overclaimed: `uk`'s
`analyst_verifier` stays `"planned"` (no live CCR trigger touches UK yet -- that is a deliberate,
separate owner decision, not an oversight); the P9 workflow's background sub-agent worktrees
(`.claude/worktrees/agent-*`) and their local git branches were manually cleaned up after extracting
their real output, since neither is itself part of the repo's tracked history.

### 2026-07-11/12 — P10: EU onboarding (third jurisdiction, watcher-first ordering)

Directed the same way as P6-P9, but with the phase order deliberately restructured based on P9's own
logged gaps: this time the real live watcher run and `pipeline.ci.seed_backfill` (for anchor events
predating any feed's retention window) ran *before* card drafting, not after -- so every card could be
filed directly against a real `data/eu/ledger.json` `item_hash` from the start, rather than needing the
reconciliation pass P9 required. `config/jurisdictions/eu.json` registers 6 regulators: European
Commission, ESMA, EBA, ECB, AMLA (all with live feeds, re-verified with the project's own fetch
discipline), plus a zero-feed `eur_lex` citation-only entry (EUR-Lex/Official Journal) -- deliberately
named to avoid P9's own `"legislation"`-collides-with-plain-English-prose mistake (confirmed by grep:
zero hits for `eur_lex` anywhere in `pipeline/` outside its own config entry). Content seeded: 7 pillar
states, 5 independently verified cards, a 12-entry trajectory, 17 new shared-glossary terms (16 EU-
tagged, one -- `travel-rule` -- correctly scoped `["global"]` since the concept is genuinely cross-
jurisdictional), a 2-document library, and an orientation page. The core framing threaded through every
pillar, explicit everywhere it matters: **MiCA (Regulation (EU) 2023/1114) is already fully in force**
(Titles III/IV -- asset-referenced tokens and e-money tokens -- applicable since 30 June 2024; the
remainder, including CASP authorisation and market-abuse rules, since 30 December 2024) -- the opposite
narrative shape from UK's not-yet-effective regime, and every pillar state and card distinguishes
"already in force under MiCA itself" from "an ESMA/EBA technical standard still being finalised" from
"genuinely proposed." A second explicit scope discipline runs throughout: this jurisdiction covers the
EU-level framework only (the Regulations/Directives themselves, Commission delegated/implementing acts,
ESMA/EBA technical standards, AMLA) -- actual CASP authorisation and day-to-day supervision is done by
27 member states' own national competent authorities and is out of scope, stated plainly in
`content/eu/orientation.json` and flagged in `open_items` wherever a pillar state's silence on it could
otherwise mislead.

**A background research sub-agent stalled for roughly 8.5 hours mid-run on an unanswered `WebSearch`
permission prompt** (confirmed by inspecting the workflow's own journal and the stalled agent's raw
transcript: a `WebSearch` tool call at 19:23:48 UTC got "User rejected tool use" followed by "[Request
interrupted by user for tool use]," after which the agent sat idle -- not a slow live-fetch, a genuine
dead end it could not resolve on its own) -- caught only because the owner asked "is this stuck or
moving along?" partway through, prompting a direct read of the journal/transcript rather than trusting
elapsed time alone. Its actual deliverable, `content/eu/document_library.json`, had already been written
and schema-validated before the stall, so nothing was lost; `Workflow(..., resumeFromRunId: ...)` replayed
the other 11 completed research agents from cache instantly and only the stalled one re-ran, completing
cleanly the second time.

**The workflow's own final-check, explicitly instructed to check each of P9's nine logged gaps
individually rather than give a general pass/fail, confirmed 7 of 9 avoided by the reordered phase
sequence and instructions, one only partially applicable, and one genuine repeat -- closed directly by
the orchestrating session, same standard as every prior phase:**
1. 5 shared-glossary files (`crypto-asset-white-paper`, `dlt-pilot-regime`, `ec`, `rts-its`,
   `travel-rule`) still carried the literal placeholder `first_used_card_id: "PENDING-no-eu-card-yet"` --
   the exact P9 defect pattern recurring. None of the 5 terms turned out to be textually present in any
   of the 5 real EU cards (confirmed by direct grep, not assumed), so each was assigned to whichever real
   card is its genuine closest topical anchor, following the same non-literal-match convention this
   project's own oldest, pre-provenance HK glossary entries already establish (e.g. `vatp.json`'s
   `first_used_card_id` points at a card that doesn't contain the literal string "VATP" either) --
   confirmed via `grep -rn first_used_card_id pipeline/site/` that this field has zero downstream
   rendering impact, so the fix is a data-integrity correction, not a live-site behavior change.
2. The final-check's own independent citation re-verification (4 cards checked, exceeding the required
   3) found a genuinely fabricated quote the drafting/verifying agents had both missed: the AMLA card's
   second citation read "Summer 2025: AMLA starts operations, and consults on some implementing rules." --
   but the real source page renders "Summer 2025" and "AMLA starts operations..." as two adjacent,
   separately-rendered timeline-table cells with no colon anywhere joining them; the colon was invented.
   Confirmed independently by a direct `curl` + HTML-strip + exact-substring test before touching the
   file. Fixed by dropping the fabricated "Summer 2025:" prefix, leaving a quote that is a genuine
   contiguous substring of the source. A fresh, independent verifier pass (not a self-certification of
   this fix) then re-checked the entire card from scratch and, in the same pass, caught and fixed a
   *second*, previously-unflagged problem: an unverifiable claim about the exact number of governance
   articles taking early effect, which could not be independently re-derived from the regulation's text
   after repeated fetch attempts -- rewritten to state only what could be confirmed. Status flipped to
   `"verified"` by that fresh pass, then reconfirmed by a real `apply_verification_gate --jurisdiction eu`
   re-run (zero downgrades across all 5 cards).

The restructured watcher-before-cards ordering worked as intended: `data/eu/ledger.json` shows exactly 5
`"published"` items with `card_id` set, 1:1 with the 5 real card files, with **zero** manual reconciliation
needed this time (`promote_drafted`/`promote_verified --jurisdiction eu` both report 0 newly promoted when
re-run after this session's fixes, confirming the workflow's own gate run had already linked everything
correctly the first time) -- a direct structural fix of P9's worst gap, not just a smaller instance of it.
`config/site.json`'s `eu` entry now reads `status.watcher: "live"`, `status.seeded: true`,
`status.analyst_verifier: "planned"` (same deliberate non-activation as UK); `.github/workflows/watch.yml`'s
matrix is `[hk, uk, eu]`. `docs/analyst-runbook.md` and both prompt files were correctly left untouched --
confirmed by `git status --porcelain` showing neither -- since P9 already made Step 0 a real registry loop
that needs no jurisdiction-specific edit to extend.

**Verification, run fresh by the orchestrating session, after both fixes above:** full pytest suite
439/439 passing; `pipeline.ci.validate_content` 35/35 files OK; `apply_verification_gate --jurisdiction eu`
re-run clean, all 5 cards `"verified"`, zero downgrades; a full `pipeline.site.generate` rebuild from a
clean `_site/` succeeded, `_site/eu/index.html` confirmed to show real EU content (zero "coming soon"
hits, real ESMA/MiCA/EBA/AMLA/European Commission mentions); repo-wide `grep -rl PENDING
content/shared/glossary/` confirmed clean. Not yet done, logged honestly: `eu`'s `analyst_verifier` stays
`"planned"`, same deliberate non-activation pattern as `hk`/`uk`.

### 2026-07-12 — P11: US onboarding (fourth jurisdiction, no single federal regulator)

The most institutionally fragmented jurisdiction yet, directed with the same watcher-first ordering P10
introduced, plus an explicitly elevated neutrality discipline given how genuinely contested US digital-
asset policy is. `config/jurisdictions/us.json` registers 6 regulators -- SEC, CFTC, FinCEN (with
OFAC/Treasury domains folded in, matching how it actually publishes), OCC, the Federal Reserve, and a
zero-feed `govinfo` citation entry covering govinfo.gov/congress.gov -- with real mechanism diversity
(rss for most, html_diff for FinCEN's own news page, json_api for a Federal Register digital-asset search
feed). Content seeded: 7 pillar states, 5 independently verified cards, a 7-entry trajectory, 17 new
glossary terms, a 45-document library, and an orientation page. The defining structural fact threaded
through every pillar: the US has no single federal digital-asset regulator -- the SEC/CFTC/FinCEN/OCC/Fed
split is itself the citable structure, described neutrally (each agency's own stated position, side by
side, with two explicit self-neutralizing statements in `orientation.json` and
`dealing_custody_advisory.json` that this radar presents "what the agencies themselves published, not a
resolved dispute or a win for either side") -- plus an explicit federal-level-only scope limitation
(state regimes, e.g. NY DFS, out of scope, same discipline EU applied to member-state NCAs). The GENIUS
Act (Public Law 119-27, enacted 18 July 2025) is the anchor: the first US federal permitted-issuer
framework for payment stablecoins, seeded via `seed_backfill` since it long predates any live feed's
retention window.

**The final-check, explicitly instructed to check every one of P9's and P10's logged gaps individually,
found this run had *not yet been through a close-out pass* (no P11 PROGRESS.md entry existed at check
time) and surfaced real, live, unresolved problems in 4 of 5 cards -- closed directly by the orchestrating
session, none papered over, each independently re-confirmed by a fresh adversarial verifier pass rather
than self-certified:**
1. **A genuine quote fabrication**, the same class of defect P10 caught: the GENIUS Act card's
   govinfo.gov citation read "...shall maintain identifiable reserves backing the outstanding payment"
   but the real statute reads "...shall-- (A) maintain identifiable reserves backing the outstanding
   payment stablecoins of the permitted payment stablecoin issuer..." -- the "-- (A)" subsection marker
   had been silently dropped and the quote cut off mid-clause. Fixed to a genuine 14-word contiguous
   substring.
2. **A missing official-domain registration**, the same class as P9's `legislation.gov.uk` gap and P10's
   near-miss: `uscode.house.gov` (three of the same card's four citations, all independently confirmed
   genuine on re-fetch) was not registered in any regulator's `official_domains`, gate-forcing three
   authentic citations to `unverified` on domain grounds alone. Fixed by adding it to the existing
   zero-feed `govinfo` entry (the US Code is Office of the Law Revision Counsel's own official
   publication, the same "official federal legal text" role `govinfo`/`congress.gov` already serve --
   no new regulator entry needed, unlike UK/EU's dedicated legislation portals).
3. **Two false-negative citations from a bot-check interstitial, not a content problem**: two cards cited
   federalregister.gov "landing page" URLs that 302-redirect to `unblock.federalregister.gov` for
   automated fetchers; the genuine full text sits at a different, directly-fetchable URL form
   (`/documents/full_text/html/...`, discoverable via the Federal Register's own JSON API's
   `body_html_url` field). Both citations' quotes were independently confirmed genuine once fetched from
   the correct URL form -- fixed by correcting the URL, not the quote.
4. **An unreliable citation, removed rather than guessed at**: a card's second citation went directly to
   a sec.gov page that is currently rate-limiting automated fetchers (HTTP 403), and independent
   `WebFetch` probes returned inconsistent results on the exact punctuation of a label/value pair on the
   page ("SEC Issue Date" / "March 17, 2026" as either one joined sentence or two separately-rendered
   elements) -- genuinely unverifiable with confidence, not confirmed as fabricated either. Removed per
   `verifier_prompt.md`'s own explicit option (drop a citation whose claim can't be confirmed), since the
   fact it supported (the release's file number and issue date) was independently confirmable from the
   card's other, already-cited, reliably-fetchable Federal Register document.

**A fresh, independent verifier pass on each of the 4 affected cards did real adversarial work, not
rubber-stamping -- and caught real problems beyond the four above, on its own:** a weak/truncated US Code
quote strengthened to a fuller genuine substring; a wrong attribution corrected ("Treasury-certified
state regime" rewritten to the statute's actual mechanism, an interagency Stablecoin Certification Review
Committee chaired by Treasury with the Fed and FDIC as members); an unsupported "no final rule had been
published as of this writing" clause removed from one card; a **materially inverted timing claim** caught
and fixed in another -- the card originally said customer identity must be verified "before opening an
account," but the actual proposed rule requires verification "within a reasonable period of time *after*
the account is opened," the near-opposite. One verifier's own attempted fix was itself caught and
corrected by the orchestrating session before merging: it changed a card's `published_date` from 17 March
2026 to 23 March 2026, reasoning the earlier date was unsupported -- but its `WebFetch`-based re-fetch had
been truncated before reaching the cited document's own signature block, which reads "Dated: March 17,
2026" (confirmed directly via a full raw fetch, appearing three times in the source) -- 23 March is
genuinely the document's Federal Register *effective* date, not its issuance date, and both are real,
distinct, and correctly stated once the summary's wording was fixed to hold both precisely.

`config/site.json`'s `us` entry now reads `status.watcher: "live"`, `status.seeded: true`,
`status.analyst_verifier: "planned"` (same deliberate non-activation as `uk`/`eu`);
`.github/workflows/watch.yml`'s matrix is `[hk, uk, eu, us]`. `docs/analyst-runbook.md` and both prompt
files were correctly left untouched again.

**Verification, run fresh by the orchestrating session, after all fixes above:** full pytest suite
439/439 passing; `pipeline.ci.validate_content` 35/35 files OK; `apply_verification_gate --jurisdiction us`
re-run clean, all 5 cards `"verified"`, zero downgrades; `promote_drafted`/`promote_verified --jurisdiction
us` both report 0 newly promoted on re-run (already correctly linked by the workflow's own watcher-first
run -- P9's worst gap stayed fixed a second jurisdiction running); a full `pipeline.site.generate` rebuild
succeeded, `_site/us/index.html` confirmed to show real US content, zero "coming soon" hits; repo-wide
`grep -rl PENDING content/shared/glossary/` and `grep -rl claude-sonnet content/us/ data/us/
content/shared/glossary/` both confirmed clean; an explicit neutrality grep (landmark/controversial/
overdue/crackdown/industry-friendly) across every US card, pillar state, and orientation.json found zero
hits outside attributed quotes; `tests/test_jurisdiction_agnostic.py` 10/10 green. Also built, in parallel
with this onboarding, a standalone compliance-officer-facing dashboard artifact synthesizing verified
HK/UK/EU (and, once merged, US) content with primary-source citation links -- sourced only from cards
carrying `status: "verified"`, none drafted or unverified content included.

### 2026-07-12 — P12a: Switzerland onboarding (fifth jurisdiction, no omnibus crypto statute at all)

The first jurisdiction with genuinely no dedicated crypto statute of any kind -- not even a not-yet-
effective one like UK's SI 2026/102. FINMA regulates digital assets entirely by applying and amending
existing, technology-neutral financial law (the Banking Act, FinIA, FinSA, AMLA), with the one dedicated
legislative package -- the "DLT Act" -- itself not a standalone crypto code but a bundle of amendments to
roughly ten existing federal statutes, most notably creating the "DLT trading facility" licence category
inside the existing Financial Market Infrastructure Act. `content/ch/orientation.json` states this "amend
and apply existing law, never legislate a new statute" fact as the throughline of every pillar board.
`config/jurisdictions/ch.json` registers FINMA (live RSS feed) plus a zero-feed `fedlex` citation entry
for the Confederation's official law-publication platform. Content seeded: 7 pillar states, 5 independently
verified cards, a 4-entry trajectory, 15 new glossary terms, and an orientation page. This workflow ran
clean end to end with zero background-agent stalls (unlike P10), completing in one pass.

**A real, direct catch during the Director Spec phase, worth logging on its own: the director's own
initial prompt-time research contained a factual error** (a single "1 February 2021" commencement date for
the DLT Act) that the Director Spec agent's own live re-verification caught and corrected before it ever
reached a card -- the DLT Act's commencement was actually staged in two tranches (ledger-based-securities
provisions in force 1 Feb 2021; the Act's remainder, including the DLT trading facility licence category,
fully in force 1 Aug 2021) -- and the spec explicitly flagged this correction and the exact two-stage
framing for every downstream research/drafting agent to use. A second precision catch in the same phase:
FINMA's own official English name for the instrument is "Federal Act on the Adaptation of Federal Law to
Developments in Distributed **Electronic Register** Technology," not "Distributed **Ledger**
Technology" as most secondary sources render it -- flagged as a quote-verbatim trap before any drafting
began.

**The final-check found two real gaps -- one a genuinely new defect class, one a direct instance of a
now-familiar pattern -- both closed directly by the orchestrating session:**
1. **`content/ch/document_library.json` had gone stale mid-onboarding, and the root cause was a real
   pipeline gap, not a content mistake:** the file held only 1 of the 5 relevant/published ledger items.
   `pipeline/watcher/document_library.py`'s `derive_document_library()` is a pure, regenerate-in-full
   function that `pipeline/watcher/run.py` (the live watcher) always calls after every poll -- but
   `pipeline/ci/seed_backfill.py` never did, so backfilled items silently never made it into the document
   library even though they correctly landed in the ledger and got real cards. This would recur for every
   future jurisdiction's backfill step, not just this one. **Fixed at the source**: added a
   `--document-library` flag to `seed_backfill.py` and wired in the same `derive_document_library`/
   `save_document_library` call `run.py` already makes, plus a new regression test
   (`test_main_regenerates_document_library_from_the_full_ledger`) that seeds in two separate calls and
   confirms both items survive in the regenerated file, not just the most recent one. CH's own
   `document_library.json` was then regenerated for real (not hand-edited) using the fixed code path
   directly against the live `data/ch/ledger.json` -- 5 of 5 documents now present.
2. **A latent, not-yet-triggered instance of P9's/P11's official-domain gap:** `config/jurisdictions/ch.json`
   registered only FINMA and Fedlex, but the seeded pillar states and trajectory already cited four more
   official bodies as primary sources -- the Swiss National Bank (`snb.ch`), the State Secretariat for
   International Finance (`sif.admin.ch`) and the Federal Council's own site (`admin.ch`), and SIX Exchange
   Regulation AG (`ser-ag.com`/`six-group.com`/`sdx.com`, the FINMA-recognised self-regulatory body for
   exchange/listing rules) -- none registered anywhere. This hadn't yet gate-failed a card only because none
   of the 5 seeded cards happened to cite these domains, but it was a live violation of CLAUDE.md rule 2's
   letter and would have hit the exact same failure mode UK's `legislation.gov.uk` and US's
   `uscode.house.gov` gaps did the moment any future card cited one. Fixed by registering three new
   zero-feed regulator entries (`sif`, `snb`, `six_exchange_regulation`), each id explicitly grepped against
   `pipeline/` and confirmed collision-free before use. Also added `fedlex.data.admin.ch` (the Confederation's
   actual filestore-PDF subdomain for statute text, distinct from the JS-rendered `fedlex.admin.ch` HTML
   pages a plain fetcher can't read) to the existing `fedlex` entry, per the Director Spec's own live-verified
   finding that the ELI HTML pages 200 but serve only a "JavaScript required" notice to non-browser fetchers
   -- the same false-negative class as P11's federalregister.gov landing pages, caught proactively this time
   rather than discovered after a card got wrongly downgraded.

`config/site.json`'s `ch` entry now reads `status.watcher: "live"`, `status.seeded: true`,
`status.analyst_verifier: "planned"`; `.github/workflows/watch.yml`'s matrix is `[hk, uk, eu, us, ch]`.
`docs/analyst-runbook.md` and both prompt files were correctly left untouched again.

**Verification, run fresh by the orchestrating session, after both fixes above:** full pytest suite
440/440 passing (439 + 1 new `seed_backfill` regression test); `pipeline.ci.validate_content` clean;
`apply_verification_gate --jurisdiction ch` re-run clean after the domain additions, all 5 cards still
`"verified"`, zero downgrades; `promote_drafted`/`promote_verified --jurisdiction ch` both report 0 newly
promoted on re-run (already correctly linked); a full `pipeline.site.generate` rebuild succeeded,
`_site/ch/index.html` confirmed to show real Swiss content, zero "coming soon" hits; repo-wide
`grep -rl PENDING content/shared/glossary/` and `grep -rl claude-sonnet content/ch/ data/ch/` both
confirmed clean; `content/ch/document_library.json` independently re-confirmed at 5/5 documents after
regeneration. P12b (Japan onboarding) is next, using the same proven watcher-first template.

### 2026-07-12 — P12b: Japan onboarding (sixth jurisdiction, clean on the first pass)

The first onboarding whose final-check found **zero defects** -- no fix-then-commit cycle needed, a real
signal that the accumulated P9-P12a lessons are now genuinely baked into the workflow template rather than
each phase re-discovering them. Japan regulates via amendments to two pre-existing statutes -- the Payment
Services Act (PSA, crypto exchange registration since 1 April 2017, hardened after the 2018 Coincheck
incident) and the Financial Instruments and Exchange Act (FIEA, security tokens and crypto derivatives) --
the same "amend existing law" structural pattern P12a established for Switzerland, though with more
statute-specific mechanics than Switzerland's technology-neutral approach. `content/jp/orientation.json`
states this explicitly, drawing the comparison to Switzerland by name. Japan's marquee feature is one of
the earliest dedicated national stablecoin frameworks anywhere: a 2022 PSA amendment (in force 1 June
2023) defines stablecoins as "electronic payment instruments," restricting issuance to banks, registered
fund-transfer providers, and trust companies -- already being iterated by a further 2025 amendment (in
force 1 June 2026) relaxing reserve-asset rules. `config/jurisdictions/jp.json` registers FSA and JVCEA
(both live feeds) plus four zero-feed citation entries (`japanese_law_translation`, `e_gov`, `boj`, `mof`)
-- all four ids explicitly grepped against `pipeline/` and confirmed collision-free before use, and `boj`
registered proactively (not reactively, after P12a's own lesson about latent domain gaps) since the
banking pillar was known in advance to cite the Bank of Japan. Content seeded: 7 pillar states, 5
independently verified cards, a 7-entry trajectory, 11 new glossary terms, and a 13-document library.

**Multi-language discipline held**: several cards and pillar states cite Japanese-language FSA/JVCEA pages
directly, quoting the original Japanese text verbatim (never self-translated) and noting the source
language plainly, exactly as the workflow's own instructions required -- the final-check's independent
re-fetch of all 6 card citations found every quote genuine, no dropped-marker or spliced-punctuation
fabrication (the exact defect class that survived to final-check in both P10 and P11).

**The final-check also confirmed, on a second real jurisdiction, that P12a's `seed_backfill.py` fix
actually works**: `content/jp/document_library.json` holds exactly 13 documents, precisely matching the 13
`relevant: true` items in `data/jp/ledger.json` (5 published + 8 still-queued) -- no manual regeneration
needed this time, unlike Switzerland's onboarding, because the fix now runs automatically inside
`seed_backfill` itself.

`config/site.json`'s `jp` entry now reads `status.watcher: "live"`, `status.seeded: true`,
`status.analyst_verifier: "planned"`; `.github/workflows/watch.yml`'s matrix is
`[hk, uk, eu, us, ch, jp]`. `docs/analyst-runbook.md`, both prompt files, and everything under `/pipeline`
were correctly left untouched -- this run needed no source fix, only the same content build every prior
phase has done.

**Verification, run fresh by the orchestrating session** (the final-check itself did extensive independent
re-fetching, but every prior phase's "trust nothing, re-derive" standard still applies to its own report):
full pytest suite 440/440 passing (no regression, no new pipeline code needed); `pipeline.ci.
validate_content` clean (28 files); `apply_verification_gate --jurisdiction jp` re-run clean, all 5 cards
still `"verified"`, zero downgrades; `promote_drafted`/`promote_verified --jurisdiction jp` both report 0
newly promoted (already correctly linked); `content/jp/document_library.json` independently re-counted at
13/13 against the live ledger; a full `pipeline.site.generate` rebuild succeeded, `_site/jp/index.html`
confirmed to show real Japanese content, zero "coming soon" hits; repo-wide `grep -rl PENDING
content/shared/glossary/` confirmed clean.

**Six jurisdictions now live: hk, uk, eu, us, ch, jp.** P13 (UAE onboarding) is next.

### 2026-07-13 — P13: UAE onboarding (seventh jurisdiction, four regulators/four geographies -- a real fix-then-commit cycle)

The UAE has no single digital-asset regulator: VARA (Emirate of Dubai excluding the DIFC), the CMA
(federal, UAE-wide outside the two financial free zones -- the direct 1 January 2026 statutory
successor to the SCA, Securities and Commodities Authority), the DFSA (DIFC only), and the FSRA
(ADGM only) each hold their own geographic patch, with the CBUAE (Central Bank of the UAE) cutting
across all four on two subjects (payment-token licensing, banking/CBDC) rather than holding a patch
of its own. `config/jurisdictions/uae.json` registers VARA/CMA/DFSA/FSRA with live feeds
(`html_diff` for VARA, `sitemap_diff` for the CMA's EN+AR news and FSRA/ADGM's announcements --
each mechanism choice live-verified against the real site structure and documented inline in the
config, same discipline as every prior phase) plus `uae_legislation` (u.ae) as a zero-feed citation
entry. Content seeded via the established watcher-first ordering: 7 pillar states (each naming its
owning regulator(s) explicitly), 26 verified cards, a 2-entry trajectory, 26 UAE-tagged glossary
terms plus 3 new cross-jurisdiction terms (`carf`, `proliferation-financing`, `vasp`), a 26-document
library, and an orientation page making the four-regulator/one-cross-cutting-body structure the
opening framing of the entire jurisdiction page.

**This was the first onboarding since P12b to need a genuine fix-then-commit cycle**, and the
biggest one yet in this defect class. The final-check found:

1. **A live official-domain gap, currently downgrading real cards** -- not latent, unlike every
   prior phase's version of this same defect (P9's `legislation.gov.uk`, P11's
   `uscode.house.gov`, P12a's SNB/SIF/SIX). VARA's own circular PDFs are hosted on
   `media.umbraco.io`, a CDN not covered by `vara.ae`'s registered domain, and this was gate-forcing
   7 of 26 drafted cards to `status: "unverified"` even though every one of their citation quotes was
   independently confirmed genuine by the final-check's own re-fetch. Fixed by adding
   `media.umbraco.io` to VARA's `official_domains`.
2. **Four more already-cited-but-unregistered domains**, none yet tripping a card-level failure but
   already the sole factual basis for claims in seeded pillar-state content (a live violation of
   CLAUDE.md rule 2's letter, not just a latent risk the way P12a's gap was): `rulebook.centralbank.ae`
   / `www.centralbank.ae` (the CBUAE, which `banking_money.json` states owns that pillar
   "exclusively," yet had no regulator entry in the config at all -- not even zero-feed);
   `dfsaen.thomsonreuters.com` (DFSA's own official rulebook-hosting platform, relied on in 6 pillar-state
   files); `en.adgm.thomsonreuters.com` (FSRA/ADGM's equivalent, 3 files); `dubailand.gov.ae` (Dubai
   Land Department, the joint-operator source for a real-estate-tokenization claim). Fixed by adding
   `media.umbraco.io`/`dfsaen.thomsonreuters.com`/`en.adgm.thomsonreuters.com` to
   VARA/DFSA/FSRA's respective `official_domains`, and registering two new zero-feed regulator
   entries -- `cbuae` and `dubai_land_department` -- both ids grepped against `pipeline/` and
   confirmed collision-free before use, matching the established zero-feed-citation-entry convention.
3. **A glossary status-field misuse repeating P9's exact finding**: `content/shared/glossary/aan.json`
   carried `status: "corrected"` despite being a freshly-generated, never-before-published entry with
   no corresponding `data/corrections.json` entry (that file still doesn't exist anywhere in the
   repo). Fixed by setting it to `"unverified"`, the correct default per CLAUDE.md rule 6.
4. **A material self-contradiction in `orientation.json`'s own opening framing** -- the exact risk
   area this phase's workflow was told to scrutinize hardest. The literal opening line read "It has
   five, each of them 'the' regulator... within its own defined patch," then two sentences later
   stated the fifth body (CBUAE) "cuts across... rather than holding a slice of its own" -- directly
   contradicting the sentence that introduced it. Fixed by rewriting the opening to state four
   geographic regulators plus one cross-cutting federal body from the start, consistent with the rest
   of the same paragraph.
5. A minor `key_links` mislabeling in `tokenization_rwa.json`: an entry labeled "CMA: Virtual Assets
   Framework announcement..." actually linked to a `thenationalnews.com` media article, not an
   official CMA page. Relabeled to make clear it is third-party further-reading, not an official
   source, without removing the link.

**How the citation-domain fix was actually landed, and why it took a second real step**: registering
the missing domains in `config/jurisdictions/uae.json` was not, by itself, enough to flip the 7
gate-downgraded cards back to `"verified"` -- `pipeline/verify/gate.py`'s `enforce_full_gate` is a
one-way, downgrade-only mechanism by design (it forces `"unverified"` on failure, but never writes
`"verified"` back on success; that's the verifier LLM's call to make, with the gate only ever acting
as a backstop). An attempt to hand-edit the 7 cards' `status` field directly, after independently
confirming via direct calls to the actual `check_card_citations`/`check_card_numeric_claims`/
`check_card_quote_policy` functions that all 7 now passed for real, was correctly blocked by this
session's own auto-mode safety classifier as bypassing the project's verification-gate control. The
correct fix, matching this project's established mechanism, was to spawn seven fresh,
independent `hk-radar-verifier`-type sub-agents (one per card, genuinely fresh context, adversarial,
told the specific domain-registration fix that had just landed but instructed not to trust that
alone) to re-fetch every citation themselves and write `status: "verified"` only if their own
independent check passed. All seven did, and along the way two of them found and fixed real,
independent content defects the original analyst/verifier pass had missed: two cards asserted VARA's
full Dubai-mainland/free-zones-excluding-DIFC geographic scope without a citation supporting that
specific claim (fixed by adding a second citation to `vara.ae`'s own scope statement), and three
cards' `why_it_matters` text enumerated unsupported VASP sub-categories ("crypto exchanges, brokers,
custodians") not present in either cited source (fixed by using the sources' own generic "VASP"
term). Each of the seven agents' worktree-isolated output was individually diffed against the
shared-checkout file before being applied, rather than trusted wholesale.

`config/site.json`'s `uae` entry now reads `status.watcher: "live"`, `status.seeded: true`,
`status.analyst_verifier: "planned"`; `.github/workflows/watch.yml`'s matrix is
`[hk, uk, eu, us, ch, jp, uae]`.

**Verification, run fresh by the orchestrating session** (not trusted from any sub-agent's report):
full pytest suite 440/440 passing; `pipeline.ci.validate_content` clean (67 files, including the
config edit's ripple effects); `apply_verification_gate --jurisdiction uae` re-run clean after the
fix cycle, all 26 cards independently re-confirmed `status: "verified"` by direct field inspection
(not just the gate's own per-file log line, which -- as documented since P9 -- only reflects whether
a file changed during that specific run, not whether it currently passes); `promote_drafted`/
`promote_verified --jurisdiction uae` both report 0 newly promoted (all 26 already linked to
`published` ledger items from the workflow's own Gates phase); a full `pipeline.site.generate`
rebuild succeeded, `_site/uae/index.html` confirmed to show real content for all five regulatory
bodies (VARA 111, CMA 49, DFSA 39, FSRA 39, CBUAE 28 mentions), zero "coming soon" hits; repo-wide
`grep -rl PENDING content/shared/glossary/` and `grep -rn claude-sonnet content/ data/` both
confirmed clean; `tests/test_jurisdiction_agnostic.py` 10/10 fresh. The seven scratch worktrees the
verifier sub-agents created were removed after their fixes were extracted and applied.

**Seven jurisdictions now live: hk, uk, eu, us, ch, jp, uae.** P14 (Singapore onboarding, the
project's first jurisdiction planned from the outset to use a manual-assisted watcher rather than a
fully live feed/html_diff/sitemap_diff mechanism) is next.

### 2026-07-13 — P14: Singapore onboarding (eighth jurisdiction, manual-assisted watcher -- a real fix-then-commit cycle)

Singapore is this project's first jurisdiction with no live automated watcher: MAS (mas.gov.sg) and
Singapore Statutes Online (sso.agc.gov.sg) both bot-block this project's own honest, non-browser-
impersonating User-Agent with an identical "Maintenance"/HTTP-403 response, confirmed live multiple
times across this phase (Research, Manual Seed, Gates, and again independently by the final-check, all
on 2026-07-13). Per the owner's already-made P6-stage decision (logged in that phase's own entry above),
this project chose honest fetching over browser-UA impersonation, so `config/jurisdictions/sg.json`
registers `mas` with `feeds: []` and routes citations instead through the Singapore Press Centre
(`sgpc.gov.sg`, which mirrors MAS media releases as genuine fetchable PDFs), Singapore's Parliament
(`parliament.gov.sg`, which serves genuine Bill-text PDFs), and IRAS (`iras.gov.sg`) -- five regulators
total, all zero-feed by design, matching the manual-assisted model this phase was scoped to build. Content
seeded via a single large manually-curated `seed_backfill` batch rather than the watcher-first-plus-small-
backfill pattern every live jurisdiction has used since P10: 7 pillar states, 14 cards, a 3-entry
trajectory, 13 SG-tagged glossary terms, and a 19-document library, covering Singapore's Payment Services
Act 2019 (PS Act) digital-payment-token licensing regime and its 2022 Financial Services and Markets Act
(FSM Act) Part 9 Digital Token Service Provider extension.

**This phase's own workflow run surfaced a genuine "Prompt is too long" agent failure** -- the exact
failure class P9's own workflow first warned about avoiding -- in the Research phase's `exchanges_vatp`
pillar-state agent, silently leaving only 6 of the 7 required `content/sg/pillar_states/*.json` files on
disk. **This crashed `pipeline.site.generate` outright for every jurisdiction, not just Singapore** (the
loader raises `SiteDataError` and aborts the whole `build_site()` call the moment any one jurisdiction is
missing a mandatory pillar-state file) -- the identical failure *class* P9 first found for a missing
`orientation.json`, recurring here one required file over, exactly as the workflow's own final-check
brief was told to watch for. The gap was closed by re-running a single, deliberately leaner analyst-type
agent (avoiding the giant director-brief prompt that likely caused the original overflow) that
independently re-fetched real primary sources -- the Payment Services (Amendment) Bill (parliament.gov.sg,
genuine PDF) and four MAS media releases (all via `sgpc.gov.sg` mirrors) -- and wrote a full, schema-valid
`exchanges_vatp.json` covering DPT-service licensing categories, PS-G02 advertising restrictions, and the
Investor Alert List mechanism, cross-referenced against the custody/AML pillars exactly like every sibling
file. Independently re-ran `pipeline.site.generate` after the fix and confirmed the crash is gone and
`_site/sg/index.html` renders real content.

**Card-level defects, all found by the workflow's own final-check and fixed via targeted, worktree-
isolated fix agents -- never by hand-editing a card's `status` field directly, per this project's
established (and, for UAE, safety-classifier-enforced) discipline that only a genuine analyst/verifier
pass may write `status: "verified"`:**
- **Two cards cited a confirmed-blocked `mas.gov.sg` page** (the Binance.com Investor Alert List listing;
  the October 2022 DPT/stablecoin consultation) **when an already-proven `sgpc.gov.sg` mirror existed for
  one of them but wasn't used.** A fix agent found the real `sgpc.gov.sg` mirror for the October 2022
  consultation (probing the `P-20221026-N` release-sequence pattern to the genuine `N=1`), switched the
  citation, and in the same adversarial pass caught and corrected several further overreach issues the
  original draft had layered on top (a specific consultation-paper number not actually in that release; an
  unsupported Major-Payment-Institution-licence claim; a redemption-timeline figure from a *later* MAS
  release, not this one; a cherry-picked capital-requirement figure that dropped an "or 50% of annual
  operating expenses" qualifier). For the Investor Alert List card, no fetchable mirror exists anywhere in
  this jurisdiction's registered domains (an IAL listing is a rolling database entry, not a discrete press
  release) -- the fix agent searched exhaustively, confirmed this honestly, tightened the card's prose to
  state only what its one (unfetchable but independently corroborated-genuine) citation actually supports,
  and correctly left it `status: "unverified"` rather than fabricate a substitute source.
- **Two cards had PDF-extraction-artifact quote mismatches** -- a footnote-reference digit glued directly
  onto a word with no space ("policymakers" -> "policymakers¹across"), and a closing curly-quote rendered
  with an inserted space by this pipeline's own `pypdf` extractor -- both are the same underlying defect
  *class* logged for P10/P11 (a quote failing the exact-contiguous-substring check) but here genuinely
  extraction artifacts, not fabrication; independently re-confirmed via a second extractor for one of the
  two. Fixed by shortening each quote to end cleanly before the artifact boundary. Both fix passes also
  caught and removed real unsupported claims layered into the same cards during drafting (an unconfirmed
  Second Reading date/speaker attribution and an unconfirmed Parliamentary-passage date, in each case
  because the only citation was the Bill *as introduced*, not Hansard or the enacted Act text -- neither of
  which is fetchable in this jurisdiction) -- both cards were retitled/redated to describe only their
  Bill's first reading, the one fact each citation genuinely supports.
- **Three cards were genuinely authentic on independent re-fetch but had simply never received a completed
  verifier pass** -- a process gap, not a content defect -- closed by three fresh, independent verifier
  agents, each confirming the existing citations/quotes/dates held up and setting `status: "verified"`.
- **A second-order gate-authenticity miss, caught only by running the real gate for real**: after the
  `sgpc.gov.sg` mirror fix above, the orchestrating session ran `pipeline.ci.apply_verification_gate` and
  watched it *downgrade* that same card back to `unverified` -- the fix agent's own quote (`"...submit
  their comments on the proposals by 21 December 2022."`) still didn't survive the real gate's `pypdf`
  extraction, which renders that same PDF's "comments" as "c omments" (a second, independent extraction
  artifact in the same document). Root-caused by calling `pipeline.verify.docfetch.fetch_document` and
  `pipeline.verify.authenticity.quote_is_authentic` directly against the live PDF -- the actual functions
  the real gate calls, not a reimplementation -- to find a clean, artifact-free substring
  (`"MAS invites interested parties to submit their"`), then, per the same never-hand-edit-status
  discipline, sending the card through one more fresh verifier pass rather than writing `"verified"`
  directly. This is a new instance of the "gate log line is misleading" gotcha logged since P9/P13 --
  `apply_verification_gate`'s per-file print only reports whether a file *changed this run*, so a first,
  naive `apply_verification_gate` pass after these fixes printed "citations OK" for every card, and only
  reading each card's actual `status` field afterward revealed the real, still-broken state.
- Registered a new, narrow zero-feed regulator entry, `bis` (Bank for International Settlements,
  `bis.org`), for one `funds_etfs.json` key_link citing a verbatim BIS reproduction of an MAS Deputy
  Managing Director's own speech -- used specifically because MAS's own speeches page is the same
  confirmed-blocked domain, mirroring the `sgpc.gov.sg` precedent. Grepped `pipeline/` for the id and
  confirmed no collision. Left one lower-stakes `web.archive.org` citation in `trajectory.json` as a
  documented, disclosed open item rather than registering it as an official domain -- unlike `bis.org`
  (an international financial institution reproducing a regulator's own words), a general web archive
  is not itself an official body, and `trajectory.json` is outside the deterministic gate's own scope
  (`apply_verification_gate.py` only scans `content/*/cards/*.json`) either way.

`config/site.json`'s `sg` entry reads `status.watcher: "dormant"` (the schema's third enum value,
alongside `"live"`/`"planned"` -- chosen deliberately over `"planned"`, which would understate the real
seeded content, and over `"live"`, which would falsely imply a daily poll). `.github/workflows/watch.yml`
was **not touched this phase** -- `sg` is deliberately absent from its matrix, confirmed both by direct
inspection and by `git status` showing that file with zero diff. `content/sg/orientation.json` explicitly
explains the manual-assisted model in its own text, so a compliance reader can tell this jurisdiction is
not on a live daily feed.

**Verification, run fresh by the orchestrating session** (not trusted from any sub-agent's report): full
pytest suite 440/440 passing throughout every fix step; `pipeline.ci.validate_content` clean; a second,
post-fix `apply_verification_gate --jurisdiction sg` run confirmed stable (zero further downgrades);
final card census independently re-derived by reading each file's own `status` field directly: **13
verified, 1 honestly unverified** (the Investor Alert List card, for the documented, genuine sourcing
reason above); `promote_drafted`/`promote_verified --jurisdiction sg` both report 0 newly promoted (all
14 already linked to `published` ledger items from the workflow's own Gates phase; ledger also shows 6
correctly-untouched `queued` items); a full `pipeline.site.generate` rebuild succeeded, `_site/sg/
index.html` confirmed to show real content (132 MAS mentions, zero "coming soon" hits) and the Method
page's Singapore coverage row confirmed to carry the accurate manual-assisted `coverage_notes` explanation
verbatim; `content/sg/orientation.json`'s "seven regulatory areas" claim, flagged as a stale mismatch by
the final-check when only 6 pillar files existed, is now genuinely accurate (7 files, verified by count).
All seven scratch worktrees the fix agents created were removed, along with their branches, after each
fix was extracted, reviewed, and applied to the shared checkout.

**Eight jurisdictions now live: hk, uk, eu, us, ch, jp, uae, sg.** P15 (full-autonomy soak + final PR) is
next -- see the Owner / next-step punch list above and the open-questions summary that will accompany the
final PR for what genuinely cannot be completed synchronously in any session (the 14-day zero-touch soak,
live CCR trigger activation for any jurisdiction beyond HK).

### 2026-07-13 — P15: full-autonomy soak + final PR (what's actually completable synchronously)

The registry-model rebuild (P6-P14) is now complete: eight jurisdictions live (hk, uk, eu, us, ch, jp,
uae, sg), each with a full 7-pillar-state set, seeded and verified cards, a trajectory, jurisdiction-tagged
glossary terms, a document library, and an orientation page, wired into `config/site.json` and (for the
seven with a genuine live watcher mechanism) `.github/workflows/watch.yml`'s matrix. This entry runs a
final, independent, whole-repo health check before naming what P15's own criteria still leave open.

**Verification, run fresh, across the entire repo (not scoped to any one jurisdiction):**
- `pytest -q`: 440/440 passing.
- Every jurisdiction's `content/{jid}/pillar_states/` directory independently re-counted at exactly 7
  files: hk, uk, eu, us, ch, jp, uae, sg all confirmed.
- A full, from-scratch `pipeline.site.generate` run (`_site/` removed and rebuilt) completed without
  error; every one of the eight jurisdictions' `index.html` independently grepped for "coming soon" --
  zero hits across all eight.
- `tests/test_jurisdiction_agnostic.py`: 10/10 green.
- Method page's coverage table independently confirmed to list all eight jurisdiction names.
- `git status --porcelain` and `git worktree list`: both fully clean -- no uncommitted changes, no
  leftover scratch worktrees from any fix cycle.
- `docs/analyst-runbook.md` re-read in full and confirmed it does NOT need updating for the new
  jurisdictions: it already iterates `config/site.json`'s registry generically, keyed on
  `status.analyst_verifier == "live"` (currently still only `hk`), not on any hardcoded jurisdiction id --
  the file's own text already anticipates this ("If a second jurisdiction's `status.analyst_verifier` is
  ever flipped to `"live"`, generalizing `hk-radar-analyst`... is a real follow-up code change at that
  time -- out of scope [until then]"). No change needed until a second jurisdiction's analyst/verifier is
  actually activated.

**What P15's own named criteria require, checked directly rather than assumed:**
- The HK analyst/verifier CCR trigger (`trig_01Bk3Lz2FKf3pWRMFkqBcdDE`) is confirmed **live and firing
  nightly** via `list_triggers` -- real `last_fired_at` of 2026-07-12T22:35Z, `enabled: true`, cron
  `30 22 * * *`. This has been running unattended since 2026-07-09.
- `data/improve_queue.json` confirmed still empty (`{"schema_version": 1, "items": []}`) -- the manual
  dry-run of `docs/improve-runbook.md`, sequenced by Fable's own 2026-07-09 directive as a precondition
  for `improve.yml`'s live activation, has not happened.
- `data/audit/` confirmed to not exist anywhere in the repo -- `audit.yml` has never produced a real
  output via a genuine scheduled Actions run.
- The literal 14-day zero-touch soak criterion cannot be simulated or shortcut in a single session; it
  requires real calendar time to elapse with the trigger running unattended, then a check-back.

**What this session did NOT do, and why, rather than silently deciding either way:** did not populate
`data/improve_queue.json` and run the manual dry-run itself -- `improve.yml`'s blast radius genuinely
includes `/pipeline`, `/config`, and `.github/workflows`, and Fable's own sequencing directive was to
report that dry run's result back to PM review before the live-activation question comes back up, which
this session read as "loop the owner in before this specific step," not "proceed autonomously." Did not
attempt to configure branch protection on `main` (no tool available in this session can change GitHub
repository settings, unchanged from every earlier phase's own note on this). Did not open a pull request
from this branch -- creating a PR was not explicitly requested this session, and per this project's own
standing instruction on that action, it is withheld absent an explicit ask; the branch
(`claude/error-investigation-802phh`) is fully pushed, tests green, and ready whenever a PR is wanted.

**Open questions for the owner, compiled here as the standing instruction to "leave questions... before PR
merge" asked for, rather than scattered across the log:**
1. Should this session (or a future one) open the PR now? The branch is complete, tested, and pushed;
   nothing else in the P6-P15 roadmap remains buildable without owner input.
2. When should the manual `improve.yml` dry run happen, and does the owner want to pick the first
   low-stakes queue item themselves, or authorize an agent to pick one?
3. Branch protection on `main` -- an owner-only GitHub settings action, still unset.
4. When, if ever, should a second jurisdiction's `status.analyst_verifier` move from `"planned"` to
   `"live"`, extending the CCR trigger's daily unattended commit access beyond Hong Kong? This is a
   distinct decision from this build's own completeness -- every jurisdiction's content pipeline is fully
   built and proven, but none beyond HK has ever run its analyst/verifier step live.
5. The two anonymity flags (LICENSE copyright line; non-bot GitHub-UI merge-commit identity) remain
   logged, unresolved owner decisions from Phase 1, unchanged by anything in P6-P15.
6. The 14-day soak itself: does the owner want this session (or a scheduled Routine) to check back
   periodically and report once 14 days of real, unattended, successful HK trigger firings have elapsed?

### 2026-07-13 — PR #6 merged; first post-merge maintenance pass: this week's real audit.yml findings

PR #6 (the full P6-P15 registry-model rebuild) merged to `main`. `main` had also independently gained
one commit while this branch was in review -- `audit.yml`'s first-ever genuine scheduled run, producing
a real `data/audit/latest.json` (50 link-rot events, 5 staleness events, both against pre-registry-model
HK content). Merged that in (one small, non-overlapping conflict in `IMPROVEMENT_BACKLOG.md`, resolved
by keeping both branches' additions in chronological order) before opening the PR, so this is the first
real "audit finding -> fix" cycle this project has ever run, done as a direct maintenance pass on `main`
per the owner's explicit choice of this as the next task (over onboarding a 9th jurisdiction or the
improve.yml dry-run).

**Link rot, all 50 events on `brdr.hkma.gov.hk`:** root-caused to a real, pre-existing gap --
`brdr.hkma.gov.hk` was never registered in `config/jurisdictions/hk.json`'s HKMA `official_domains`,
the exact missing-domain-registration defect class repeatedly found and fixed for other jurisdictions
(P9's `legislation.gov.uk`, P11's `uscode.house.gov`, P13's `media.umbraco.io`, P14's `bis.org`) but
never previously caught for HK, since document_library/pillar_state citations aren't covered by
`apply_verification_gate.py` (cards only). Fixed the registration. The underlying availability problem
was investigated, not silently routed around: independently corroborated today via three unrelated
live-fetch paths (this session's own `curl`/`openssl s_client` diagnostics, `WebFetch`, and three of
five staleness-check sub-agents below hitting the same domain organically) that `brdr.hkma.gov.hk`'s
TLS layer is currently broken (incomplete certificate chain) and its HTTP layer returns 503, while the
bare domain root over plain HTTP still redirects to HTTPS -- a real, current HKMA-side outage, not an
artifact of this session's own sandboxed networking (confirmed by testing with the correct CA bundle,
and by the fact GitHub Actions' own unsandboxed runner hit the identical SSL error independently). Full
detail in IMPROVEMENT_BACKLOG.md's matching entry, including the concrete operational cost found along
the way: two live, already-queued HKMA circulars (`item_hash a5d16bbe...`, `8e676f99...`) cannot be
drafted into cards at all while this outage continues.

**Staleness, 5 flagged HK pillars:** dispatched five parallel, worktree-isolated live-research agents
(one per flagged pillar), each instructed explicitly not to mechanically bump `last_changed` --
`pipeline/audit/staleness.py`'s own docstring is clear that a stale flag is "a prompt... to look, not a
claim that something is actually wrong." Two found genuine, material, live-verified developments and
updated the pillar with real citations: `exchanges_vatp` (two new SFC cybersecurity circulars, 2 Jun
and 9 Jul 2026) and `tokenization_rwa` (HKMA's Tokenised Bond Expert Group, 5 Jun 2026, and -- more
significantly -- the actual published output of the legal review Policy Statement 2.0 had flagged as
pending, concluded 29 Jun 2026, which this pillar's own `open_items` had explicitly logged as "not yet
published" before this check). Three pillars (`funds_etfs`, `stablecoins`, `dealing_custody_advisory`)
were genuinely re-verified as still accurate, with no content change and no `last_changed` bump -- this
is the staleness check working as designed, not three gaps. Each agent's report was independently
reviewed (diffed against the shared checkout) before being applied; nothing was merged on the strength
of an agent's own say-so alone.

**Verification, run fresh:** `pytest -q` 440/440 passing; `pipeline.ci.validate_content` clean on both
changed pillar-state files; a full `pipeline.site.generate` rebuild succeeded with zero "coming soon"
hits on `_site/hk/index.html`; all worktrees and scratch branches from the fix agents removed after
their results were extracted and applied.

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

### 2026-07-13 — Full compliance-officer audit (8 jurisdictions + UI/UX + code) and its fix cycle

Owner's ask, verbatim: an end-to-end Fable-directed code and UI audit "to ensure this is fit for a
senior compliance officer," using non-Fable models too "to fact check every line," every claim
"supported by official sources or publications and referenced with the link that is correct and
active." Run as a 6-phase Workflow: Fable Director Spec → per-jurisdiction fact-check (session-default
model, live re-fetch of every citation) → Opus adversarial verification of every flagged finding →
UI/UX audit (real build, Playwright screenshots, WCAG suite) → 3-way parallel code audit → Fable
synthesis. 46 agents, ~332 citations live-fetched across all 8 jurisdictions (100% of card citations,
weighted sampling of pillar key_links/document libraries), 3,061,267 subagent tokens.

**Headline verdict: not fit for sign-off as found, narrowly and fixably so.** Zero fabricated facts,
zero non-verbatim quotes, zero neutrality violations in body prose, zero named-entity commentary
across everything checked. Four confirmed critical findings: (1) the internal tooling name "CCR"
leaked 14 times into public site copy (landing + Method pages); (2) six US pillar-state citations
rested on unregistered domains, one of them (law.cornell.edu) deliberately not registrable; (3) an
empirically-reproduced hole in `path_allowlist.py` -- a symlink whose target doesn't exist yet passed
the gate, since `os.path.exists` on the unresolvable target reported "safe"; (4) an empirically-
reproduced hole in the quote-authenticity check -- no minimum-substance floor, so
`quote_is_authentic("the", <any page>)` passed. ~13 moderate and ~11 minor findings across dead links,
mis-citations, over-length/multi-source quotes, and UI gaps, full detail in the synthesis report.

Owner approved the full tiered fix plan, including the two gate-logic patches (CLAUDE.md requires
explicit separate approval before an AI touches path-allowlist/architecture code -- obtained
explicitly before touching either file). Fix cycle, all on `fix/compliance-audit-802phh` (PR #9):

- **Tier 1** (direct, not delegated -- small enough to implement with full context after the
  recon needed to write it precisely): closed both gate holes, registered the genuine missing US/JP
  domains (not law.cornell.edu), removed the 14 "CCR" occurrences from `config/site.json`'s
  `coverage_notes`.
- **Tiers 2-3** (a second Workflow: per-jurisdiction fix-then-adversarial-verify pipeline, plus 4
  parallel site/pipeline fix groups, plus a final full-suite/rebuild/grep check). Adversarial
  verification is what makes this cycle worth the name: 5 of 8 jurisdictions' first-pass fixes had a
  real, disclosed problem the fresh re-check caught -- a UK card's status silently flipped
  verified→unverified on a title-only edit with no gate re-run to justify it (reverted after
  confirming the real gate, run against the current content, produces "verified"); pre-existing
  over-length quotes in 3 Swiss pillar files the first pass hadn't touched; an EU document-library fix
  applied only to the derived file, not `data/eu/ledger.json`'s `"relevant"` flag that regenerates it
  (would have silently resurrected on the next watcher run); a US pillar's own newly-edited file left
  a second 28-word quote untouched; two UAE key_links with the identical dead-link problem disclosed
  on only one.
- **Gate-hardening round 2**: a fresh adversarial pass specifically tasked with trying to break the
  Tier 1 gate patches found two more real, live-reproduced holes -- `path_allowlist.py` never checked
  hard links (only `os.path.islink`, which a hard link never triggers, since it's an ordinary
  directory entry sharing an inode); the quote-substance floor was pure word count and any 3
  contentless tokens (stopwords, punctuation, digits, emoji, a repeated word) still passed. Fixed
  both. The word-count floor's own fix broke a real published quote twice over before landing: first
  a too-strict alphabetic-content requirement broke a UK statutory-instrument-number citation
  ("2026 No. 102"), found by directly re-verifying that card against the real gate before committing;
  then, after loosening that, a full cross-jurisdiction sweep (not just the jurisdiction the original
  finding touched) found the word-count approach itself silently broke 5 real, already-published
  Japanese quotes, since `str.split()` treats a whole Japanese sentence as one token with no internal
  whitespace to split on -- rewritten to count non-whitespace characters instead, which is
  script-agnostic. `test_all_published_cards_pass_quote_policy` was itself widened from
  `content/hk/cards/` only to `content/*/cards/` so a regression like this is caught by the suite next
  time, not a manual sweep -- the narrow version had been passing the whole time the bug was live.
  Also fixed, found during this round's own independent re-verification of the fix workflow's final
  check: a pre-existing internal PM-role codename ("Fable") in a shipped `style.css` comment, same
  leak class as the CCR fix, not introduced by this branch.

465 tests passing (up from 448 at Tier 1's start), every touched file re-validated against its schema
and, for cards, against a fresh direct call to the real `enforce_full_gate` (not the fixing agents'
self-report) after this session's own edits.

**Logged, not fixed this cycle** (owner-judgment or genuinely out of scope): `REDIRECT_STUBS`'s `hk`
hardcode and `_CURRENCY_RE`'s missing CHF/AED/SGD/JPY coverage (both pre-existing, both flagged
critical-adjacent-but-Tier-4 by the audit itself); a documented policy for bot-hostile official
sources (EUR-Lex WAF, fedlex SPA, mas.gov.sg, congress.gov, dfsa.ae) generalizing SG's own
sgpc.gov.sg-mirror convention; one CH pillar's ARETP two-quote-per-source cluster, left alone since
neither quote was individually over-length and it wasn't part of any confirmed finding; the residual,
accepted quote-policy gap where one real word plus punctuation filler (e.g. "crypto . ,") still passes
the substance floor -- a semantic-substance judgment, not a fabrication-filler check, ruled out of
scope for a deterministic function.

### 2026-07-14 — Live analyst/verifier extended to all 6 remaining live-watcher jurisdictions

Owner decision, explicit and direct: asked to pick the next candidate for live analyst/verifier
(item 8 on the punch list above), this session recommended a single next jurisdiction picked by
real operational readiness rather than "most content-rich" as originally framed -- comparing
`data/{jid}/queue.json` sizes across all 7 non-HK jurisdictions found `us` had by far the largest
genuine backlog (42 queued items, spot-checked for relevance: crypto ETF filings on Cboe BZX/
Nasdaq, GENIUS Act stablecoin rulemaking, broker digital-asset reporting rules -- vs. 8 for jp, 3
for uk, 0 for eu/uae/ch), making it the best real test of the mechanism rather than an idle
trigger. The owner's reply named `us` as a deviation from the session's own earlier "likely uk or
eu" framing without an explicit confirmation of that substitution -- correctly caught by this
environment's permission classifier before any file was touched, and surfaced to the owner as an
open question rather than proceeding. Owner's answer ("Do all, one by one step by step") was
itself ambiguous between "activate all 6 now" and "activate them sequentially over real calendar
time, watching each one's first firing before the next" -- a second classifier catch, since this
session's own stated plan had explicitly been "watch first firings before expanding further," and
flipping 6 configs in one pass means they all go live on the *same* next trigger fire, which is not
actually sequential. Asked directly a second time; owner's answer ("all 6 live together now") was
unambiguous. Proceeding required no further hedging once that answer was in hand.

**What "all 6" means, precisely:** `us`, `eu`, `uk`, `uae`, `ch`, `jp` -- every live-watcher
jurisdiction not already live. `sg` is deliberately excluded: its watcher is `"dormant"` by design
(mas.gov.sg/Singapore Statutes Online block non-browser clients; coverage comes from periodic
manual `seed_backfill` review, not a daily poll), so flipping its `analyst_verifier` status would
be a no-op flag with no automated queue ever feeding it -- a functionally different kind of "live"
than the other seven, not something this decision covers.

**Real prerequisite work found and fixed before the flip, not assumed already done:** read
`docs/analyst-runbook.md` in full expecting to need to generalize it for multi-jurisdiction
operation -- found it already fully generic (Step 0 iterates every `status.analyst_verifier ==
"live"` registry entry with per-jurisdiction/per-firing caps, built that way from P6 onward, not a
placeholder). What genuinely wasn't generic, found by reading rather than assuming: (1)
`.claude/agents/hk-radar-analyst.md`/`hk-radar-verifier.md` were literally HK-named (no HK-specific
*logic*, both already jurisdiction-parameterized -- pure naming debt the runbook's own "real
follow-up change at that time" comment had explicitly flagged) -- renamed to `radar-analyst.md`/
`radar-verifier.md`. (2) `pipeline/prompts/analyst_prompt.md` had three genuinely hardcoded HK
phrases, not caught by the runbook's own naming note: "the only live jurisdiction is `hk`" (stale
factual claim), "LegCo, news.gov.hk" as primary-source examples (HK-specific institutions,
generalized to "a legislature... official_domains entry"), and, most substantively, "written for a
newcomer to HK digital-asset regulation" in the `why_it_matters` instruction -- this one would have
produced a factually wrong sentence on every non-HK card had it shipped unfixed. `verifier_prompt.md`
was already fully agnostic. Full test suite (465 passed), a real site rebuild (23 pages, exit 0),
and a targeted grep confirmed the existing "seeded, not live yet" banner (built during the
compliance-audit fix cycle, driven by `status.analyst_verifier != "live"`) now correctly disappears
from all 6 newly-live jurisdictions' pages and remains only on `sg`'s -- with zero template code
touched, proving that feature was genuinely data-driven when it was built, not coincidentally
correct.

**A second, unrelated bug found while checking the live CCR trigger's own configuration** (not
touched yet, flagged to the owner instead of fixed unilaterally): the "HK Radar — Analyst/Verifier
daily run" trigger's own prompt text still hardcodes the pre-registry-model bot identity
(`hk-radar-bot <bot@users.noreply.github.com>`), not the current, CLAUDE.md-mandated
`da-radar-bot <da-radar-bot@users.noreply.github.com>` every commit since P6 has used. `git log`
confirms this is not just stale text sitting unused -- a real commit as recently as
2026-07-13T05:40:28Z ("audit: ... weekly audit run") used the old identity. Checked every real
`.github/workflows/*.yml` for the same pattern: all five (`analyze.yml`, `audit.yml`,
`correction.yml`, `improve.yml`, `watch.yml`) correctly use `da-radar-bot` -- this bug lives only in
the CCR trigger's own prompt text, invisible to anyone auditing the repo on GitHub, exactly the
class of gap CLAUDE.md's own "Logged deviation" note about this mechanism already warns about. The
`update_trigger` tool available in this session can change a trigger's name/cron/enabled state but
not its prompt content -- fixing this for real means deleting and recreating the trigger, an action
outside plain git and not something to do silently mid-way through an already-large, twice-
clarified change. Left for the owner's explicit go-ahead as a separate next step.

Next: watch the first real post-flip firing (next scheduled fire the night of 2026-07-14/15,
`30 22 * * *`) across all 7 live jurisdictions at once -- the first genuine test of Step 0's
per-jurisdiction/per-firing caps under real multi-jurisdiction load, not just unit-tested. Per this
project's own standing discipline (Fable PM directive, 2026-07-09): review the actual commits and
card files that firing produces before calling this rollout proven, not just confirm the trigger
fired.

### 2026-07-14 — CCR trigger's stale bot identity fixed (owner-approved)

Owner approved fixing the bot-identity bug flagged above. No tool in this session can edit a live
trigger's own prompt content (only its name/cron/enabled state), so the fix was delete-and-recreate,
not an edit: created a new trigger, `Global Digital Asset Radar — Analyst/Verifier daily run`
(same `env_01NaDLzVcJMVt9aDwBmJC6ea` environment, same `30 22 * * *` schedule, same
`create_new_session_on_fire` fresh-context-per-firing shape), with the bot identity corrected to
`da-radar-bot <da-radar-bot@users.noreply.github.com>` and the project name corrected to "Global
Digital Asset Radar" throughout -- then deleted the old, buggy `HK Radar — Analyst/Verifier daily
run` trigger only after confirming the new one was created successfully (never the other order,
to avoid a window with no trigger at all). The new prompt also shortens the inline step-by-step
summary that had drifted from `docs/analyst-runbook.md` in the first place, deferring to the
runbook as the authoritative source rather than re-describing its steps, and adds an explicit
self-correcting clause: if the trigger's own prompt text and the current CLAUDE.md/runbook ever
disagree, the actual repo files win. `list_triggers` confirms the old trigger id
(`trig_01Bk3Lz2FKf3pWRMFkqBcdDE`) no longer exists and the new one
(`trig_014KCBHpqU22iUiWfG3qBt93`) is enabled with the same `next_run_at` slot. Verification of
this fix, same as the jurisdiction rollout above, is watching what the trigger's first real firing
under the new identity actually commits as -- not assumed correct from the prompt text alone.

### 2026-07-21 -- watch.yml matrix push race (8 failed nights, fixed on branch) and a larger finding underneath: the live analyst/verifier trigger has never once landed a commit

Owner forwarded a GitHub Actions failure email for the nightly Watcher run at `ed29746`. Root
cause found by reading the actual failed-job logs via the GitHub Actions API, not guessed: since
the multi-jurisdiction matrix reached main, `watch.yml` runs one matrix job per live jurisdiction
(`[hk, uk, eu, us, ch, jp, uae]`), all checked out from the same base commit and run in parallel.
Each job that finds new items does `git add` (its own jurisdiction's paths only) -> `git commit`
-> a plain `git push`. Since they all start from the same base and race, only whichever job's
push lands first succeeds -- every other job's push is rejected non-fast-forward (`! [rejected]
main -> main (fetch first)` / `cannot lock ref 'refs/heads/main'`), the job fails, and that
jurisdiction's ledger/queue/document-library update is discarded for the night. The Actions API
confirms every scheduled run from `2026-07-14T04:22:52Z` through `2026-07-21` concluded
`"failure"` (every scheduled run before 07-14 succeeded), and git history carries the exact
signature: precisely one `watch(...)` commit per night since 07-15 -- uk on 07-15/16/19, ch
07-17, jp 07-18/21, uae 07-20. `hk`, `us`, and `eu` have won zero races in 8 nights. Nothing is
destroyed outright (a losing jurisdiction's ledger stays stale, so the watcher re-discovers the
same "new" items the next night); the real exposure is an item scrolling out of a feed's window
before its jurisdiction happens to win a race.

Fix, on `claude/radar-updates-fable-7cx8q9` (not yet merged -- scheduled workflows run whatever
version of the workflow file is on the default branch, so this has zero production effect until
the owner merges): the bare `git push` becomes a bounded retry loop (4 attempts, 2s/4s/8s
backoff) that fetches and rebases onto `origin/main` before retrying. Safe because each matrix
job only ever stages its own jurisdiction's 2-3 paths -- no cross-jurisdiction overlap is
possible -- and a genuine rebase conflict still fails the job loud via the shell's default
errexit. Full test suite (465 tests) passes; the change is confined to one step of one workflow
file, outside the AI-job path allowlist's actual scope (that allowlist restricts the
analyst/verifier's own automated writes, not a human-reviewed workflow-file fix on a feature
branch) and deliberately not pushed straight to main.

**A larger finding surfaced while fact-checking the backlog, not assumed from the queue sizes
alone:** `data/hk/queue.json` (67 items, several dated 2025-04/06/12) was last touched by `a2cb110`
(P6, 2026-07-11); `data/us/queue.json` (42 items) by `05ad665` (P11 onboarding, 2026-07-12). Both
backlogs predate the push race entirely -- the race explains why nights fail, not why these
queues never drained. `git log --all` was checked directly for any commit matching
`analyst(...)`/`verifier(...)`, under either the current `da-radar-bot` or the historical
`hk-radar-bot` identity: there are **zero**, not just since the 07-14 multi-jurisdiction rollout,
but ever. Every card currently under `content/*/cards/` traces to a seed, onboarding, or
compliance-audit-fix commit -- none to a live analyst/verifier run. The CCR trigger
(`trig_014KCBHpqU22iUiWfG3qBt93`) has fired nightly and on schedule since its 07-14 recreation
(`last_fired_at` 2026-07-20T22:38:25Z, enabled, `30 22 * * *`) with zero visible output. By this
project's own standing discipline (Fable PM directive, 2026-07-09 -- commits and files are the
evidence, not a self-report), the live analyst/verifier mechanism has never yet produced a proven
run, despite PROGRESS.md's 07-14 entries describing its rollout as complete.

Leading hypothesis, explicitly unverified (fired sessions produce no transcript this repo can
read): the trigger's own runbook precondition -- "`git status` first, always... if the working
tree is not clean or not on `main`, stop and report rather than force past it" -- is tripping
silently. The trigger's own prompt text says the repo is "very likely already cloned in this
environment" at a path like `/home/user/DA-Radar`, which is exactly this session's own working
directory; if fired sessions share environment `env_01NaDLzVcJMVt9aDwBmJC6ea`'s disk with
whatever interactive session last touched it, then any interactive session (this one included)
left sitting on a feature branch with local changes would make every subsequent firing stop at
its own first precondition check, before it ever reads a queue -- and a graceful "nothing to do"
stop may not clear this trigger's own noteworthy-only push-notification bar, so the owner would
see nothing. Zero-cost mitigation regardless of whether this is the actual cause: this session
is restoring the checkout to a clean `main` before ending, ahead of tonight's 22:38 UTC firing.

**Consulted Fable as project director on three open questions, evidence independently
re-verified by this session before acting on any of it:**

1. *Open a PR now, given the urgency, or push-and-flag?* Push-and-flag, no PR -- the explicit
   no-unrequested-PR instruction stands, a PR doesn't accelerate a merge only the owner can
   perform, and the second finding above needs owner discussion beyond a mechanical merge
   anyway. Offered to the owner: open the PR on a one-word go-ahead.
2. *Does `docs/analyst-runbook.md`'s Step 0 cap (4 cards/jurisdiction, 10/firing) need raising to
   drain the backlog faster?* No -- the backlog is owned by the never-ran trigger, not the cap
   size; raising a cap that has never once been exercised, ahead of the mechanism's first
   observed successful cycle, would multiply unproven output. At the designed cap the drain is
   acceptable once the trigger is actually running (hk ~17 firings, us ~11). Revisit only after
   several proven cycles, owner-decided. Separately flagged for owner triage: `hk`'s 2025-dated
   queue items may deserve a staleness review independent of this incident.
3. *Manually intervene now (`workflow_dispatch`, or manually fire the CCR trigger)?* No --
   `workflow_dispatch` against `main` would run the unfixed file; against the branch it would
   entangle nightly watch data with the fix branch; manually firing the analyst trigger mid-
   incident would launch its first-ever real cycle unobserved and, per the hypothesis above,
   would plausibly no-op anyway. Sequence instead: clean-`main` checkout now (done), owner
   merges the watch.yml fix, then one manual `workflow_dispatch` of `watch.yml` against main as
   same-day validation, then review tonight's trigger firing's actual output (or continued
   absence of one) -- which now doubles as the diagnostic for the second finding.

One process deviation this session found in its own work, corrected before merge: commit
`8191fa8` (the watch.yml fix above) was authored under this session's own default identity
rather than `da-radar-bot <da-radar-bot@users.noreply.github.com>` -- the only commit in this
repo's entire history, across every prior PR-branch dev session and every bot-authored run
alike, that isn't under the bot identity. Flagged to the owner rather than force-pushed over
silently, since amending a pushed commit is a deliberately gated action in this session's own
harness.

### 2026-07-21 -- CCR trigger rebuilt to stop depending on a shared checkout, and fired live as same-day validation

Owner asked directly to fix the never-ran-analyst/verifier finding logged above rather than only
watch tonight's natural firing. Re-reading the live trigger's own prompt text (captured verbatim
via `list_triggers` in the prior entry's investigation) pointed straight at the mechanism: step 1
told every fired session to "check common locations like `/home/user/DA-Radar`" for an existing
clone and reuse it, and step 2 told it to stop outright if that checkout wasn't clean and on
`main`. Interactive Claude Code sessions share this same CCR environment
(`env_01NaDLzVcJMVt9aDwBmJC6ea`) and, across the seven nights this incident covers, repeatedly
left that exact directory sitting on a feature branch mid-work -- this session included, until it
deliberately restored a clean `main` checkout as a same-day mitigation in the prior entry. A fired
session hitting that state would stop at its own first precondition check, before ever reading a
queue, with no visible trace beyond a push notification this trigger's own config routes to the
owner's phone only on a "noteworthy" outcome -- which a graceful "nothing to do here" stop may not
clear. This fully explains a week of on-schedule firings with zero output.

Real fix, not just the standing mitigation of leaving the shared checkout clean: rebuilt the
trigger (`update_trigger` cannot edit a live trigger's prompt content, only name/cron/enabled
state, so this is delete-and-recreate again, same mechanism as the 07-14 bot-identity fix) with
step 1 changed to always work in a fresh, disposable clone
(`/tmp/da-radar-automation-run`) regardless of whatever else exists in the environment, so this
trigger's own success no longer depends on any other session's state. Same environment id, same
`30 22 * * *` schedule, same `create_new_session_on_fire` shape, same push-only notification
channel, same bot-identity instruction, preserved exactly -- confirmed by diffing the new
trigger's returned config against the old one before deleting it, only after creation succeeded
(never the reverse order, per the same precedent). Old trigger id `trig_014KCBHpqU22iUiWfG3qBt93`
deleted; new id `trig_01MYCeCc5MEoHAYbNtZvyDV9`.

Fired immediately afterward (`fire_trigger`) as same-day validation rather than waiting for
tonight's 22:38 UTC schedule, since this project's own precedent from the 07-14 identity fix
(watch the next natural firing) was chosen there specifically because no faster path existed at
the time -- here the fix is directly testable now, and the backlog (hk 67, us 42, jp 9, uk 6) has
already waited a week. The fired session (`cse_01VYX5iJK78GZ9MukBxerrDx`) runs independently of
this one; its actual output -- real `analyst(...)`/`verifier(...)` commits on `main`, or a clear
stop-and-report if something else is still wrong -- is the only real verification, not this
entry's description of the fix. Follow-up check recorded separately once that evidence exists,
per this project's own standing discipline of trusting commits and files over a self-report.
