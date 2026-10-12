"""Map each model period (2006 ... 2025, Q1-13 ... Q2-26) to its source documents in $MCO_SRC/txt: the earnings release (8-K Item
2.02, Ex. 99.1), the 10-Q / 10-K for the period, and the same documents one year later (prior-year comparatives). Writes
$MCO_SRC/period_index.json. Run after make_index.py, fetch.py and fetch_txt.py."""
import json, os, glob, datetime as dt
S = os.environ.get('MCO_SRC', '/tmp/mco_src')
F = json.load(open(os.path.join(S, 'filings.json')))
TXT = sorted(os.listdir(os.path.join(S, 'txt')))

def qend(y, q): return dt.date(y, 3 * q, 31 if q in (1, 4) else 30)
def periods():
    out = [(str(y), qend(y, 4), True) for y in range(2006, 2026)]
    for y in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if (y, q) > (2026, 2): break
            out.append((f'Q{q}-{str(y)[2:]}', qend(y, q), False))
    return out

def docs(acc):
    return [os.path.join(S, 'txt', t) for t in TXT if f'_{acc}_' in t]

def release_for(end):
    lim = (end + dt.timedelta(days=75)).isoformat()
    c = [o for o in F if o['form'] == '8-K' and '2.02' in o['items'] and end.isoformat() < o['date'] <= lim]
    if not c: return None
    def expick(o):
        d = docs(o['acc'])
        ex = [p for p in d if any(k in os.path.basename(p).lower() for k in ('ex99', 'ex-99', 'dex991', 'earningsrelease', 'earningspr', 'ex991'))]
        return ex or sorted([p for p in d if o['primary'].rsplit('.', 1)[0] not in os.path.basename(p)], key=os.path.getsize)[-1:] or d
    # the earnings release is the largest Item 2.02 exhibit in the window (pre-announcements, e.g. 6-Jan-2011 and 17-Jan-2017, are short)
    o = max(c, key=lambda o: max([os.path.getsize(p) for p in expick(o)] or [0]))
    pick = expick(o)
    return {'date': o['date'], 'acc': o['acc'], 'file': max(pick, key=os.path.getsize) if pick else None,
            'url': f"https://www.sec.gov/Archives/edgar/data/1059556/{o['acc'].replace('-', '')}/{os.path.basename(max(pick, key=os.path.getsize)).split('_', 3)[3].rsplit('.', 1)[0] if pick else ''}"}

def filing_for(end, annual_or_q4):
    form = '10-K' if annual_or_q4 else '10-Q'
    c = [o for o in F if o['form'] == form and o['report'] == end.isoformat()]
    if not c: return None
    o = c[0]
    d = docs(o['acc'])
    p = [x for x in d if o['primary'].rsplit('.', 1)[0] in x]
    return {'date': o['date'], 'acc': o['acc'], 'file': p[0] if p else None,
            'url': f"https://www.sec.gov/Archives/edgar/data/1059556/{o['acc'].replace('-', '')}/{o['primary']}"}

out = {}
for key, end, ann in periods():
    q4 = key.startswith('Q4')
    nxt = dt.date(end.year + 1, end.month, end.day)
    out[key] = {'period_end': end.isoformat(), 'release': release_for(end), 'filing': filing_for(end, ann or q4),
                'next_release': release_for(nxt), 'next_filing': filing_for(nxt, ann or q4)}
json.dump(out, open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
miss = [k for k, v in out.items() if not v['release'] or not v['filing'] or not v['release']['file'] or not v['filing']['file']]
print(len(out), 'periods; missing:', miss)
