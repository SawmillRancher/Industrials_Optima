"""Assemble data/<period>.json for ODFL from the downloaded EDGAR documents.

Quarter records (Q1-13 ... Q2-26): IS / operating statistics from that quarter's earnings release (8-K Item 2.02, Ex. 99.1),
three-month column, as originally reported; balance sheet and year-to-date cash flow from the 10-Q (Q4: 10-K).
Annual records (2006 ... 2025): Q4 release year-to-date columns + the 10-K (balance sheet, cash flow, network data).
Units: USD millions (source in thousands ÷ 1,000), shares in millions; per-share as published, split basis recorded.
"""
import csv, datetime as dt, glob, json, os, re, sys
import parse_release as PR
import parse_fin as PF

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('ODFL_SRC', '/tmp/claude-0/-home-user-Industrials-Optima/9730001d-1163-52b2-9b31-6b83e69b543f/scratchpad/src')
OUT = os.path.join(BASE, 'data')
FIL = list(csv.DictReader(open(os.path.join(BASE, 'filings.csv'))))
D = lambda s: dt.date.fromisoformat(s)

# stock splits: (payment date, ratio) — 3-for-2 Aug-2010, Sep-2012, Mar-2020; 2-for-1 Mar-2024
SPLITS = [(D('2010-08-23'), 1.5), (D('2012-09-07'), 1.5), (D('2020-03-25'), 1.5), (D('2024-03-27'), 2.0)]
def split_factor(filed):
    """multiplier that restates a document filed on `filed` to the current (post Mar-2024) share basis."""
    f = 1.0
    for d, r in SPLITS:
        if D(filed) < d: f *= r
    return f

def docs(f, kind):
    tag = f"{f['filed']}_{f['form'].replace('/', '')}_{f['accession']}"
    fs = sorted(glob.glob(os.path.join(SRC, tag + '__*.txt')))
    if kind == 'release':
        ex = [p for p in fs if re.search(r'(?i)ex-?99|dex99|ex99|press', os.path.basename(p).split('__')[1])]
        return ex or [p for p in fs if not p.endswith('__' + f['primary_doc'].rsplit('.', 1)[0] + '.txt')] or fs
    return [p for p in fs if p.endswith('__' + f['primary_doc'].rsplit('.', 1)[0] + '.txt')] or fs

QEND = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
QWORD = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth'}

def find_release(y, q):
    end = dt.date(y, *QEND[q])
    for f in FIL:
        if not f['form'].startswith('8-K') or '2.02' not in f['items']: continue
        if not (end < D(f['filed']) <= end + dt.timedelta(days=80)): continue
        for p in docs(f, 'release'):
            t = open(p, errors='ignore').read()
            head = t[:6000].lower()
            if QWORD[q] not in head and f'{QWORD[q]} quarter' not in head and not (q == 4 and 'year' in head): continue
            r = PR.parse(t)
            if r and r['q'].get('revenue'): return f, p, r
    return None, None, None

def find_filing(end, form):
    c = [f for f in FIL if f['form'] == form and f['period'] == end.isoformat()]
    return c[0] if c else None

M = lambda v: None if v is None else round(v / 1000.0, 6)

def is_record(v, filed):
    sf = split_factor(filed)
    g = v.get
    rec = {k: M(g(k)) for k in ('revenue', 'ltl_rev', 'other_rev', 'swb', 'ops', 'gen', 'taxlic', 'ins', 'comm', 'dda', 'pt', 'rents',
                                 'misc', 'total_opex', 'op_income', 'int_exp', 'int_inc', 'int_net', 'other_exp', 'ebt', 'tax', 'cum_eff', 'net_income')}
    if rec['int_net'] is None and rec['int_exp'] is not None:
        rec['int_net'] = round(rec['int_exp'] + (rec['int_inc'] or 0.0), 6)
    for k in ('sh_basic', 'sh_dil'):
        rec[k] = None if g(k) is None else round(g(k) / 1000.0 * sf, 4)
    for k in ('eps_basic', 'eps_dil', 'dps'):
        rec[k] = None if g(k) is None else round(g(k) / sf, 6)
    rec['eps_dil_pub'] = g('eps_dil'); rec['split_factor'] = sf
    return rec

def st_record(v):
    keys = ('work_days', 'or_pub', 'miles', 'ltl_tons', 'tons_day', 'total_tons', 'ltl_ship', 'ship_day', 'total_ship', 'rev_mile',
            'rev_cwt', 'rev_cwt_xf', 'rev_shp', 'rev_shp_xf', 'wps', 'loh', 'emp_avg')
    return {k: v.get(k) for k in keys}

def fin_record(path, filed):
    t = open(path, errors='ignore').read()
    bs, cf = PF.parse(t)
    sf = split_factor(filed)
    out = {}
    if bs:
        raw = bs.pop('lines_raw')
        out['bs'] = {k: M(v) for k, v in bs.items()}
        out['bs']['lines_raw'] = [[a, M(b)] for a, b in raw]
        m = re.search(r'(?i)([\d,]{9,})\s+(and\s+[\d,]{9,}\s+)?shares (issued and )?outstanding', ' '.join(a for a, _ in raw))
        if m: out['bs']['shares_outstanding_end'] = round(int(m.group(1).replace(',', '')) / 1e6 * sf, 4)
    if cf:
        raw = cf.pop('lines_raw')
        out['cf'] = {k: M(v) for k, v in cf.items()}
        out['cf']['lines_raw'] = [[a, M(b)] for a, b in raw]
    return out, t

