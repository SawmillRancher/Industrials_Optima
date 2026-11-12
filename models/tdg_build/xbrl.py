"""EDGAR XBRL company facts (us-gaap, TransDigm Group Incorporated, CIK 1260221) -> values by fiscal period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. TransDigm's fiscal year ends 30 September
(quarters end on the Saturday nearest the calendar quarter end); FY label = calendar year of the September year end
(FY2026 = Oct-2025 - Sep-2026). pick='first' returns the value as originally filed (10-K / 10-Q only), pick='last' the latest."""
import json, os, datetime as dt
S = os.environ.get('TDG_SRC', '/tmp/tdg_src')
CIK = '1260221'
_F = None
USED = ['ShareBasedCompensation', 'AllocatedShareBasedCompensationExpense', 'DeferredIncomeTaxExpenseBenefit', 'Depreciation',
        'AmortizationOfIntangibleAssets', 'DepreciationDepletionAndAmortization', 'CommonStockSharesIssued', 'TreasuryStockCommonShares',
        'TreasuryStockShares', 'CommonStockSharesOutstanding', 'NetCashProvidedByUsedInOperatingActivities', 'Revenues', 'SalesRevenueNet',
        'RevenueFromContractWithCustomerExcludingAssessedTax', 'NetIncomeLoss', 'ProfitLoss', 'Assets', 'EarningsPerShareDiluted',
        'EarningsPerShareBasicAndDiluted', 'OperatingIncomeLoss', 'InterestExpense', 'InterestIncomeExpenseNet', 'PaymentsOfDividends',
        'PaymentsForRepurchaseOfCommonStock', 'LongTermDebt', 'IncomeTaxesPaidNet', 'InterestPaidNet',
        'FiniteLivedIntangibleAssetsAmortizationExpenseNextTwelveMonths', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearTwo',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearThree', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearFour',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearFive', 'FiniteLivedIntangibleAssetsAmortizationExpenseRemainderOfFiscalYear']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def dump_subset():
    keep = ('start', 'end', 'val', 'filed', 'form')
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
    return e.year + (1 if e.month >= 10 else 0)

def qtr_of(end):
    return {12: 1, 1: 1, 3: 2, 4: 2, 6: 3, 7: 3, 9: 4, 10: 4}.get(dt.date.fromisoformat(end).month)

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def value(concept, fy, kind, q=None, pick='first', with_date=False):
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
    if concept.startswith(('CommonStockShares', 'TreasuryStock')): v = v / 1e6
    elif not concept.startswith('EarningsPerShare'): v = v / 1e6 if abs(v) > 1000 else v
    return (best[0], v) if with_date else v

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None

def earliest_of(concepts, *a, **k):
    """value of the earliest-filed fact across several concepts (as first filed)."""
    best = None
    for c in concepts:
        v = value(c, *a, pick='first', with_date=True, **k)
        if v is not None and (best is None or v[0] < best[0]): best = v
    return None if best is None else best[1]
