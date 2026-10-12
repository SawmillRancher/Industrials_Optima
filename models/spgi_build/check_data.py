"""Data consistency checks on the normalised model data (normalize.run()): statement arithmetic, division sums, bridges vs
published, quarters vs years, cash and balance-sheet tie-outs, XBRL cross-checks. Prints failures; known exceptions are listed."""
import normalize as nz, xbrl
D = nz.run(); P = nz.periods(); fails = []; n = 0
def x(p, k): return D.get(p, {}).get('x', {}).get(k)
def chk(p, name, a, b, tol=1.01):
    global n
    if a is None or b is None: return
    n += 1
    if abs(a - b) > tol: fails.append(f'{p:6} {name}: {a:,.1f} vs {b:,.1f} ({a - b:+,.1f})')
N = nz.N
for p in P:
    if x(p, 'rev') is None: continue
    if x(p, 'exp') is not None: chk(p, 'rev-exp+gain+eq=op', x(p, 'rev') - x(p, 'exp') + N(x(p, 'gain')) + N(x(p, 'eq_inc')), x(p, 'op'))
    if all(x(p, k) is not None for k in ('op_rel', 'sga', 'dep', 'amort', 'exp')):
        chk(p, 'opex lines = expenses', x(p, 'op_rel') + x(p, 'sga') + x(p, 'dep') + x(p, 'amort'), x(p, 'exp'), 2.01)
    chk(p, 'op+oth-int=ebt', x(p, 'op') + N(x(p, 'oth_inc')) - N(x(p, 'int')), x(p, 'ebt'))
    if x(p, 'ebt') is not None: chk(p, 'ni attr', x(p, 'ebt') - x(p, 'tax') - N(x(p, 'nci')) + N(x(p, 'disc')), x(p, 'ni_attr'))
    segs = [x(p, f'sr_{r}') for r in ('RAT', 'IDX', 'CI', 'MI', 'MOB', 'ES', 'LEG')]
    if x(p, 'sr_RAT') is not None: chk(p, 'sum divisions = revenue', sum(N(v) for v in segs) + N(x(p, 'elim')), x(p, 'rev'))
    if x(p, 'adj_op_pub') is not None and x(p, 'sa_RAT') is not None:
        a = sum(N(x(p, f'sa_{r}')) for r in ('RAT', 'IDX', 'CI', 'MI', 'MOB', 'ES', 'LEG')) - N(x(p, 'adj_corp')) + N(x(p, 'adj_eq')) + N(x(p, 'g_res'))
        chk(p, 'adjusted divisions = adjusted OP', a, x(p, 'adj_op_pub'))
    if x(p, 'adj_op_pub') is not None:
        chk(p, 'OP + items + amort = adjusted OP', x(p, 'op') + sum(N(x(p, f'oa_{c}')) for c in nz.CATS) + N(x(p, 'deal_amort')), x(p, 'adj_op_pub'))
    if x(p, 'e_pub') is not None and x(p, 'adj_ni_pub') is not None:
        sh = x(p, 'adj_sh_d') or x(p, 'sh_d'); chk(p, 'adj NI / shares = adj EPS', x(p, 'adj_ni_pub') / sh, x(p, 'e_pub'), 0.0201)
    if x(p, 'eps_d') is not None and x(p, 'sh_d'): chk(p, 'NI / shares = EPS', x(p, 'ni_attr') / x(p, 'sh_d'), x(p, 'eps_d'), 0.0201)
    if x(p, 'cf_cfo') is not None and x(p, 'cf_beg') is not None and x(p, 'cf_end') is not None:
        chk(p, 'beg + net = end cash', x(p, 'cf_beg') + x(p, 'cf_net'), x(p, 'cf_end'))
    if x(p, 'bs_ta') is not None:
        chk(p, 'BS cash = CF end cash', x(p, 'bs_cash'), x(p, 'cf_end'))
        tle = sum(N(x(p, k)) for k in ('bs_ap', 'bs_acc', 'bs_std', 'bs_taxp', 'bs_unr', 'bs_ocl', 'bs_ltd', 'bs_lease', 'bs_dtl', 'bs_onl', 'bs_rnci', 'bs_eq', 'bs_nci'))
        chk(p, 'TA = TL&E', x(p, 'bs_ta'), tle)
# quarters vs years
for y in range(2013, 2026):
    for k in ('rev', 'op', 'ni_attr', 'adj_op_pub', 'cf_cfo', 'op_rel', 'sga', 'deal_amort'):
        qs = [x(f'Q{q}-{str(y)[2:]}', k) for q in (1, 2, 3, 4)]
        if all(v is not None for v in qs): chk(str(y), f'sum Q = FY {k}', sum(qs), x(str(y), k), 2.01)
# XBRL cross-checks (as first filed), annual
for y in range(2012, 2025):
    p = str(y)
    chk(p, 'XBRL revenue', xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'], y, 'FY'), x(p, 'rev'))
    chk(p, 'XBRL OP', xbrl.value('OperatingIncomeLoss', y, 'FY'), x(p, 'op'))
    chk(p, 'XBRL NI attr', xbrl.value('NetIncomeLoss', y, 'FY'), x(p, 'ni_attr'))
    chk(p, 'XBRL diluted EPS', xbrl.value('EarningsPerShareDiluted', y, 'FY'), x(p, 'eps_d'), 0.011)
KNOWN = {('2014', 'rev'): 'Q1-Q2/14 as originally reported include McGraw Hill Construction; Q3-14 release moved it to discontinued operations and FY2014 excludes it',
         ('2014', 'op'): 'same (Construction)', ('2014', 'adj_op_pub'): 'same (Construction)', ('2014', 'op_rel'): 'same (Construction)', ('2014', 'sga'): 'same (Construction)',
         ('2019', 'op_rel'): 'FY2019 10-K reclassified ~$8m between operating-related and selling & general expenses (quarters as first filed)',
         ('2019', 'sga'): 'same (2019 reclassification)',
         ('2025', 'adj_op_pub'): 'pro forma quarterization: company quarterly pro forma adjusted OP sums to 6,971 vs 6,974 for the year (rounding in the 8-K/A)'}
known = [f for f in fails if any(f.startswith(f'{y:6} sum Q = FY {k}:') for (y, k) in KNOWN)]
other = [f for f in fails if f not in known]
print(f'{n} checks, {len(other)} unexplained failures, {len(known)} known exceptions')
for f in known: print('  known:', f)
print('\n'.join(other))
