"""EDGAR XBRL company facts (Union Pacific, CIK 100885; calendar fiscal year) -> values by period, for cross-checks and for the
items the releases omit (share-based compensation, shares outstanding, interest on operating leases).

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated) value. data/_xbrl.json holds the subset the build needs."""
import json, os, datetime as dt
S = os.environ.get('UNP_SRC', '/tmp/unp_src')
_F = None
USED = ['Revenues', 'OperatingIncomeLoss', 'NetIncomeLoss', 'EarningsPerShareDiluted', 'NetCashProvidedByUsedInOperatingActivities', 'Assets',
        'ShareBasedCompensation', 'AllocatedShareBasedCompensationExpense', 'Depreciation', 'DepreciationDepletionAndAmortization',
        'CommonStockSharesOutstanding', 'EntityCommonStockSharesOutstanding', 'CommonStockDividendsPerShareDeclared', 'LongTermDebt',
        'OperatingLeaseLiability', 'DefinedBenefitPlanFundedStatusOfPlan', 'PaymentsForRepurchaseOfCommonStock', 'IncomeTaxExpenseBenefit',
        'InterestExpense', 'DeferredIncomeTaxExpenseBenefit', 'CostsAndExpenses', 'OperatingExpenses', 'PaymentsToAcquireProductiveAssets',
        'StockholdersEquity', 'LongTermDebtNoncurrent', 'LongTermDebtCurrent', 'DebtCurrent', 'CashAndCashEquivalentsAtCarryingValue',
        'WeightedAverageNumberOfDilutedSharesOutstanding', 'OtherNonoperatingIncomeExpense', 'PaymentsOfDividendsCommonStock']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def dump_subset():
    keep = ('start', 'end', 'val', 'filed', 'form', 'fy', 'fp')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')] for k in USED}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    raw = os.path.join(S, 'companyfacts.json')
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(raw):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        d = json.load(open(raw))['facts']
        for tax in ('us-gaap', 'dei'):
            for k, v in d.get(tax, {}).items():
                for u, fs in v['units'].items():
                    _F.setdefault(k, []).extend(fs)
    return _F

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def qtr_of(end):
    return {3: 1, 6: 2, 9: 3, 12: 4}.get(dt.date.fromisoformat(end).month)

def value(concept, year, kind, q=None, pick='first', scale=1e6):
    """kind: 'FY' | 'Q' | 'YTD' (q months-to-date) | 'I' (instant at quarter q end; q=4 -> 31 Dec)."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in ('10-K', '10-Q', '10-K/A', '10-Q/A'): continue
        if dur(f) != want: continue
        e = dt.date.fromisoformat(f['end'])
        if e.year != year or qtr_of(f['end']) != qq: continue
        if kind == 'I' and e.day < 28: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    if concept in ('EarningsPerShareDiluted', 'CommonStockDividendsPerShareDeclared'): return v
    return v / scale

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None

if __name__ == '__main__':
    dump_subset()
    print('subset written', os.path.getsize(SUBSET))
