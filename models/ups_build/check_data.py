"""Data consistency checks on the normalised UPS data (run after extract.py). Prints every failure; exits 1 if any is not a known,
documented exception (KNOWN)."""
import sys
import normalize, xbrl

D = normalize.run()
SEG = ('us', 'intl', 'scs')
KNOWN = {
    # (period, check): reason
    ('Q1-25', 'published FCF'): 'release (29-Apr-2025) other investing activities -20 vs -10 in the Q1-2025 10-Q (reclassified after the release)',
    ('2025', 'published FCF'): 'carries the Q1-2025 reclassification: FY release other investing vs the 10-K differ by 10',
}
fails, n = [], 0


def chk(p, name, a, b, tol=1.0):
    global n
    if a is None or b is None: return
    n += 1
    if abs(a - b) > tol: fails.append((p, name, round(a, 2), round(b, 2)))


for p, d in D.items():
    x = d['x']; g = x.get
    # income statement arithmetic and segments
    chk(p, 'segment revenue sum', sum(g(f'rev_{s}', 0) for s in SEG), g('rev'))
    chk(p, 'segment operating profit sum', sum(g(f'op_{s}', 0) for s in SEG), g('op'))
    chk(p, 'revenue - opex = op', g('rev') - g('opex'), g('op'))
    chk(p, 'op + other income - interest = ebt', g('op') + g('oth_inc') - g('int_exp'), g('ebt'), 1.5)
    chk(p, 'ebt - tax = ni', g('ebt') - g('tax'), g('ni'))
    if g('sh_d'): chk(p, 'eps diluted', g('ni') / g('sh_d'), g('eps_d'), 0.011)
    if all(g('x_' + k) is not None for k in normalize.OPX):
        chk(p, 'opex detail sum', sum(g('x_' + k) for k in normalize.OPX), g('opex'), 1.5)
    # operating data
    for s, prods in (('us', ('nda', 'def', 'gnd', 'cargo')), ('intl', ('dom', 'exp', 'cargo')), ('scs', ('fl', 'frt', 'oth'))):
        chk(p, f'product revenue sum {s}', sum(g(f'o_rev_{s}_{k}', 0) or 0 for k in prods), g(f'o_rev_{s}'), 1.5)
        chk(p, f'operating-data revenue vs segment {s}', g(f'o_rev_{s}'), g(f'rev_{s}'))
    for s, prods in (('us', ('nda', 'def', 'gnd')), ('intl', ('dom', 'exp'))):
        chk(p, f'ADV sum {s}', sum(g(f'o_adv_{s}_{k}', 0) for k in prods), g(f'o_adv_{s}'), 1.5)
        for k in prods:       # average daily volume (000) x revenue per piece x operating days = product revenue (rounding of the published KPIs)
            a, r, dd, rv = g(f'o_adv_{s}_{k}'), g(f'o_rpp_{s}_{k}'), g('o_days'), g(f'o_rev_{s}_{k}')
            if None not in (a, r, dd, rv): chk(p, f'ADV x RPP x days {s}_{k}', a * r * dd / 1000, rv, max(3.0, 0.004 * rv))
    # adjusted measures
    if g('adj_pub'):
        chk(p, 'adjusted segment op sum', sum(g(f'aop_{s}') for s in SEG), g('aop_pub'))
        if g('sh_d'): chk(p, 'adjusted eps', g('a_ni_pub') / g('a_sh', g('sh_d')), g('a_eps_pub'), 0.011)
    # cash flow and balance sheet
    chk(p, 'cfo + cfi + cff + fx = net', g('cf_cfo') + g('cf_cfi') + g('cf_cff') + g('cf_fx'), g('cf_net'), 1.5)
    chk(p, 'beg + net + held-for-sale cash = end', g('cf_beg') + g('cf_net') + g('cf_hfs'), g('cf_end'), 1.5)
    # published free cash flow is 'preliminary, subject to reclassification' in the releases: compared from 2016, when the release statements match the filings
    if (int(p) if len(p) == 4 else 2000 + int(p[3:])) >= 2016:
        chk(p, 'published FCF', g('cf_cfo') + g('cf_capex') + g('cf_disp') + g('cf_finrec') + (g('cf_oinv_pub') or 0), g('fcf_pub'), 1.5)
    chk(p, 'cash-flow D&A vs income-statement D&A', g('cf_da'), g('x_da'), 1.5)
    if len(p) == 4:
        y = int(p)
        qs = [D.get(normalize.qk(y, q)) for q in (1, 2, 3, 4)]
        if all(qs):
            for k in ('rev', 'op', 'ni', 'rev_us', 'rev_intl', 'rev_scs', 'op_us', 'op_intl', 'op_scs', 'cf_cfo', 'cf_capex', 'dps', 'x_comp', 'x_othx'):
                if all(q['x'].get(k) is not None for q in qs): chk(p, f'sum of quarters {k}', sum(q['x'][k] for q in qs), g(k), 1.5 if k != 'dps' else 0.005)
        # XBRL cross-checks (as first filed)
        for k, c in (('rev', ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax')), ('op', ('OperatingIncomeLoss',)), ('ni', ('NetIncomeLoss',)),
                     ('eps_d', ('EarningsPerShareDiluted',)), ('cf_cfo', ('NetCashProvidedByUsedInOperatingActivities',))):
            v = next((xbrl.value(cc, y, 'FY') for cc in c if xbrl.value(cc, y, 'FY') is not None), None)
            chk(p, f'XBRL {k}', g(k), v, 0.011 if k == 'eps_d' else 1.0)
        chk(p, 'XBRL total assets', g('bs_ta'), xbrl.value('Assets', y, 'I', 4))
    else:
        y, q = 2000 + int(p[3:]), int(p[1])
        for k, c in (('rev', ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax')), ('op', ('OperatingIncomeLoss',)), ('ni', ('NetIncomeLoss',))):
            if q < 4:
                v = next((xbrl.value(cc, y, 'Q', q) for cc in c if xbrl.value(cc, y, 'Q', q) is not None), None)
                chk(p, f'XBRL {k}', g(k), v)
        chk(p, 'XBRL total assets', g('bs_ta'), xbrl.value('Assets', y, 'I', q))

bad = [f for f in fails if (f[0], f[1]) not in KNOWN]
for f in fails: print(('known  ' if (f[0], f[1]) in KNOWN else 'FAIL   '), *f, KNOWN.get((f[0], f[1]), ''))
print(f'{n} checks, {len(fails)} differences, {len(bad)} unexplained')
sys.exit(1 if bad else 0)
