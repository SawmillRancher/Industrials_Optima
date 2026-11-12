"""Consistency checks on the normalised RTX data: statement arithmetic, segment sums, customer-type disaggregation, adjusted operating
profit bridge vs published, EPS and adjusted EPS, cash-flow and balance-sheet tie-outs, and quarters vs years (same basis only)."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok, notes = [], [0], []
def chk(name, a, b, tol=1.01):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:,.3f} vs {b:,.3f} ({a - b:+,.3f})')
SEGS = ['col', 'pw', 'rtn', 'otis', 'car', 'fs', 'sik']
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    if v.get('cogs') is not None:
        chk(f'{p} op', v['rev'] - v['cogs'] - n(v.get('rnd')) - n(v.get('sga')) + n(v.get('oth_inc')), v.get('op'))
    chk(f'{p} ebt', n(v.get('op')) + n(v.get('nsp')) - n(v.get('int_net')) + n(v.get('oth_nonop')), v.get('ebt'))
    chk(f'{p} cont', n(v.get('ebt')) - n(v.get('tax')), v.get('cont'))
    chk(f'{p} ni_tot', n(v.get('cont')) + n(v.get('disc')), v.get('ni_tot'))
    chk(f'{p} ni', n(v.get('ni_tot')) - n(v.get('nci')), v.get('ni'))
    if v.get('sh_d') and v.get('eps_d') is not None and n(v.get('ni')) > 0: chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0151)
    if v.get('s_col_rev') is not None:
        chk(f'{p} seg sales', sum(n(v.get(f's_{s}_rev')) for s in SEGS) + n(v.get('s_elim_rev')), v['rev'])
        chk(f'{p} seg op', sum(n(v.get(f's_{s}_op')) for s in SEGS) + n(v.get('s_elim_op')) + n(v.get('s_corp_op')) + n(v.get('s_fascas')) + n(v.get('s_acqadj')), v.get('op'))
    for s in ('col', 'pw', 'rtn'):
        if v.get(f'c_{s}_comm') is not None and v.get(f's_{s}_rev') is not None:
            ext = (n(v.get(f'c_{s}_def')) + n(v.get(f'c_{s}_comm'))) if s != 'rtn' else (n(v.get('c_rtn_usg')) + n(v.get('c_rtn_intl')) + n(v.get('c_rtn_comm')))
            chk(f'{p} cust {s}', ext + n(v.get(f'c_{s}_inter')), v[f's_{s}_rev'])
    if v.get('adj_op_pub') is not None:
        chk(f'{p} adj op bridge', n(v.get('op')) + n(v.get('a_restr')) + n(v.get('a_acq')) - n(v.get('a_sig')), v['adj_op_pub'])
    if v.get('adj_ni_pub') is not None and v.get('adj_eps_pub') is not None and v.get('sh_d'):
        chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['adj_eps_pub'], 0.0151)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash roll', n(v.get('cf_beg')) + n(v.get('cf_net')), v.get('cf_end'))
        chk(f'{p} cash sum', n(v['cf_cfo']) + n(v.get('cf_cfi')) + n(v.get('cf_cff')) + n(v.get('cf_fx')) + n(v.get('cf_disc')), v.get('cf_net'))
        if v.get('fcf_pub') is not None: chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'], v['fcf_pub'])
        if v.get('bs_cash') is not None and v.get('cf_restr') is not None: chk(f'{p} cash vs bs', v['cf_end'] - v['cf_restr'], v['bs_cash'])
    if v.get('bs_ta') is not None: chk(f'{p} bs', v['bs_ta'], v.get('bs_tle'))
# quarters vs years where both are on the same basis
for y in range(2013, 2026):
    yy = str(y)[2:]
    if any(D.get(f'Q{q}-{yy}', {}).get('basis', ('?',))[0] != D.get(str(y), {}).get('basis', ('!',))[0] for q in (1, 2, 3, 4)):
        notes.append(f'FY{y}: quarters and year on different bases — sum-of-quarters checks skipped'); continue
    CF_EXEMPT = {2015: 'Q1-Q2 cash flows include Sikorsky (as originally reported); the FY statement is continuing operations',
                 2016: 'FY statement re-presents restricted cash (ASU 2016-18) and H1 cash flows (ASU 2016-15); Q3 / Q4 taken from the release quarter columns',
                 2020: 'Q1 includes Otis and Carrier (standalone UTC); FY statement is continuing operations'}
    if y in CF_EXEMPT: notes.append(f'FY{y} cash-flow quarters vs year not compared: {CF_EXEMPT[y]}')
    for k in ('rev', 'op', 'ni', 'ebt', 'tax', 's_col_rev', 's_pw_rev', 's_rtn_rev', 's_col_op', 's_pw_op', 's_rtn_op', 'adj_op_pub', 'a_restr', 'a_acq', 'cf_cfo', 'cf_capex', 'cf_div', 'cf_bb'):
        if y in CF_EXEMPT and k.startswith('cf_'): continue
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 2.5)
print('\n'.join(bad) or 'all checks pass')
print('\n'.join(notes))
print(f'{ok[0]} checks, {len(bad)} issues')

# ---------------------------------------------------------------- XBRL cross-check (periods kept as originally reported; facts as first filed)
import xbrl
xb, xn = [], [0]
CON = {'rev': ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'], 'op': ['OperatingIncomeLoss'], 'ni': ['NetIncomeLoss'],
       'eps_d': ['EarningsPerShareDiluted'], 'bs_ta': ['Assets']}
for p in normalize.periods():
    if D.get(p, {}).get('basis', ('orig',))[0] != 'orig' or not x(p): continue
    fy, q = (int(p), 4) if p.isdigit() else (int('20' + p[-2:]), int(p[1]))
    if fy < 2009: continue
    for k, cs in CON.items():
        kind = 'I' if k == 'bs_ta' else ('FY' if p.isdigit() else 'Q')
        v = xbrl.first_of(cs, fy, kind, q)
        if v is None or x(p).get(k) is None: continue
        xn[0] += 1
        tol = 0.0151 if k == 'eps_d' else 1.5
        if abs(v - x(p)[k]) > tol: xb.append(f'{p} {k}: model data {x(p)[k]:,.2f} vs XBRL {v:,.2f}')
print('\n'.join(xb) or 'XBRL cross-check: all match')
print(f'{xn[0]} XBRL comparisons, {len(xb)} differences')
