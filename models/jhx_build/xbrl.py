"""EDGAR XBRL company facts (us-gaap / dei) for James Hardie (CIK 1159152) -> values by fiscal period.

Fiscal year ends 31 March; FY label = calendar year of the March year end (FY2026 = Apr-2025 - Mar-2026). 20-F XBRL covers
FY2011 onward (annual only); 10-K / 10-Q from FY2026. pick='first' = as originally filed; 'last' = latest (restated)."""
import json, os, datetime as dt
S = os.environ.get('JHX_SRC', '/tmp/jhx_src')
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')
_F = None
USED = ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'SalesRevenueGoodsNet', 'OperatingIncomeLoss',
        'NetIncomeLoss', 'ProfitLoss', 'IncomeLossFromContinuingOperations', 'EarningsPerShareDiluted', 'EarningsPerShareBasic',
        'WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic',
        'NetCashProvidedByUsedInOperatingActivities', 'Assets', 'DepreciationDepletionAndAmortization', 'DepreciationAndAmortization',
        'ShareBasedCompensation', 'DeferredIncomeTaxExpenseBenefit', 'PaymentsToAcquirePropertyPlantAndEquipment', 'CommonStockSharesOutstanding',
        'EntityCommonStockSharesOutstanding', 'LongTermDebtNoncurrent', 'LongTermDebt', 'StockholdersEquity', 'InterestExpense',
        'IncomeTaxExpenseBenefit', 'GrossProfit', 'CostOfGoodsAndServicesSold', 'CostOfRevenue', 'SellingGeneralAndAdministrativeExpense',
        'ResearchAndDevelopmentExpense', 'AmortizationOfIntangibleAssets', 'Goodwill', 'IntangibleAssetsNetExcludingGoodwill',
        'PaymentsOfDividends', 'PaymentsForRepurchaseOfCommonStock', 'CommonStockDividendsPerShareDeclared', 'Depreciation']

def dump_subset():
    keep = ('start', 'end', 'val', 'filed', 'form', 'fy', 'fp')
    out = {}
    for k, fs in facts().items():
        if k in USED: out[k] = [{a: f[a] for a in keep if a in f} for f in fs]
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    if _F is None:
        raw = os.path.join(S, 'companyfacts.json')
        if os.path.exists(raw):
            _F = {}
            d = json.load(open(raw))['facts']
            for tax in ('us-gaap', 'dei'):
                for k, v in d.get(tax, {}).items():
                    for u, fs in v['units'].items():
                        _F.setdefault(k, []).extend(fs)
        else:
            _F = json.load(open(SUBSET))
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

def value(concept, fy, kind, q=None, pick='first', forms=('20-F', '10-K', '10-Q', '20-F/A', '10-K/A', '10-Q/A')):
    """kind: 'FY' | 'Q' | 'YTD' (q months-to-date: 1->Q, 2->H, 3->9M, 4->FY) | 'I' (instant at quarter q end; q=4 -> FY end)."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in forms: continue
        if dur(f) != want: continue
        if fy_of(f['end']) != fy or qtr_of(f['end']) != qq: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    return v / 1e6 if abs(v) > 100000 else v

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
