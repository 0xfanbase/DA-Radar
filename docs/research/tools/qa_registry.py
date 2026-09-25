import json,glob,re,collections
def words(t): return re.findall(r"[a-z0-9']+",t.lower())
def ngrams(w,n): return {' '.join(w[i:i+n]) for i in range(len(w)-n+1)}
N=12; STAT={"in_force","issued_future_effective","consultation","conclusions","bill","enacted_pending","pilot","announced_target","exploratory","superseded","historical","informational"}
meta={json.load(open(f))['id']:json.load(open(f)) for f in glob.glob('meta/*.json')}
issues=collections.defaultdict(list); total=0; ents=[]
for f in sorted(glob.glob('registry/*.jsonl')):
    for ln,l in enumerate(open(f)):
        l=l.strip()
        if not l: continue
        try: e=json.loads(l)
        except Exception as ex: issues['bad_json'].append(f"{f}:{ln}"); continue
        total+=1; e['_file']=f; ents.append(e)
        i=e.get('id'); m=meta.get(i)
        src=''
        ids=[i]+([a['id'] for a in m['attachments']] if m else [])
        for x in ids:
            try: src+=open(f'text/{x}.txt').read()+'\n'
            except: pass
        if e.get('parent_id'):
            try: src+=open(f"text/{e['parent_id']}.txt").read()
            except: pass
        sg=ngrams(words(src),N)
        own=' '.join([e.get('summary','')]+[k.get('point','') for k in e.get('key_points',[])]+[e.get('why_it_matters_for_bank_HoDA','')])
        sw=words(src); s8={' '.join(sw[k:k+8]) for k in range(len(sw)-7)}
        tw=words(e.get('title','')); t8={' '.join(tw[k:k+8]) for k in range(max(0,len(tw)-7))}
        ow=words(own); cov=[0]*len(ow)
        for k in range(len(ow)-7):
            g=' '.join(ow[k:k+8])
            if g in s8 and g not in t8:
                for j in range(k,k+8): cov[j]=1
        ratio=sum(cov)/max(1,len(ow))
        if ratio>0.15: issues['close_paraphrase_over15pct'].append((i,f.split('/')[-1],e.get('title','')[:50],round(ratio,2)))
        if not i or i not in meta: issues['unknown_id'].append((i,e.get('title','')[:60]))
        if e.get('status_as_of_2026_09_25') not in STAT: issues['bad_status'].append((i,e.get('status_as_of_2026_09_25')))
        kp=e.get('key_points',[])
        if any(not k.get('locator') for k in kp): issues['missing_locator'].append((i,e.get('title','')[:60]))
        q=(e.get('quote') or {}).get('text','')
        if q and len(words(q))>15: issues['quote_too_long'].append((i,len(words(q))))
        if 'text_unavailable' in ' '.join(e.get('flags',[])): issues['text_unavailable'].append((i,e.get('title','')[:60]))
print('entries',total,'unique ids',len({e.get('id') for e in ents}))
for k,v in issues.items(): print(k,len(v)); [print('   ',x) for x in v[:12]]
print(collections.Counter(e.get('importance') for e in ents))
