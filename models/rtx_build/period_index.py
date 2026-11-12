"""Map each model period to its source documents (text versions in $RTX_SRC/txt) -> $RTX_SRC/period_index.json and
data/_period_index.json (URLs only).

Keys: '2006'..'2025' (annual) and 'Q1-13'..'Q3-26' (quarters). For each: release (8-K Ex. 99 of that quarter; the Q4 release for
annual records), filing (10-Q; 10-K + Exhibit 13 annual report for Q4 / annual), next_release / next_filing (the same documents one
year later: prior-year comparatives), and for annual records filing_2y (the 10-K two years later, for two-step recasts such as
the FY2018 continuing-operations recast in the FY2020 10-K)."""
import json, os, re, datetime as dt
S = os.environ.get('RTX_SRC', '/tmp/rtx_src')
BASE = os.path.dirname(os.path.abspath(__file__))
ARCH = 'https://www.sec.gov/Archives/edgar/data/101829/'

def txt_path(o, doc):
    return os.path.join(S, 'txt', f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc

def fyq_of_release(date):
    d = dt.date.fromisoformat(date)
    if d.month <= 2: return d.year - 1, 4
    if d.month <= 5: return d.year, 1
    if d.month <= 8: return d.year, 2
    return d.year, 3

def build():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings = {}, {}
    for o in fl:
        if o['form'] == '8-K' and ('2.02' in o['items'] or ('2.01' in o['items'] and 'xker' in o['primary'])):   # Q3-17 8-K was coded Item 2.01
            ex = [x for x in o['files'] if x != o['primary'] and x.lower().endswith('.htm')]
            ex = [x for x in ex if os.path.exists(txt_path(o, x))]
            if not ex: continue
            doc = max(ex, key=lambda x: os.path.getsize(txt_path(o, x)))      # the news release is the largest exhibit
            p = txt_path(o, doc)
            if os.path.getsize(p) < 15000: continue       # dividend / other 2.02 notices
            fy, q = fyq_of_release(o['date'])
            if (fy, q) not in rel: rel[(fy, q)] = dict(date=o['date'], url=url(o, doc), txt=p)
        if o['form'] in ('10-Q', '10-K'):
            e = dt.date.fromisoformat(o['report'])
            fy, q = e.year, {3: 1, 6: 2, 9: 3, 12: 4}[e.month]
            d = dict(date=o['date'], form=o['form'], url=url(o, o['primary']), txt=txt_path(o, o['primary']))
            ex13 = [x for x in o['files'] if x.lower().endswith('13.htm') and 'ex313' not in x.lower() and 'exhibit313' not in x.lower() and 'exhibit1013' not in x.lower()]
            if ex13:
                d['ex13_url'] = url(o, ex13[0]); d['ex13_txt'] = txt_path(o, ex13[0])
            filings[(fy, q)] = d
    idx = {}
    def rec(fy, q, annual):
        key = str(fy) if annual else f'Q{q}-{str(fy)[2:]}'
        r = {'period': key, 'period_end': f'{fy}-{[3, 6, 9, 12][q - 1]:02d}-{[31, 30, 30, 31][q - 1]}'}
        if (fy, q) in rel: r['release'] = rel[(fy, q)]
        if (fy, q) in filings: r['filing'] = filings[(fy, q)]
        if (fy + 1, q) in rel: r['next_release'] = rel[(fy + 1, q)]
        if (fy + 1, q) in filings: r['next_filing'] = filings[(fy + 1, q)]
        if annual and (fy + 2, 4) in filings: r['filing_2y'] = filings[(fy + 2, 4)]
        if not annual and q == 4 and (fy, 3) in filings: r['q3_filing'] = filings[(fy, 3)]
        return key, r
    for fy in range(2006, 2026):
        k, r = rec(fy, 4, True); idx[k] = r
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if fy == 2026 and q == 4: break
            k, r = rec(fy, q, False); idx[k] = r
    return idx

if __name__ == '__main__':
    idx = build()
    json.dump(idx, open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
    slim = {k: {kk: ({a: b for a, b in v.items() if not a.endswith('txt')} if isinstance(v, dict) else v) for kk, v in r.items()} for k, r in idx.items()}
    os.makedirs(os.path.join(BASE, 'data'), exist_ok=True)
    json.dump(slim, open(os.path.join(BASE, 'data', '_period_index.json'), 'w'), indent=1)
    miss = [(k, [f for f in ('release', 'filing') if f not in r]) for k, r in idx.items() if any(f not in r for f in ('release', 'filing'))]
    print(len(idx), 'periods; missing:', miss)
