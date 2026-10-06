"""Masimo (MASI, CIK 0000937556) standalone quarterly history from EDGAR XBRL companyfacts, as last reported
(continuing operations; the consumer audio business sold in 2025 is in discontinued operations in MASI's later filings).
Writes data/masimo_standalone.json used for the memo rows of the Masimo block."""
import json, os, datetime as dt
S = os.environ.get('DHR_SRC', '/tmp/dhr_src')
F = json.load(open(os.path.join(S, 'masi_facts.json')))['facts']['us-gaap']
TAGS = {'sales': ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues'], 'gp': ['GrossProfit'],
        'op': ['OperatingIncomeLoss'], 'rnd': ['ResearchAndDevelopmentExpense'], 'sga': ['SellingGeneralAndAdministrativeExpense'],
        'dep_amort': ['DepreciationDepletionAndAmortization', 'DepreciationAndAmortization']}
def days(a, b): return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days
out = {}
for k, tags in TAGS.items():
    best = {}
    for t in tags:
        for x in F.get(t, {}).get('units', {}).get('USD', []):
            if 'start' not in x or x['end'] < '2022-12-01': continue
            n = days(x['start'], x['end'])
            # discrete quarters (~91 days) and fiscal years; prefer the latest filing (recast for discontinued operations)
            kind = 'Q' if 80 <= n <= 100 else ('FY' if 350 <= n <= 380 else None)
            if not kind: continue
            key = (kind, x['end'])
            if key not in best or x['filed'] > best[key]['filed']: best[key] = x
    for (kind, end), x in best.items():
        out.setdefault(f'{kind}:{end}', {})[k] = round(x['val'] / 1e6, 1)
        out[f'{kind}:{end}'].setdefault('_src', []).append(x['accn'])
# Q4 = FY − 9M is not tagged discretely: derive from FY − Q1 − Q2 − Q3
res = dict(sorted(out.items()))
json.dump({'note': 'USD m; latest-filed values (continuing operations); quarter keys = fiscal quarter end. Source: SEC XBRL companyfacts CIK0000937556.',
           'periods': res}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'masimo_standalone.json'), 'w'), indent=1)
for k, v in res.items(): print(k, {a: b for a, b in v.items() if a != '_src'})
