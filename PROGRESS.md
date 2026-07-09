# PROGRESS.md

Running, dated log of what has been built and verified. Read this first in any fresh session —
along with `git log` — to know exactly where the project stands before doing anything else.

## Phase status

- **P1 — Chassis:** in progress
- P2 — Analyst + verifier: not started
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

*(Further entries appended as each build stage lands — config, schemas, watcher modules, tests,
the live watcher run and its idempotent re-run, and final sign-off.)*

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
(PM) kickoff review" section for the specifics of each. Checkpoint 2 (post-pytest-green,
post-live-verification) will report back against Fable's stated sign-off criteria before Phase 1
is declared done.
