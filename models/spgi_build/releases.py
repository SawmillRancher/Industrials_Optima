"""Map each earnings release (8-K Item 2.02 Ex. 99.1; the Q4-2016 release was filed under Items 2.01 / 7.01) to its fiscal quarter.
Writes data/_releases.json: {period: {date, url, doc}}."""
import json, os, re, datetime as dt
S = os.environ.get('SPGI_SRC', '/tmp/spgi_src')
BASE = os.path.dirname(os.path.abspath(__file__))
def run():
    out = {}
    for o in json.load(open(os.path.join(S, 'filings.json'))):
        if o['form'] != '8-K': continue
        ex = [x for x in o['files'] if x != o['primary'] and re.search(r'earningsrel|ex99|exhibit99', x.lower())]
        if not ex: continue
        if '2.02' not in o['items'] and 'earningsrel' not in ' '.join(ex).lower(): continue
        d = dt.date.fromisoformat(o['date'])
        if o['date'] in ('2020-03-26', '2022-02-28', '2015-01-21', '2015-02-03', '2014-11-05', '2025-04-29x'): continue   # non-results 2.02 / 7.01 filings
        # results are released 3-6 weeks after quarter end
        qe = dt.date(d.year, ((d.month - 1) // 3) * 3 + 1, 1) - dt.timedelta(days=1)
        if (d - qe).days > 62: continue
        q = (qe.month) // 3; per = f'Q{q}-{str(qe.year)[2:]}'
        doc = [x for x in ex if 'earningsrel' in x.lower()] or [x for x in ex if not re.search(r'metropolis|eager|prwith', x.lower())]
        doc = doc[0]
        base = f"{o['date']}_{o['form']}_{o['acc']}_{doc}".rsplit('.', 1)[0] + '.txt'
        out[per] = dict(date=o['date'], url=f"https://www.sec.gov/Archives/edgar/data/64040/{o['acc'].replace('-', '')}/{doc}", doc=base)
    json.dump(dict(sorted(out.items(), key=lambda kv: (kv[0][-2:], kv[0][1]))), open(os.path.join(BASE, 'data', '_releases.json'), 'w'), indent=1)
    return out
if __name__ == '__main__':
    o = run(); print(len(o)); print(sorted(o, key=lambda k: (k[-2:], k[1])))
