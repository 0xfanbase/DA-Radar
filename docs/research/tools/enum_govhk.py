import json,re,time,urllib.request,datetime,html,concurrent.futures as cf
exec(open('enum_apis.py').read().split('out=[]')[0])
A=re.compile(r'<a[^>]*href="(/gia/general/\d{6}/\d{2}/P\d+\.htm)"[^>]*>(.*?)</a>',re.S)
def day(d):
    url=f"https://www.info.gov.hk/gia/general/{d:%Y%m}/{d:%d}.htm"
    for i in range(3):
        try:
            t=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30).read().decode('utf-8','ignore')
            res=[]
            for h,ti in A.findall(t):
                ti=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>','',ti))).strip()
                if KW.search(ti): res.append({"src":"govhk","date":d.isoformat(),"title":ti,"url":"https://www.info.gov.hk"+h})
            return res
        except Exception as e: time.sleep(2**i)
    return [{"src":"govhk-FAIL","date":d.isoformat(),"url":url}]
d0=datetime.date(2017,1,1); n=(datetime.date(2026,9,25)-d0).days+1
out=[]
with cf.ThreadPoolExecutor(4) as ex:
    for i,r in enumerate(ex.map(day,[d0+datetime.timedelta(k) for k in range(n)])):
        out+=r
        if i%250==0: print(i,len(out),flush=True)
json.dump(out,open("enum_govhk.json","w"),indent=1,ensure_ascii=False)
print("done",len(out),sum(1 for o in out if o["src"]=="govhk-FAIL"))
