"""Consistency checks on the normalised CSX data: statement arithmetic, market sums (volume x revenue per unit = revenue; sum of
markets = total revenue), company adjusted-measure bridges, EPS, cash-flow and balance-sheet tie-outs, XBRL cross-checks and
quarters vs fiscal years."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
MK = ('chem', 'agfood', 'minerals', 'auto', 'metals', 'forest', 'fert')
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    exp = v['labor'] + v['pso'] + v['fuel'] + v['dep'] + v['rents'] + v['inland'] + v['oth_exp'] + v['gain_disp'] + v['impair'] + v['restr']
    chk(f'{p} total expense', exp, v['tot_exp'])
    chk(f'{p} oi', v['rev'] - v['tot_exp'], v['oi'])
    chk(f'{p} ebt', v['oi'] + v['oth_inc'] - v['int_exp'] - v['debt_rep'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'] + v['disc_ops'], v['ni'])
    if v.get('sh_d'): chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0051 if p >= '2013' or len(p) > 4 else 0.0101)
    # markets
    if v.get('a_total_rev') is not None: chk(f'{p} market total vs revenue', v['a_total_rev'], v['rev'])
    if v.get('m_merch_rev') is not None:
        chk(f'{p} merchandise markets sum (rev)', sum(n(v.get(f'm_{k}_rev')) for k in MK), v['m_merch_rev'], 1.1)
        chk(f'{p} merchandise markets sum (vol)', sum(n(v.get(f'm_{k}_vol')) for k in MK), v['m_merch_vol'], 1.1)
        chk(f'{p} groups sum', v['m_merch_rev'] + v['m_intermodal_rev'] + v['m_coal_rev'] + n(v.get('m_trucking_rev')) + n(v.get('m_other_rev')), v['m_total_rev'], 1.1)
        for k in MK + ('intermodal', 'coal'):
            if v.get(f'm_{k}_vol') and v.get(f'm_{k}_rpu'):
                chk(f'{p} {k} vol x rpu', v[f'm_{k}_vol'] * v[f'm_{k}_rpu'] / 1000, v[f'm_{k}_rev'], max(1.0, 0.0006 * v[f'm_{k}_vol'] + 0.5 * v[f'm_{k}_rpu'] / 1000))
    # adjusted measures (company items)
    if v.get('adj_oi_pub') is not None:
        chk(f'{p} adj OI bridge', v['oi'] + v['oa_impair'] + v['oa_restr'] + v['oa_gain'] + v['oa_other'] + v['oa_basis'], v['adj_oi_pub'])
    if v.get('adj_eps_pub') is not None and v.get('adj_ni_pub') is not None and v.get('sh_d'):
        chk(f'{p} adj EPS', v['adj_ni_pub'] / v['sh_d'], v['adj_eps_pub'], 0.0051)
    # cash flow
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash roll', v['cf_beg'] + v['cf_net'], v['cf_end'])
        chk(f'{p} cash vs bs', v['cf_end'], v.get('bs_cash'))
        fy_ = int(p) if p.isdigit() else int('20' + p[-2:])
        fcf = v['cf_cfo'] + v['cf_capex'] + v['cf_disp'] + (v['cf_oinv'] if fy_ <= 2021 else 0.0)   # company definition to 2021: + other investing (excl. acquisitions and short-term investments)
        chk(f'{p} fcf pub', fcf, v.get('cf_fcf_pub'))
        chk(f'{p} cfo lines', v['cf_ni'] + v['cf_dep'] + v['cf_def'] + v['cf_impair'] + v['cf_oth'], v['cf_cfo'])
        chk(f'{p} cfi lines', v['cf_capex'] + v['cf_disp'] + v['cf_sti'] + v['cf_acq'] + v['cf_oinv'], v['cf_cfi'])
        chk(f'{p} cff lines', v['cf_bb'] + v['cf_div'] + v['cf_debt_iss'] + v['cf_debt_rep'] + v['cf_std'] + v['cf_ofin'], v['cf_cff'])
        if v.get('cf_ni') is not None and p.isdigit(): chk(f'{p} cf ni vs is', v['cf_ni'], v['ni'])
    # balance sheet
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    chk(f'{p} bs assets', v['bs_tca'] + v['bs_ppe'] + v['bs_affil'] + v['bs_olta'], v['bs_ta'])
    chk(f'{p} bs liab', v['bs_tcl'] + v['bs_ltd'] + v['bs_dit'] + v['bs_oltl'] + v['bs_te'], v['bs_tle'])
    # XBRL cross-checks (as first filed)
    chk(f'{p} xbrl oi', v.get('x_oi'), v['oi']); chk(f'{p} xbrl ni', v.get('x_ni'), v['ni']); chk(f'{p} xbrl rev', v.get('x_rev'), v['rev'])
    chk(f'{p} xbrl ta', v.get('x_ta'), v['bs_ta']); chk(f'{p} xbrl eps', v.get('x_eps'), v.get('eps_d'), 0.0051)
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'labor', 'pso', 'fuel', 'dep', 'rents', 'oi', 'int_exp', 'oth_inc', 'ebt', 'tax', 'ni', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_dep',
              'm_chem_rev', 'm_coal_rev', 'm_intermodal_vol', 'a_merch_rev', 'a_total_vol', 'fuel_gal', 'dps'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs) and x(str(y)).get(k) is not None: chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 1.1 if k != 'dps' else 0.011)
        elif x(str(y)).get(k) is not None and not k.startswith('m_'): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
KNOWN = ('FY2013 ', 'FY2024 ', 'FY2017 pso', 'FY2017 rents', 'FY2021 pso', 'Q4-23 xbrl')
known = [b for b in bad if b.startswith(KNOWN)]
bad = [b for b in bad if not b.startswith(KNOWN)]
print('\n'.join(bad) or 'all checks pass')
print(f'{len(known)} known, documented exceptions (2013 and 2024 prior-period revisions; 2017 / 2021 within-year reclassifications; Q4-23 XBRL facts tagged after the 2024 revision):')
print('\n'.join('  ' + k for k in known))
print(f'{ok[0]} checks, {len(bad)} issues')
