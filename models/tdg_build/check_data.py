"""Consistency checks on the normalised TransDigm data: statement arithmetic, EBITDA / EBITDA As Defined / adjusted net income
bridges vs the published figures, two-class EPS, segment and end-market sums, quarters vs fiscal years, cash-flow and
balance-sheet tie-outs, and XBRL company-facts cross-checks (as first filed)."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok, known, info = [], [0], [], []
KNOWN = {          # period/check -> explanation (documented exceptions; see README)
    'FY2016 tax sum-q': 'ASU 2016-09 early-adopted in Q4 FY2016 retroactive to 1-Oct-2015; Q1-Q3 as first reported are pre-adoption',
    'FY2016 ni sum-q': 'ASU 2016-09 early adoption (see tax)',
    'FY2017 rev sum-q': 'Q1-Q3 FY2017 as first reported include businesses presented as discontinued operations in the FY2017 10-K',
    'FY2017 cogs sum-q': 'FY2017 discontinued operations (see revenue)', 'FY2017 sga sum-q': 'FY2017 discontinued operations',
    'FY2017 oa_acq sum-q': 'FY2017 discontinued operations', 'Q4-17 organic + acquisitions': 'FY2017 10-K organic table on the discontinued-operations basis less 9M as first reported',
    'FY2019 rev sum-q': 'Q2-Q3 FY2019 as first reported include Esterline businesses later presented as held for sale / discontinued operations',
    'FY2019 cogs sum-q': 'FY2019 discontinued operations (Esterline)', 'FY2019 sga sum-q': 'FY2019 discontinued operations',
    'FY2019 amort_is sum-q': 'FY2019 discontinued operations', 'FY2019 oi sum-q': 'FY2019 discontinued operations',
    'FY2019 ebt sum-q': 'FY2019 discontinued operations', 'FY2019 tax sum-q': 'FY2019 discontinued operations',
    'FY2019 ebitda_pub sum-q': 'FY2019 discontinued operations', 'FY2019 ebitda_ad_pub sum-q': 'FY2019 discontinued operations',
    'FY2019 adj_ni_pub sum-q': 'FY2019 discontinued operations', 'FY2019 d_dda sum-q': 'FY2019 discontinued operations',
    'Q4-19 organic + acquisitions': 'FY2019 10-K organic table on the discontinued-operations basis less 9M as first reported',
    'FY2022 oa_sbc sum-q': 'FY2022 release relabelled the line "non-cash stock and deferred compensation" for the year (deferred compensation moved out of Other, net); EBITDA As Defined itself sums',
}
def chk(name, a, b, tol):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol:
        msg = f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})'
        if name in KNOWN: known.append(msg + f'  [known: {KNOWN[name]}]')
        else: bad.append(msg)
OC = normalize.OCATS
def tol_of(p, base=0.15):
    y, _ = normalize.fyq(p)
    return base if y <= 2019 else 1.01           # documents in thousands to FY2019, whole millions from FY2020
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    t = tol_of(p); t2 = 2 * t
    chk(f'{p} oi', v['gp'] - n(v['sga']) - v['amort_is'] - v['oth_op'], v['oi'], t2)
    chk(f'{p} ebt', v['oi'] - v['int_net'] - v['refin'] - v['oth_exp'], v['ebt'], t2)
    chk(f'{p} ni', v['ebt'] - v['tax'] + v['disc'], v['ni'], t2)
    ebitda = v['ni_cont'] + v['tax'] + v['int_net'] + n(v.get('d_dda'))
    chk(f'{p} ebitda', ebitda, v.get('ebitda_pub'), t2)
    items = sum(n(v.get('oa_' + c)) for c in OC)
    chk(f'{p} ebitda as defined', n(v.get('ebitda_pub')) + items, v.get('ebitda_ad_pub'), t2)
    if v.get('adj_ni_pub') is not None:
        chk(f'{p} adj gross = items', n(v.get('adj_gross')), items, t2)
        chk(f'{p} adj ni', v['ni_cont'] + n(v.get('adj_start_diff')) + n(v.get('adj_gross')) + n(v.get('adj_backlog')) + n(v.get('adj_tax')), v['adj_ni_pub'], t2)
        sh = v.get('sh_adj') or v.get('sh_d')
        chk(f'{p} adj eps', v['adj_ni_pub'] / sh, v.get('adj_eps_pub'), 0.0101 if t < 1 else 0.06)
    if v.get('sh_d'):
        chk(f'{p} gaap eps', (v['ni_td'] - n(v.get('div_part'))) / v['sh_d'], v.get('eps_d'), 0.0101 if t < 1 else 0.06)
    # segments / end markets (latest basis) vs consolidated as originally reported (difference = basis row in the model)
    if v.get('sg_pc_rev') is not None:
        sr = sum(n(v.get(f'sg_{g}_rev')) for g in ('pc', 'af', 'na', 'es'))
        se = sum(n(v.get(f'sg_{g}_eb')) for g in ('pc', 'af', 'na', 'es')) - n(v.get('sg_corp'))
        if abs(sr - v['rev']) > t2: info.append(f'{p} segment basis difference (sales): {sr - v["rev"]:+.1f} (model basis row) [{v.get("seg_basis", "as reported")}]')
        if abs(se - n(v.get('ebitda_ad_pub'))) > t2: info.append(f'{p} segment basis difference (EBITDA As Defined): {se - n(v.get("ebitda_ad_pub")):+.1f} (model basis row)')
    if v.get('em_pc_coem') is not None:
        for g in ('pc', 'af'):
            chk(f'{p} end markets {g}', sum(n(v.get(f'em_{g}_{k}')) for k in ('coem', 'caft', 'def', 'est')), v.get(f'sg_{g}_rev'), t2)
        chk(f'{p} end markets na', v.get('em_na'), v.get('sg_na_rev'), t2)
    if v.get('org_sales') is not None:
        chk(f'{p} organic + acquisitions', v['org_sales'] + n(v.get('acq_sales')), v['rev'], t2)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'], t2)
        chk(f'{p} cash vs bs (incl. restricted)', v['cf_end'], v.get('bs_cash', 0) + v.get('bs_rcash', 0), t2)
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'], t2)
    # XBRL cross-checks (as first filed; from fiscal 2010)
    y, q = normalize.fyq(p)
    if y >= 2010:
        rv = xbrl.earliest_of(['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'], y, 'FY' if p.isdigit() else 'Q', 4 if p.isdigit() else q)
        chk(f'{p} xbrl revenue', rv, v['rev'], t2)
        ta = xbrl.value('Assets', y, 'I', 4 if p.isdigit() else q)
        chk(f'{p} xbrl total assets', ta, v.get('bs_ta'), t2)
for y in range(normalize.FYQ0, normalize.FYL + 1):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'sga', 'amort_is', 'oi', 'int_net', 'ebt', 'tax', 'ni', 'ebitda_pub', 'ebitda_ad_pub', 'adj_ni_pub', 'oa_acq', 'oa_sbc',
              'cf_cfo', 'cf_capex', 'cf_acq', 'cf_bb', 'cf_div', 'd_dda'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q_ is not None for q_ in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 1.6 if y <= 2019 else 3.01)
        elif x(str(y)).get(k) is not None: bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q_ in enumerate(qs) if q_ is None]}')
print('Information (segment data on the latest-filing basis vs consolidated as first reported; shown as a basis row in the model):')
print('\n'.join('  ' + i for i in info))
print('Documented exceptions:'); print('\n'.join('  ' + k for k in known))
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(known)} documented exceptions, {len(bad)} issues')
