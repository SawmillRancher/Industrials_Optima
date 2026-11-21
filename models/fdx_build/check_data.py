"""Data consistency checks on the normalised FedEx data (both bases). Prints every failure; known, explained exceptions are listed
in EXC and reported separately. Run after extract.py."""
import normalize as n, xbrl
D = n.run()
X = lambda p, k: D.get(p, {}).get('x', {}).get(k)
N = lambda v: v or 0.0
EXC = {
    ('L2013', 'sumq:sal'): 'FY2013 salaries: the FY total in the Q4 release is $8m below the sum of the quarters as first reported (reclassification between cost lines)',
    # FY2015: mark-to-market pension accounting adopted in Q4 FY2015; Q1-Q3 FY2015 stay as originally reported (old basis)
    ('L2015', 'sumq'): 'FY2015 Q1-Q3 as originally reported before the Q4 FY15 change to MTM pension accounting / segment cost allocation',
}
fails, exc, cnt = [], [], 0
def chk(p, name, a, b, tol=1.01):
    global cnt
    if a is None or b is None: return
    cnt += 1
    if abs(a - b) > tol:
        (exc if (p, name) in EXC or (p, name.split(':')[0]) in EXC else fails).append(f'{p:8s} {name:22s} {a:12.2f} vs {b:12.2f}  diff {a - b:9.2f}')

SEGR = ['sr_' + k for k in ('exp', 'tnt', 'gnd', 'frt', 'kin', 'svc', 'fec', 'usd', 'intl', 'oth')]
SEGO = ['so_' + k for k in ('exp', 'tnt', 'gnd', 'frt', 'kin', 'svc', 'fec', 'usd', 'intl', 'oth')]
for p in n.periods() + ['C9M-25', 'C9M-26']:
    if X(p, 'rev') is None: continue
    opex = sum(N(X(p, k)) for k in ('sal', 'pt', 'rent', 'da', 'fuel', 'maint', 'spec', 'oth'))
    chk(p, 'opex lines', opex, X(p, 'opex_tot')); chk(p, 'rev-opex=oi', X(p, 'rev') - X(p, 'opex_tot'), X(p, 'oi'))
    chk(p, 'seg rev', sum(N(X(p, k)) for k in SEGR), X(p, 'rev')); chk(p, 'seg oi', sum(N(X(p, k)) for k in SEGO), X(p, 'oi'))
    chk(p, 'ebt', X(p, 'oi') + N(X(p, 'int_net')) + N(X(p, 'ret')) + N(X(p, 'inv_gain')) + N(X(p, 'oth_nonop')), X(p, 'ebt'))
    chk(p, 'ni cont', X(p, 'ebt') - X(p, 'tax'), X(p, 'ni_cont')); chk(p, 'ni', X(p, 'ni_cont') + N(X(p, 'disc')), X(p, 'ni'))
    if X(p, 'sh_d') and not X(p, 'sh_d_derived'): chk(p, 'eps', X(p, 'ni') / X(p, 'sh_d'), X(p, 'eps_d'), 0.105)   # two-class method; share count printed in whole millions
    if X(p, 'bs_ta') is not None:
        chk(p, 'TA=TLE', X(p, 'bs_ta'), X(p, 'bs_tle'))
    if X(p, 'cf_cfo') is not None and X(p, 'cf_beg') is not None and X(p, 'cf_end') is not None:
        chk(p, 'cash roll', X(p, 'cf_beg') + X(p, 'cf_net'), X(p, 'cf_end'))
    if X(p, 'cf_end') is not None and X(p, 'bs_cash') is not None: chk(p, 'BS cash=CF end', X(p, 'bs_cash') + N(X(p, 'bs_rcash')), X(p, 'cf_end'))
    if X(p, 'adj_basis') == 'published':
        oa = sum(N(X(p, 'oa_' + c)) for c in n.OCATS)
        chk(p, 'adj OI bridge', X(p, 'oi') + oa, X(p, 'adj_oi_pub'), 1.51)
        chk(p, 'adj NI bridge', X(p, 'ni_cont') + oa + N(X(p, 'oa_nonop')) - N(X(p, 'oa_tax')), X(p, 'adj_ni_pub'), 2.01)
        chk(p, 'adj EPS', X(p, 'adj_ni_pub') / X(p, 'sh_d'), X(p, 'adj_eps_pub'), 0.105)
    if p.startswith('C') and X(p, 'adv_pri'):
        d = X(p, 'days')
        for a, y, r in (('adv_pri', 'y_pri', 'r_pri'), ('adv_def', 'y_def', 'r_def'), ('adv_gnd', 'y_gnd', 'r_gnd'), ('adv_ip', 'y_ip', 'r_ip'),
                        ('adv_ie', 'y_ie', 'r_ie'), ('adv_id', 'y_id', 'r_id')):
            if X(p, a) and X(p, r): chk(p, 'stats:' + r, X(p, a) * X(p, y) * d / 1000 / X(p, r), 1.0, 0.012)
        chk(p, 'usd rev', N(X(p, 'r_pri')) + N(X(p, 'r_def')) + N(X(p, 'r_gnd')) + N(X(p, 'r_ufrt')) + N(X(p, 'r_uoth')), X(p, 'usd_rev'))
        chk(p, 'intl rev', N(X(p, 'r_ip')) + N(X(p, 'r_ie')) + N(X(p, 'r_id')) + N(X(p, 'r_ifrt')) + N(X(p, 'r_ioth')), X(p, 'intl_rev'))
        chk(p, 'usd=seg', X(p, 'usd_rev'), X(p, 'sr_usd')); chk(p, 'intl=seg', X(p, 'intl_rev'), X(p, 'sr_intl'))
