"""Write $MA_SRC/period_index.json: for each period key (2006 ... 2025, Q1-13 ... Q2-26) the text path, URL and date of its
earnings release (8-K Ex. 99.1; annual = the Q4 release) and of its 10-Q / 10-K. Used by the transcription agents (see
EXTRACTION_SCHEMA.md). Run after make_index.py and fetch.py."""
import json, os, re
S = os.environ.get('MA_SRC', '/tmp/ma_src')
F = json.load(open(os.path.join(S, 'filings.json')))
def txt(o, doc):
    p = os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")
    return p if os.path.exists(p) else None
def url(o, doc): return f"https://www.sec.gov/Archives/edgar/data/1141391/{o['acc'].replace('-', '')}/{doc}"
idx = {}
for o in F:
    m, y = int(o['date'][5:7]), int(o['date'][:4])
    if o['form'] == '8-K' and '2.02' in o['items']:
        ex = [x for x in o['files'] if re.search(r'99[_.-]?1|991|ex-?99', x.lower()) and '992' not in x.lower()]
        if not ex or not txt(o, ex[0]) or not re.search(r'statements? of operations', open(txt(o, ex[0])).read(), re.I): continue
        q = 4 if m <= 3 else 1 if m <= 6 else 2 if m <= 9 else 3; fy = y - 1 if q == 4 else y
        k = f'Q{q}-{str(fy)[2:]}'
        idx.setdefault(k, {})['release'] = {'txt': txt(o, ex[0]), 'url': url(o, ex[0]), 'date': o['date']}
        if q == 4: idx.setdefault(str(fy), {})['release'] = idx[k]['release']
    if o['form'] in ('10-Q', '10-K'):
        rd = o['report']; fy = int(rd[:4]); q = {3: 1, 6: 2, 9: 3, 12: 4}[int(rd[5:7])]
        k = str(fy) if o['form'] == '10-K' else f'Q{q}-{str(fy)[2:]}'
        idx.setdefault(k, {})['filing'] = {'txt': txt(o, o['primary']), 'url': url(o, o['primary']), 'date': o['date'], 'form': o['form']}
for k, v in idx.items():
    if k.startswith('Q4-'): v['filing'] = idx.get('20' + k[-2:], {}).get('filing')
json.dump(idx, open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
print(len(idx), 'periods;', 'missing:', sorted(k for k, v in idx.items() if not v.get('release') or not v.get('filing')))
