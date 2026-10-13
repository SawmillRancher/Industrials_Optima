"""Consistency checks on the normalised Netflix data: income-statement arithmetic, EPS, cash-flow and balance-sheet tie-outs,
regions / legacy segments vs consolidated revenue, published free cash flow / adjusted EBITDA / non-GAAP net income vs the model
bridges, quarters vs fiscal years, and XBRL company facts (as first filed) for revenue, operating income, net income, diluted EPS,
CFO and total assets."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:,.3f} vs {b:,.3f} ({a - b:+,.3f})')

for p in normalize.periods():
    v = x(p)
    if not v.get('rev'): bad.append(f'{p}: no data'); continue
    chk(f'{p} oi', v['rev'] - v['cor'] - v['mkt'] - v['td'] - v['ga'] - v['oth_op'], v['oi'])
    chk(f'{p} ebt', v['oi'] - v['int_exp'] + v['oth_inc'] + v['ext'], v['ebt'])
    if v.get('sh_d'): chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0051 if p >= 'Q' or int(p) >= 2015 else 0.0011)
    # cash flow
    if v.get('cf_cfo') is not None:
        chk(f'{p} cf ni', v['cf_ni'], v['ni'])
        chk(f'{p} cash roll', v['cf_beg'] + v['cf_net'], v['cf_end'])
        if v.get('fcf_pub') is not None: chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'] + n(v.get('fcf_oth')), v['fcf_pub'])
        if v.get('adj_ebitda_pub') is not None: chk(f'{p} adj ebitda', v['oi'] + v['cf_dep'] + v['cf_sbc'], v['adj_ebitda_pub'])
    if v.get('ng_ni_pub') is not None:
        chk(f'{p} non-GAAP NI', v['ni'] + v['ng_items_pre'] + v['ng_items_tax'], v['ng_ni_pub'])
    # balance sheet
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
        chk(f'{p} bs liab', v['bs_tl'] + v['bs_eq'], v['bs_tle'])
        if (p.isdigit() and int(p) < 2018) or (not p.isdigit() and int('20' + p[-2:]) < 2018): chk(f'{p} cash vs bs', v.get('cf_end'), v['bs_cash'])
    # regions / legacy segments
    if v.get('rg_ucan_rev') is not None:
        s = sum(v[f'rg_{g}_rev'] for g in ('ucan', 'emea', 'latam', 'apac'))
        if s > v['rev'] + 0.2: bad.append(f'{p} regions {s:,.1f} > revenue {v["rev"]:,.1f}')
        if p.endswith(('-24', '-25', '-26')) or p in ('2024', '2025'): chk(f'{p} regions = revenue', s, v['rev'])
    if v.get('sg_dom_rev') is not None:
        chk(f'{p} legacy segments', v['sg_dom_rev'] + v['sg_int_rev'] + n(v.get('sg_dvd_rev')), v['rev'], 0.2)
        chk(f'{p} legacy CP', v['sg_dom_cp'] + v['sg_int_cp'] + n(v.get('sg_dvd_cp')), v['rev'] - v['cor'] - v['mkt'] + n(v.get('oth_op')), 0.2)

for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'cor', 'mkt', 'td', 'ga', 'oi', 'ni', 'cf_cfo', 'cf_capex', 'cf_cadd', 'cf_camort', 'cf_bb', 'rg_ucan_rev', 'sg_dom_rev', 'sg_int_cp'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 0.25)

# XBRL (as first filed) cross-checks
XB = [('Revenues', 'rev', 1e6), ('OperatingIncomeLoss', 'oi', 1e6), ('NetIncomeLoss', 'ni', 1e6), ('Assets', 'bs_ta', 1e6)]
for p in normalize.periods():
    v = x(p)
    if p.isdigit(): y, q, kind = int(p), 4, 'FY'
    else: y, q, kind = int('20' + p[-2:]), int(p[1]), 'Q'
    if v.get('q4_derived') or p == '2007': continue        # FY2007 XBRL facts are the restated comparatives in the FY2008 10-K
    for c, k, sc in XB:
        f = xbrl.value_full(c, y, 'I' if c == 'Assets' else kind, q)
        if f and v.get(k) is not None: chk(f'{p} XBRL {c}', v[k], f[1] / sc, 0.6)
    f = xbrl.value_full('EarningsPerShareDiluted', y, kind, q)
    if f and v.get('eps_d') is not None: chk(f'{p} XBRL EPS', v['eps_d'], f[1] / normalize.split_factor(f[0]), 0.0051)
    f = xbrl.value_full('NetCashProvidedByUsedInOperatingActivities', y, 'FY' if kind == 'FY' else 'YTD', q)
    if f and v.get('cf_cfo') is not None and (kind == 'FY' or q == 1): chk(f'{p} XBRL CFO', v['cf_cfo'], f[1] / 1e6, 0.6)

print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
print('\n'.join(normalize.LOG))