# quarters vs years
for y in range(2013, 2027):
    a = f'L{y}'; qs = [f'LQ{q}-{str(y)[2:]}' for q in (1, 2, 3, 4)]
    for k in ('rev', 'oi', 'ni', 'tax', 'sal', 'capex_is'):
        if all(X(q, k) is not None for q in qs): chk(a, 'sumq:' + k, sum(X(q, k) for q in qs), X(a, k), 2.01)
for y in (2024, 2025):
    a = f'CY{y}'; qs = [f'CQ{q}-{str(y)[2:]}' for q in (1, 2, 3, 4)]
    for k in ('rev', 'oi', 'ni_cont', 'ni', 'usd_rev', 'intl_rev', 'r_gnd', 'adj_oi_pub', 'adj_ni_pub'):
        if all(X(q, k) is not None for q in qs): chk(a, 'sumq:' + k, sum(X(q, k) for q in qs), X(a, k), 2.01)
qs = ['CQ1-26', 'CQ2-26', 'CQ3-26']
for k in ('rev', 'oi', 'ni_cont', 'ni', 'usd_rev', 'intl_rev'): chk('C9M-26', 'sumq:' + k, sum(X(q, k) for q in qs), X('C9M-26', k), 2.01)
# XBRL cross-checks (as first filed), legacy basis
for y in range(2010, 2027):
    p = f'L{y}'
    chk(p, 'xbrl OI', X(p, 'oi'), xbrl.value('OperatingIncomeLoss', y, 'FY')); chk(p, 'xbrl NI', X(p, 'ni'), xbrl.value('NetIncomeLoss', y, 'FY'))
    chk(p, 'xbrl EPS', X(p, 'eps_d'), xbrl.value('EarningsPerShareDiluted', y, 'FY'), 0.011)
    chk(p, 'xbrl assets', X(p, 'bs_ta'), xbrl.value('Assets', y, 'I', 4)); chk(p, 'xbrl CFO', X(p, 'cf_cfo'), xbrl.value('NetCashProvidedByUsedInOperatingActivities', y, 'FY'))
    if y >= 2013:
        for q in (1, 2, 3):
            pq = f'LQ{q}-{str(y)[2:]}'
            chk(pq, 'xbrl OI', X(pq, 'oi'), xbrl.value('OperatingIncomeLoss', y, 'Q', q)); chk(pq, 'xbrl NI', X(pq, 'ni'), xbrl.value('NetIncomeLoss', y, 'Q', q))
            chk(pq, 'xbrl EPS', X(pq, 'eps_d'), xbrl.value('EarningsPerShareDiluted', y, 'Q', q), 0.011)
            chk(pq, 'xbrl assets', X(pq, 'bs_ta'), xbrl.value('Assets', y, 'I', q))
print(cnt, 'checks;', len(fails), 'failures;', len(exc), 'documented exceptions')
for f in fails: print('FAIL', f)
for f in exc: print('EXC ', f)
for l in n.LOG: print('LOG ', l)
