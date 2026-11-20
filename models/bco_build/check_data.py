"""Data consistency checks on the normalised Brink's data (run after extract.py). Prints every failure; exit code 1 if any
unexplained failure remains. Known, explained exceptions are listed in KNOWN (and in the README)."""
import sys
import normalize
D = normalize.run()
KNOWN = {('Q2-16', 'CF: beg + cfo + cfi + cff + fx = end'): 'Q2-16 10-Q six-month cash flow opens at $181.9m; the Q1-16 10-Q closed at $186.8m from an opening $198.3m (31-Dec-2015 as first filed) - $16.4m re-presentation of the opening balance between the two filings.',
         ('Q4-18', 'EPS: cont_att / diluted shares'): 'Q4 shares derived as 4 x FY - sum(Q1-Q3) in a GAAP-loss year (FY uses basic shares).'}
for q_ in ('Q1-25', 'Q2-25', 'Q3-25'):
    for k_ in ('eu', 'row'):
        KNOWN[(q_, f'GROWTH {k_}: current vs segment revenue')] = 'The fourth-quarter 2025 release re-presented Q1-Q3/25 Europe and Rest of World segment revenues (about $20m a quarter moved to Europe); the growth tables are as first published.'
fails, n = [], 0
def chk(per, name, a, b, tol=0.15):
    global n
    if a is None or b is None: return
    n += 1
    if abs(a - b) > tol + 1e-9:
        (fails.append((per, name, round(a, 2), round(b, 2), KNOWN.get((per, name)))))
