"""EDGAR XBRL company facts (FedEx Corporation, CIK 1048911) -> values by period, as first filed (10-K / 10-Q only).

Legacy fiscal periods end 31-Aug (Q1), 30-Nov (Q2), 28/29-Feb (Q3), 31-May (Q4 / FY); FY label = calendar year of the May year end.
Used for items the releases omit: share-based compensation, dividends declared per share, weighted basic shares, basic EPS, cover-page
shares outstanding, and for cross-checks (operating income, net income, diluted EPS, total assets, operating cash flow).
data/_xbrl.json holds the subset used, so the build runs without the raw download."""
import json, os, datetime as dt
S = os.environ.get('FDX_SRC', '/tmp/fdx_src')
CIK = '1048911'
_F = None
USED = ['ShareBasedCompensation', 'AllocatedShareBasedCompensationExpense', 'CommonStockDividendsPerShareDeclared',
        'WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfDilutedSharesOutstanding', 'EarningsPerShareBasic',
        'EarningsPerShareDiluted', 'OperatingIncomeLoss', 'NetIncomeLoss', 'Assets', 'NetCashProvidedByUsedInOperatingActivities',
        'Revenues', 'StockholdersEquity', 'dei:EntityCommonStockSharesOutstanding']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')
FORMS = ('10-K', '10-Q', '10-K/A', '10-Q/A', '10-KT')

def facts():
    global _F
    if _F is not None: return _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if os.path.exists(raw):
        d = json.load(open(raw))['facts']; _F = {}
        for ns in ('us-gaap', 'dei'):
            for k, v in d.get(ns, {}).items():
                kk = k if ns == 'us-gaap' else 'dei:' + k
                for u, fs in v['units'].items():
                    if kk in ('EarningsPerShareBasic', 'EarningsPerShareDiluted') and u == 'shares': continue
                    _F.setdefault(kk, []).extend(fs)
    else:
        _F = json.load(open(SUBSET))
    return _F

def dump_subset():
    keep = ('start', 'end', 'val', 'filed', 'form')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in FORMS] for k in USED}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def fy_of(end):
    e = dt.date.fromisoformat(end)
    return e.year + (1 if e.month >= 6 else 0)
def qtr_of(end):
    return {8: 1, 11: 2, 2: 3, 5: 4}.get(dt.date.fromisoformat(end).month)
def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def value(concept, fy, kind, q=None, pick='first'):
    """kind 'FY' | 'Q' | 'YTD' (q: 1 Q, 2 H, 3 9M, 4 FY) | 'I' (instant at the end of fiscal quarter q)."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in FORMS or dur(f) != want: continue
        if fy_of(f['end']) != fy or qtr_of(f['end']) != qq: continue
        if best is None or (f['filed'] < best[0] if pick == 'first' else f['filed'] > best[0]): best = (f['filed'], f['val'])
    if best is None: return None
    v = best[1]
    return v / 1e6 if abs(v) > 5000 else v

def span(concept, start, end, pick='first'):
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in FORMS or f.get('start') != start or f['end'] != end: continue
        if best is None or f['filed'] < best[0]: best = (f['filed'], f['val'])
    if best is None: return None
    return best[1] / 1e6 if abs(best[1]) > 5000 else best[1]

def cover_shares(lo, hi):
    """dei:EntityCommonStockSharesOutstanding with an 'as of' date in [lo, hi] (cover page of the 10-Q / 10-K for the period)."""
    c = [f for f in facts().get('dei:EntityCommonStockSharesOutstanding', []) if lo <= f['end'] <= hi and f.get('form') in FORMS]
    if not c: return None, None
    f = sorted(c, key=lambda f: f['filed'])[0]
    return f['val'] / 1e6, f['end']
