"""Consistency checks on the normalised Booz Allen data: statement arithmetic, the three company bridges (adjusted operating income,
adjusted EBITDA, adjusted net income / EPS) vs the published figures, two-class EPS, free cash flow, customer sums, cash and
balance-sheet tie-outs, quarters vs fiscal years, and XBRL cross-checks (revenue, operating income, net income, diluted EPS, CFO,
total assets). Tolerances: 0.11 ($m, thousands-basis releases) / 0.6 ($m, whole-million releases from Q1 FY2025) / 0.0101 (EPS)."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def millions(p):
    fy, q = normalize.fyq(p)
    return (fy, q) >= (2025, 1) and not (p.isdigit() and fy < 2025)
def chk(name, a, b, tol=None, p=None):
    if a is None or b is None: return
    tol = tol if tol is not None else (0.6 if p and millions(p) else 0.11)
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
OC = normalize.OCATS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    costs = v['cost_rev'] + v['bill'] + v['ga'] + v['da'] + v['restr'] + v['oth_op']
    chk(f'{p} oi', v['rev'] - costs, v['oi'], p=p)
    chk(f'{p} ebt', v['oi'] - v['int_exp'] + v['oth_inc'], v['ebt'], p=p)
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'], p=p)
    chk(f'{p} ni common', v['ni'] - v['nci'], v['ni_c'], p=p)
    if v.get('earn_dil') is not None and v.get('sh_d'):
        chk(f'{p} gaap eps (two-class)', v['earn_dil'] / v['sh_d'], v['eps_d'], 0.0101)
    # adjusted EBITDA: EBITDA = start + tax + interest & other + D&A; adjusted = + operating items
    ebitda = v['ni_c'] + n(v.get('eb_nci')) + v['tax'] + v['int_exp'] - v['oth_inc'] + v['da']
    chk(f'{p} ebitda start basis is NCI', n(v.get('eb_nci')), v['nci'] if abs(n(v.get('eb_nci'))) > 0.001 else 0.0, p=p)
    chk(f'{p} ebitda', ebitda, v.get('ebitda_pub'), p=p)
    items = sum(n(v.get(f'eb_{c}')) for c in OC)
    chk(f'{p} adj ebitda', n(v.get('ebitda_pub')) + items, v.get('adj_ebitda_pub'), p=p)
    if v.get('adj_oi_pub') is not None:
        chk(f'{p} adj oi', v['oi'] + v['ao_op'] + v['ao_amort'], v['adj_oi_pub'], p=p)
        chk(f'{p} adj oi op items vs ebitda items', v['ao_op'], items, p=p)
    if v.get('adj_ni_pub') is not None:
        chk(f'{p} adj ni start basis is NCI', v['an_nci'], v['nci'] if abs(v['an_nci']) > 0.001 else 0.0, p=p)
        chk(f'{p} adj ni bridge', v['ni_c'] + v['an_nci'] + v['an_op'] + v['an_amort'] + v['an_nonop'] + v['an_tax'] + v['an_taxd'], v['adj_ni_pub'], p=p)
        chk(f'{p} adj ni op items vs ebitda items', v['an_op'], items, p=p)
        chk(f'{p} adj eps', v['adj_ni_pub'] / v['adj_sh'], v['adj_eps_pub'], 0.0101)
        chk(f'{p} adj shares vs gaap diluted', v['adj_sh'], v.get('sh_d'), 0.05)
    chk(f'{p} rev ex billables', v['rev_xb'], v.get('rev_xb_pub'), p=p)
    if v.get('c_ns') is not None:
        # FY2017-18: ASC 606 recast revenue (FY2019 10-K comparatives) vs revenue as originally reported (documented basis difference)
        if p not in ('2017', '2018'): chk(f'{p} customers', v['c_ns'] + v['c_cc'], v['rev'], 1.0 if millions(p) else 0.11)
    if v.get('bl_total') is not None and v.get('bl_funded') is not None:
        chk(f'{p} backlog', v['bl_funded'] + v['bl_unfunded'] + v['bl_options'], v['bl_total'], 1.01)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'], p=p)
        chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'], p=p)
        chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'], v.get('fcf_pub'), p=p)
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'], p=p)
for p in normalize.periods():
    r = normalize.REC[p]['x']; v = x(p)
    fy, q = normalize.fyq(p)
    for k, kk in (('x_rev', 'rev'), ('x_oi', 'oi'), ('x_ni', 'ni_c'), ('x_ta', 'bs_ta')):
        if k == 'x_rev' and p in ('2017', '2018'): continue        # XBRL first fact for FY2017-18 is the FY2019 10-K ASC 606 recast
        chk(f'{p} xbrl {kk}', v.get(kk), r.get(k), (1.01 if q == 4 and not p.isdigit() else 0.6) if millions(p) else 0.11)
    if r.get('x_eps_d') is not None: chk(f'{p} xbrl eps', v['eps_d'], r['x_eps_d'], 0.0101)
    if p.isdigit() or q == 4:
        if r.get('x_cfo') is not None and p.isdigit(): chk(f'{p} xbrl cfo', v.get('cf_cfo'), r['x_cfo'], 0.11)
for y in range(2022, 2027):
    yy = str(y)[2:]
    for k in ('rev', 'cost_rev', 'bill', 'ga', 'da', 'oi', 'int_exp', 'oth_inc', 'ebt', 'tax', 'ni', 'ebitda_pub', 'adj_ebitda_pub', 'adj_ni_pub',
              'an_amort', 'an_tax', 'an_taxd', 'eb_acq', 'eb_legal', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_sbc', 'c_ns', 'c_cc', 'fcf_pub'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        tol = 2.01 if y >= 2025 else 0.25
        if y == 2025 and k in ('int_exp', 'oth_inc', 'ga'): continue   # Q4 FY25 re-presentation (interest expense, net); see README
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), tol)
        elif x(str(y)).get(k) is not None: bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
