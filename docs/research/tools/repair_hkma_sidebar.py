"""Re-derive text + attachments for every hkma.gov.hk HTML parent using the fixed main_body().
Writes repair_report.json listing parents whose stored attachments/text included sidebar content."""
import json,glob,time,sys,importlib.util
spec=importlib.util.spec_from_file_location('fc','fetch_corpus.py'); fc=importlib.util.module_from_spec(spec); spec.loader.exec_module(fc)
report=[]
metas={json.load(open(f))['id']:json.load(open(f)) for f in glob.glob('meta/*.json')}
parents=[m for m in metas.values() if not m.get('parent') and 'www.hkma.gov.hk' in m['url'] and m['content_type']=='html']
for m in parents:
    b,ct=fc.fetch(m['url'])
    if not b: report.append({"id":m['id'],"error":ct}); continue
    t=b.decode('utf-8','ignore')
    good=set(fc.links(t,m['url']))
    stored={a['url']:a['id'] for a in m['attachments']}
    bad=[u for u in stored if u not in good]
    missing=[u for u in good if u not in stored]
    newtext=fc.html2text(t)
    oldtext=open(f"text/{m['id']}.txt").read() if m['chars'] else ''
    if bad or missing or len(newtext)!=len(oldtext):
        report.append({"id":m['id'],"title":m['title'][:90],"url":m['url'],"bad_attachments":[{"url":u,"id":stored[u]} for u in bad],"missing_attachments":missing,"text_chars_old":len(oldtext),"text_chars_new":len(newtext)})
        # apply repair
        open(f"text/{m['id']}.txt","w").write(newtext)
        m['chars']=len(newtext)
        m['attachments']=[a for a in m['attachments'] if a['url'] in good]
        for u in missing[:12]:
            ch=fc.process({"url":u,"title":"attachment of: "+m['title'],"parent":m['id'],"src":m['src']+"-att","date":m['date']},1)
            m['attachments'].append({"id":ch['id'],"url":u,"chars":ch['chars']})
        m['repaired']="2026-09-25 sidebar-link fix"
        json.dump(m,open(f"meta/{m['id']}.json","w"),indent=1,ensure_ascii=False)
    time.sleep(0.3)
json.dump(report,open('repair_report.json','w'),indent=1,ensure_ascii=False)
print('hkma html parents checked',len(parents),'changed',len(report))
print('with bad attachments',sum(1 for r in report if r.get('bad_attachments')),'with missing',sum(1 for r in report if r.get('missing_attachments')))
