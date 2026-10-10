"""Consistency checks on the normalised Woodward data: statement arithmetic, segment sums, EBIT / EBITDA / adjusted bridges vs the
published figures, EPS, sales-by-market sums, cash-flow and balance-sheet tie-outs, and quarters vs fiscal years."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
OC = normalize.OCATS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    ebt = v['gp'] - v['sga'] - v['rd'] - v['amort_is'] - v['restr'] - v['oth_op'] + v['oth_inc'] - v['int_exp'] + v['int_inc']
    chk(f'{p} ebt', ebt, v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'] + n(v.get('nci')))
    chk(f'{p} seg sales', v['sr_aero'] + v['sr_ind'], v['rev'])
    chk(f'{p} seg ebit', v['se_aero'] + v['se_ind'] + v['nonseg'], v['ebit'])
    chk(f'{p} ebit pub', v['ebit'], v.get('ebit_pub'))
    if v.get('d_dep') is not None: chk(f'{p} ebitda pub', v['ebit'] + v['d_dep'] + v['d_amort'], v.get('ebitda_pub'))
    chk(f'{p} gaap eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101)
    items = sum(n(v.get('oa_' + c)) for c in OC)
    if v.get('adj_ni_pub') is not None:
        chk(f'{p} adj ni bridge', v['ni'] + items + v['oa_tax'], v['adj_ni_pub'])
        chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['e_pub'], 0.0101)
        chk(f'{p} adj ebit', v['ebit'] + items, v.get('adj_ebit_pub'))
        if v.get('adj_ebitda_pub') is not None:
            chk(f'{p} adj ebitda', v['ebit'] + v['d_dep'] + v['d_amort'] + items - n(v.get('oa_in_dda')), v['adj_ebitda_pub'])
    if v.get('em_com_oem') is not None:
        chk(f'{p} aero markets', sum(v[f'em_{k}'] for k in ('com_oem', 'com_aft', 'def_oem', 'def_aft')), v['sr_aero'])
    if v.get('em_pg') is not None and not v.get('em_ind_recast'):
        chk(f'{p} ind markets', sum(v[f'em_{k}'] for k in ('pg', 'trans', 'og')), v['sr_ind'])
    if v.get('em_recip') is not None:
        chk(f'{p} ind markets (legacy)', sum(n(v.get(f'em_{k}')) for k in ('recip', 'ind_turb', 'renew')), v['sr_ind'])
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'])
        chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'], v.get('fcf_pub'))
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
for y in range(2021, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'sga', 'rd', 'ebt', 'tax', 'ni', 'sr_aero', 'sr_ind', 'se_aero', 'se_ind', 'nonseg', 'ebit', 'd_dep', 'd_amort',
              'oa_restr', 'oa_acq', 'oa_gain', 'oa_other', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_sbc', 'em_com_oem', 'em_def_oem', 'em_pg', 'em_trans'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 0.25)
        elif x(str(y)).get(k) is not None and k not in ('em_pg', 'em_trans'): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
