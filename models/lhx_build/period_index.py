"""Period index for the extraction: maps each period key to its text sources in $LHX_SRC/txt (release = 8-K Item 2.02 exhibits,
filing = 10-Q / 10-K / 10-KT, next_release / next_filing = the same documents one year later, for comparatives).
Period keys: 2013..2019 = Harris fiscal years ended the Friday nearest 30-Jun; Q3-19 / Q4-19 / TP19 = the transition period
(29-Jun-2019 - 3-Jan-2020); Q1-20.. = calendar-fiscal quarters; 2020.. = fiscal years ended the Friday nearest 31-Dec."""
import json, os
S = os.environ.get('LHX_SRC', '/tmp/lhx_src')
F = json.load(open(os.path.join(S, 'filings.json')))
def txt(o, x): return f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{x.rsplit('.', 1)[0]}.txt"
def url(o, x): return f"https://www.sec.gov/Archives/edgar/data/202058/{o['acc'].replace('-', '')}/{x}"
REL = [o for o in F if o['form'] == '8-K' and '2.02' in o['items']]
FIL = [o for o in F if o['form'] in ('10-K', '10-Q', '10-KT')]
def rel(d0, d1):
    out = []
    for o in REL:
        if d0 <= o['date'] <= d1:
            for x in o['files']:
                if x != o['primary'] and os.path.exists(os.path.join(S, 'txt', txt(o, x))) and 'transcript' not in x:
                    out.append({'txt': txt(o, x), 'url': url(o, x)})
    return out
def fil(d0, d1):
    for o in FIL:
        if d0 <= o['date'] <= d1: return {'txt': txt(o, o['primary']), 'url': url(o, o['primary']), 'form': o['form']}
P = {}
def add(k, r, f, end): P[k] = {'period_end': end, 'release': rel(*r), 'filing': fil(*f)}
FYREL = {2013: '2013-07-30', 2014: '2014-07-29', 2015: '2015-08-07', 2016: '2016-08-02', 2017: '2017-08-01', 2018: '2018-07-31', 2019: '2019-07-31'}
FYEND = {2013: '2013-06-28', 2014: '2014-06-27', 2015: '2015-07-03', 2016: '2016-07-01', 2017: '2017-06-30', 2018: '2018-06-29', 2019: '2019-06-28'}
for y, d in FYREL.items(): add(str(y), (d, d), (f'{y}-08-01', f'{y}-09-15'), FYEND[y])
add('Q3-19', ('2019-10-30', '2019-10-30'), ('2019-10-01', '2019-11-15'), '2019-09-27')
add('Q4-19', ('2020-02-04', '2020-02-04'), ('2020-02-15', '2020-03-15'), '2020-01-03')
add('TP19', ('2020-02-04', '2020-02-04'), ('2020-02-15', '2020-03-15'), '2020-01-03')
QEND = {}
for o in FIL:
    if o['date'] >= '2020-04-01':
        e = o['report']; y, m = int(e[:4]), int(e[5:7])
        if o['form'] == '10-K': fy = y if m == 12 else y - 1; QEND[(fy, 4)] = (e, o)
        else: QEND[(y, {3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3}[m])] = (e, o)
for (y, q), (e, o) in sorted(QEND.items()):
    k = f'Q{q}-{str(y)[2:]}'
    r = [x for x in REL if x['date'] <= o['date'] and x['date'] >= e]
    r = r[-1] if r else None
    P[k] = {'period_end': e, 'release': rel(r['date'], r['date']) if r else [], 'filing': {'txt': txt(o, o['primary']), 'url': url(o, o['primary']), 'form': o['form']}}
    if q == 4: P[str(y)] = dict(P[k])
def nxt(k):
    if k.isdigit(): return str(int(k) + 1)
    if k == 'TP19': return '2020'
    return f'{k[:3]}{int(k[3:]) + 1}'
for k, v in P.items():
    n = P.get(nxt(k))
    if n: v['next_release'] = n['release']; v['next_filing'] = n['filing']
json.dump(P, open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
for k, v in P.items(): print(k, v['period_end'], [r['txt'][-34:] for r in v['release']], v['filing'] and v['filing']['txt'][11:40])