def g(x, k): return x.get(k)
def s(x, *ks): return sum(x.get(k) or 0.0 for k in ks)
for per in sorted(D, key=lambda p: (int(p[-2:]) + 2000 if p.startswith('Q') else int(p), p)):
    x = D[per]['x']
    if 'rev' in x:
        chk(per, 'IS: rev - cor - sga + ooi = op', x['rev'] - x['cor'] - x['sga'] + x.get('ooi', 0), x['op'])
        chk(per, 'IS: op - int + oth - decon = ebt', x['op'] - x['int'] + x.get('oth', 0) - x.get('ven_decon', 0), x['ebt'], 0.25)
        chk(per, 'IS: ebt - tax = cont', x['ebt'] - x['tax'], x.get('cont'), 0.25)
        chk(per, 'IS: cont - nci = cont_att', (x['cont'] - x['nci']) if 'cont' in x and 'nci' in x else None, x.get('cont_att'), 0.25)
        chk(per, 'IS: cont_att + disc_att = ni', x.get('cont_att', 0) + x.get('disc_att', 0), x.get('ni'), 0.25)
        if x.get('sh_d') and x.get('eps_cont_d') is not None and x.get('cont_att') is not None and x['cont_att'] > 0:
            chk(per, 'EPS: cont_att / diluted shares', x['cont_att'] / x['sh_d'], x['eps_cont_d'], 0.011 if not per.startswith('Q4') else 0.03)
        chk(per, 'OP: release table GAAP vs statement', x.get('op_tbl') or x.get('op_seg_tbl'), x['op'], 0.15)
        chk(per, 'INC: release table GAAP vs statement', x.get('inc_tbl'), x.get('cont_att'), 0.15)
    b = x.get('seg_basis')
    if b == 'cur4':
        chk(per, 'SEG: sum 4 segments = segment revenues', s(x, 'na_rev', 'la_rev', 'eu_rev', 'row_rev'), x.get('seg_rev'), 0.25)
        chk(per, 'SEG: sum segment op + corporate = non-GAAP op', s(x, 'na_op', 'la_op', 'eu_op', 'row_op', 'corp'), x.get('ng_op_seg'), 0.25)
    if b == 'three':
        chk(per, 'SEG3: sum = segment revenues', s(x, 'l3_na_rev', 'l3_sa_rev', 'l3_row_rev'), x.get('seg_rev'), 0.25)
        chk(per, 'SEG3: sum op + corporate = non-GAAP op', s(x, 'l3_na_op', 'l3_sa_op', 'l3_row_op', 'corp'), x.get('ng_op_seg'), 0.25)
    if b == 'mkts':
        chk(per, 'MKT: sum = non-GAAP revenue', s(x, 'm_l5_rev', 'm_gm_rev', 'm_ps_rev'), x.get('seg_rev'), 0.25)
        chk(per, 'MKT: sum op + corporate = non-GAAP op', s(x, 'm_l5_op', 'm_gm_op', 'm_ps_op', 'corp'), x.get('ng_op_seg'), 0.25)
    if 'i_intl_rev' in x:
        chk(per, 'INTL: sum = revenues', s(x, 'i_intl_rev', 'i_na_rev'), x.get('rev'), 0.15)
        chk(per, 'INTL: sum op + non-segment = op', s(x, 'i_intl_op', 'i_na_op', 'i_nonseg'), x.get('op'), 0.15)
    if 'it_restr' in x and x.get('ng_op_seg') is not None and 'op' in x:
        chk(per, 'BRIDGE OP: GAAP op + items = non-GAAP op', x['op'] + s(x, *('it_' + k for k in normalize.ITK)), x['ng_op_seg'], 0.25)
    chk(per, 'BRIDGE OP: segment table non-GAAP = reconciliation non-GAAP', x.get('ng_op_seg'), x.get('op_ng_pub'), 0.15)
    if x.get('ebitda_pub') is not None and 'ni' in x:
        chk(per, 'EBITDA: ni + int + tax + da = published EBITDA', x['ni'] + (x.get('eb_int_tbl') or x['int']) + x['tax'] + (x.get('eb_da_tbl') or x.get('cf_da', 0)), x['ebitda_pub'], 0.25)
        chk(per, 'EBITDA: da table vs cash-flow da', x.get('eb_da_tbl'), x.get('cf_da'), 0.25)
        chk(per, 'EBITDA: + disc + items + sbc + mkt = adjusted', x['ebitda_pub'] + s(x, 'eb_disc', 'eb_items', 'eb_sbc', 'eb_mkt'), x.get('adj_ebitda_pub'), 0.35)
    if x.get('eps_ng_pub') is not None and x.get('inc_ng_pub') is not None and x.get('sh_d'):
        chk(per, 'EPS: non-GAAP income / diluted shares = non-GAAP EPS', x['inc_ng_pub'] / (x.get('sh_ng') or x['sh_d']), x['eps_ng_pub'], 0.03 if per.startswith('Q4') else 0.015)
    if 'cf_cfo' in x and 'cf_cfi' in x:
        chk(per, 'CF: beg + cfo + cfi + cff + fx = end', (x['cf_beg'] + x['cf_cfo'] + x['cf_cfi'] + x['cf_cff'] + x['cf_fx']) if x.get('cf_beg') is not None else None, x.get('cf_end'), 0.25)
    if 'bs_ta' in x:
        chk(per, 'BS: ta = tle', x['bs_ta'], x.get('bs_tle'))
        chk(per, 'BS: tl + teq = tle', s(x, 'bs_tl', 'bs_teq'), x.get('bs_tle'), 0.15)
        chk(per, 'BS: eq + nci = teq', s(x, 'bs_eq', 'bs_nci'), x.get('bs_teq'), 0.15)
    if 'g_base' in x:
        chk(per, 'GROWTH: base + org + acq + fx = current', s(x, 'g_base', 'g_org', 'g_acq', 'g_fx'), x.get('g_cur'), 2.1)
        chk(per, 'GROWTH: current vs revenues', x.get('g_cur'), (x.get('seg_rev') or x.get('rev_ng_pub') or x.get('rev')) if x.get('g_ng') else x.get('rev'), 0.6)
        for k in ('na', 'la', 'eu', 'row'):
            if f'g_{k}_base' in x:
                chk(per, f'GROWTH {k}: base + org + acq + fx = current', s(x, f'g_{k}_base', f'g_{k}_org', f'g_{k}_acq', f'g_{k}_fx'), x[f'g_{k}_cur'], 2.1)
                chk(per, f'GROWTH {k}: current vs segment revenue', x[f'g_{k}_cur'], x.get(k + '_rev'), 0.6)
# quarters vs full year
for y in range(normalize.YQ, normalize.YL):
    qs = [D.get(f'Q{q}-{str(y)[2:]}', {}).get('x', {}) for q in (1, 2, 3, 4)]; fy = D[str(y)]['x']
    for k in ('na_rev', 'la_rev', 'eu_rev', 'row_rev', 'na_op', 'la_op', 'eu_op', 'row_op', 'corp', 'ng_op_seg', 'adj_ebitda_pub', 'inc_ng_pub', 'l3_na_rev', 'l3_sa_op', 'm_l5_rev', 'm_gm_op',
              'it_restr', 'it_acq', 'it_arg', 'it_ven', 'it_transf', 'it_ret', 'it_oth', 'fcf_pub', 'rev_ng_pub'):
        if k in fy and all(k in q for q in qs):
            chk(str(y), f'SUMQ: {k}', sum(q[k] for q in qs), fy[k], 0.35)
    for q, qd in zip((1, 2, 3, 4), qs):
        if not qd: fails.append((f'Q{q}-{y}', 'missing quarter', 0, 0, None))
print(f'{n} checks, {len(fails)} failures ({sum(1 for f in fails if f[4])} explained)')
for f in fails: print(' ', f)
sys.exit(1 if any(not f[4] for f in fails) else 0)
