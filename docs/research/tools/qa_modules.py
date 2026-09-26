import json,re,glob,sys,collections
import os
canon={json.loads(l)['id']:json.loads(l) for l in open('canon.jsonl')}
IND={}   # industry registry (Part F): industry/registry/*.jsonl, text in industry/text/
for f in glob.glob('industry/registry/*.jsonl'):
    for l in open(f):
        if l.strip(): e=json.loads(l); IND[e['id']]=e
metas={json.load(open(f))['id']:json.load(open(f)) for f in glob.glob('meta/*.json')}
def words(t): return re.findall(r"[a-z0-9']+",t.lower())
def srctext(i):
    s=''
    m=metas.get(i); ids=[i]+([a['id'] for a in m['attachments']] if m else [])
    pid=(canon.get(i) or {}).get('parent_id')
    if pid: ids.append(pid)
    for x in ids:
        try: s+=open(f'text/{x}.txt').read()+'\n'
        except: pass
    return s
CITE=re.compile(r"(?:\[|;\s*)S:([0-9a-f]{12})(?:,\s*([^\];]*))?")
ICITE=re.compile(r"(?:\[|;\s*)I:([0-9a-f]{12})(?:,\s*([^\];]*))?")
files=sys.argv[1:] or sorted(glob.glob('modules/*.md'))
TITLE8=set()
for e in canon.values():
    tw=words(e.get('title',''))
    TITLE8|={' '.join(tw[k:k+8]) for k in range(max(0,len(tw)-7))}
ORG=re.compile(r'https|www|gov hk|financial services and the treasury bureau|hongkong and shanghai banking|stock exchange of hong kong|anti money laundering and counter|monetary authority')
for f in files:
    t=open(f).read(); cites=CITE.findall(t); icites=ICITE.findall(t)
    iunknown=sorted({i for i,_ in icites if i not in IND}); inoloc=sum(1 for i,l in icites if not l.strip())
    unknown=sorted({i for i,_ in cites if i not in canon})
    noloc=sum(1 for i,l in cites if not l.strip())
    superseded=sorted({i for i,_ in cites if canon.get(i,{}).get('status_as_of_2026_09_25')=='superseded'})
    # verbatim: 8-gram overlap between module prose and any cited source
    body=re.sub(r"\[[SI]:[^\]]*\]","",t); bw=words(body); b8={' '.join(bw[k:k+8]) for k in range(len(bw)-7)}
    hits=[]
    for i in {i for i,_ in cites if i in canon}:
        sw=words(srctext(i)); tw=words(canon[i].get('title',''))
        t8={' '.join(tw[k:k+8]) for k in range(max(0,len(tw)-7))}
        for k in range(len(sw)-7):
            g=' '.join(sw[k:k+8])
            if g in b8 and g not in t8 and g not in TITLE8 and not ORG.search(g): hits.append((i,g)); break
    for i in {i for i,_ in icites if i in IND}:
        p=f'industry/text/{i}.txt'
        if not os.path.exists(p): continue
        sw=words(open(p).read()); tw=words(IND[i].get('title','')); t8={' '.join(tw[k:k+8]) for k in range(max(0,len(tw)-7))}
        for k in range(len(sw)-7):
            g=' '.join(sw[k:k+8])
            if g in b8 and g not in t8 and not ORG.search(g): hits.append(('I:'+i,g)); break
    quotes=[q for q in re.findall(r"[\"“]([^\"”]{20,})[\"”]",t) if " ".join(words(q))[:60] not in " ".join(" ".join(words(e.get("title",""))) for e in canon.values())]
    longq=[q for q in quotes if len(words(q))>15]
    print(f"{f}: cites={len(cites)} icites={len(icites)} iunknown={iunknown} ino_locator={inoloc} unknown={unknown} no_locator={noloc} superseded_cited={len(superseded)} verbatim8={len(hits)} long_quotes={len(longq)}")
    for h in hits[:5]: print('   verbatim:',h)
