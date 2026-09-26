# HKDA Brief — build notes (handoff state, 26 Sep 2026)

## Owner decisions (final)
- Name: **HKDA Brief**. For the owner only. Hosted as a **private Claude artifact**, opened on the owner's own devices.
- Updates: a **scheduled Claude routine** (cloud; computer can be off). GitHub repo `0xfanbase/DA-Radar` = private storage + history (owner will switch it to private). No GitHub Pages.
- English only. Audience: head of compliance (digital assets) at a HK bank; goal = talk clearly to CCO, business, CEO, Risk.
- Design: reading-first, cream background #FAF9F5, mobile + desktop, every line fact-checked, citations name the paragraph and link to the official document.
- Tabs: Home (map + start here) · Learn (21 modules) · Projects (initiative profiles) · Documents (all 737 sources, sortable/filterable, links to official pages) · Glossary/Timeline.

## Where things are
- Proposal (published): https://claude.ai/artifact/WFz8kEwZiUJgYcCsrrvii5 — source `docs/proposal.html`.
- **Site (published, private):** https://claude.ai/artifact/5qZ2jZ78frrNL8LL67ZzDM — source `site/app/`, data built by `python3 site/build.py`. Republish via `url`.
- Source registry: `docs/research/source-registry.jsonl` (737 entries; fields: id, title, issuer, date, doc_type, importance, applies_to, status_as_of_2026_09_25, summary, key_points[{point,locator,modal}], bank_relevance, bank_compliance_angle, topics, source_url, deep_link_base, quote, flags, parent_id).
- Module briefs (verified): `docs/modules/*.md` (A1–A3, B1–B3, C1–C7, D1–D5, E1–E3). Citation syntax `[S:<12-hex id>, <locator>]`.
- Research method, tools, gaps: `docs/research/METHOD.md`, `docs/research/tools/`.
- Research scratch (not in repo, session-local): full source text corpus used for verification.

## Stage 1 build plan
1. Data build script → `site/data/*.json` (registry trimmed, modules parsed, projects, glossary).
2. Project profiles (~15) written from verified modules + registry, then verified.
3. Single-page app (vanilla JS, hash routes with plain tokens e.g. `#m-C3`, `#docs`, `#p-ensemble`), multi-file artifact.
4. Publish as new private artifact "HKDA Brief"; then set up routine and fire one test run.

## Rules to keep
Official sources only; own words (no 8+ word copying; ≤15-word quotes); keep modal force; status chips with as-of date; no advice/predictions; named entities only as regulator states; footer disclaimer on every page; bot commit identity via env vars.
