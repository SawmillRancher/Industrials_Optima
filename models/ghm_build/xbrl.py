"""EDGAR XBRL company facts (us-gaap / dei, Graham Corporation, CIK 716314) -> values by fiscal period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. Graham's fiscal year ends 31 March;
FY label = calendar year of the March year end (FY2027 = Apr-2026 - Mar-2027). pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated) value. Graham's XBRL starts with FY2010 (FY2011 10-K comparatives)."""
import json, os, datetime as dt
S = os.environ.get('GHM_SRC', '/tmp/ghm_src')
CIK = '716314'
_F = None
USED = ['ShareBasedCompensation', 'DeferredIncomeTaxExpenseBenefit', 'Depreciation', 'AmortizationOfIntangibleAssets',
        'CommonStockSharesIssued', 'CommonStockSharesOutstanding', 'TreasuryStockCommonShares', 'TreasuryStockShares',
        'NetCashProvidedByUsedInOperatingActivities', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues',
        'NetIncomeLoss', 'Assets', 'EarningsPerShareDiluted', 'OperatingIncomeLoss', 'IncomeTaxExpenseBenefit', 'PaymentsToAcquirePropertyPlantAndEquipment',
        'FiniteLivedIntangibleAssetsAmortizationExpenseNextTwelveMonths', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearTwo',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearThree', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearFour',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearFive', 'FiniteLivedIntangibleAssetsAmortizationExpenseRemainderOfFiscalYear',
        'CommonStockDividendsPerShareDeclared', 'PaymentsOfDividendsCommonStock', 'PaymentsForRepurchaseOfCommonStock', 'WeightedAverageNumberOfDilutedSharesOutstanding']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def dump_subset():
    """write the concepts used by the model (10-K / 10-Q facts only) to data/_xbrl.json so the build runs without the raw downloads."""
    keep = ('start', 'end', 'val', 'filed', 'form')
    fs = facts()
    out = {k: [{a: f[a] for a in keep if a in f} for f in fs.get(k, []) if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')] for k in USED + ['dei:EntityCommonStockSharesOutstanding']}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(raw):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        d = json.load(open(raw))['facts']
        for k, v in d.get('us-gaap', {}).items():
            for u, fs in v['units'].items():
                _F.setdefault(k, []).extend(fs)
        for k, v in d.get('dei', {}).items():
            for u, fs in v['units'].items():
                _F.setdefault('dei:' + k, []).extend(fs)
    return _F

def fy_of(end):
    e = dt.date.fromisoformat(end)
    return e.year + (1 if e.month >= 4 else 0)

def qtr_of(end):
    return {6: 1, 7: 1, 9: 2, 10: 2, 12: 3, 1: 3, 3: 4, 4: 4}.get(dt.date.fromisoformat(end).month)

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
    if concept.startswith(('CommonStockShares', 'TreasuryStock', 'WeightedAverage')): return v / 1e6
    if concept in ('EarningsPerShareDiluted', 'CommonStockDividendsPerShareDeclared'): return v
    return v / 1e6 if abs(v) > 1000 else v

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None

def dei_shares(fy, q):
    """cover-page shares outstanding (dei) of the 10-Q / 10-K for fiscal quarter q of fy (date = cover date), in millions."""
    best = None
    for f in facts().get('dei:EntityCommonStockSharesOutstanding', []):
        if f.get('form') not in ('10-K', '10-Q'): continue
        e = dt.date.fromisoformat(f['end'])
        # cover date is ~1-2 months after the quarter end
        pe = {1: (6, 30), 2: (9, 30), 3: (12, 31), 4: (3, 31)}[q]
        yr = fy - 1 if q in (1, 2, 3) else fy
        pend = dt.date(yr, pe[0], pe[1])
        if 0 <= (e - pend).days <= 80:
            if best is None or f['filed'] < best[0]: best = (f['filed'], f['val'], f['end'])
    return None if best is None else {'shares': best[1] / 1e6, 'date': best[2]}
