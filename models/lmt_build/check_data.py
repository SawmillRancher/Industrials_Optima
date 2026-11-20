"""Consistency checks on the normalised Lockheed Martin data: statement arithmetic, segment sums, unallocated items, EPS, cash-flow and
balance-sheet tie-outs, pension identities and quarters vs years."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    fy, q = normalize.fyq(p)
    chk(f'{p} gp', v['rev'] - v['cos'], v['gp'])
    chk(f'{p} op', v['gp'] + n(v.get('othinc')), v['op'])
    chk(f'{p} ebt', v['op'] - v['int'] + n(v.get('nonsvc')) + n(v.get('othnonop')), v['ebt'])
    chk(f'{p} cont', v['ebt'] - v['tax'], v['cont'])
    chk(f'{p} ni', v['cont'] + n(v.get('disc')), v['ni'])
    chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101 if v['ni'] > 0 else 0.03)
    segs = sum(n(v.get(f'sr_{k}')) for k in normalize.SEGS)
    chk(f'{p} seg sales', segs, v['rev'])
    segop = sum(n(v.get(f'so_{k}')) for k in normalize.SEGS)
    chk(f'{p} seg op pub', segop, v.get('segop_pub'))
    chk(f'{p} ua items', sum(n(v.get(k)) for k in normalize.UA_KEYS), v.get('ua_tot'))
    if v.get('p_fas_exp') is not None and v.get('p_fascas') is not None and v.get('p_cas') is None: bad.append(f'{p}: CAS not derivable')
    chk(f'{p} op cons', segop + n(v.get('ua_tot')), v['op'])
    chk(f'{p} op cons pub', v.get('op_cons'), v['op'])
    if v.get('p_fas_exp') is not None and v.get('p_cas') is not None and v.get('p_fascas') is not None:
        chk(f'{p} fas/cas', v['p_cas'] + v['p_fas_exp'], v['p_fascas'])
    if v.get('p_fascas_op') is not None and v.get('p_nonsvc') is not None and v.get('p_fascas') is not None:
        chk(f'{p} fas/cas split', v['p_fascas_op'] + v['p_nonsvc'], v['p_fascas'])
    if fy >= 2018 and v.get('p_fascas_op') is not None: chk(f'{p} fascas op vs unalloc', v['p_fascas_op'], v['ua_fascas'])
    if fy >= 2021 and q and v.get('nonsvc') is not None and v.get('p_nonsvc') is not None: chk(f'{p} nonsvc', v['nonsvc'], v['p_nonsvc'])
    if v.get('cf_cfo') is not None:
        if not v.get('is_basis'): chk(f'{p} cf ni', v['cf_ni'], v['ni'])      # re-presented periods: CF stays as reported (basis-difference memo in the model)
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'])
        chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'], v.get('fcf_pub'))
    chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    chk(f'{p} bs tca', v['bs_cash'] + v['bs_ar'] + v['bs_ca'] + v['bs_inv'] + v['bs_oca'], v['bs_tca'])
    chk(f'{p} bs tl+te', v['bs_tl'] + v['bs_teq'], v['bs_tle'])
    bk = sum(n(v.get(f'bk_{k}')) for k in normalize.SEGS)
    if v.get('bk_tot') and bk and p != '2006': chk(f'{p} backlog', bk, v['bk_tot'], 1.0)     # 2006: sub-segment table
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'cos', 'gp', 'othinc', 'op', 'int', 'nonsvc', 'othnonop', 'ebt', 'tax', 'cont', 'disc', 'ni', 'dps',
              'sr_aero', 'sr_mfc', 'sr_rms', 'sr_space', 'sr_isgs', 'so_aero', 'so_mfc', 'so_rms', 'so_space', 'so_isgs', 'ua_fascas', 'ua_sev',
              'ua_amort', 'ua_sbc_other', 'ua_tot', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_dda', 'cf_sbc', 'cf_def', 'cf_pens', 'cf_chg', 'cf_ca', 'cf_cl',
              'dl_f35'):
        g = (lambda d: n(d.get('ua_sbc')) + n(d.get('ua_other')) if d else None) if k == 'ua_sbc_other' else (lambda d: d.get(k))
        qs = [g(x(f'Q{q}-{yy}')) for q in (1, 2, 3, 4)]
        a = g(x(str(y)))
        if y == 2020 and k in ('nonsvc', 'othnonop'): continue      # non-service FAS pension line not presented for Q1/Q2-20 (introduced Q3-21; only Q3/Q4-20 re-presented)
        if all(v is not None for v in qs) and a is not None: chk(f'FY{y} {k} sum-q', sum(qs), a, 0.6 if k != 'dps' else 0.011)
        elif a is not None and any(v is not None for v in qs) and k not in ('dl_f35',): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, v in enumerate(qs) if v is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
