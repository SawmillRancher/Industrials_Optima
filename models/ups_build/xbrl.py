"""EDGAR XBRL company facts (us-gaap, United Parcel Service, Inc., CIK 1090727) -> values by calendar period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated) value. Used for dividends per share (from Q3-2016) and for the
cross-checks in check_data.py; every primary input comes from the releases and the face statements."""
import json, os, datetime as dt
S = os.environ.get('UPS_SRC', '/tmp/ups_src')
CIK = '1090727'
_F = None
USED = ['CommonStockDividendsPerShareCashPaid', 'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'OperatingIncomeLoss', 'NetIncomeLoss',
        'EarningsPerShareDiluted', 'NetCashProvidedByUsedInOperatingActivities', 'Assets', 'DepreciationAndAmortization', 'ShareBasedCompensation',
        'PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsForRepurchaseOfCommonStock', 'PaymentsOfDividends', 'AmortizationOfIntangibleAssets']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')


def dump_subset():
    """write the concepts used (10-K / 10-Q facts only) to data/_xbrl.json so the build and checks run without the raw download."""
    keep = ('start', 'end', 'val', 'filed', 'form')
    raw = json.load(open(os.path.join(S, f'cf_{CIK}.json')))['facts'].get('us-gaap', {})
    out = {}
    for k in USED:
        fs = [f for u in raw.get(k, {}).get('units', {}).values() for f in u]
        out[k] = [{a: f[a] for a in keep if a in f} for f in fs if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')]
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))


def facts():
    global _F
    if _F is None:
        if os.path.exists(SUBSET): _F = json.load(open(SUBSET))
        else:
            dump_subset(); _F = json.load(open(SUBSET))
    return _F


def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None


def value(concept, y, kind, q=None, pick='first'):
    """kind: 'FY' | 'Q' | 'YTD' (q -> Q / H / 9M / FY) | 'I' (instant at quarter q end; q=4 -> year end). USD -> millions."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    end = f"{y}-{ {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[qq] }".replace(' ', '')
    best = None
    for f in facts().get(concept, []):
        if dur(f) != want or f['end'] != end: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    return v / 1e6 if abs(v) > 1000 else v
