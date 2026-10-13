"""Consistency checks on the normalised GE Aerospace data: statement arithmetic, segment sums, the operating-profit / adjusted-earnings /
free-cash-flow bridges vs the published figures, EPS, cash-flow and balance-sheet tie-outs, and quarters vs fiscal years."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=1.01):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
AE = ['ins', 'te', 'nonop', 'gbiz', 'geq', 'restr', 'sep', 'gw', 'ru']
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} revenue', v['rev_eq'] + v['rev_sv'] + v['rev_ins'], v['rev'])
    tc = v['cogs'] + v['sga'] + v['sep'] + v['gw_imp'] + v['debt_ext'] + v['rd'] + v['int'] + v['ins_cost'] + v['nonop']
    chk(f'{p} costs', tc, v['tcost'], 2.01)
    chk(f'{p} ebt', v['rev'] - v['tcost'] + v['oth'], v['ebt'])
    chk(f'{p} ni cont', v['ebt'] - v['tax'], v['ni_cont'])
    chk(f'{p} ni', v['ni_cont'] + v['disc'], v['ni'])
    chk(f'{p} seg revenue', v['ces'] + v['dpt'] + v['c_rev'], v['rev'])
    chk(f'{p} ces eq+sv', v['ces_eq'] + v['ces_sv'], v['ces'])
    chk(f'{p} dpt ds+pat', v['ds'] + v['pat'], v['dpt'])
    chk(f'{p} dpt eq+sv', v['dpt_eq'] + v['dpt_sv'], v['dpt'])
    chk(f'{p} corp rev', v['c_ins_rev'] + v['c_elim'], v['c_rev'])
    if v.get('c_op_gaap') is not None:
        chk(f'{p} seg -> ebt', v['ces_op'] + v['dpt_op'] + v['c_op_gaap'] - v['int'] - v['nonop'] - v['debt_ext'], v['ebt'] - v['nci_cont'], 2.01)
        chk(f'{p} corp adj', v['c_op_gaap'] - v['c_g_biz'] - v['c_g_eq'] - v['c_restr'] - v['c_sep'] - v['c_ins_op'] - v['c_te_op'] - v['c_imp'] - v['c_ru'], v['c_adj'], 2.01)
        chk(f'{p} corp costs+elim', n(v.get('c_costs')) + n(v.get('c_elim_op')), v['c_adj'], 2.01)
    if v.get('op_pub') is not None:
        op = (v['ebt'] - (v['ng_ins_rev'] - v['ng_ins_cost']) - (v['ng_te_oi'] - v['ng_te_cost']) + v['ng_int'] + v['ng_nonop'] + v['ng_restr'] + v['ng_sep']
              + v['ng_gw'] - v['ng_g_eq'] - v['ng_g_biz'] - v['ng_nci_add'])
        chk(f'{p} op bridge', op, v['op_pub'], 3.01)
        chk(f'{p} op = seg', v['ces_op'] + v['dpt_op'] + v['c_adj'], v['op_pub'], 2.01)
        chk(f'{p} adj rev', v['adj_rev'], v['adj_rev_pub'])
        chk(f'{p} int', v['int'], v['ng_int']); chk(f'{p} nonop', v['nonop'], v['ng_nonop'])
        adj = v['ae_start'] - sum(v[f'ae_{k}_pre'] + v[f'ae_{k}_tax'] for k in AE) - v['ae_pref']
        chk(f'{p} adj ni bridge', adj, v['adj_ni_pub'], 4.01)
        chk(f'{p} adj start vs model', v['ae_start'], v['ni_cc'], 8.01)
        chk(f'{p} adj eps', v['adj_ni_pub'] / v['sh_d'], v['adj_eps_pub'], 0.0101)
        if v.get('fcf_fcf') is not None:
            f = v['fcf_cfoa'] - v['fcf_ins_cfoa'] + v['fcf_capex'] + v['fcf_ppe_disp'] - v['fcf_sep'] - v['fcf_restr'] - v['fcf_tax_sale']
            chk(f'{p} fcf bridge', f, v['fcf_fcf'], 2.01)
            chk(f'{p} cfoa vs cf', v['fcf_cfoa'], v.get('cf_cfo'))
            chk(f'{p} capex vs cf', v['fcf_capex'], v.get('cf_capex'))
    if v.get('eps_cont_d') is not None and v.get('sh_d'):
        chk(f'{p} gaap eps', v['ni_cc'] / v['sh_d'], v['eps_cont_d'], 0.0101 if not v.get('sh_q4_derived') else 0.03)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'], 2.01)
        chk(f'{p} cash cont', v['cf_end'] - v['cf_disc_cash'], v['cf_end_cont'])
        chk(f'{p} cf ni', v['cf_ni'], v['ni'])
        chk(f'{p} cf dep+amort>0', 1 if v['cf_dep'] > 0 else 0, 1)
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
        chk(f'{p} bs tl+te', v['bs_tl'] + v['bs_teq'], v['bs_tle'])
        chk(f'{p} bs teq', v['bs_eq'] + v['bs_nci'], v['bs_teq'])
# FY2025 FCF: definition changed in the Q3-25 release (adds dispositions of PP&E; prior periods re-presented there); Q1-Q2-25 keep the
# definition in force when first published, so the quarters do not sum to the re-presented year (7,668 vs 7,694)
EXEMPT = {(2025, 'fcf_fcf')}
for y in (2023, 2024, 2025):
    yy = str(y)[2:]
    for k in ('rev', 'adj_rev', 'cogs', 'sga', 'rd', 'int', 'ebt', 'tax', 'ni_cont', 'ni_cc', 'ces', 'ces_op', 'ces_eq', 'dpt', 'dpt_op', 'ds', 'c_adj',
              'op_pub', 'adj_ni_pub', 'ng_restr', 'ng_sep', 'fcf_fcf', 'ord_ces', 'ord_dpt', 'u_ce', 'u_leap', 'u_def',
              'cf_cfo', 'cf_capex', 'cf_cfi', 'cf_cff', 'cf_bb', 'cf_div'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if (y, k) in EXEMPT: continue
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 4.01 if k == 'adj_ni_pub' else 3.01)
        elif x(str(y)).get(k) is not None and not (y == 2023 and k.startswith('cf_')):
            bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
    if y == 2023:
        for k in ('cf_cfo', 'cf_capex', 'cf_bb'):
            h1 = normalize.CFY['H1-23']
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
print('\n'.join(normalize.LOG))
