"""Lint 'Commercial and customer benefits' boxes: grammar, citations or (concept) on every item, no advice/forecast words."""
import re, sys
LABELS = ["For customers:", "For the bank:", "Evidence so far:", "Limits:", "Business lines:"]
BANNED = re.compile(r"\b(will|likely|recommend|best|guarantee[sd]?)\b", re.I)
def boxes(md):
    out, cur = [], None
    for line in md.splitlines():
        if line.startswith("> **Commercial and customer benefits**"):
            cur = []; out.append(cur); continue
        if cur is not None:
            if line.startswith(">"): cur.append(line[1:].strip())
            else: cur = None
    return out
tot = 0
for f in sys.argv[1:]:
    md = open(f).read(); bx = boxes(md); probs = []
    if len(bx) != 1: probs.append(f"expected 1 box, found {len(bx)}")
    for b in bx:
        text = "\n".join(b)
        for lab in LABELS:
            if f"**{lab}**" not in text: probs.append("missing label " + lab)
        body = re.sub(r"\*\*Business lines:\*\*.*", "", text, flags=re.S)
        items = [x for x in re.split(r"\n-\s|\n\*\*[^*]+\*\*|(?<=[.!?])\s+(?=[A-Z])", body) if len(x.split()) > 4]
        for it in items:
            if not re.search(r"\[[SI]:[0-9a-f]{12}|\(concept\)", it): probs.append("uncited: " + it[:80])
            m = BANNED.search(re.sub(r"\[[^\]]*\]", "", it))
            if m and not re.search(r"\[S:", it): probs.append(f"banned word '{m.group(0)}': " + it[:80])
        n = len(re.findall(r"\w+", re.sub(r"\[[SI]:[^\]]*\]|\([^)]*#[^)]*\)", "", text)))
        if not 100 <= n <= 260: probs.append(f"length {n} words")
    tot += len(probs)
    print(f"{f}: boxes={len(bx)} problems={len(probs)}")
    for p in probs[:20]: print("   ", p)
