"""Consistency checks on the normalised Meta data: statement arithmetic, segment / geography sums, the company's non-GAAP and free-cash-flow
reconciliations, EPS, cash-flow and balance-sheet tie-outs, quarters vs fiscal years, and a cross-check of revenue, operating income, net
income, diluted EPS, CFO and total assets against the XBRL company facts (earliest-filed 10-K / 10-Q fact)."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
EXC = {                                     # documented exceptions (FY column = the Q4 release's year column; quarters as first reported)
    'FY2013 cf_dda sum-q': 'FY2013 release year column vs quarters as first reported (later re-presented); FY uses the year column',
    'FY2014 ng_oi sum-q': 'non-GAAP excludes amortization of intangibles from Q3-2014; the FY2014 figure applies it to the full year',
    'FY2014 ng_ni sum-q': 'same definition change (amortization from Q3-2014)',
    'FY2018 cf_cfo sum-q': 'FY2018 release reclassified $65m between operating cash flow and capex vs Q1-Q3 2018 as first reported',
    'FY2018 cf_capex sum-q': 'same $65m reclassification', 'FY2018 cf_cfi sum-q': 'same reclassification',
    'FY2018 cf_cff sum-q': 'rounding ($2m)', 'FY2019 cf_cff sum-q': 'rounding ($2m)'}
for k in ('rd', 'mm', 'costs', 'oi', 'ebt', 'tax', 'ni', 'cf_cfo', 'cf_sbc', 'cf_cff', 'fcf_pub'):
    EXC[f'FY2016 {k} sum-q'] = 'ASU 2016-09 early-adopted in Q4-2016 with effect from 1-Jan-2016; Q1-Q3 2016 as originally reported, FY2016 on the new basis'
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol:
        reason = EXC.get(name)
        bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})' + (f'  [documented: {reason}]' if reason else ''))
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} costs', v['cogs'] + v['rd'] + v['mm'] + v['ga'], v['costs'], 1.1)
    chk(f'{p} oi', v['rev'] - v['costs'], v['oi'])
    chk(f'{p} ebt', v['oi'] + v['io_net'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'])
    chk(f'{p} ni common', v['ni'] - v['ni_part'], v['ni_common'])
    tol_eps = 0.0101 if p.isdigit() or int('20' + p[-2:]) >= 2014 else 0.011
    if v.get('sh_d'): chk(f'{p} eps', (v['ni_common'] + v['ni_dil_realloc']) / v['sh_d'], v['eps_d'], tol_eps)
    else: bad.append(f'{p}: no diluted shares')
    if v.get('foa_rev') is not None:
        chk(f'{p} seg rev', v['foa_rev'] + v['rl_rev'], v['rev']); chk(f'{p} seg oi', v['foa_oi'] + v['rl_oi'], v['oi'])
        chk(f'{p} foa rev', v['foa_adv'] + v['foa_oth'], v['foa_rev'])
    if v.get('geo_usc') is not None:
        chk(f'{p} geo', v['geo_usc'] + v['geo_eu'] + v['geo_ap'] + v['geo_row'], v['rev'], 1.1)
    if v.get('ng_oi') is not None:
        chk(f'{p} ng oi', v['oi'] + n(v.get('ng_sbc')) + v['ng_payroll'] + v['ng_amort'], v['ng_oi'])
        if v.get('ng_ni') is not None and v.get('ng_taxadj') is not None:
            chk(f'{p} ng ni', v['ni'] + n(v.get('ng_sbc')) + v['ng_payroll'] + v['ng_amort'] + v['ng_taxadj'], v['ng_ni'])
            chk(f'{p} ng eps', v['ng_ni'] / v['ng_sh'], v['ng_eps'], 0.0101)
    if v.get('fcf_pub') is not None:
        chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'] + v['fcf_cl'] + v['fcf_flp'], v['fcf_pub'])
    if v.get('cf_cfo') is not None and v.get('cf_beg') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        if v.get('bs_cash') is not None and int(p[-2:] if not p.isdigit() else p) < 18 and not p.isdigit(): chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'])
    if v.get('bs_ta') is not None: chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    # XBRL cross-check (earliest-filed fact)
    fy, q = normalize.fyq(p)
    kind = 'FY' if p.isdigit() else 'Q'
    if fy >= 2010:
        for key, concepts in (('rev', ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax']), ('oi', ['OperatingIncomeLoss']),
                              ('ni', ['NetIncomeLoss']), ('eps_d', ['EarningsPerShareDiluted'])):
            xv = xbrl.first_of(concepts, fy, kind, q) if (p.isdigit() or q < 4) else None
            if xv is not None: chk(f'{p} xbrl {key}', v[key], xv, 0.0101 if key == 'eps_d' else 0.6)
        if p.isdigit() or q == 1:
            xv = xbrl.first_of(['NetCashProvidedByUsedInOperatingActivities'], fy, 'FY' if p.isdigit() else 'YTD', q)
            if xv is not None and v.get('cf_cfo') is not None: chk(f'{p} xbrl cfo', v['cf_cfo'], xv)
        xa = xbrl.value('Assets', fy, 'I', q)
        if xa is not None and v.get('bs_ta') is not None: chk(f'{p} xbrl ta', v['bs_ta'], xa)
FLOW = ('rev', 'cogs', 'rd', 'mm', 'ga', 'costs', 'oi', 'io_net', 'ebt', 'tax', 'ni', 'adv', 'cf_cfo', 'cf_capex', 'cf_dda', 'cf_sbc', 'cf_cfi', 'cf_cff',
        'cf_bb', 'cf_div', 'cf_lease', 'foa_rev', 'rl_rev', 'foa_oi', 'rl_oi', 'geo_usc', 'fcf_pub', 'ng_oi', 'ng_ni')
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in FLOW:
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        fyv = x(str(y)).get(k)
        if all(q is not None for q in qs) and fyv is not None: chk(f'FY{y} {k} sum-q', sum(qs), fyv, 1.6)
print('\n'.join(bad) or 'all checks pass')
und = [b for b in bad if '[documented' not in b and 'no diluted shares' not in b]
print(f'{ok[0]} checks, {len(bad)} exceptions ({len(bad) - len(und)} documented), {len(und)} undocumented')
