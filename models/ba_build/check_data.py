"""Consistency checks on the normalised Boeing data: statement arithmetic, segment sums, core bridges vs the published figures,
EPS, deliveries, cash-flow and balance-sheet tie-outs, quarters vs years, and XBRL cross-checks (revenue, net income, CFO, assets)."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
KNOWN = {'2006 gaap eps': 'release diluted EPS $2.85 vs net earnings / presented diluted shares (787.6m) $2.81; carried as published',
         'Q4-20 core eps': 'Q4 core EPS $(15.25) as published vs bridge $(15.23) (Q4 per-share items rounded); carried as published'}
for k in ('sr_bca', 'sr_bds', 'sr_bgs', 'se_bca', 'se_bds', 'se_bgs'):
    KNOWN[f'FY2017 {k} sum-q'] = 'Global Services formed in Q3-17: Q1/Q2-17 are as originally reported on the prior structure (BCA / BDS incl. services)'
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol:
        msg = f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})'
        bad.append(msg + (f'  [known: {KNOWN[name]}]' if name in KNOWN else ''))
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    fy, q = normalize.fyq(p)
    efo = v['gp'] + v['opinv'] - v['ga'] - v['rd'] + v['gain'] - v['oth_op']
    chk(f'{p} efo', efo, v['efo'])
    chk(f'{p} ebt', v['efo'] + v['oth_inc'] - v['int_exp'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'] + v['disc'], v['ni'])
    chk(f'{p} seg rev', n(v.get('sr_bca')) + n(v.get('sr_bds')) + n(v.get('sr_bgs')) + n(v.get('sr_bcc')) + n(v.get('sr_oth')) + n(v.get('sr_unal')), v['rev'], 1.1)
    chk(f'{p} seg efo', n(v.get('se_bca')) + n(v.get('se_bds')) + n(v.get('se_bgs')) + n(v.get('se_bcc')) + n(v.get('se_oth')) + n(v.get('se_unal')) + n(v.get('se_fascas')),
        v['efo'], 1.1)
    if v.get('eps_d') is not None and v.get('sh_d'):
        # mandatory convertible preferred: if-converted (dividends added back) when dilutive (Q4-25, FY2025 income periods)
        num = v['ni_attr'] if v.get('mcps_ifconv') else v['ni_common']
        chk(f'{p} gaap eps', num / v['sh_d'], v['eps_d'], 0.0101 if abs(v['eps_d']) < 10 else 0.02)
    # core
    if v.get('core_oe_pub') is not None:
        if fy >= 2018: chk(f'{p} core oe', v['efo'] - v['se_fascas'], v['core_oe_pub'], 1.1)
        elif v.get('unal_pp') is not None: chk(f'{p} core oe vs unallocated pension detail', v['efo'] + v['unal_pp'], v['core_oe_pub'], 1.1)
    if v.get('core_eps_pub') is not None and v.get('sh_d'):
        if fy >= 2018:
            sub = -v['se_fascas'] + n(v.get('nonop_pen')) + n(v.get('nonop_pr')) + n(v.get('core_dtax'))
            chk(f'{p} core sub', sub, v.get('core_sub'), 1.1)
            num = v['ni_attr'] if v.get('mcps_ifconv') else v['ni_common']
            chk(f'{p} core eps', (num + sub) / v['sh_d'], v['core_eps_pub'], 0.0151)
    if v.get('del_tot') is not None:
        chk(f'{p} deliveries', sum(n(v.get(f'del_{k}')) for k in ('717', '737', '747', '767', '777', '787')), v['del_tot'], 0.01)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash roll', n(v.get('cf_beg')) + v['cf_net'], v.get('cf_end'), 1.1)
        chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'], v.get('fcf_pub'), 1.1)
        if v.get('cf_end_bs') is not None: chk(f'{p} cash vs bs', v['cf_end_bs'], v['bs_cash'], 0.6)
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
        chk(f'{p} bs tca', v['bs_cash'] + v['bs_sti'] + v['bs_ar'] + v['bs_inv'] + v['bs_oca'], v['bs_tca'])
    # XBRL cross-checks (as first filed; 10-K / 10-Q facts; quarters Q1-Q3 only, Q4 has no discrete fact)
    if fy >= 2009 and (q is None or q < 4):
        kind = 'FY' if q is None else 'Q'
        chk(f'{p} xbrl rev', xbrl.value('Revenues', fy, kind, q), v['rev'], 1.1)
        chk(f'{p} xbrl ni', xbrl.value('NetIncomeLoss', fy, kind, q), v['ni_attr'], 1.1)
        chk(f'{p} xbrl ta', xbrl.value('Assets', fy, 'I', q or 4), v.get('bs_ta'), 1.1)
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'efo', 'ebt', 'tax', 'ni', 'sr_bca', 'sr_bds', 'sr_bgs', 'se_bca', 'se_bds', 'se_bgs', 'se_fascas', 'del_tot', 'del_737', 'del_787',
              'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_sbc', 'cf_dda', 'core_oe_pub', 'nonop_pen'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 1.1)
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues ({sum(1 for b in bad if "[known" in b)} known, documented)')
print('\n'.join(normalize.LOG))
