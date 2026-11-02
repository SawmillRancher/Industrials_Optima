"""Consistency checks on the normalised Graham data: statement arithmetic, EBITDA / adjusted bridges vs the published figures,
EPS, market and region sums, cash-flow and balance-sheet tie-outs, XBRL cross-checks and quarters vs fiscal years."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    tol = 0.0011
    chk(f'{p} op', v['gp'] - v['sga'] - v['amort'] - v['restr'] - v['impair'] - v['oth_op'], v['op'], tol)
    chk(f'{p} ebt', v['op'] - v['int_net'] - v['oth_nonop'], v['ebt'], tol)
    chk(f'{p} ni', v['ebt'] - v['tax'] + v['disc_ops'], v['ni'], tol)
    chk(f'{p} gaap eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101 if v['split_factor'] == 1 else 0.0101 / v['split_factor'] + 0.003)
    # non-GAAP bridges (as published in the period)
    if v.get('ebitda_pub') is not None and v.get('cf_dep') is not None:
        chk(f'{p} ebitda pub', v['ni'] + v['tax'] + v['int_net'] + n(v.get('eb_dda')), v['ebitda_pub'], 0.06 if v['ebitda_pub'] == round(v['ebitda_pub'], 1) and abs(v['ebitda_pub'] * 10 - round(v['ebitda_pub'] * 10)) < 1e-6 and v['ebitda_pub'] < 100 and v.get('eb_start') != v['ni'] else 0.0011)
        chk(f'{p} ebitda dda vs cf', n(v.get('eb_dda')), n(v.get('cf_dep')) + n(v.get('cf_amort')), 0.06)
    if v.get('adj_ebitda_pub') is not None:
        items = sum(n(v.get('eb_' + b)) for b in ('acq', 'restr', 'impair', 'erp', 'sbc', 'oth'))
        base = v['ni'] + v['tax'] + v['int_net'] + n(v.get('eb_dda')) if v.get('eb_start') is not None else None
        rough = v.get('eb_start') is not None and abs(v['eb_start'] - v['ni']) > 0.0015   # table published in USD m (FY2011-12)
        chk(f'{p} adj ebitda', base + items, v['adj_ebitda_pub'], 0.16 if rough else 0.0011)
    if v.get('adj_ni_pub') is not None:
        items = sum(n(v.get('an_' + b)) for b in ('acq', 'amort', 'restr', 'impair', 'erp', 'sbc', 'oth', 'tax', 'taxd'))
        chk(f'{p} adj ni bridge', v['ni'] + items, v['adj_ni_pub'], 0.0011)
        if v.get('adj_eps_pub') is not None: chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['adj_eps_pub'], 0.0101)
    if v.get('adj_op_pub') is not None:
        items = sum(n(v.get('ao_' + b)) for b in ('acq', 'restr', 'impair', 'erp', 'oth'))
        chk(f'{p} adj op bridge', v['op'] + items, v['adj_op_pub'], 0.0011)
    # markets / regions
    mk = [v.get(f'mk_{m}') for m in ('refining', 'chem', 'power', 'defense', 'space', 'other', 'ep')]
    if any(m is not None for m in mk):
        tolm = 0.0011 if (v.get('mkt_src') or '').endswith(('note', 'k')) else 0.36
        chk(f'{p} markets', sum(n(m) for m in mk), v['rev'], tolm)
    if v.get('cb_defense') is not None and v.get('cb_ep') is not None:
        chk(f'{p} current-basis markets', v['cb_defense'] + v['cb_space'] + v['cb_ep'], v['rev'], 0.0011)
    if v.get('rg_us') is not None:
        chk(f'{p} regions', v['rg_us'] + v['rg_intl'], v['rev'], 0.0011 if (v.get('mkt_src') or '').endswith(('note', 'k')) else 0.36)
    # cash flow / balance sheet
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'], 0.0011)
        chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'], 0.0011)
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'], 0.0011)
        chk(f'{p} bs tl', v['bs_tcl'] + v['bs_ltd'] + v['bs_opln'] + v['bs_ol'] + v['bs_eq'], v['bs_tle'], 0.0011)
    # XBRL cross-checks (as first filed)
    for a, b in (('rev', 'xb_rev'), ('ni', 'xb_ni'), ('bs_ta', 'xb_ta')):
        chk(f'{p} xbrl {a}', v.get(a), v.get(b), 0.0011)
    if v.get('xb_eps_d') is not None: chk(f'{p} xbrl eps', v.get('eps_d'), v.get('xb_eps_d'), 0.0101)
    if p.isdigit() and v.get('xb_cfo_ytd') is not None: chk(f'{p} xbrl cfo', v.get('cf_cfo'), v.get('xb_cfo_ytd'), 0.0011)
for y in range(2013, 2027):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'sga', 'amort', 'restr', 'impair', 'oth_op', 'op', 'int_net', 'oth_nonop', 'ebt', 'tax', 'ni', 'orders',
              'cf_cfo', 'cf_capex', 'cf_dep', 'cf_hfs', 'cf_wc', 'cf_net', 'cf_amort', 'cf_sbc', 'cf_def', 'cf_div', 'cf_withhold', 'cf_acq', 'cf_debt', 'cb_defense', 'cb_space', 'cb_ep'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs) and x(str(y)).get(k) is not None:
            tolq = 0.25 if k.startswith('cb_') and not (x(str(y)).get('mkt_src') or '').endswith(('note', 'k')) else (0.05 if k.startswith('cb_') else 0.0025)
            if k == 'orders': tolq = 0.25
            chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), tolq)
        elif x(str(y)).get(k) is not None and k not in ('cb_defense', 'cb_space', 'cb_ep', 'impair', 'restr'):
            bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
