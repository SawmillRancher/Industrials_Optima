"""Consistency checks on the normalised RBC Bearings data: statement arithmetic, segment sums, adjusted-operating-income / adjusted
EBITDA / adjusted EPS bridges vs the published figures, EPS, cash-flow and balance-sheet tie-outs, and quarters vs fiscal years.
Known exceptions are listed in EXC with the reason (also in README.md)."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok, exc = [], [0], []
EXC = {}
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol:
        msg = f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})'
        (exc if name in EXC else bad).append(msg + (f'  [known: {EXC[name]}]' if name in EXC else ''))
OC = normalize.OCATS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} gp', v['rev'] - v['cogs'], v['gp'])
    chk(f'{p} oi', v['gp'] - v['sga'] - v['oth'], v['oi'])
    chk(f'{p} ebt', v['oi'] - v['int'] - v['loe'] - v['onop'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni'])
    chk(f'{p} gaap eps', v['ni_c'] / v['sh_d'], v['eps_d'], 0.0101 if v['ni_c'] > 0 else 0.03)
    if v.get('s_aero') is not None: chk(f'{p} seg sales', v['s_aero'] + v['s_ind'], v['rev'], 0.15)
    if v.get('gm_aero') is not None: chk(f'{p} seg gm', v['gm_aero'] + v['gm_ind'], v['gp'], 0.15)
    if v.get('soi_aero') is not None: chk(f'{p} seg oi', v['soi_aero'] + v['soi_ind'] + n(v.get('soi_corp')), v['oi'], 0.15)
    leg = [v.get(f'l_{k}') for k in ('plain', 'roller', 'ball', 'other')]
    if all(l is not None for l in leg): chk(f'{p} legacy seg', sum(leg), v['rev'], 0.15)
    items = sum(n(v.get('oa_' + c)) for c in OC)
    chk(f'{p} adj oi', v['oi'] + items, v.get('adj_oi_pub'))
    if v.get('adj_gm_pub') is not None: chk(f'{p} adj gm', v['gp'] + v['ga_tot'], v['adj_gm_pub'])
    if v.get('e_pub') is not None: chk(f'{p} adj eps', v['adj_nic_pub'] / v['e_sh'], v['e_pub'], 0.0101)
    if v.get('cf_dda') is not None and v.get('adj_ebitda_pub') is not None:
        chk(f'{p} adj ebitda', v['oi'] + v['cf_dda'] + v['cf_sbc'] + items - n(v.get('oa_sbc')), v['adj_ebitda_pub'], 0.15)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        chk(f'{p} cash vs bs', v['cf_end'], v.get('bs_cash'))
        chk(f'{p} cf ni', v['cf_ni'], v['ni'])
    if v.get('bs_ta') is not None: chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
for y in range(normalize.FYQ0, normalize.FYC):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'gp', 'sga', 'oth', 'oi', 'int', 'ebt', 'tax', 'ni', 's_aero', 's_ind', 'gm_aero', 'gm_ind',
              'oa_restr', 'oa_acq', 'cf_cfo', 'cf_capex', 'cf_acq', 'cf_dda', 'cf_sbc', 'cf_cfi', 'cf_cff', 'adj_oi_pub', 'adj_ebitda_pub'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 0.25)
print('\n'.join(bad) or 'all checks pass')
if exc: print('known exceptions:\n  ' + '\n  '.join(exc))
print(f'{ok[0]} checks, {len(bad)} issues, {len(exc)} known exceptions')
