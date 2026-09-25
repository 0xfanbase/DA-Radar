import json,re,time,urllib.request
exec(open('enum_apis.py').read().split('out=[]')[0])
out=[]
for yr in range(2017,2027):
    pg=0
    while True:
        d=get("https://apps.sfc.hk/edistributionWeb/api/consultation/search",{"lang":"EN","year":yr,"pageNo":pg,"pageSize":100})
        if not d: break
        items=d.get("items",[])
        for it in items:
            t=it.get("cpTitle") or ""; app=it.get("ccTitle") or ""
            if KW.search(t) or KW.search(app):
                out.append({"src":"sfc-consultation","date":(it.get("cpIssueDate") or "")[:10],"title":re.sub(r"\s+"," ",t),"ref":it.get("cpRefNo"),"cc_ref":it.get("ccRefNo"),"cc_date":(it.get("firstCommentIssueDate") or "")[:10],"extra":app,"url":"https://apps.sfc.hk/edistributionWeb/gateway/EN/consultation/doc?refNo="+str(it.get("cpRefNo"))})
        if len(items)<100: break
        pg+=1
    time.sleep(0.3)
json.dump(out,open("enum_consult.json","w"),indent=1,ensure_ascii=False); print(len(out))
for o in out: print(o["date"],o["ref"],o["title"][:100])
