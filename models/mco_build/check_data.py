"""Consistency checks on the normalised Moody's data: statement arithmetic, revenue-line and segment sums, Adjusted Operating
Income / adjusted EPS bridges vs the published figures, EPS, cash-flow and balance-sheet tie-outs, XBRL cross-checks and
quarters vs years. Tolerances: ±0.6 for one-decimal releases (to Q3-19), ±1.5 for whole-million releases (from Q4-19)."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def tol(p):
    fy, q = normalize.fyq(p)
    return 1.5 if (fy, q) >= (2019, 4) else 0.6
def chk(name, a, b, t=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > t: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
CUR_MA = ('bank', 'ins', 'kyc', 'ri', 'di')
for p in normalize.periods():
    v = x(p); t = tol(p)
    if not v or 'rev' not in v: bad.append(f'{p}: no data'); continue
    exp = n(v.get('opr')) + n(v.get('sga')) + n(v.get('dna')) + n(v.get('restr')) + n(v.get('othop'))
    chk(f'{p} oi', v['rev'] - exp, v.get('oi'), t)
    chk(f'{p} ebt', n(v.get('oi')) + n(v.get('int_net')) + n(v.get('onop')) + n(v.get('gain')), v.get('ebt'), t)
    chk(f'{p} ni', v['ebt'] - v['tax'] - n(v.get('nci')), v['ni'], t)
    if v.get('mis_ext') is not None and v.get('ma_ext') is not None: chk(f'{p} seg rev', v['mis_ext'] + v['ma_ext'], v['rev'], t)
    ml = [v.get(f'r_{k}') for k in ('cfg', 'sfg', 'fig', 'ppif')]
    if all(m is not None for m in ml): chk(f'{p} mis lines', sum(ml) + n(v.get('r_moth')), v.get('mis_ext'), t)
    if all(v.get(f'r_{k}') is not None for k in CUR_MA): chk(f'{p} ma lines', sum(v[f'r_{k}'] for k in CUR_MA), v.get('ma_ext'), t)
    if v.get('mis_aoi') is not None and v.get('adj_oi_pub') is not None: chk(f'{p} seg aoi', v['mis_aoi'] + v['ma_aoi'], v['adj_oi_pub'], 1.5)
    if v.get('adj_oi_pub') is not None:
        chk(f'{p} adj oi bridge', v['oi'] + v['dna'] + n(v.get('oa_restr')) + n(v.get('oa_other')), v['adj_oi_pub'], t)
    if v.get('sh_d'): chk(f'{p} gaap eps', v['ni'] / v['sh_d'], v.get('eps_d'), 0.0101)
    if v.get('adj_ni_pub') is not None and v.get('sh_d'): chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v.get('e_pub'), 0.0201)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'], t)
        chk(f'{p} cash vs bs', v['cf_end'], n(v.get('bs_cash')) + n(v.get('bs_rcash')), t)
        chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'], v.get('fcf_pub'), t)
    if v.get('bs_ta') is not None: chk(f'{p} bs', v['bs_ta'], v['bs_tle'], t)
    # XBRL cross-checks (as first filed)
    fy, q = normalize.fyq(p)
    if fy >= 2009 and p.isdigit():
        chk(f'{p} xbrl rev', v['rev'], xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'], fy, 'FY'), t)
        chk(f'{p} xbrl ni', v['ni'], xbrl.value('NetIncomeLoss', fy, 'FY'), t)
    elif fy >= 2010 and q < 4:
        chk(f'{p} xbrl rev', v['rev'], xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'], fy, 'Q', q), t)
        chk(f'{p} xbrl oi', v.get('oi'), xbrl.value('OperatingIncomeLoss', fy, 'Q', q), t)
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'opr', 'sga', 'dna', 'restr', 'oi', 'ebt', 'tax', 'ni', 'mis_ext', 'ma_ext', 'r_cfg', 'r_sfg', 'r_fig', 'r_ppif', 'mis_aoi', 'ma_aoi',
              'amort', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_sbc', 'adj_oi_pub', 'fcf_pub'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 2.5 if y >= 2019 else 0.35)
        elif x(str(y)).get(k) is not None and k not in ('mis_aoi', 'ma_aoi', 'adj_oi_pub', 'fcf_pub'):
            bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
