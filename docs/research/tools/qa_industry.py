"""Check industry registry entries: schema, publisher types, figure locators, own words, quote length.
usage (from the industry/ folder): python3 qa_industry.py [registry/*.jsonl]"""
import json, re, sys, glob, os
TYPES = {"international_official","foreign_regulator","consultancy","bank_research","association","listed_filing","data_provider"}
EST = {"reported","survey","modelled","forecast"}
REQ = ["id","url","title","publisher","publisher_type","date","geography","summary","capture_date","review_by"]
def words(t): return re.findall(r"[a-z0-9']+", t.lower())
files = sys.argv[1:] or sorted(glob.glob("registry/*.jsonl"))
n = bad = 0; seen = set()
for f in files:
    for line in open(f):
        if not line.strip(): continue
        e = json.loads(line); n += 1; probs = []
        for k in REQ:
            if not e.get(k): probs.append("missing " + k)
        if e.get("publisher_type") not in TYPES: probs.append("bad publisher_type")
        if e["id"] in seen: probs.append("duplicate id")
        seen.add(e["id"])
        if not os.path.exists(f"text/{e['id']}.txt"): probs.append("no captured text")
        for g in e.get("figures") or []:
            if not g.get("locator"): probs.append("figure without locator: " + str(g.get("metric")))
            if g.get("estimate_type") not in EST: probs.append("bad estimate_type: " + str(g.get("metric")))
        q = e.get("quote") or ""
        if isinstance(q, dict): q = q.get("text", "")
        if len(words(q)) > 15: probs.append("quote > 15 words")
        if os.path.exists(f"text/{e['id']}.txt"):
            src = words(open(f"text/{e['id']}.txt").read()); s8 = {" ".join(src[i:i+8]) for i in range(len(src)-7)}
            mine = " ".join([e.get("summary","")] + [g.get("definition","") + " " + g.get("note","") for g in e.get("figures") or []] + [r.get("point","") for r in e.get("rules") or []])
            mw = words(mine); t8 = {" ".join(words(e["title"])[i:i+8]) for i in range(max(0, len(words(e["title"]))-7))}
            hits = [" ".join(mw[i:i+8]) for i in range(len(mw)-7) if " ".join(mw[i:i+8]) in s8 and " ".join(mw[i:i+8]) not in t8]
            if hits: probs.append(f"copied 8-word run: {hits[0]!r}")
        if probs:
            bad += 1; print(e["id"], e.get("publisher"), "|", "; ".join(probs[:4]))
print(f"entries={n} with_problems={bad}")
sys.exit(1 if bad else 0)
