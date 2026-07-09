# PROGRESS.md

Running, dated log of what has been built and verified. Read this first in any fresh session —
along with `git log` — to know exactly where the project stands before doing anything else.

## Phase status

- **P1 — Chassis: complete** (signed off by Fable PM checkpoint 2, 2026-07-09)
- **P2 — Analyst + verifier: deterministically complete, live-LLM-unverified** (see 2026-07-09
  entry below — designed and fully tested, but blocked on `CLAUDE_CODE_OAUTH_TOKEN` for an actual
  live run, same shape as Phase 1's pre-merge blocker)
- P3 — Seed backfill: not started
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

*(Further entries appended as Phase 3+ work lands.)*

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
