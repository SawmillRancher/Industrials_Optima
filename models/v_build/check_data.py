"""Consistency checks on the normalised Visa data: statement arithmetic, revenue categories, EPS, non-GAAP tie-outs (adjusted EPS
and adjusted operating expenses vs published), cash-flow and balance-sheet tie-outs, quarters vs fiscal years, and a cross-check
of revenue / net income / total assets / CFO against XBRL company facts (as first filed)."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
EXC = {             # known, explained exceptions: key -> reason
    '2008 gaap eps': 'FY2008 class A EPS ($0.96 pre-split) was computed by the company on net income allocated to class A from the 19-Mar-2008 IPO '
                     '(two-class method, reorganization-year share weighting); net income / weighted diluted shares does not reproduce it.'}
def chk(name, a, b, tol=1.01):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol:
        if name in EXC: return
        bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
OPC, NOPC = normalize.OPC, normalize.NOPC
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    if v.get('rev_gross') is not None: chk(f'{p} rev cats', v['rev_gross'] - v['rev_ci'], v['rev_net'])
    if v.get('personnel') is not None:
        chk(f'{p} opex lines', sum(n(v.get(k)) for k in ('personnel', 'marketing', 'network', 'prof', 'dna', 'ga', 'litig', 'oth_op')), v['opex'])
    chk(f'{p} opinc', v['rev_net'] - v['opex'], v['opinc'])
    chk(f'{p} ebt', v['opinc'] + v['nonop'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni_tot'])
    chk(f'{p} ni attr', v['ni_tot'] - n(v.get('nci')), v['ni'])
    if v.get('eps_d') is not None and v.get('sh_d'): chk(f'{p} gaap eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101)
    if v.get('adj_basis') == 'published':
        pre_op = sum(n(v.get('oa_' + c)) for c in OPC); pre_no = sum(n(v.get('na_' + c)) for c in NOPC)
        chk(f'{p} adj ni bridge', v['ni'] + pre_op + pre_no + v['ng_taxeff'], v['adj_ni_pub'])
        if v.get('adj_opex_pub') is not None: chk(f'{p} adj opex', v['opex'] - pre_op, v['adj_opex_pub'])
        if v.get('sh_d') and v.get('adj_eps_pub') is not None: chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['adj_eps_pub'], 0.0151)
    if v.get('cf_cfo') is not None and v.get('cf_beg') is not None:
        chk(f'{p} cash roll', v['cf_beg'] + v['cf_net'], v['cf_end'])
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
        chk(f'{p} bs tl+te', v['bs_tl'] + v['bs_te'], v['bs_tle'])
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev_svc', 'rev_dp', 'rev_itr', 'rev_oth', 'rev_ci', 'rev_net', 'personnel', 'marketing', 'network', 'prof', 'dna', 'ga', 'litig', 'opex',
              'opinc', 'int_exp', 'nonop', 'ebt', 'tax', 'ni', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_sbc', 'cf_cfi', 'cf_cff', 'k_pv', 'k_ptx',
              'oa_litig', 'oa_amort', 'oa_acq', 'oa_restr', 'na_eqinv'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if k == 'litig': qs = [n(q) for q in qs]                   # litigation provision line not presented in quarters without a provision
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 10.01 if k == 'k_pv' else 1.01)
        elif x(str(y)).get(k) is not None and k not in ('oa_litig', 'oa_amort', 'oa_acq', 'oa_restr', 'na_eqinv'):
            bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
# XBRL cross-check (10-K / 10-Q as first filed; FY2009+)
for p in normalize.periods():
    fy, q = normalize.fyq(p)
    if fy < 2010: continue
    v = x(p); kind = 'FY' if p.isdigit() else 'Q'
    if not p.isdigit() and q == 4: continue
    xr = xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'], fy, kind, q)
    chk(f'{p} xbrl revenue', v.get('rev_net'), xr)
    chk(f'{p} xbrl ni', v.get('ni'), xbrl.value('NetIncomeLoss', fy, kind, q))
    chk(f'{p} xbrl assets', v.get('bs_ta'), xbrl.value('Assets', fy, 'I', 4 if p.isdigit() else q))
    if p.isdigit(): chk(f'{p} xbrl cfo', v.get('cf_cfo'), xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, 'FY'))
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
