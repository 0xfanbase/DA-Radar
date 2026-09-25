import json, re, time, urllib.request
KW = re.compile(r"virtual[- ]asset|\bVA\b|VATP|VASP|crypto|stablecoin|token|digital asset|digital bond|digital green bond|distributed ledger|\bDLT\b|blockchain|e-HKD|\bCBDC|Ensemble|mBridge|Evergreen|Web ?3|\bNFT|Aurum|\bSela\b|Genesis|OmniClear|e-CNY|programmable|travel rule|CARF|crypto-asset|staking|custod.*digital|digital.*custod|Fintech 2025|Fintech Promotion|wholesale central bank|Project Ensemble|Digital Bond Grant|JPEX|Alert List.*platform|unregulated.*platform|metaverse|smart contract", re.I)
UA={"User-Agent":"HK-DA-learning-research/0.1 (non-commercial study)"}
def get(url, data=None):
    req=urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers={**UA, **({"Content-Type":"application/json"} if data else {})})
    for i in range(3):
        try: return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e: err=e; time.sleep(2**i)
    print("FAIL",url,data,err); return None
out=[]
# HKMA press releases (full history via offset)
off=0
while True:
    d=get(f"https://api.hkma.gov.hk/public/press-releases?lang=en&pagesize=100&offset={off}")
    if d is None: off+=100; continue
    recs=d["result"]["records"]
    for r in recs:
        if KW.search(r["title"]): out.append({"src":"hkma-pr","date":r["date"],"title":r["title"].strip("﻿ "),"url":r["link"]})
    if len(recs)<100 or recs[-1]["date"]<"2016-01-01": break
    off+=100; time.sleep(0.5)
print("hkma pr done", len(out), "last date", recs[-1]["date"])
# SFC circulars, news, consultations
for kind in ["circular","news","consultation"]:
    for yr in range(2017,2027):
        pg=0
        while True:
            d=get(f"https://apps.sfc.hk/edistributionWeb/api/{kind}/search", {"lang":"EN","category":"all","year":yr,"pageNo":pg,"pageSize":100})
            if d is None: break
            items=d.get("items",[])
            for it in items:
                if kind=="circular":
                    t=it["title"]; ref=it["refNo"]; dt=it["releasedDate"][:10]
                    url="https://apps.sfc.hk/edistributionWeb/api/circular/openFile?lang=EN&refNo="+ref
                    app=" | ".join(a.get("title","") for a in it.get("appendixDocList") or [])
                elif kind=="news":
                    t=it["title"]; ref=it["newsRefNo"]; dt=it["issueDate"][:10]; app=""
                    url="https://apps.sfc.hk/edistributionWeb/gateway/EN/news-and-announcements/news/doc?refNo="+ref
                else:
                    t=it.get("cpTitle") or ""; ref=it.get("cpRefNo"); dt=(it.get("cpIssueDate") or "")[:10]
                    app=(it.get("ccTitle") or "")
                    url="https://apps.sfc.hk/edistributionWeb/gateway/EN/consultation/doc?refNo="+str(ref)
                if KW.search(t) or KW.search(app):
                    out.append({"src":"sfc-"+kind,"date":dt,"title":re.sub(r"\s+"," ",t),"ref":ref,"url":url,"extra":app})
            if len(items)<100: break
            pg+=1; time.sleep(0.3)
        time.sleep(0.3)
    print(kind,"done",len(out))
json.dump(out,open("enum_apis.json","w"),indent=1,ensure_ascii=False)
print("total",len(out))
