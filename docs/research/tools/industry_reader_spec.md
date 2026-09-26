# Industry source reader spec

Purpose: fill commercial gaps the official Hong Kong sources cannot (fees, margins, volumes, costs,
market sizes, competitor economics, foreign-regulator facts) with named, checkable, non-official sources.

## What qualifies
- publisher_type one of: `international_official` (BIS, FSB, IOSCO, BCBS, IMF, OECD, World Bank),
  `foreign_regulator` (MAS, VARA, and other regulators' own sites), `consultancy` (e.g. KPMG, EY,
  Deloitte, Oliver Wyman, Accenture), `bank_research` (e.g. Citi GPS, J.P. Morgan, Standard Chartered),
  `association` (e.g. GFMA, ASIFMA, FSDC, HKAB), `listed_filing` (a listed firm's annual/interim report
  or exchange filing — its own figures only), `data_provider` (e.g. rwa.xyz; public dashboards).
- Must have: a named publisher, a date, a stable URL, and readable text we can capture.
- Prefer the most recent edition; prefer sources that state their method.
- Not allowed: anonymous blogs, press coverage as a source for numbers (go to the original), social
  media, paywalled text we cannot read, vendor marketing with no method.

## Capture
Work in the `industry/` folder. Put candidates in `inventory/<batch>.json` as
`[{"url":..., "title":..., "date":"YYYY-MM-DD", "src":"<publisher>"}]` and run
`python3 fetch_corpus.py inventory/<batch>.json` (writes `text/<id>.txt`, `meta/<id>.json`,
id = first 12 hex of sha1(url)). If a site blocks access (403/000), drop it; never bypass TLS.
Text is never committed.

## Registry entry (one JSON per line in `registry/<batch>.jsonl`)
```
{"id", "url", "title", "publisher", "publisher_type", "sponsor" (who paid/commissioned, or "none stated"),
 "conflict" (true if the publisher sells the product measured), "date", "geography" (global/Asia/HK/SG/UAE…),
 "topics" [...], "summary" (own words, 2–4 sentences),
 "figures": [{"metric", "value", "unit", "as_of", "scope", "estimate_type": reported|survey|modelled|forecast,
              "definition" (what exactly is counted), "locator" (page/section/chart), "note"}],
 "methodology_note", "caveats", "quote" (≤15 words, optional), "capture_date", "review_by" (date +12 months)}
```
Rules: own words (no 8+ word runs); every figure has a locator where it appears in the captured text;
mark forecasts as `forecast`; note if a global figure is being used for Hong Kong questions.
For `foreign_regulator` entries, figures may be empty; key rules go in `summary` + a `rules` list of
`{"point", "locator"}`.

## Verify
A second agent re-opens `text/<id>.txt` for each entry and checks every figure, locator, date and the
publisher_type/sponsor fields; fixes in place; appends to `registry/<batch>.verify.md`.
