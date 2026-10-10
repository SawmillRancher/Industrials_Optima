"""EDGAR XBRL company facts (us-gaap) for the three STERIS registrants -> values by fiscal period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. STERIS fiscal year ends 31 March;
FY label = calendar year of the March year end (FY2026 = Apr-2025 - Mar-2026). Each fact keeps the filing it came from;
pick='first' returns the value as originally filed, pick='last' the latest (restated) value."""
import json, os, datetime as dt
S = os.environ.get('STE_SRC', '/tmp/ste_src')
CIKS = ['815065', '1624899', '1757898']
_F = None

USED = ['DepreciationDepletionAndAmortization', 'ShareBasedCompensation', 'DeferredIncomeTaxExpenseBenefit', 'Goodwill', 'MinorityInterest',
        'CommonStockSharesOutstanding', 'InterestExpense', 'InterestExpenseDebt', 'InterestExpenseNonoperating']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def dump_subset():
    """write the concepts used by the model (10-K / 10-Q facts only) to data/_xbrl.json so the build runs without the raw downloads."""
    keep = ('start', 'end', 'val', 'filed', 'form')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')] for k in USED}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(os.path.join(S, f'cf_{CIKS[0]}.json')):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        for c in CIKS:
            d = json.load(open(os.path.join(S, f'cf_{c}.json')))['facts'].get('us-gaap', {})
            for k, v in d.items():
                for u, fs in v['units'].items():
                    _F.setdefault(k, []).extend(fs)
    return _F

def fy_of(end):
    e = dt.date.fromisoformat(end)
    return e.year + (1 if e.month > 3 else 0)

def qtr_of(end):
    m = dt.date.fromisoformat(end).month
    return {6: 1, 7: 1, 9: 2, 10: 2, 12: 3, 1: 3, 3: 4, 4: 4}.get(m)

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
    return None if best is None else best[1] / 1e6 if abs(best[1]) > 1000 else best[1]

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
