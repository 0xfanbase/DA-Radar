"""Fetch full text for every inventory item (+ one hop of attached official PDFs/annexes).
usage: python3 fetch_corpus.py inventory.json   -> text/<id>.txt, meta/<id>.json"""
import json,re,sys,os,time,html,hashlib,io,urllib.request,urllib.parse,concurrent.futures as cf
from pypdf import PdfReader
def extract_text(f):
    r=PdfReader(f)
    return '\n'.join(f'[[page {i+1}]]\n'+(p.extract_text() or '') for i,p in enumerate(r.pages))
UA={"User-Agent":"Mozilla/5.0 (HK-DA-learning-research; polite; contact via repo)"}
OFFICIAL=re.compile(r"^https?://([a-z0-9-]+\.)*(hkma\.gov\.hk|sfc\.hk|info\.gov\.hk|gov\.hk|legco\.gov\.hk|elegislation\.gov\.hk|ia\.org\.hk|hkex\.com\.hk|bis\.org|cyberport\.hk|fsdc\.org\.hk|mpfa\.org\.hk)(/|$)",re.I)
os.makedirs("text",exist_ok=True); os.makedirs("meta",exist_ok=True); os.makedirs("raw",exist_ok=True)
def iid(url): return hashlib.sha1(url.encode()).hexdigest()[:12]
def fetch(url):
    for i in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60)
            return r.read(), r.headers.get("Content-Type","")
        except Exception as e: err=str(e); time.sleep(2**i)
    return None, "ERR "+err
def main_body(t):
    """hkma.gov.hk pages: keep only the article body. The page ends with a site-wide
    'Latest Speeches/Press Releases' sidebar (after <!--NO INDEX START-->) whose links
    change daily and must never be treated as this document's attachments."""
    m=re.search(r'(?s)<div class="template-content-area">(.*)',t)
    body=m.group(1) if m else t
    body=re.sub(r'(?s)<!--NO INDEX START-->.*?<!--NO INDEX END-->','',body)
    return body.split('<!--NO INDEX START-->')[0]  # unterminated block = rest of page is chrome
def html2text(t):
    body=main_body(t)
    body=re.sub(r'(?s)<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>','',body)
    body=re.sub(r'(?i)<br\s*/?>|</p>|</li>|</h\d>|</tr>','\n',body)
    s=html.unescape(re.sub('<[^>]+>',' ',body))
    return re.sub(r'[ \t]+',' ',re.sub(r'\n\s*\n+','\n\n',s)).strip()
def links(t,base):
    out=[]
    for h in re.findall(r'href="([^"#]+)',main_body(t)):
        u=urllib.parse.urljoin(base,html.unescape(h))
        if OFFICIAL.match(u) and (u.lower().endswith(".pdf") or "getPdf" in u or "openFile" in u or "openAppendix" in u): out.append(u)
    return list(dict.fromkeys(out))
def to_text(url):
    """returns (text, content_type, links)"""
    m=re.search(r"edistributionWeb/gateway/EN/news-and-announcements/news/(?:[a-z-]+/)?doc\?refNo=(\w+)",url)
    if m:
        b,ct=fetch(f"https://apps.sfc.hk/edistributionWeb/api/news/content?refNo={m.group(1)}&lang=EN")
        if b:
            j=json.loads(b); h=j.get("html","")
            return j.get("title","")+"\n\n"+html2text(h), "sfc-news-json", links(h,url)
    m=re.search(r"edistributionWeb/gateway/EN/consultation/doc\?refNo=(\w+)",url)
    if m: url=f"https://apps.sfc.hk/edistributionWeb/api/consultation/openFile?lang=EN&refNo={m.group(1)}"
    b,ct=fetch(url)
    if b is None: return None, ct, []
    if b[:4]==b"%PDF" or "pdf" in ct:
        try: return extract_text(io.BytesIO(b)), "pdf", []
        except Exception as e: return None, "pdf-parse-error "+str(e)[:80], []
    t=b.decode("utf-8","ignore")
    return html2text(t), "html", links(t,url)
def process(item, depth=0):
    url=item["url"]; k=iid(url)
    if os.path.exists(f"meta/{k}.json"): return json.load(open(f"meta/{k}.json"))
    txt,ct,lk=to_text(url)
    # SFC circular appendices
    kids=[]
    if "circular/openFile" in url and depth==0:
        for n in range(8):
            u=url.replace("openFile","openAppendix")+f"&appendix={n}"
            try:
                r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30)
                if r.status==200: lk.append(u)
                else: break
            except Exception: break
    meta={**item,"id":k,"content_type":ct,"chars":len(txt or ""),"attachments":[],"fetched":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    if txt: open(f"text/{k}.txt","w").write(txt)
    if depth==0:
        for u in lk[:12]:
            ch=process({"url":u,"title":"attachment of: "+item.get("title",""),"parent":k,"src":item.get("src","")+"-att","date":item.get("date","")},1)
            meta["attachments"].append({"id":ch["id"],"url":u,"chars":ch["chars"]})
    json.dump(meta,open(f"meta/{k}.json","w"),indent=1,ensure_ascii=False)
    time.sleep(0.4)
    return meta
if __name__=="__main__":
    inv=json.load(open(sys.argv[1]))
    with cf.ThreadPoolExecutor(3) as ex:
        for i,m in enumerate(ex.map(process,inv)):
            if i%20==0: print(i,m["content_type"],m["chars"],m.get("title","")[:60],flush=True)
    print("done")
