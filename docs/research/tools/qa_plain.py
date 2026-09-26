"""Readability audit for HKDA Brief content.
usage: python3 qa_plain.py <md files...>   or   python3 qa_plain.py --registry <jsonl>
Reports per file: sentences, average words per sentence, share of sentences over 25 words, longest
sentence, passive-voice hits, jargon hits, and acronyms used before they are explained."""
import re, sys, json
JARGON = r"de minimis|grandfather\w*|deeming|deemed|notwithstanding|pursuant|in respect of|vis-?à-?vis|thereof|herein|hereby|whereby|inter alia|mutatis|operative|non-contravention|encumber\w*|have regard to|in the event that|prior to|with a view to|in relation to|in accordance with|commence\w*|utili[sz]\w*|facilitat\w*|aforementioned|said \w+ shall|shall|ex ante|ex post|bona fide|per se|ceteris|et al"
PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)\s+(\w+ed|\w+en)\b(?!\s+(?:to|than))", re.I)
KNOWN = {"HK", "US", "UK", "EU", "UAE", "PDF", "FAQ", "FAQs", "CEO", "CCO", "CRO", "COO", "CFO", "OK", "Q1", "Q2", "Q3", "Q4", "H1", "H2", "AI"}
def clean(t):
    t = re.sub(r"\[[SI]:[^\]]*\]", "", t)
    t = re.sub(r"`[^`]*`|https?://\S+|\(#[^)]*\)", "", t)
    t = re.sub(r"^\s*\|?[-: |]+\|?\s*$", "", t, flags=re.M)
    return t
def sentences(t):
    t = clean(t)
    parts = []
    for line in t.splitlines():
        line = re.sub(r"^[#>*\-\d.\s|]+", "", line).strip()
        if not line: continue
        for cell in line.split("|"):
            for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"“(])", cell.strip()):
                if len(re.findall(r"[A-Za-z0-9$%]+", s)) >= 3: parts.append(s.strip())
    return parts
def acro_issues(t):
    t = clean(t); seen_def = set(); out = []
    for m in re.finditer(r"\b([A-Z][A-Za-z]*[A-Z][A-Za-z0-9]*)\b", t):
        a = m.group(1)
        if a in KNOWN or len(a) < 2 or not re.search(r"[A-Z].*[A-Z]", a): continue
        ctx = t[max(0, m.start()-120): m.end()+80]
        if re.search(r"\(" + re.escape(a) + r"\)", ctx) or re.search(re.escape(a) + r"\s*(=|\(|:|—| means| is short for| stands for)", ctx):
            seen_def.add(a); continue
        if a not in seen_def and a not in [x for x, _ in out]: out.append((a, t[max(0, m.start()-40): m.end()+20].replace("\n", " ")))
    return out
def report(name, text):
    ss = sentences(text)
    if not ss: return None
    lens = [len(re.findall(r"[A-Za-z0-9$%']+", s)) for s in ss]
    long_ = [s for s, n in zip(ss, lens) if n > 25]
    jar = re.findall(JARGON, clean(text), re.I)
    pas = PASSIVE.findall(clean(text))
    ac = acro_issues(text)
    return {"file": name, "sentences": len(ss), "avg": round(sum(lens)/len(lens), 1), "over25": round(100*len(long_)/len(ss)),
            "max": max(lens), "passive": len(pas), "jargon": len(jar), "jargon_terms": sorted(set(j.lower() for j in jar))[:8],
            "undefined_acronyms": [a for a, _ in ac][:12], "worst": sorted(long_, key=len, reverse=True)[:2]}
if __name__ == "__main__":
    rows = []
    if sys.argv[1] == "--registry":
        text = []
        for line in open(sys.argv[2]):
            e = json.loads(line)
            text.append(" ".join([e.get("summary", ""), e.get("why_it_matters_for_bank_HoDA", ""), e.get("reading_guide", "")] + [k.get("point", "") for k in e.get("key_points") or []]))
        r = report("registry", "\n".join(text)); rows.append(r)
    else:
        for f in sys.argv[1:]:
            r = report(f.split("/")[-1], open(f).read())
            if r: rows.append(r)
    for r in rows:
        print(f"{r['file']:<32} sent={r['sentences']:<4} avg={r['avg']:<5} >25w={r['over25']:>3}% max={r['max']:<3} passive={r['passive']:<3} jargon={r['jargon']:<3} undefined={len(r['undefined_acronyms'])}")
    if len(rows) > 1:
        n = sum(r["sentences"] for r in rows)
        print(f"TOTAL sentences={n} avg_len={round(sum(r['avg']*r['sentences'] for r in rows)/n,1)} over25={round(sum(r['over25']*r['sentences'] for r in rows)/n)}%")
