"""Map each model period to its source documents: the 8-K Item 2.02 earnings release (Ex. 99.1) and the 10-Q / 10-K for the period,
and the same documents one year later (prior-year comparatives). Writes $RBC_SRC/period_index.json.

RBC's fiscal year ends on the Saturday nearest 31 March; FY label = calendar year of the March / April year end (FY2026 =
30-Mar-2025 - 28-Mar-2026). Quarter ends fall in late June / early July (Q1), late September / early October (Q2),
late December / early January (Q3) and late March / early April (Q4)."""
import json, os, glob, datetime as dt
S = os.environ.get('RBC_SRC', '/tmp/rbc_src')

def fq(end):
    e = dt.date.fromisoformat(end)
    m = e.month
    if m in (3, 4): return (e.year, 4)
    if m in (6, 7): return (e.year + 1, 1)
    if m in (9, 10): return (e.year + 1, 2)
    if m in (12,): return (e.year + 1, 3)
    if m in (1,): return (e.year, 3)
    raise ValueError(end)

def key(fy, q, annual=False): return str(fy) if annual else f'Q{q}-{str(fy)[2:]}'

def txt(o, doc):
    p = glob.glob(os.path.join(S, 'txt', f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt"))
    return p[0] if p else None

def run():
    F = json.load(open(os.path.join(S, 'filings.json')))
    rel = [o for o in F if o['form'] == '8-K' and '2.02' in o['items']]
    per = [o for o in F if o['form'] in ('10-Q', '10-K')]
    idx = {}
    for o in per:
        fy, q = fq(o['report'])
        url = f"https://www.sec.gov/Archives/edgar/data/1324948/{o['acc'].replace('-', '')}/{o['primary']}"
        # release = the latest Item 2.02 8-K filed on or before the 10-Q / 10-K and within 75 days of the period end
        cands = [r for r in rel if r['date'] <= o['date'] and r['date'] > o['report']]
        r = cands[-1] if cands else None
        rd = None
        if r:
            ex = [x for x in r['files'] if x != r['primary'] and '99' in x and x.lower().endswith(('.htm', '.html'))]
            doc = sorted(ex)[0] if ex else r['primary']
            rd = dict(url=f"https://www.sec.gov/Archives/edgar/data/1324948/{r['acc'].replace('-', '')}/{doc}", date=r['date'], txt=txt(r, doc))
        rec = dict(fy=fy, q=q, period_end=o['report'], filing=dict(url=url, date=o['date'], form=o['form'], txt=txt(o, o['primary'])), release=rd)
        idx[key(fy, q, o['form'] == '10-K')] = rec
        if o['form'] == '10-K': idx[key(fy, 4)] = rec
    for k, v in idx.items():
        fy = v['fy']
        nk = str(fy + 1) if k.isdigit() else f'{k[:3]}{str(fy + 1)[2:]}'
        if nk in idx: v['next'] = dict(filing=idx[nk]['filing'], release=idx[nk]['release'])
    json.dump(idx, open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
    return idx

if __name__ == '__main__':
    idx = run()
    for k in sorted(idx, key=lambda k: (idx[k]['fy'], idx[k]['q'], k.isdigit())):
        v = idx[k]; print(k, v['period_end'], v['filing']['form'], v['filing']['date'], (v['release'] or {}).get('date'), bool((v['release'] or {}).get('txt')))
