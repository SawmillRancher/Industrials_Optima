"""Consistency checks on the normalised Federal Signal data: statement arithmetic, segment sums, adjusted EBITDA / adjusted EPS bridges
vs the published figures, EPS, quarters vs years, cash-flow and balance-sheet tie-outs, and XBRL cross-checks (as first filed)."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok, exc = [], [0], []
# documented exceptions (explained in README / cell comments)
EXC = {
    'FY2015 sum-q rev': 'none expected',
}
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
SEG = normalize.SEGS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    # IS arithmetic
    chk(f'{p} gp-opex=oi', v['gp'] - v['sga'] - v['amort'] - v['acq'] - v['restr'] - v['opx_oth'], v['oi'])
    chk(f'{p} oi-int-nonop=ebt', v['oi'] - v['int'] - v['nonop'], v['ebt'])
    chk(f'{p} ebt-tax=cont', v['ebt'] - v['tax'], v['cont'])
    chk(f'{p} cont+disc=ni', v['cont'] + v['disc'], v['ni'])
    if v.get('sh_d') and v.get('eps_d') is not None:
        chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0151)
    if abs(n(v.get('opx_oth'))) > 0.15 and not v.get('opx_lab') and p[0] != 'Q':
        exc.append(f'{p}: other operating items {v["opx_oth"]:.1f} without a label')
    # segments
    if v.get('sales_esg') is not None:
        chk(f'{p} seg sales', sum(n(v.get(f'sales_{s}')) for s in SEG), v['rev'], 0.15)
        if v.get('corp_pub') is not None: chk(f'{p} corp vs published', v['corp'], v['corp_pub'], 0.15)
    # non-GAAP
    if v.get('ebitda_pub') is not None and v.get('cf_dda') is not None:
        items = sum(n(v.get(f'ea_{c}')) for c in ('acq', 'restr', 'stepup', 'other'))
        chk(f'{p} adj ebitda bridge', v['oi'] + v['cf_dda'] + items, v['ebitda_pub'], 0.15)
    if v.get('adj_ni_pub') is not None and v.get('e_pub') is not None and v.get('sh_d'):
        chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['e_pub'], 0.0151)
    # cash flow
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash roll', n(v.get('cf_beg')) + v['cf_net'] + n(v.get('cf_cashadj')), v.get('cf_end'))
        chk(f'{p} cash vs bs', v.get('cf_end'), n(v.get('bs_cash')) + n(v.get('cf_cash_disc')), 0.15)
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
    # XBRL as first filed
    if p not in ('2009', '2011'):      # FY2009 / FY2011 revenue facts were first tagged in the following 10-K's restated comparatives (documented)
        chk(f'{p} xbrl rev', v.get('rev') if not v.get('recast') else v.get('rev_orig'), v.get('xb_rev'), 0.15)
    chk(f'{p} xbrl ni', v.get('ni'), v.get('xb_ni'), 0.15)
    chk(f'{p} xbrl ta', v.get('bs_ta'), v.get('xb_ta'), 0.15)
for y in range(2013, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'sga', 'amort', 'acq', 'restr', 'oi', 'int', 'ebt', 'tax', 'cont', 'ni', 'sales_esg', 'sales_ssg', 'oi_esg', 'oi_ssg', 'corp',
              'cf_cfo', 'cf_capex', 'cf_div', 'cf_bb', 'cf_dda', 'cf_sbc', 'ebitda_pub', 'adj_ni_pub'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 0.35)
        elif x(str(y)).get(k) is not None and k not in ('ebitda_pub',): bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print('\n'.join(exc))
print(f'{ok[0]} checks, {len(bad)} issues')
print('\n'.join(normalize.LOG))
