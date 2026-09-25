import json,glob,re,hashlib,sys
prefix=sys.argv[1]
done=set()
for f in glob.glob('registry/*.jsonl'):
    for l in open(f):
        try: done.add(json.loads(l)['id'])
        except: pass
assigned=set()
for f in glob.glob('batches/*.json'):
    for it in json.load(open(f)): assigned.add(it['id'])
ms=[json.load(open(f)) for f in glob.glob('meta/*.json')]
def th(i):
    try: return hashlib.sha1(re.sub(r'\s+','',open(f'text/{i}.txt').read()).encode()).hexdigest()
    except: return None
seen={}; dup={}
prim=sorted([m for m in ms if not m.get('parent')],key=lambda m:(m['date'],m['url']))
for m in prim:
    h=th(m['id']) or m['id']
    atts=tuple(sorted(th(a['id']) or a['id'] for a in m['attachments']))
    key=(h,atts)
    if key in seen: dup[m['id']]=seen[key]
    else: seen[key]=m['id']
json.dump(dup,open(f'dups_{prefix}.json','w'),indent=0)
excl=set(json.load(open('excluded_ids.json')))
skip_src=set(sys.argv[2].split(',')) if len(sys.argv)>2 else set()
prim=[m for m in prim if m['id'] not in excl and m['src'] not in skip_src and m['id'] not in dup and m['id'] not in done and m['id'] not in assigned]
routine=re.compile(r'Anti-Money Laundering and Counter-Financing of Terrorism|warns public|Warning|impersonat|suspected virtual asset-related fraud|False News|alleged|Fraudulent|Beware|Misrepresentation|Alert',re.I)
sz=lambda m:m['chars']+sum(a['chars'] for a in m['attachments'])
r=[m for m in prim if routine.search(m['title'])]; c=[m for m in prim if not routine.search(m['title'])]
def w(name,items):
    if items: json.dump([{"id":m["id"],"title":m["title"],"date":m["date"],"url":m["url"],"src":m["src"],"attachments":[a["id"] for a in m["attachments"]],"chars":sz(m)} for m in items],open(f'batches/{name}.json','w'),indent=0,ensure_ascii=False)
chunks=[];cur=[];size=0
for m in c:
    if cur and size+sz(m)>480000: chunks.append(cur);cur=[];size=0
    cur.append(m);size+=sz(m)
if cur: chunks.append(cur)
for i,ch in enumerate(chunks): w(f'{prefix}_{i:02d}',ch)
w(f'{prefix}_routine',r)
print('dups',len(dup),'batches',[(len(x),sum(map(sz,x))) for x in chunks],'routine',len(r))
