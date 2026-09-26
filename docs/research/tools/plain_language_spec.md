# Plain-English spec (applies to every word on HKDA Brief)

Reader: a busy, smart professional who is not a lawyer and reads on a phone. Every line must be
understood on the first read. If a sentence needs to be read twice, rewrite it.

## The rules
1. **Lead with the point.** Start each sentence or bullet with who does what. "Banks must keep 98% of
   client crypto offline." Not "In relation to custody, it is the case that…".
2. **One idea per sentence.** Aim for 20 words or fewer. Never more than 30 (official titles excepted).
   If a sentence lists more than three things, turn it into bullets.
3. **Everyday words.** Use these swaps (and the same spirit everywhere):
   commence → start; prior to → before; in respect of / in relation to → about, for; utilise → use;
   facilitate → help; notwithstanding → even if; pursuant to → under; have regard to → take into account;
   deemed → treated as; grandfathering / deeming → letting existing firms carry on while they apply
   (explain); de minimis → small-amount exception; encumber → pledge or use as security;
   non-contravention period → grace period; operative → in force; in the event that → if;
   with a view to → to; whereby → where / under which; thereof → of it; shall → must (only if the
   source is binding).
4. **Explain every technical term the first time it appears on a page**, in a few plain words:
   "cold storage (keys kept offline)", "risk weight (how much capital a bank holds against an asset)".
   Spell out every abbreviation on first use on each page: "Hong Kong Monetary Authority (HKMA)".
   If a term is used only once, use the plain words instead of the abbreviation.
5. **Active voice with a named actor.** "The HKMA expects banks to…", not "It is expected that…".
6. **No riddles.** No vague openers ("Not quite", "The picture is mixed", "Here's the twist"), no
   metaphors, no rhetorical questions in body text, no "this/it" whose meaning is unclear — name the
   thing. No noun stacks ("VA custody delegation counterparty standard") — unpack them.
7. **Say what numbers mean.** "1,250% risk weight — in effect, the bank holds capital equal to the whole
   exposure." Dates as "27 May 2026". Money as HK$ / US$.
8. **Keep the force words exact.** must / required = binding law or rule; should / expects = guidance;
   may = allowed; proposes / would = not yet law; stated target = a government aim. Never change one
   into another when simplifying.
9. **Positive and direct.** Avoid double negatives. "Only banks can…" beats "No firm other than a bank
   may not…".
10. **Lists are parallel.** Action bullets start with a verb. "Common mix-ups" use **Myth:** … **Fact:** …
11. **Talking points are sayable** — one or two short sentences you could say out loud in a meeting.

## What must never change when rewriting
- Facts, numbers, dates, names, and who is bound.
- Every citation `[S:…]` / `[I:…]` stays attached to the sentence that states that fact, with the same
  locator. You may split a sentence in two; then repeat or move the citation so each new sentence that
  states a sourced fact still carries it.
- Section headings, table columns and bold labels the site build depends on:
  `## In 60 seconds`, `## Status board`, `## Key facts`, `## What your bank must do`, `## Talking points`,
  `## Common mix-ups`, `## Read these first`, `## Open items`, `## Related modules`, `## At a glance`,
  bold labels **Obligations**, **Controls & monitoring**, **Notify / consult HKMA or SFC**,
  **Counterparty due diligence**, **To the CEO**, **To the CCO**, **To business heads**, **To Risk / CRO**,
  and every table's column count and row count. Status chip words in tables stay the same.
- No new facts. Explanations of terms must be general meaning only, not new claims.

## Checks
`python3 qa_preserve.py <old> <new>` must pass (same citations, numbers, force words, headings, table
shape). `python3 qa_plain.py <new>` should show: average ≤ 16 words, under 5% of sentences over 25
words, no jargon hits, and no abbreviation used before it is explained.
