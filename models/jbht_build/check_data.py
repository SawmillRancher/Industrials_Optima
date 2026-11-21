"""Consistency checks on the normalised J.B. Hunt data: statement arithmetic, segment sums, EPS, XBRL cross-checks (operating
income, net earnings, release vs XBRL operating cash flow and net capital expenditures), cash and balance-sheet tie-outs,
published statistics vs revenue, and quarters vs years."""
import json, os
import normalize
D = normalize.run()
REC = normalize.REC
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok, info = [], [0], []
def chk(name, a, b, tol=0.011):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
SEG = normalize.SEGS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    costs = sum(v[k] for k in ('pt', 'sw', 'fuel', 'da', 'supplies', 'ins', 'ga', 'taxlic', 'comm'))
    chk(f'{p} revenue split', v['rev_xfuel'] + v['fuel_rev'], v['rev'])
    chk(f'{p} opex', costs, v['opex']); chk(f'{p} oi', v['rev'] - v['opex'], v['oi'])
    chk(f'{p} ebt', v['oi'] - v['net_int'] - v['equity_loss'], v['ebt']); chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'])
    chk(f'{p} seg revenue', sum(n(v.get(f'sr_{g}')) for g in SEG) + v['sr_elim'], v['rev'])
    chk(f'{p} seg oi', sum(n(v.get(f'so_{g}')) for g in SEG) + v['so_other'], v['oi'])
    chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0051)
    chk(f'{p} xbrl oi', v['oi'], v.get('x_oi')); chk(f'{p} xbrl ni', v['ni'], v.get('x_ni'))
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'], 0.02)
        chk(f'{p} cf ni', v['cf_ni'], v['ni'])
    for g, vol in (('jbi', 'jbi_loads'), ('ics', 'ics_loads'), ('jbt', 'jbt_loads')):       # published revenue per load vs revenue / loads (rounding)
        pub = v.get(f'{g}_rpl_pub')
        if pub and v.get(vol): chk(f'{p} {g} revenue per load', v[f'sr_{g}'] * 1000 / v[vol], pub, 1.0)
    r = REC[p].get('cf') or {}
    # information only: preliminary release supplemental data vs the filed cash-flow statement (the filing is used)
    if 'cfo_rel' in r and 'cfo' in r and abs(r['cfo'] - r['cfo_rel']) > 0.011: info.append(f"{p} cfo: filing {r['cfo']:.1f} vs release {r['cfo_rel']:.1f}")
    if 'netcapex_rel' in r and 'capex' in r and abs(r['capex'] - n(r.get('sale')) - r['netcapex_rel']) > 0.6:
        info.append(f"{p} net capex: filing {r['capex'] - n(r.get('sale')):.1f} vs release {r['netcapex_rel']:.1f}")
KEYS = ('rev', 'pt', 'sw', 'fuel', 'da', 'ins', 'ga', 'oi', 'net_int', 'tax', 'ni', 'sr_jbi', 'sr_dcs', 'sr_ics', 'sr_fms', 'sr_jbt', 'so_jbi', 'so_dcs', 'so_ics',
        'so_fms', 'so_jbt', 'jbi_loads', 'ics_loads', 'jbt_loads', 'fms_stops', 'cf_cfo', 'cf_capex', 'cf_sale', 'cf_bb', 'cf_div', 'cf_da', 'dps', 'oa_items')
EXC = {(2019, 'fms_stops')}          # known exception (manual_items.json 'known_exceptions')
for y in range(normalize.YQ0, normalize.YC):
    yy = str(y)[2:]
    for k in KEYS:
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        fy = x(str(y)).get(k)
        if (y, k) in EXC: continue
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), fy, 0.02 if not k.endswith(('loads', 'stops')) else 0.5)
        elif fy is not None and any(q is not None for q in qs): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
print('information (release vs filing):', '; '.join(info))
