"""Cross-check values from the SEC XBRL companyfacts dump (CIK 878927): earliest-filed fact for each period, i.e. as originally reported.
Writes data/xbrl.json {period_key: {rev, op, ni, dda, gain, ta, eps}} — discrete quarters (Q4 = FY − 9M for flows; cash-flow tags YTD → discrete)."""
import json, os, datetime as dt
BASE = os.path.dirname(os.path.abspath(__file__))
FACTS = os.environ.get('ODFL_FACTS', '/tmp/claude-0/-home-user-Industrials-Optima/9730001d-1163-52b2-9b31-6b83e69b543f/scratchpad/odfl_facts.json')
F = json.load(open(FACTS))['facts']['us-gaap']
TAGS = {'rev': ['Revenues', 'RevenueFromContractWithCustomerIncludingAssessedTax', 'SalesRevenueServicesNet'],
        'op': ['OperatingIncomeLoss'], 'ni': ['NetIncomeLoss', 'ProfitLoss'], 'dda': ['DepreciationAndAmortization'],
        'gain': ['GainLossOnSaleOfPropertyPlantEquipment'], 'ta': ['Assets']}
def facts(tag):
    out = {}
    for u in F.get(tag, {}).get('units', {}).values():
        for x in u:
            k = (x.get('start'), x['end'])
            if k not in out or x['filed'] < out[k]['filed']: out[k] = x
    return out
def val(key, start, end):
    for t in TAGS[key]:
        f = facts(t).get((start, end))
        if f: return f['val'] / 1e6
    return None
from extract import split_factor
def dps(start, end):
    """dividends declared per share, restated to the current share basis by the filing date of the fact."""
    f = facts('CommonStockDividendsPerShareDeclared').get((start, end))
    return None if f is None else f['val'] / split_factor(f['filed'])
QE = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
out = {}
for y in range(2006, 2027):
    s, e = f'{y}-01-01', f'{y}-12-31'
    a = {k: val(k, s, e) for k in ('rev', 'op', 'ni', 'dda', 'gain')}
    a['ta'] = val('ta', None, e)
    a['dps'] = dps(s, e)
    if any(v is not None for v in a.values()): out[str(y)] = a
    ytd_prev = {}
    for q in (1, 2, 3, 4):
        if y == 2026 and q > 2: break
        e = f'{y}-{QE[q]}'
        ps = (dt.date.fromisoformat(e) - dt.timedelta(days=88)).replace(day=1).isoformat()
        rec = {}
        for k in ('rev', 'op', 'ni'):
            v = val(k, ps, e) if q < 4 else None
            if v is None:
                ytd = val(k, s, e); p9 = val(k, s, f'{y}-09-30') if q == 4 else None
                v = (ytd - p9) if (q == 4 and ytd is not None and p9 is not None) else None
            rec[k] = v
        for k in ('dda', 'gain'):
            ytd = val(k, s, e)
            prev = ytd_prev.get(k) if q > 1 else 0.0
            rec[k] = (ytd - prev) if (ytd is not None and prev is not None) else None
            ytd_prev[k] = ytd
        rec['ta'] = val('ta', None, e)
        if q < 4:
            rec['dps'] = dps(ps, e)
        else:
            fy, n9 = dps(s, e), dps(s, f'{y}-09-30')
            rec['dps'] = None if fy is None or n9 is None else fy - n9
        if any(v is not None for v in rec.values()): out[f'Q{q}-{str(y)[2:]}'] = rec
json.dump(out, open(os.path.join(BASE, 'data', 'xbrl.json'), 'w'), indent=1)
print(len(out), out.get('2017'), out.get('Q4-25'), out.get('Q2-26'))
