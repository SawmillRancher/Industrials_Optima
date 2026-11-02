"""EDGAR XBRL company facts (us-gaap / dei, Federal Signal Corporation, CIK 277509) -> values by calendar period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated) value. Facts are in USD (converted to millions) or shares (millions)."""
import json, os, datetime as dt
S = os.environ.get('FSS_SRC', '/tmp/fss_src')
CIK = '277509'
_F = None
USED = ['ShareBasedCompensation', 'AllocatedShareBasedCompensationExpense', 'DeferredIncomeTaxExpenseBenefit', 'DepreciationDepletionAndAmortization',
        'PaymentsOfDividendsCommonStock', 'CommonStockDividendsPerShareDeclared', 'CommonStockSharesOutstanding', 'EntityCommonStockSharesOutstanding',
        'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'OperatingIncomeLoss', 'NetIncomeLoss',
        'IncomeLossFromContinuingOperations', 'EarningsPerShareDiluted', 'Assets', 'InterestExpense', 'IncomeTaxExpenseBenefit',
        'AmortizationOfIntangibleAssets', 'Depreciation', 'PaymentsForRepurchaseOfCommonStock', 'LongTermDebtAndCapitalLeaseObligations',
        'LongTermDebtAndCapitalLeaseObligationsCurrent', 'Goodwill', 'IntangibleAssetsNetExcludingGoodwill',
        'FiniteLivedIntangibleAssetsAmortizationExpenseNextTwelveMonths', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearTwo',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearThree', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearFour',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearFive', 'FiniteLivedIntangibleAssetsAmortizationExpenseRemainderOfFiscalYear',
        'FiniteLivedIntangibleAssetsAmortizationExpenseAfterYearFive', 'RestructuringCharges', 'BusinessCombinationAcquisitionRelatedCosts',
        'IncomeLossFromDiscontinuedOperationsNetOfTax', 'WeightedAverageNumberOfDilutedSharesOutstanding', 'CommonStockSharesIssued', 'TreasuryStockCommonShares',
        'TreasuryStockShares', 'PaymentsRelatedToTaxWithholdingForShareBasedCompensation']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def dump_subset():
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
        j = json.load(open(raw))['facts']
        for tax in ('us-gaap', 'dei'):
            for k, v in j.get(tax, {}).items():
                for u, fs in v['units'].items():
                    _F.setdefault(k, []).extend(fs)
    return _F

def qtr_of(end):
    return {3: 1, 6: 2, 9: 3, 12: 4}.get(dt.date.fromisoformat(end).month)

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def value(concept, fy, kind, q=None, pick='first'):
    """kind: 'FY' | 'Q' | 'YTD' (q months-to-date: 1->Q, 2->H, 3->9M, 4->FY) | 'I' (instant at quarter q end) | 'cover' (dei shares on the cover of the filing for fy/q)."""
    if kind == 'cover':
        best = None
        for f in facts().get(concept, []):
            if f.get('form') not in ('10-K', '10-Q'): continue
            if f.get('fy') != fy: continue
            fp = f.get('fp')
            if (q == 4 and fp == 'FY') or (q and fp == f'Q{q}'):
                key = f['filed']
                if best is None or key < best[0]: best = (key, f['val'])
        return None if best is None else best[1] / 1e6
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in ('10-K', '10-Q', '10-K/A', '10-Q/A'): continue
        if dur(f) != want: continue
        e = dt.date.fromisoformat(f['end'])
        if e.year != fy or qtr_of(f['end']) != qq: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    if concept.startswith(('CommonStockShares', 'TreasuryStock', 'WeightedAverage', 'EntityCommon')): return v / 1e6
    if concept in ('EarningsPerShareDiluted', 'CommonStockDividendsPerShareDeclared'): return v
    return v / 1e6

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
