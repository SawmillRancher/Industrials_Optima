"""Consistency checks on the normalised Union Pacific data: statement arithmetic, business-group sums and carloads x ARPC,
adjusted bridges vs the published figures, EPS, cash-flow and balance-sheet tie-outs, quarters vs fiscal years, XBRL."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    fy, q = normalize.fyq(p)
    chk(f'{p} rev', n(v.get('frt')) + n(v.get('oth_rev')), v['rev'])
    chk(f'{p} opex', v['comp'] + v['fuel'] + v['psm'] + v['dep'] + v['rents'] + v['oth_exp'], v['opex'])
    chk(f'{p} oi', v['rev'] - v['opex'], v['oi'])
    chk(f'{p} ebt', v['oi'] + v['oth_inc'] - v['int'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'])
    if v.get('sh_d'): chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101)
    groups = normalize.GROUPS3 if v.get('g_bulk_rev') else ([f's4_{g}' for g in normalize.LEG4] if v.get('s4_ag_rev') else [f's6_{g}' for g in normalize.LEG6])
    pre = 'g_' if v.get('g_bulk_rev') else ''
    tot = sum(n(v.get(f'{pre}{g}_rev')) for g in groups)
    if tot: chk(f'{p} groups sum', tot, v['g_total_rev'] if v.get('recast') else v['frt'], 1.5)
    if v.get('g_bulk_rev') and v.get('g_grain_rev'):
        chk(f'{p} bulk subs', sum(n(v.get(f'g_{g}_rev')) for g in ('grain', 'fert', 'food', 'coalren')), v['g_bulk_rev'], 1.5)
        chk(f'{p} ind subs', sum(n(v.get(f'g_{g}_rev')) for g in ('chemplas', 'metals', 'forest', 'energyspec')), v['g_industrial_rev'], 1.5)
        chk(f'{p} prem subs', n(v.get('g_auto_rev')) + n(v.get('g_intermodal_rev')), v['g_premium_rev'], 1.5)
    for g in groups:
        rv, c, a = v.get(f'{pre}{g}_rev'), v.get(f'{pre}{g}_cars'), v.get(f'{pre}{g}_arpc')
        if rv and c and a: chk(f'{p} {g} cars x arpc', c * a / 1000, rv, max(2.0, 0.012 * rv))
    if v.get('adj_published'):
        items = sum(n(v.get(f'oa_{c}')) for c in ('acq', 'impair', 'gain', 'other'))
        chk(f'{p} adj oi', v['oi'] + items, v.get('adj_oi_pub'))
        chk(f'{p} adj ni', v['ni'] + n(v.get('oa_ni')), v.get('adj_ni_pub'))
        chk(f'{p} adj ni bridge', v['ni'] + items + n(v.get('oa_othinc')) - n(v.get('oa_tax')), v.get('adj_ni_pub'))
        if v.get('sh_d'): chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v.get('adj_eps_pub'), 0.0101)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cfo lines', v['cf_ni'] + v['cf_dep'] + v['cf_dtax'] + v['cf_oth'], v['cf_cfo'])
        chk(f'{p} cf net', v['cf_cfo'] + v['cf_cfi'] + v['cf_cff'], v['cf_net'])
        if v.get('cf_beg') is not None: chk(f'{p} cash roll', v['cf_beg'] + v['cf_net'], v.get('cf_end'))
        if v.get('cf_end') is not None and fy < 2018: chk(f'{p} cash vs bs', v['cf_end'], v.get('bs_cash'))
        if not p.isdigit(): chk(f'{p} cf ni vs is', v['cf_ni'], v['ni'])
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    chk(f'{p} bs assets', n(v.get('bs_cash')) + v['bs_sti'] + v['bs_oca'] + v['bs_inv'] + v['bs_ppe'] + v['bs_oa'], v['bs_ta'])
    chk(f'{p} bs liab', v['bs_std'] + v['bs_ocl'] + v['bs_ltd'] + v['bs_dtl'] + v['bs_oltl'] + v['bs_eq'], v['bs_tle'])
    if fy >= 2009 and v.get('rev') is not None:
        kind = 'FY' if p.isdigit() else 'Q'
        for name, c, k, t in (('rev', 'Revenues', 'rev', 0.6), ('oi', 'OperatingIncomeLoss', 'oi', 0.6), ('ni', 'NetIncomeLoss', 'ni', 0.6),
                              ('eps', 'EarningsPerShareDiluted', 'eps_d', 0.0101), ('ta', 'Assets', 'bs_ta', 0.6)):
            xv = xbrl.value(c, fy, 'I' if name == 'ta' else kind, q)
            if xv is not None and (name != 'eps' or not v.get('split_adj')): chk(f'{p} xbrl {name}', xv, v.get(k), t)
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'frt', 'oth_rev', 'comp', 'fuel', 'psm', 'dep', 'rents', 'oth_exp', 'opex', 'oi', 'oth_inc', 'int', 'ebt', 'tax', 'ni', 'g_bulk_rev', 'g_industrial_rev',
              'g_premium_rev', 'g_total_cars', 'g_bulk_cars', 's6_ag_rev', 's6_energy_rev', 'gtm', 'gallons', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_dep', 'fcf_pub', 'sbc'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(v is not None for v in qs) and x(str(y)).get(k) is not None: chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 1.6 if k != 'gtm' else 5)
        elif x(str(y)).get(k) is not None and any(v is None for v in qs) and k not in ('sbc',): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, v in enumerate(qs) if v is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
