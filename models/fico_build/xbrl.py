"""EDGAR XBRL company facts (us-gaap, Fair Isaac Corporation, CIK 814547) -> values by fiscal period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. Fair Isaac's fiscal year ends 30 September;
FY label = calendar year of the September year end (FY2026 = Oct-2025 - Sep-2026). pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated) value."""
import json, os, datetime as dt
S = os.environ.get('FICO_SRC', '/tmp/fico_src')
CIK = '814547'
_F = None
USED = ['CommonStockSharesOutstanding', 'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'NetIncomeLoss',
        'OperatingIncomeLoss', 'Assets', 'EarningsPerShareDiluted', 'NetCashProvidedByUsedInOperatingActivities', 'ShareBasedCompensation',
        'DepreciationDepletionAndAmortization', 'DepreciationAndAmortization', 'PaymentsForRepurchaseOfCommonStock', 'IncomeTaxExpenseBenefit']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def shares_out():
    """shares outstanding at each fiscal period end (CommonStockSharesOutstanding, balance-sheet parenthetical, as first filed), millions,
    keyed by model period ('2009' ... '2025' for 30-Sep; 'Q1-13' ... 'Q3-26' for quarter ends)."""
    out = {}
    for f in facts().get('CommonStockSharesOutstanding', []):
        if f.get('form') not in ('10-K', '10-Q', '10-K/A', '10-Q/A') or 'start' in f: continue
        fy, q = fy_of(f['end']), qtr_of(f['end'])
        if q is None: continue
        for k in ([str(fy)] if q == 4 else []) + ([f'Q{q}-{str(fy)[2:]}'] if fy >= 2013 else []):
            if k not in out or f['filed'] < out[k][0]: out[k] = (f['filed'], f['val'] / 1e6)
    return {k: v for k, (_, v) in out.items()}

def dump_subset():
    """write the concepts used by the build (10-K / 10-Q facts only) and the shares-outstanding map to data/_xbrl.json, so the
    build and check_data run without the raw downloads."""
    keep = ('start', 'end', 'val', 'filed', 'form')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')] for k in USED}
    out['shares_out'] = shares_out()
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(raw):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        d = json.load(open(raw))['facts'].get('us-gaap', {})
        for k, v in d.items():
            for u, fs in v['units'].items():
                _F.setdefault(k, []).extend(fs)
    return _F

def fy_of(end):
    e = dt.date.fromisoformat(end)
    return e.year + (1 if e.month >= 10 else 0)

def qtr_of(end):
    return {12: 1, 1: 1, 3: 2, 4: 2, 6: 3, 7: 3, 9: 4, 10: 4}.get(dt.date.fromisoformat(end).month)

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def value(concept, fy, kind, q=None, pick='first'):
    """kind: 'FY' | 'Q' | 'YTD' (q months-to-date: 1->Q, 2->H, 3->9M, 4->FY) | 'I' (instant at quarter q end, q=4 -> FY end)."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in ('10-K', '10-Q', '10-K/A', '10-Q/A'): continue
        if dur(f) != want: continue
        if fy_of(f['end']) != fy or qtr_of(f['end']) != qq: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    if concept.startswith(('CommonStockShares', 'TreasuryStock')): return v / 1e6
    return v / 1e6 if abs(v) > 1000 else v

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
