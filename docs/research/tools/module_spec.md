# Module brief spec (content backbone for the HK bank-compliance learning site)

Reader: Head of Compliance (digital assets) at a Hong Kong bank (an Authorized Institution, usually also an SFC Registered Institution). Goal: after reading, they know the basics, key projects and moving pieces, and can speak clearly and briefly with the CCO, business heads, CEO and Risk.

Inputs: synthesis_index.md (by topic), canon.jsonl (full entries — grep by id), text/<id>.txt (full source text — check every number/date/threshold you use against it), corrections_for_synthesis.md (MUST apply), owner_requirements.md (../owner_requirements.md).

Write each module to modules/<CODE>.md with EXACTLY these sections:
1. `# <CODE> <Title>` then one line: who this is for / what you'll be able to do.
2. `## In 60 seconds` — 4-6 plain-English sentences. The whole idea.
3. `## Status board` — table: Instrument | Issuer | Date | Status (chip) | Applies to | Source. Status chips (closed vocabulary): In force · Issued, effective <date> · Consultation · Conclusions published · Bill before LegCo · Enacted, commencement pending · Pilot · Stated target · Exploratory · Superseded. Always "as of 25 Sep 2026".
4. `## Key facts` — 8-20 bullets. Each bullet: one fact in own words, then the citation `[S:<canon id>, <locator>]` (locator = paragraph/section/page exactly as in the source). Keep the source's modal: statutes "require", guidelines "expect"/"should", consultations "propose". Say who is bound.
5. `## What your bank must do` — checklist grouped: Obligations · Controls & monitoring · Notify / consult HKMA or SFC · Counterparty due diligence. Every line cited. Only what the text states; never invent.
6. `## Talking points` — four sub-lists, 2-4 bullets each, each bullet ≤35 words and cited: **To the CCO**, **To business heads**, **To the CEO**, **To Risk / CRO**. Factual, no advice, no predictions beyond officially stated timelines.
7. `## Common mix-ups` — 3-6 bullets correcting frequent misconceptions (from entry flags), cited.
8. `## Read these first` — 3 primary documents max: title, issuer, date, exact sections/pages to read, why, and the source_url from canon.
9. `## Open items` — genuine uncertainties / not-yet-published / gaps in the corpus.
10. `## Related modules` — codes.

Hard rules: official sources only (the canon); own words — never copy 8+ consecutive words from a source; at most one ≤15-word quote per module; named licensees/enforcement targets only as the regulator states them, no commentary; no advice; no speculation. If canon entries conflict, re-read the source text and say which is right. Plain English, short sentences, define acronyms on first use. Target 900-1600 words per module.
