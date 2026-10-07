"""Consistency checks on the normalised data (statement arithmetic, segment / revenue-type sums, GAAP -> adjusted bridge totals,
quarter sums vs fiscal years, cash-flow and balance-sheet tie-outs)."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad = []
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
CATS = normalize.CATS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    if v.get('sga') is not None:
        chk(f'{p} op', v['gp'] - v['sga'] - n(v.get('rd')) - n(v.get('restr')) - n(v.get('oth_opex')), v['op'])
    chk(f'{p} ebt', n(v.get('op')) - n(v.get('nonop')), v.get('ebt'))
    chk(f'{p} ni_cont', n(v.get('ebt')) - n(v.get('tax')), v.get('ni_cont'))
    chk(f'{p} ni', n(v.get('ni_cont')) + n(v.get('disc')), v.get('ni'))
    segs = sum(n(v.get(f'sr_{s}')) for s in ('hc', 'ast', 'ls', 'dental', 'oth'))
    chk(f'{p} seg rev', segs, v.get('rev'), 0.11)
    if v.get('so_corp') is not None and v.get('so_basis') != 'gaap':
        chk(f'{p} seg oi', sum(n(v.get(f'so_{s}')) for s in ('hc', 'ast', 'ls', 'dental')) + v['so_corp'], v.get('adj_op_pub'), 0.11)
    for s in ('hc', 'ls'):
        if v.get(f'ty_{s}_cap') is not None:
            chk(f'{p} type {s}', sum(n(v.get(f'ty_{s}_{t}')) for t in ('cap', 'cons', 'serv')), v.get(f'sr_{s}'), 0.11)
    if v.get('ty_ast_serv') is not None: chk(f'{p} type ast', n(v.get('ty_ast_cap')) + v['ty_ast_serv'], v.get('sr_ast'), 0.11)
    if v.get('adj_op_pub') is not None:
        chk(f'{p} op bridge', n(v.get('op')) + sum(n(v.get('oa_' + k)) for k in CATS), v['adj_op_pub'], 0.11)
    if v.get('adj_gp_pub') is not None:
        chk(f'{p} gp bridge', n(v.get('gp')) + sum(n(v.get('ga_' + k)) for k in CATS), v['adj_gp_pub'], 0.11)
    if v.get('adj_ni_pub') is not None and v.get('sh_d'):
        chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v.get('e_pub'), 0.0101)
    if v.get('ni_cont_attr') is not None and v.get('sh_d') and v.get('eps_d_cont') is not None:
        chk(f'{p} gaap eps', v['ni_cont_attr'] / v['sh_d'], v['eps_d_cont'], 0.0101)
    if v.get('cf_cfo') is not None and v.get('cf_beg') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v.get('cf_end'), 0.11)
        chk(f'{p} cash vs bs', v.get('cf_end'), v.get('bs_cash'), 0.11)
    chk(f'{p} bs', v.get('bs_ta'), v.get('bs_tle'), 0.11)
for y in range(2022, 2027):
    yy = str(y)[2:]
    for k in ('rev', 'gp', 'op', 'ebt', 'tax', 'ni_cont', 'ni', 'sga', 'adj_op_pub', 'adj_ni_pub', 'sr_hc', 'sr_ast', 'sr_ls', 'so_hc', 'so_corp',
              'cf_cfo', 'cf_capex', 'cf_dda', 'cf_bb', 'cf_div', 'int_exp', 'oa_amort', 'ty_hc_cap', 'ty_ls_cons'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 0.25)
        elif x(str(y)).get(k) is not None: bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(len(bad), 'issues')
print('\n'.join(normalize.LOG))
