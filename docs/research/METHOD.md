# How the research corpus was built (25 September 2026)

This folder holds the evidence base for the Hong Kong bank-compliance guide. It records what was read,
how, and what could not be reached. Extracted source text is **not** committed ("link, don't republish").

## 1. Listing every publication

Each official source was listed through its own index, then filtered for digital-asset relevance
(virtual assets, crypto, stablecoins, tokenisation, DLT, CBDC/e-HKD, Ensemble, mBridge, digital bonds,
custody, staking, CARF and related terms).

| Source | Method | Tool |
|---|---|---|
| HKMA press releases | HKMA open API `api.hkma.gov.hk/public/press-releases`, full history | `tools/enum_apis.py` |
| SFC circulars, news, consultations | SFC e-distribution search API (POST), 2017–2026 | `tools/enum_apis.py`, `tools/enum_consult.py` |
| GovHK press releases (FSTB, LegCo replies, IRD, mirrors) | Daily index pages `info.gov.hk/gia/general/YYYYMM/DD.htm`, 2017–2026 | `tools/enum_govhk.py` |
| HKMA circulars, guidelines, SPM modules | Banking Regulatory Document Repository (BRDR) search, 35 keyword searches plus the "Virtual assets" topic | research agent |
| HKMA speeches, inSight, hub pages | hkma.gov.hk site search and topic hubs (stablecoin issuers, CBDC, fintech, bond market) | research agent |
| SFC codes, guidelines, FAQs, registers; FSTB; LegCo; HKEX; Policy Address; Budget; Gazette; IRD; FSDC | Site crawls and targeted searches | research agent |

## 2. Reading

- `tools/fetch_corpus.py` downloaded every item and its attachments (SFC appendices, HKMA annexes,
  BRDR PDFs) and extracted text with page markers. 948 files, about 26 million characters.
- Duplicates were removed by content hash. 737 unique documents were read in full by reading agents
  following `tools/reader_spec.md`. Very large general documents (for example whole SPM modules or a
  Policy Address) were searched for every digital-asset passage, and those passages were read in full.
- The most bank-critical documents (HKMA AML/CFT Guideline for AIs, SPM CRP-1 and the capital package,
  the HKMA 27 May 2026 custody package) were read by a stronger model for accuracy.

## 3. The source registry

`source-registry.jsonl` has one entry per document: exact title, issuer, date, document type, status as
of 25 September 2026, who it applies to, what it supersedes, a summary and key points in our own words
with paragraph/page locators and the source's modal force, why it matters to a bank compliance head,
and a structured bank-compliance angle (obligations, controls, notifications, counterparty due
diligence, board escalation).

Quality gates (`tools/qa_registry.py`, `tools/qa_canon.py`):
- no run of 8 or more consecutive words copied from the source (official titles excepted);
- at most one quote of 15 words or fewer;
- every key point has a locator;
- status from a closed vocabulary.
Entries that failed were rewritten. The final registry passes all checks.

## 4. Module briefs

`../modules/` holds 21 briefs written to `tools/module_spec.md`. Each was then checked by a separate
verifier (`tools/verify_spec.md`) that opened the cited paragraph of every claim. Logs are in
`../modules/verification/`. `tools/qa_modules.py` checks citations resolve, locators exist, no copied
phrasing and quote length.

## 5. Corrections found along the way

See `tools/corrections_for_synthesis.md`. Main ones:
- HKMA custody annex of 27 May 2026 replaced the fixed 50%/100% compensation footnote for banks with
  liability plus adequate financial resources (para 11(n)); the 2024 annex is superseded.
- A bank's AML rulebook is the HKMA AML/CFT Guideline for AIs; the SFC's Chapter 12 applies to the
  bank's registered-institution activities and to counterparties.
- The HKMA named Project Ensemble's pilot phase "Ensemble TX" / "EnsembleTX" (13 Nov 2025).
- The 3 June 2026 CRP-1 letter loosened para 2.6.4.

## 6. A fetch bug found and fixed

HKMA pages carry site-wide "Latest Speeches" sidebars. The first fetch took links from the whole page,
so the newest speech (25 Sep 2026) was attached to 26 older pages. `fetch_corpus.py` now strips every
`<!--NO INDEX START--> … <!--NO INDEX END-->` block; `tools/repair_hkma_sidebar.py` re-fetched all 110
HKMA pages and repaired the corpus. The live site's link checker will compare content hashes, not only
HTTP status.

## 7. Known gaps

- **e-Legislation** (Cap. 615 Part 5B, Cap. 656 statute text) is a JavaScript application with no
  text export reachable from the research environment. Modules rely on HKMA/SFC documents that cite
  the sections.
- **LegCo** (bills, committee papers) failed TLS verification from the research environment;
  verification was not bypassed. LegCo question replies were read via GovHK.
- **Insurance Authority** and **Cyberport** returned HTTP 403.
- 14 registry entries are marked `text_unavailable` (unreadable PDF fonts, a .docx, landing pages
  without the PDF).
- Bills whose passage is not yet in the corpus (VA dealing/custodian regime, CARF) are shown with
  their last confirmed status.