def cover_shares(t, filed):
    m = re.search(r'(?is)([\d,]{9,})\s*(shares of (the registrant.s )?common stock|shares of common stock).{0,120}outstanding', t[:20000])
    if not m:
        m = re.search(r'(?is)outstanding.{0,200}?([\d,]{9,})\s*shares', t[:20000])
    return round(int(m.group(1).replace(',', '')) / 1e6 * split_factor(filed), 4) if m else None

def network(t):
    """10-K Item 1 / Item 2: service centers, tractors, trailers, full-time employees (year end)."""
    def g(*rxs):
        for rx in rxs:
            m = re.search(rx, t, re.I | re.S)
            if m: return int(m.group(1).replace(',', ''))
        return None
    return {
        'service_centers': g(r'total of (\d{3}) service centers', r'(?:operated|operate)\s+(\d{3})\s+service centers',
                             r'\d{3} of the (\d{3}) service centers', r'network of (\d{3}) service centers'),
        'tractors': g(r'owned ([\d,]{4,6}) tractors', r'\n\s*Tractors \| ([\d,]{4,6}) \| \d+\.\d', r'([\d,]{4,6})\s+tractors'),
        'trailers_lh': g(r'\n\s*Linehaul trailers \| ([\d,]{4,6})', r'([\d,]{4,6}) linehaul trailers'),
        'trailers_pd': g(r'\n\s*Pickup and delivery trailers \| ([\d,]{4,6})', r'([\d,]{4,6}) pickup and delivery trailers'),
        'employees': g(r'employed ([\d,]{4,6}) (?:active )?full-time',
                       r'(?:employed|employ|had)\s+(?:approximately\s+)?([\d,]{4,6})\s+(?:full-time\s+)?(?:employees|associates|team members|individuals)'),
    }

def build_quarter(y, q):
    key = f'Q{q}-{str(y)[2:]}'
    f, p, r = find_release(y, q)
    rec = {'period': key, 'sources': {}, 'notes': []}
    if r:
        rec['sources']['release'] = f['folder_url'] + os.path.basename(p).split('__')[1].replace('.txt', '.htm')
        rec['is'] = is_record(r['q'], f['filed']); rec['stats'] = st_record(r['q']); rec['labels'] = r['labels']
        rec['is']['_filed'] = f['filed']
    else:
        rec['notes'].append('no earnings release found')
    end = dt.date(y, *QEND[q])
    ff = find_filing(end, '10-Q' if q < 4 else '10-K')
    if ff:
        dp = docs(ff, 'filing')
        if dp:
            fr, t = fin_record(dp[0], ff['filed'])
            rec.update(fr)
            rec['sources']['10k_or_10q'] = ff['folder_url'] + ff['primary_doc']
            if rec.get('cf') is not None: rec['cf']['ytd_months'] = 3 * q
            if 'bs' in rec and rec['bs'].get('shares_outstanding_end') is None:
                rec['bs']['shares_outstanding_end'] = cover_shares(t, ff['filed'])
            rec['_filing_filed'] = ff['filed']
    return key, rec

def build_year(y):
    key = str(y)
    f, p, r = find_release(y, 4)
    rec = {'period': key, 'sources': {}, 'notes': []}
    if r and r['ytd'].get('revenue'):
        rec['sources']['release'] = f['folder_url'] + os.path.basename(p).split('__')[1].replace('.txt', '.htm')
        rec['is'] = is_record(r['ytd'], f['filed']); rec['stats'] = st_record(r['ytd']); rec['labels'] = r['labels']
        rec['is']['_filed'] = f['filed']
    ff = find_filing(dt.date(y, 12, 31), '10-K')
    if ff:
        dp = docs(ff, 'filing')
        fr, t = fin_record(dp[0], ff['filed'])
        rec.update(fr)
        rec['sources']['10k_or_10q'] = ff['folder_url'] + ff['primary_doc']
        if rec.get('cf') is not None: rec['cf']['ytd_months'] = 12
        if 'bs' in rec and rec['bs'].get('shares_outstanding_end') is None:
            rec['bs']['shares_outstanding_end'] = cover_shares(t, ff['filed'])
        rec['extra'] = network(t)
        rec['_filing_filed'] = ff['filed']
        if 'is' not in rec: rec['notes'].append('IS from 10-K required (no Q4 release YTD columns)')
    return key, rec

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    recs = {}
    for y in range(2006, 2026):
        k, r = build_year(y); recs[k] = r
    for y in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if y == 2026 and q > 2: break
            k, r = build_quarter(y, q); recs[k] = r
    for k, r in recs.items():
        # manual overrides (data/manual/<key>.json) are merged by normalize.py, raw extraction kept here
        json.dump(r, open(os.path.join(OUT, f'{k}.json'), 'w'), indent=1)
    miss = [(k, [s for s in ('is', 'stats', 'bs', 'cf') if s not in r]) for k, r in recs.items()]
    print([m for m in miss if m[1]])
