"""Consistency checks on the normalised Norfolk Southern data: statement arithmetic, commodity-group sums, market-group units /
revenue per unit, operating-expense classification, published adjusted figures vs the income-statement items, EPS, cash-flow and
balance-sheet tie-outs, XBRL cross-checks, prior-year comparatives (restatements) and quarters vs years."""
import json, os
import normalize
D = normalize.run()
REC = normalize.REC
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok, KNOWN = [], [0], []
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} rev groups', v['rev_coal'] + v['rev_merch'] + v['rev_im'], v['rev'])
    opex = v['comp'] + v['psr'] + v['fuel'] + v['dep'] + v['mat'] + n(v.get('merger')) + n(v.get('restr')) + n(v.get('eoi')) + n(v.get('loss_disp'))
    chk(f'{p} opex lines', opex, v['opex'])
    chk(f'{p} oi', v['rev'] - v['opex'], v['oi'])
    chk(f'{p} ebt', v['oi'] + v['oth_inc'] - v['int'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'])
    if v.get('tax_cur') is not None and v.get('tax_def') is not None: chk(f'{p} tax split', v['tax_cur'] + v['tax_def'], v['tax'])
    fy_, q_ = normalize.fyq(p)
    chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0251 if fy_ <= 2016 else 0.0101)   # two-class method (dividend equivalents) to 2016
    chk(f'{p} oi xbrl', v['oi'], v.get('oi_xb')); chk(f'{p} ni xbrl', v['ni'], v.get('ni_xb'))
    # market groups
    if v.get('mg_units_total') is not None:
        subs = [v.get(f'mg_units_{g}') for g in ('chem', 'agr', 'metals', 'auto', 'paper', 'forest')]
        if v.get('mg_units_merch') is not None and all(s is not None for s in subs[:4]):
            chk(f'{p} merch units', sum(n(s) for s in subs), v['mg_units_merch'], 0.15)
        chk(f'{p} total units', n(v.get('mg_units_merch')) + n(v.get('mg_units_coal')) + n(v.get('mg_units_im')), v['mg_units_total'], 0.15)
        for g, k in (('coal', 'rev_coal'), ('merch', 'rev_merch'), ('im', 'rev_im'), ('total', 'rev')):
            chk(f'{p} mg rev {g}', v.get(f'mg_rev_{g}'), v[k])
            if v.get(f'mg_rpu_{g}') and v.get(f'mg_units_{g}') and not v.get('mg_rpu_derived'):
                chk(f'{p} rpu {g}', v[f'mg_rpu_{g}'] * v[f'mg_units_{g}'] / 1000.0, v[k], max(1.0, 0.0005 * v[f'mg_units_{g}'] + 0.5))
        if v.get('mg_rev_merch') is not None and all(v.get(f'mg_rev_{g}') is not None for g in ('chem', 'agr', 'metals', 'auto')):
            chk(f'{p} merch sub-group rev', sum(n(v.get(f'mg_rev_{g}')) for g in ('chem', 'agr', 'metals', 'auto', 'paper', 'forest')), v['mg_rev_merch'])
    if v.get('coal_total') is not None:
        chk(f'{p} coal tons', n(v.get('coal_utility')) + n(v.get('coal_export')) + n(v.get('coal_domestic_metallurgical')) + n(v.get('coal_industrial')), v['coal_total'], 1.5)
    if v.get('im_total') is not None: chk(f'{p} im units', n(v.get('im_domestic')) + n(v.get('im_international')), v['im_total'], 0.15)
    if v.get('od_ps') is not None and v.get('od_rents') is not None: chk(f'{p} ps+rents', v['od_ps'] + v['od_rents'], v['psr'])
    if v.get('od_mat') is not None and v.get('od_claims') is not None and v.get('od_other') is not None: chk(f'{p} mat+claims+other', v['od_mat'] + v['od_claims'] + v['od_other'], v['mat'])
    # published adjusted figures vs model items
    if v.get('adj_oi_pub') is not None:
        chk(f'{p} adj oi vs items', v['oi'] + n(v.get('adj_items_oi')), v['adj_oi_pub'])
        if v.get('adj_or_pub') is not None: chk(f'{p} adj OR', 1 - v['adj_oi_pub'] / v['rev'], v['adj_or_pub'], 0.0006)
    if v.get('adj_eps_pub') is not None and v.get('adj_items_eps') is not None: chk(f'{p} adj eps items', v['eps_d'] + v['adj_items_eps'], v['adj_eps_pub'], 0.0101)
    # cash and balance sheet
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        if fy_ in (2018, 2019): KNOWN.append(f'{p} cash vs bs: CF cash incl. restricted cash (ASU 2016-18) {v["cf_end"]} vs BS cash {v["bs_cash"]} (diff {v["cf_end"] - v["bs_cash"]:+.0f})')
        else: chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'])
        chk(f'{p} cf ni', v['cf_ni'], v['ni'])
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    chk(f'{p} bs tl+eq', v['bs_tl'] + v['bs_teq'], v['bs_tle'])
    chk(f'{p} eq comps', n(v.get('bs_cs')) + n(v.get('bs_apic')) + n(v.get('bs_aoci')) + n(v.get('bs_re')), v['bs_teq'], 25.0)
    # prior-year comparative as presented in this period's release vs the original record
    r = REC.get(p); py = (r or {}).get('py', {}).get('is') or {}
    fy, q = normalize.fyq(p); pp = str(fy - 1) if p.isdigit() else normalize.qk(fy - 1, q)
    if py and x(pp):
        for k in ('rev', 'opex', 'oi', 'ni', 'eps_d'):
            if py.get(k) is not None and x(pp).get(k) is not None and abs(py[k] - x(pp)[k]) > (0.0101 if k == 'eps_d' else 0.6):
                (KNOWN if fy == 2018 else bad).append(f'{p} py {k} restated: {py[k]} vs original {x(pp)[k]}' + (' (ASU 2017-07 pension-cost reclassification; original kept)' if fy == 2018 else ''))
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'rev_coal', 'rev_merch', 'rev_im', 'comp', 'psr', 'fuel', 'dep', 'mat', 'opex', 'oi', 'oth_inc', 'int', 'tax', 'ni', 'merger', 'restr', 'eoi',
              'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_cff', 'cf_cfi', 'mg_units_total', 'mg_units_coal', 'mg_units_im', 'mg_units_merch', 'coal_total'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 1.5 if k.startswith('mg_') or k.startswith('coal') else 0.6)
        elif x(str(y)).get(k) is not None and k not in ('coal_total', 'merger', 'restr', 'eoi'): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print('known, documented exceptions:'); print('\n'.join(KNOWN))
print(f'{ok[0]} checks, {len(bad)} issues, {len(KNOWN)} known exceptions')
