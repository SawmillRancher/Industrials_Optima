"""Consistency checks on the normalised Microsoft data: statement arithmetic, segment sums for every segment structure, the FY27
restated product lines and segments vs reported revenue / operating income, non-GAAP bridge bases vs the income statement, EPS, cash
and balance-sheet tie-outs, quarters vs fiscal years, and an XBRL company-facts cross-check (revenue, operating income, net income,
diluted EPS, CFO, total assets; earliest-filed facts). Known, documented exceptions are listed in EXC and in manual_items.json."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
EXC = {('2016', 'tax'), ('2016', 'ni'), ('2016', 'cf_cfo'), ('2016', 'cf_cff'), ('2016', 'cf_wc'), ('2016', 'cf_ofin'),   # ASU 2016-09 (Q1-Q3 FY16 not restated)
       ('2008', 'xbrl oi'),                                                                                           # FY2008 OI restated in later 10-Ks
       ('2014', 'oa_revdef'),   # Q1 FY14 Windows 8.1 pre-sales deferral (+$113m) not reversed in the FY2014 annual presentation (adjusted = GAAP)
       ('2015', 'oa_revdef'),   # Q2 FY15 -$326m revenue-deferral item exists only in the Q2 FY16 re-presentation; FY2015 annual shows none
       ('2016', 'oa_revdef'),   # Q2 FY16 'net impact from revenue deferrals' $1,897m (incl. non-Windows 10 items) vs FY2016 Windows 10 total $6,643m
       ('2016', 's3_mpc_r'), ('2016', 's3_pbp_o'), ('2016', 's3_mpc_o')}  # FY2016 annual segments (Q4 release) re-allocated vs Q1-Q3 as first reported                                                                                           # FY2008 OI restated in later 10-Ks
def chk(name, a, b, tol=1.01, key=None):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol and key not in EXC: bad.append(f'{name}: {a:,.3f} vs {b:,.3f} ({a - b:+,.3f})')

for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} oi', v['gp'] - v['rd'] - v['sm'] - v['ga'] - v['impair'], v['oi'])
    chk(f'{p} ebt', v['oi'] + v['oth'], v['ebt']); chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'])
    chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101)
    if v.get('rev_prod') is not None: chk(f'{p} rev split', v['rev_prod'] + v['rev_serv'], v['rev'])
    # segments
    if v.get('l1_win_r') is not None:
        chk(f'{p} L1 rev', sum(n(v.get(f'l1_{k}_r')) for k in normalize.L1), v['rev'])
        chk(f'{p} L1 oi', sum(n(v.get(f'l1_{k}_o')) for k in normalize.L1), v['oi'])
    if v.get('l2_cl_r') is not None:
        chk(f'{p} L2 rev', sum(n(v.get(f'l2_{k}_r')) for k in normalize.L2), v['rev'])
        chk(f'{p} L2 gm', sum(n(v.get(f'l2_{k}_g')) for k in normalize.L2), v['gp'])
    if v.get('s3_pbp_r') is not None:
        chk(f'{p} S3 rev', sum(n(v.get(f's3_{k}_r')) for k in normalize.S3), v['rev'])
        chk(f'{p} S3 oi', sum(n(v.get(f's3_{k}_o')) for k in normalize.S3), v['oi'])
    if v.get('sg_ai_rev') is not None:
        chk(f'{p} FY27 lines', sum(v[f'pl_{k}'] for k in normalize.LINES), v['rev'])
        chk(f'{p} FY27 seg rev', v['sg_ai_rev'] + v['sg_dc_rev'], v['rev']); chk(f'{p} FY27 seg oi', v['sg_ai_oi'] + v['sg_dc_oi'], v['oi'])
        chk(f'{p} A&I lines', sum(v[f'pl_{k}'] for k in ('az', 'm365', 'psl', 'ind', 'fss')), v['sg_ai_rev'])
        chk(f'{p} D&C lines', sum(v[f'pl_{k}'] for k in ('sa', 'xbox', 'win')), v['sg_dc_rev'])
        chk(f'{p} FY27 seg cost', v['sg_ai_cogs'] + v['sg_dc_cogs'], v['cogs'])
    # non-GAAP: bridge bases are the reported GAAP figures
    ng = normalize.NG.get(p)
    if ng:
        chk(f'{p} ng gaap rev', ng['gaap'][0], v['rev']); chk(f'{p} ng gaap oi', ng['gaap'][1], v['oi'])
        if ng['gaap'][2] is not None: chk(f'{p} ng gaap ni', ng['gaap'][2], v['ni'])
        chk(f'{p} ng gaap eps', ng['gaap'][3], v['eps_d'], 0.0101)
        chk(f'{p} adj oi', v['oi'] + v['oa_revdef'] + v['oa_restr'] + v['oa_legal'], v['adj_oi_pub'])
        if v.get('adj_ni_pub') is not None and ng['gaap'][2] is not None:
            chk(f'{p} adj ni', v['ni'] + v['na_op'] + v['na_tax'] + v['na_openai'], v['adj_ni_pub'])
            chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['adj_eps_pub'], 0.0151)
        else:
            chk(f'{p} adj eps (per share)', v['eps_d'] + v['na_op_ps'], v['adj_eps_pub'], 0.0101)
    # cash and balance sheet
    chk(f'{p} cfo', v['cf_ni'] + v['cf_dda'] + v['cf_sbc'] + v['cf_def'] + v['cf_wc'], v['cf_cfo'])
    chk(f'{p} cash roll', v['cf_beg'] + v['cf_net'], v['cf_end']); chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'])
    chk(f'{p} bs', v['bs_ta'], v['bs_tle']); chk(f'{p} bs liab', v['bs_tl'] + v['bs_eq'], v['bs_tle'])
    chk(f'{p} cf ni', v['cf_ni'], v['ni'])

for y in range(2013, 2027):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'rd', 'sm', 'ga', 'oi', 'oth', 'tax', 'ni', 'cf_cfo', 'cf_capex', 'cf_acq', 'cf_cfi', 'cf_bb', 'cf_div', 'cf_iss', 'cf_cff',
              'cf_dda', 'cf_sbc', 'cf_def', 'cf_wc', 'cf_ofin', 'dps', 's3_pbp_r', 's3_ic_r', 's3_mpc_r', 's3_pbp_o', 's3_ic_o', 's3_mpc_o', 'l1_win_r', 'l2_cl_r',
              'pl_az', 'pl_m365', 'pl_xbox', 'sg_ai_oi', 'sg_dc_oi', 'oa_revdef', 'oa_restr', 'na_openai'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 0.0101 if k == 'dps' else 2.01, key=(str(y), k))
REV = ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax']
for p in normalize.periods():
    v = x(p); fy, q = normalize.fyq(p)
    if q == 4: continue
    kind, qq = ('FY', 4) if q is None else ('Q', q)
    chk(f'{p} xbrl rev', xbrl.first_of(REV, fy, kind, qq), v['rev'], 0.6)
    chk(f'{p} xbrl oi', xbrl.value('OperatingIncomeLoss', fy, kind, qq), v['oi'], 0.6, key=(p, 'xbrl oi'))
    chk(f'{p} xbrl ni', xbrl.value('NetIncomeLoss', fy, kind, qq), v['ni'], 0.6)
    chk(f'{p} xbrl eps', xbrl.value('EarningsPerShareDiluted', fy, kind, qq), v['eps_d'], 0.0101)
    chk(f'{p} xbrl ta', xbrl.value('Assets', fy, 'I', qq), v['bs_ta'], 0.6)
    if q is None: chk(f'{p} xbrl cfo', xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, 'FY'), v['cf_cfo'], 0.6)
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues; documented exceptions: {sorted(EXC)}')
