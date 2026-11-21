"""EDGAR XBRL company facts (us-gaap, L3Harris Technologies / Harris Corporation, CIK 202058) -> values by period end date.

The fiscal calendar changed in 2019 (June year-ends -> December year-ends, with a six-month transition period), so facts are
matched on the period end date and the duration in months rather than on fiscal-year labels. xv() returns the value as first
filed in a 10-K / 10-KT / 10-Q (as originally reported). data/_xbrl.json holds the subset of concepts the model uses, so the
build runs without the raw company-facts download."""
import json, os, datetime as dt
S = os.environ.get('LHX_SRC', '/tmp/lhx_src')
CIK = '202058'
_F = None
USED = ['ShareBasedCompensation', 'DeferredIncomeTaxExpenseBenefit', 'DeferredIncomeTaxesAndTaxCredits', 'DepreciationDepletionAndAmortization',
        'NetCashProvidedByUsedInOperatingActivities', 'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet',
        'NetIncomeLoss', 'Assets', 'EarningsPerShareDiluted', 'OperatingIncomeLoss', 'CommonStockSharesOutstanding',
        'PaymentsForRepurchaseOfCommonStock', 'PaymentsToAcquirePropertyPlantAndEquipment']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')
FORMS = ('10-K', '10-Q', '10-KT', '10-K/A', '10-Q/A')

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(raw):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        if os.path.exists(raw):
            d = json.load(open(raw))['facts'].get('us-gaap', {})
            for k, v in d.items():
                for u, fs in v['units'].items():
                    _F.setdefault(k, []).extend(fs)
    return _F

def dump_subset():
    keep = ('start', 'end', 'val', 'filed', 'form')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in FORMS] for k in USED}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def xv(concepts, end, months, pick='first'):
    """value ($m) of the earliest-filed fact among the concepts ending on `end` (+/- 3 days) with a duration of `months` (0 = instant)."""
    e0 = dt.date.fromisoformat(end)
    best = None
    for c in concepts:
        for f in facts().get(c, []):
            if f.get('form') not in FORMS: continue
            if abs((dt.date.fromisoformat(f['end']) - e0).days) > 3: continue
            if months == 0:
                if 'start' in f: continue
            else:
                if 'start' not in f: continue
                d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
                if abs(d - months * 30.44) > 25: continue
            key = f['filed']
            if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    return best[1] / 1e6 if best is not None else None

if __name__ == '__main__':
    dump_subset(); print('wrote', SUBSET, os.path.getsize(SUBSET))
