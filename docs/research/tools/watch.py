"""Find new Hong Kong digital-asset publications not yet in the source registry.

Usage (from docs/research/tools):  python3 watch.py [--since YYYY-MM-DD] [--out new_items.json]
Default --since = latest registry date minus 21 days (catches late-indexed items).
Sources: HKMA press-release API, HKMA BRDR search, SFC circular/news/consultation APIs,
GovHK daily press-release index. Output items use the same shape as the original inventory,
so fetch_corpus.py can process them. Items are candidates: a human-grade reading step decides
whether each one is really about digital assets.
"""
import argparse, datetime, hashlib, html, json, pathlib, re, subprocess, sys, time, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REG = HERE.parent / "source-registry.jsonl"
exec(open(HERE / "enum_apis.py").read().split("out=[]")[0])  # KW, UA, get()

BRDR_WORDS = ["virtual asset", "cryptoasset", "crypto-asset", "stablecoin", "tokenised", "tokenized",
              "digital asset", "distributed ledger", "blockchain", "staking", "e-HKD", "CBDC", "Ensemble",
              "mBridge", "digital bond", "OmniClear", "travel rule", "VASP"]


def iid(url):
    return hashlib.sha1(url.encode()).hexdigest()[:12]


def known():
    ids, urls = set(), set()
    for line in open(REG):
        e = json.loads(line)
        ids.add(e["id"])
        for k in ("url", "source_url", "deep_link_base"):
            if e.get(k):
                urls.add(e[k].split("#")[0])
    return ids, urls


def hkma_pr(since):
    out, off = [], 0
    while True:
        d = get(f"https://api.hkma.gov.hk/public/press-releases?lang=en&pagesize=100&offset={off}")
        if not d:
            break
        recs = d["result"]["records"]
        for r in recs:
            if r["date"] >= since and KW.search(r["title"]):
                out.append({"src": "hkma-pr", "date": r["date"], "title": r["title"].strip("﻿ "), "url": r["link"]})
        if len(recs) < 100 or recs[-1]["date"] < since:
            break
        off += 100
        time.sleep(0.5)
    return out


def sfc(since):
    out = []
    for kind in ("circular", "news", "consultation"):
        for yr in range(int(since[:4]), datetime.date.today().year + 1):
            body = {"lang": "EN", "year": yr, "pageNo": 0, "pageSize": 100}
            if kind != "consultation":
                body["category"] = "all"
            d = get(f"https://apps.sfc.hk/edistributionWeb/api/{kind}/search", body) or {}
            for it in d.get("items", []):
                if kind == "circular":
                    t, ref, dt = it["title"], it["refNo"], it["releasedDate"][:10]
                    url = "https://apps.sfc.hk/edistributionWeb/api/circular/openFile?lang=EN&refNo=" + ref
                    extra = " | ".join(a.get("title", "") for a in it.get("appendixDocList") or [])
                elif kind == "news":
                    t, ref, dt, extra = it["title"], it["newsRefNo"], it["issueDate"][:10], ""
                    url = "https://apps.sfc.hk/edistributionWeb/gateway/EN/news-and-announcements/news/doc?refNo=" + ref
                else:
                    t, ref, dt = it.get("cpTitle") or "", it.get("cpRefNo"), (it.get("cpIssueDate") or "")[:10]
                    extra = it.get("ccTitle") or ""
                    url = "https://apps.sfc.hk/edistributionWeb/gateway/EN/consultation/doc?refNo=" + str(ref)
                if dt >= since and (KW.search(t) or KW.search(extra)):
                    out.append({"src": "sfc-" + kind, "date": dt, "title": re.sub(r"\s+", " ", t), "ref": ref, "url": url, "extra": extra})
            time.sleep(0.3)
    return out


def brdr(since):
    out, seen = [], set()
    for w in BRDR_WORDS:
        body = {"langCode": "ENG", "pageNumber": "1", "pageSize": "50", "sortBy": "ISSUE_DATE_DESCENDING",
                "docSrchCriteriaDtoList": [{"fieldCode": "searchWordExact", "valueList": [w]}]}
        r = subprocess.run(["curl", "-s", "-m", "30", "-X", "POST", "https://brdr.hkma.gov.hk/restapi/doc-search",
                            "-H", "Content-Type: application/json; charset=utf-8", "-d", json.dumps(body)],
                           capture_output=True, text=True, timeout=40)
        try:
            items = json.loads(r.stdout).get("resultList") or []
        except Exception:
            print("BRDR FAIL", w, file=sys.stderr)
            continue
        for it in items:
            # issueDate is UTC midnight of the HK date minus 8h; issueDateStr is the HK date
            dt = datetime.datetime.strptime(it["issueDateStr"], "%d %b %Y").date().isoformat()
            if it["docId"].endswith("-CHI") or re.search(r"[\u4e00-\u9fff]", it.get("docLongTitle") or ""):
                continue   # Chinese version; the English one is listed separately
            if dt >= since and it["docId"] not in seen:
                seen.add(it["docId"])
                out.append({"src": "brdr", "date": dt, "title": re.sub(r"\s*</?br\s*/?>.*$", "", it.get("docLongTitle") or ""),
                            "url": f"https://brdr.hkma.gov.hk/eng/doc-ldg/docId/{it['docId']}"})
        time.sleep(0.5)
    return out


A = re.compile(r'<a[^>]*href="(/gia/general/\d{6}/\d{2}/P\d+\.htm)"[^>]*>(.*?)</a>', re.S)


def govhk(since):
    out, d = [], datetime.date.fromisoformat(since)
    while d <= datetime.date.today():
        url = f"https://www.info.gov.hk/gia/general/{d:%Y%m}/{d:%d}.htm"
        try:
            t = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")
            for h, ti in A.findall(t):
                ti = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", ti))).strip()
                if KW.search(ti):
                    out.append({"src": "govhk", "date": d.isoformat(), "title": ti, "url": "https://www.info.gov.hk" + h})
        except Exception as e:
            print("GovHK FAIL", url, e, file=sys.stderr)
        d += datetime.timedelta(1)
        time.sleep(0.3)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--since")
    ap.add_argument("--out", default="new_items.json")
    a = ap.parse_args()
    ids, urls = known()
    if not a.since:
        last = max(json.loads(l).get("date") or "" for l in open(REG))
        a.since = (datetime.date.fromisoformat(last) - datetime.timedelta(21)).isoformat()
    found = hkma_pr(a.since) + brdr(a.since) + sfc(a.since) + govhk(a.since)
    new = [f for f in found if iid(f["url"]) not in ids and f["url"] not in urls]
    json.dump(new, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"since {a.since}: found {len(found)}, new {len(new)} -> {a.out}")
    for f in new:
        print(f"  {f['date']}  {f['src']:<16} {f['title'][:90]}")
