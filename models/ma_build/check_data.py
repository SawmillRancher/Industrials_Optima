"""Consistency checks on the normalised Mastercard data: statement arithmetic, non-GAAP bridges vs published, revenue categories,
EPS, cash-flow and balance-sheet tie-outs, quarters vs years, and cross-checks to XBRL company facts (as first filed)."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
KNOWN = {           # documented exceptions: key -> reason (README / cell comments)
    '2008 adj eps': 'two-class method (participating securities) in the EPS denominator; net income / diluted shares overstates EPS by ~$0.007 (pre-split $0.07)',
    '2009 eps': 'two-class method (FSP EITF 03-6-1, adopted 2009): EPS uses net income allocated to common shares',
    '2009 adj eps': 'two-class method, as 2009 GAAP EPS',
    'FY2018 ga sum-q': 'the Q4-18 release reclassified $89m between advertising & marketing and G&A for the year; quarters as originally reported',
    'FY2018 am sum-q': 'see FY2018 ga',
    'FY2019 oa_eqgl sum-q': 'equity-investment (gains) losses excluded from non-GAAP from Q2-19; Q1-19 as originally reported (FY2019 includes Q1)',
    'FY2016 gdv sum-q': 'GDV is customer-reported and revised; annual table vs quarterly tables as first published',
    'FY2017 gdv sum-q': 'GDV revisions', 'FY2018 gdv sum-q': 'GDV revisions', 'FY2020 gdv sum-q': 'GDV revisions', 'FY2025 gdv sum-q': 'GDV revisions (Q4-25 annual table)',
}
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol:
        msg = f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})'
        bad.append(msg + (f'  [known: {KNOWN[name]}]' if name in KNOWN else ''))
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} opex lines', v['ga'] + v['am'] + n(v.get('da')) + v['lit'] + v['char'], v['opex'], 1.1)
    chk(f'{p} oi', v['rev'] - v['opex'], v['oi'], 1.1)
    chk(f'{p} ebt', v['oi'] + v['inv_inc'] + v['eq_gl'] - v['int_exp'] + v['oth_inc'], v['ebt'], 1.1)
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni_tot'], 1.1)
    chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101 if not v.get('split_adj') else 0.006)
    if v.get('adj_basis') == 'published':
        items_o = n(v.get('oa_lit')) + n(v.get('oa_restr')) + n(v.get('oa_oth'))
        if v.get('adj_rev_pub') is not None: chk(f'{p} adj rev', v['rev'] + n(v.get('oa_rev')), v['adj_rev_pub'], 1.1)
        if v.get('adj_opex_pub') is not None: chk(f'{p} adj opex', v['opex'] - items_o, v['adj_opex_pub'], 1.1)
        if v.get('e_pub') is not None and v.get('adj_ni_pub') is not None: chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['e_pub'], 0.0201 if not v.get('split_adj') else 0.006)
    leg = [v.get(k) for k in ('rcl_dom', 'rcl_xb', 'rcl_tp', 'rcl_oth', 'rcl_reb')]
    if v.get('rc_pn') is not None: chk(f'{p} revcat current', v['rc_pn'] + v['rc_vas'], v['rev'], 1.1)
    elif all(l is not None for l in leg): chk(f'{p} revcat legacy', sum(leg), v['rev'], 1.1)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash roll', v['cf_beg'] + v['cf_net'], v['cf_end'], 1.1)
        if v.get('bs_cash') is not None:
            bs = v['bs_cash'] + (v['bs_rcash'] + v['bs_rsd'] if v.get('cf_basis') == 'restricted' else 0.0)
            if abs(n(v.get('bs_rc_oth'))) > 1.1:
                bad.append(f'{p} cash vs bs: {v["bs_rc_oth"]:+.0f} restricted cash held in other assets (memo line in the model)  [known]')
            else:
                chk(f'{p} cash vs bs ({v.get("cf_basis")})', v['cf_end'], bs, 1.1)
    if v.get('bs_ta') is not None: chk(f'{p} bs', v['bs_ta'], v['bs_tle'], 1.1)
    # XBRL cross-checks (as first filed; from FY2009 / Q2-09)
    fy, q = normalize.fyq(p)
    kind = 'FY' if p.isdigit() else 'Q'
    if fy >= 2010 and not (kind == 'Q' and q == 4):
        rv = xbrl.first_of(['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'], fy, kind, q)
        chk(f'{p} xbrl rev', v['rev'], rv, 1.1)
        chk(f'{p} xbrl oi', v['oi'], xbrl.value('OperatingIncomeLoss', fy, kind, q), 1.1)
        chk(f'{p} xbrl ni', v['ni'], xbrl.first_of(['NetIncomeLoss', 'ProfitLoss'], fy, kind, q), 1.1)
        e = xbrl.value('EarningsPerShareDiluted', fy, kind, q, pick='first')
        chk(f'{p} xbrl eps (as first filed)', v['eps_d_asrep'], e, 0.0101)
    if fy >= 2010 and kind == 'FY':
        chk(f'{p} xbrl cfo', v['cf_cfo'], xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, 'FY'), 1.1)
    if fy >= 2010 and v.get('bs_ta') is not None:
        chk(f'{p} xbrl assets', v['bs_ta'], xbrl.value('Assets', fy, 'I', q), 1.1)
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'ga', 'am', 'da', 'lit', 'opex', 'oi', 'ebt', 'tax', 'ni', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_cfi', 'cf_cff',
              'oa_lit', 'oa_restr', 'oa_oth', 'oa_eqgl', 'rc_pn', 'rc_vas', 'rcl_dom', 'rcl_xb', 'rcl_tp', 'rcl_oth', 'rcl_reb', 'dps', 'gdv'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        fyv = x(str(y)).get(k)
        if all(qv is not None for qv in qs) and fyv is not None:
            tol = 1.1 if k not in ('gdv',) else 3.1
            chk(f'FY{y} {k} sum-q', sum(qs), fyv, tol)
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
