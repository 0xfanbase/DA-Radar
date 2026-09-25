import json,glob,collections
metas={json.load(open(f))['id']:json.load(open(f)) for f in glob.glob('meta/*.json')}
ents=[]
for f in sorted(glob.glob('registry/*.jsonl')):
    for l in open(f):
        l=l.strip()
        if not l: continue
        try: e=json.loads(l)
        except: continue
        e['_batch']=f.split('/')[-1][:-6]; ents.append(e)
def score(e):
    pri=2 if e['_batch'].startswith('rewrite') else 1 if e['_batch'].startswith('enrich') else 0
    return (pri, 1 if e.get('bank_compliance_angle') else 0, len(e.get('key_points',[])), len(json.dumps(e)))
best={}
for e in ents:
    if e['id'] not in best or score(e)>score(best[e['id']]): best[e['id']]=e
# fix the sidebar-captured speech deck: a genuine standalone document, not an attachment of older speeches
SID='a50e9dc16dc7'
if SID in best:
    e=best[SID]; e['parent_id']=None
    e['url']='https://www.hkma.gov.hk/media/eng/doc/key-information/speeches/s20260925e1.pdf'
    e['date']='2026-09-25'
    e.setdefault('flags',[]).append('corpus-note: originally captured via the HKMA site "Latest Speeches" sidebar and wrongly linked to older speeches; relationship removed 2026-09-25')
for e in best.values():
    if e.get('package'): e['package']=[p for p in e['package'] if p!=SID]
    if e.get('parent_id')==SID: e['parent_id']=None
    m=metas.get(e['id'])
    if m:
        e['source_url']=m['url']; e['fetched']=m.get('fetched'); e['chars']=m['chars']
        if m.get('parent') and not e.get('parent_id'): e['parent_id']=m['parent']
    e['flags']=[f for f in e.get('flags',[]) if not (SID in f and 'mismatch' in f.lower())]
out=sorted(best.values(),key=lambda e:(e.get('date') or '',e['id']))
with open('canon.jsonl','w') as f:
    for e in out: f.write(json.dumps(e,ensure_ascii=False)+'\n')
c=collections.Counter(e.get('importance') for e in out); r=collections.Counter(e.get('bank_relevance','(missing)') for e in out)
print('canon entries',len(out),dict(c)); print('bank_relevance',dict(r))
print('missing compliance angle among core/important:',sum(1 for e in out if e.get('importance') in('core','important') and not e.get('bank_compliance_angle')))
