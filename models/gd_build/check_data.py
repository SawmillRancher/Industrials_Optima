"""Consistency checks on the normalised General Dynamics data: statement arithmetic, segment sums, backlog sums, free cash flow vs
published, EPS, the FY2012 / FY2017 adjusted bridges, cash and balance-sheet tie-outs, XBRL cross-checks and quarters vs years."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
SEGS = normalize.SEGS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} oi', v['rev'] - v['costs'], v['oi'])
    chk(f'{p} ebt', v['oi'] + v['int'] + v['oth'], v['ebt'])
    chk(f'{p} cont', v['ebt'] - v['tax'], v['cont'])
    chk(f'{p} ni', v['cont'] + v['disc'], v['ni'])
    chk(f'{p} seg rev', sum(v[f'sr_{s}'] for s in SEGS), v['rev'])
    chk(f'{p} seg oi', sum(v[f'so_{s}'] for s in SEGS) + v['so_corp'], v['oi'])
    chk(f'{p} seg tot', v['sr_tot'], v['rev']); chk(f'{p} seg oi tot', v['so_tot'], v['oi'])
    if v.get('bl_tot_total') is not None:
        chk(f'{p} backlog', sum(n(v.get(f'bl_{s}_total')) for s in SEGS), v['bl_tot_total'], 1.1)
        chk(f'{p} backlog f+u', sum(n(v.get(f'bl_{s}_funded')) + n(v.get(f'bl_{s}_unfunded')) for s in SEGS), v['bl_tot_total'], 1.1)
    chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101 if v['ni'] > 0 else 0.03)
    if v.get('adj_ni_pub') is not None:
        items = sum(v[f'oa_{c}'] for c in ('impair', 'disputes', 'restr', 'inv', 'debt', 'taxd'))
        chk(f'{p} adj ni', v['cont'] + items + v['oa_tax'], v['adj_ni_pub'])
        chk(f'{p} adj eps', v['adj_ni_pub'] / v['adj_sh'], v['adj_eps_pub'], 0.0101)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'])
        chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'], v.get('fcf_pub'))
        chk(f'{p} cfo lines', v['cf_ni'] + v['cf_dda'] + v['cf_sbc'] + v['cf_def'] + v['cf_wc'] + v['cf_oth'], v['cf_cfo'])
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    chk(f'{p} bs tl+te', v['bs_tl'] + v['bs_te'], v['bs_tle'])
    # XBRL (as first filed) cross-checks, 2008+ (XBRL facts start with the FY2008 10-K comparatives)
    for k, kk in (('rev', 'rev_xbrl'), ('oi', 'oi_xbrl'), ('ni', 'ni_xbrl'), ('bs_ta', 'ta_xbrl')):
        if v.get(kk) is not None and (int(p[-2:]) >= 9 if not p.isdigit() else int(p) >= 2008): chk(f'{p} xbrl {k}', v[k], v[kk], 1.1)
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'costs', 'oi', 'int', 'oth', 'ebt', 'tax', 'ni', 'disc', 'sr_aero', 'sr_marine', 'sr_combat', 'sr_tech', 'so_aero', 'so_marine', 'so_combat', 'so_tech', 'so_corp',
              'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_dda', 'cf_sbc', 'cf_def', 'cf_wc', 'dl_outfitted', 'dl_green', 'dps'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs) and x(str(y)).get(k) is not None: chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 1.1 if not k.startswith('dps') else 0.011)
        elif x(str(y)).get(k) is not None and k not in ('dl_outfitted', 'dl_green'): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
