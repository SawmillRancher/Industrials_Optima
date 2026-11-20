"""Cross-check the normalised data against the XBRL company facts ($TLN_SRC/cf_1622536.json, downloaded by fetch.py):
operating revenues, operating income, net income, operating cash flow (year to date) and total assets, FY2023-Q3/26.
The earliest-filed fact for each period is used (as originally reported)."""
import json, os, normalize
S = os.environ.get('TLN_SRC', '/tmp/tln_src')
F = json.load(open(os.path.join(S, 'cf_1622536.json')))['facts']['us-gaap']
D = normalize.run()
def facts(tag):
    out = {}
    for u in F.get(tag, {}).get('units', {}).get('USD', []):
        if u.get('form') not in ('10-K', '10-Q', 'S-1', 'S-1/A'): continue
        k = (u.get('start'), u['end'])
        if k not in out or u['filed'] < out[k][1]: out[k] = (u['val'] / 1e6, u['filed'])
    return out
ENDS = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}; STARTS = {1: '01-01', 2: '04-01', 3: '07-01'}
bad = n = 0
for tag, key, kind in (('Revenues', 'rev', 'q'), ('OperatingIncomeLoss', 'oi', 'q'), ('ProfitLoss', 'ni_tot', 'q'), ('Assets', 'bs_ta', 'i'),
                       ('NetCashProvidedByUsedInOperatingActivities', 'cf_cfo', 'ytd')):
    fx = facts(tag)
    for p in normalize.periods():
        if p in ('2021', '2022', '2023') or p.endswith('-23'): continue
        y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1])
        if kind == 'i': k = (None, f'{y}-{ENDS[q or 4]}'); mv = D[p]['x'].get(key)
        elif kind == 'ytd':
            k = (f'{y}-01-01', f'{y}-{ENDS[q or 4]}')
            mv = sum(D[f'Q{i}-{str(y)[2:]}']['x'].get(key) or 0 for i in range(1, q + 1)) if q else D[p]['x'].get(key)
        else:
            if q == 4: continue
            k = (f'{y}-{STARTS[q]}', f'{y}-{ENDS[q]}') if q else (f'{y}-01-01', f'{y}-12-31'); mv = D[p]['x'].get(key)
        if k in fx and mv is not None:
            n += 1
            if abs(fx[k][0] - mv) > 0.6: bad += 1; print(f'{p} {tag}: XBRL {fx[k][0]:.1f} vs data {mv:.1f}')
print(f'{n} XBRL comparisons, {bad} differences')
