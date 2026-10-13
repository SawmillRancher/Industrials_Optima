"""EDGAR XBRL company facts (RBC Bearings, CIK 1324948) -> values by fiscal period (cross-checks and shares outstanding).

RBC's fiscal year ends on the Saturday nearest 31 March (FY label = calendar year of that March / April). Durations: 'Q' (~3 months),
'H' (6), '9M' (9), 'FY' (12); instants at period end. pick='first' returns the value as originally filed (10-K / 10-Q only)."""
import json, os, datetime as dt
from period_index import fq
S = os.environ.get('RBC_SRC', '/tmp/rbc_src')
CIK = '1324948'
_F = None
USED = ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'OperatingIncomeLoss', 'NetIncomeLoss',
        'EarningsPerShareDiluted', 'NetCashProvidedByUsedInOperatingActivities', 'Assets', 'CommonStockSharesOutstanding',
        'CommonStockSharesIssued', 'TreasuryStockShares', 'TreasuryStockCommonShares', 'dei:EntityCommonStockSharesOutstanding']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(raw):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        d = json.load(open(raw))['facts']
        for ns in ('us-gaap', 'dei'):
            for k, v in d.get(ns, {}).items():
                kk = k if ns == 'us-gaap' else 'dei:' + k
                for u, fs in v['units'].items(): _F.setdefault(kk, []).extend(fs)
    return _F

def dump_subset():
    keep = ('start', 'end', 'val', 'filed', 'form')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')] for k in USED}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def value(concept, fy, kind, q=None, pick='first'):
    """kind: 'FY' | 'Q' | 'I' (instant at quarter q end; q=4 -> fiscal year end)."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}[kind]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in ('10-K', '10-Q', '10-K/A', '10-Q/A'): continue
        if dur(f) != want: continue
        try:
            if fq(f['end']) != (fy, qq): continue
        except ValueError: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    if 'Shares' in concept: return v / 1e6
    return v / 1e6 if abs(v) > 1000 else v

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
