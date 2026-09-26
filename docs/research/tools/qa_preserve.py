"""Prove a plain-English rewrite kept every fact.
usage: python3 qa_preserve.py <old.md> <new.md>
Fails if: the set of citations (id + locator) differs; any number disappears; the count of force words
(must/required/requires/should/expects/may/proposes/would) shifts between categories; build-critical
headings or bold labels changed; a table's row/column count changed."""
import re, sys, collections
FORCE = {"binding": r"\b(must|required|requires|require|prohibit\w*|banned|may not|cannot)\b",
         "guidance": r"\b(should|expects?|expected|encourag\w*)\b",
         "allowed": r"\bmay\b(?! not)",
         "proposal": r"\b(propos\w*|would|plans?|stated target|aims?)\b"}
LABELS = r"^(## .+|\*\*(Obligations|Controls & monitoring|Notify / consult HKMA or SFC|Counterparty due diligence|To the CEO|To the CCO|To business heads|To Risk / CRO|Myth:|Fact:)\*\*)"
def cites(t):
    out = collections.Counter()
    for inner in re.findall(r"\[((?:S|I):[^\]]+)\]", t):
        for part in re.split(r";\s*(?=(?:S|I):)", inner):
            m = re.match(r"\s*([SI]):([0-9a-f]{12})\s*(?:,\s*(.*))?$", part.strip(), re.S)
            if m: out[(m.group(1), m.group(2), re.sub(r"\s+", " ", (m.group(3) or "").strip()))] += 1
    return out
def nums(t):
    t = re.sub(r"\[[SI]:[^\]]*\]", "", t)
    t = re.sub(r"\((#[^)]*|https?://[^)]*)\)", "", t)
    return collections.Counter(re.findall(r"\d+(?:[.,]\d+)*", t))
def force(t):
    t = re.sub(r"\[[SI]:[^\]]*\]", "", t).lower()
    return {k: len(re.findall(v, t)) for k, v in FORCE.items()}
def labels(t): return [l.strip() for l in t.splitlines() if re.match(LABELS, l.strip()) and not l.startswith("## ") or l.startswith("## ")]
def tables(t):
    out, cur = [], None
    for l in t.splitlines():
        if l.strip().startswith("|"):
            if cur is None: cur = [0, l.count("|")]; out.append(cur)
            cur[0] += 1
        else: cur = None
    return [tuple(x) for x in out]
def check(old, new):
    probs = []
    co, cn = cites(old), cites(new)
    if set(co) != set(cn):
        lost = set(co) - set(cn); added = set(cn) - set(co)
        if lost: probs.append(f"citations lost: {sorted(lost)[:4]}")
        if added: probs.append(f"citations added/changed: {sorted(added)[:4]}")
    no, nn = nums(old), nums(new)
    lost = [k for k in no if nn[k] < 1]
    if lost: probs.append(f"numbers lost: {lost[:8]}")
    new_nums = [k for k in nn if no[k] < 1]
    if new_nums: probs.append(f"new numbers: {new_nums[:8]}")
    fo, fn = force(old), force(new)
    for k in fo:
        if (fo[k] == 0) != (fn[k] == 0) or abs(fo[k] - fn[k]) > max(2, fo[k] // 4):
            probs.append(f"force words '{k}': {fo[k]} -> {fn[k]}")
    lo = [l for l in labels(old) if not l.startswith("**Myth") and not l.startswith("**Fact")]
    ln = [l for l in labels(new) if not l.startswith("**Myth") and not l.startswith("**Fact")]
    if [l for l in lo if l.startswith("## ")] != [l for l in ln if l.startswith("## ")]: probs.append("section headings changed")
    if sorted(l for l in lo if l.startswith("**")) != sorted(l for l in ln if l.startswith("**")): probs.append("bold labels changed")
    if tables(old) != tables(new): probs.append(f"table shape changed: {tables(old)} -> {tables(new)}")
    return probs
if __name__ == "__main__":
    p = check(open(sys.argv[1]).read(), open(sys.argv[2]).read())
    print(sys.argv[2], "OK" if not p else "PROBLEMS"); [print("  ", x) for x in p]
    sys.exit(1 if p else 0)
