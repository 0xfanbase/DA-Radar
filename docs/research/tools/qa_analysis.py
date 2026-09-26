"""Lint Part F files: analysis-box grammar and banned forecast/advice language.
usage: python3 qa_analysis.py <files...>
Checks (1) each '> **Analysis — not official**' box has the five labelled slots; (2) inside analysis
boxes and case 'Discussion notes' sections: banned words and uncited numbers; (3) '(concept)' sentences
contain no digits."""
import re, sys
SLOTS = ["Question:", "How to think about it:", "What it depends on:", "Official signposts:", "What this is not:"]
BANNED = re.compile(r"\b(will|won't|likely|unlikely|expected to|should|recommend\w*|best|must|we believe|poised|set to|bound to)\b", re.I)
NUM = re.compile(r"(\d[\d,.]*\s*%|HK\$\s?\d|US\$\s?\d|\$\s?\d|\b\d+(\.\d+)?\s*(bn|billion|million|m|trillion|tn)\b)", re.I)
CITED = re.compile(r"\[[SI]:[0-9a-f]{12}")
def boxes(text):
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith("> **Analysis — not official**"):
            cur = [line]; out.append(cur)
        elif cur is not None and line.startswith(">"):
            cur.append(line)
        else:
            cur = None
    return ["\n".join(b) for b in out]
def notes(text):
    return re.findall(r"### Discussion notes\n(.*?)(?=\n## |\n### |\Z)", text, re.S)
bad = 0
for f in sys.argv[1:]:
    t = open(f).read(); probs = []
    for b in boxes(t):
        miss = [s for s in SLOTS if s not in b]
        if miss: probs.append(f"box missing slots {miss}: {b[:60]!r}")
    for seg in boxes(t) + notes(t):
        for sent in re.split(r"(?<=[.!?])\s+", seg):
            if CITED.search(sent): continue   # cited sentences may state rules/figures
            m = BANNED.search(sent)
            if m: probs.append(f"banned '{m.group(0)}': {sent.strip()[:110]}")
            n = NUM.search(sent)
            if n and "(illustrative)" not in sent: probs.append(f"uncited number '{n.group(0)}': {sent.strip()[:110]}")
    for sent in re.findall(r"[^.\n]*\(concept\)", t):
        if re.search(r"\d", sent): probs.append(f"digit in concept: {sent.strip()[:110]}")
    print(f"{f}: analysis_boxes={len(boxes(t))} problems={len(probs)}")
    for p in probs[:12]: print("   ", p)
    bad += len(probs)
sys.exit(1 if bad else 0)
