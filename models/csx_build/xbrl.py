"""EDGAR XBRL company facts (us-gaap / dei, CSX Corporation, CIK 277948) -> values by fiscal period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. CSX's fiscal year is the calendar year
(quarters ended on the last Friday of the month through 2009, calendar month ends from 2010). pick='first' returns the value
as originally filed (10-K / 10-Q only), pick='last' the latest (restated) value."""
import json, os, datetime as dt
S = os.environ.get('CSX_SRC', '/tmp/csx_src')
CIK = '277948'
_F = None
USED = ['AllocatedShareBasedCompensationExpense', 'DeferredIncomeTaxExpenseBenefit', 'Depreciation', 'DepreciationDepletionAndAmortization',
        'CommonStockSharesOutstanding', 'EntityCommonStockSharesOutstanding', 'NetIncomeLoss', 'Assets', 'EarningsPerShareDiluted', 'OperatingIncomeLoss',
        'Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'NetCashProvidedByUsedInOperatingActivities',
        'WeightedAverageNumberOfDilutedSharesOutstanding', 'Goodwill', 'IntangibleAssetsNetExcludingGoodwill', 'IntangibleAssetsNetIncludingGoodwill',
        'AccountsReceivableNetCurrent', 'InterestExpense', 'InterestExpenseNonoperating', 'PaymentsForRepurchaseOfCommonStock', 'FuelCosts',
        'LaborAndRelatedExpense', 'GoodwillImpairmentLoss', 'CommonStockDividendsPerShareDeclared', 'CommonStockDividendsPerShareCashPaid',
        'GainLossOnDispositionOfAssets', 'EntityNumberOfEmployees', 'LongTermDebtAndCapitalLeaseObligations', 'LongTermDebtAndCapitalLeaseObligationsCurrent',
        'IncomeTaxExpenseBenefit', 'AmortizationOfIntangibleAssets', 'AssetImpairmentCharges', 'RestructuringCharges', 'StockholdersEquity']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def dump_subset():
    """write the concepts used by the model (10-K / 10-Q facts only) to data/_xbrl.json so the build runs without the raw downloads."""
    keep = ('start', 'end', 'val', 'filed', 'form', 'fy', 'fp')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')] for k in USED}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
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

def fy_of(end):
    e = dt.date.fromisoformat(end)
    return e.year + (1 if e.month == 1 else 0)          # 52/53-week year ends never fall in January for CSX; safety only

def qtr_of(end):
    return {3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3, 12: 4, 1: 4}.get(dt.date.fromisoformat(end).month)

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def value(concept, fy, kind, q=None, pick='first', with_filed=False):
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
    if with_filed: return (v / 1e6 if concept in ('CommonStockSharesOutstanding', 'EntityCommonStockSharesOutstanding', 'WeightedAverageNumberOfDilutedSharesOutstanding') else v), best[0]
    if concept in ('CommonStockSharesOutstanding', 'EntityCommonStockSharesOutstanding', 'WeightedAverageNumberOfDilutedSharesOutstanding'): return v / 1e6
    if concept in ('EarningsPerShareDiluted', 'CommonStockDividendsPerShareDeclared', 'CommonStockDividendsPerShareCashPaid', 'EntityNumberOfEmployees'): return v
    return v / 1e6

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None

def cover_shares(fy, q):
    """dei:EntityCommonStockSharesOutstanding from the 10-Q / 10-K for fiscal quarter q (cover-page date, after quarter end)."""
    best = None
    for f in facts().get('EntityCommonStockSharesOutstanding', []):
        if f.get('fy') == fy and f.get('fp') == ('FY' if q == 4 else f'Q{q}') and f.get('form') in ('10-K', '10-Q'):
            if best is None or f['filed'] < best[0]: best = (f['filed'], f['val'], f['end'])
    return None if best is None else (best[1] / 1e6, best[2])
