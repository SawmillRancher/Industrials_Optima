"""Consistency checks on the normalised Talen data: statement arithmetic, the net income -> Adjusted EBITDA -> Adjusted FCF
bridges vs the published figures, EPS, cash-flow and balance-sheet tie-outs, segments, and quarters vs fiscal years."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
bad, ok = [], [0]
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
C = normalize.CATS
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    chk(f'{p} revenues', v['en_rev'] + v['cap_rev'] + v['unr_rev'], v['rev'])
    chk(f'{p} energy expenses', v['fuel'] + v['nfa'] - v['unr_exp'], v['en_exp'])
    chk(f'{p} oi', v['rev'] - v['en_exp'] - v['om'] - v['ga'] - v['dda'] - v['impair_restr'] + v['oth_op'], v['oi'])
    chk(f'{p} ebt', v['oi'] + v['ndt'] - v['int'] + v['reorg_consol'] + v['gain_sale'] + v['oth_nonop'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'], v['ni_tot'])
    chk(f'{p} ni attributable', v['ni_tot'] - v['nci'], v['ni'])
    if v.get('eps_d') is not None and not p.isdigit(): chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0151)
    chk(f'{p} bridge ni', v['ng_ni'], v['ni_tot'])
    chk(f'{p} bridge tax', v['ng_tax'], v['tax'])
    chk(f'{p} bridge nfa', v['ng_nfa'], v['nfa'])
    chk(f'{p} adj ebitda', v['ng_ni'] + v['ng_int'] + v['ng_tax'] + v['ng_dda'] + v['ng_nfa'] + v['ng_items'], v['adj_ebitda_pub'], 1.6 if p in ('2023', 'Q4-23', 'Q2-23') else 0.6)
    if v.get('adj_fcf_pub') is not None:
        chk(f'{p} adj fcf', v['adj_ebitda_pub'] + v['f_capex'] + v['f_int'] + v['f_tax'] + v['f_pension'], v['adj_fcf_pub'], 1.6)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'])
        chk(f'{p} cf sum', v['cf_cfo'] + v['cf_cfi'] + v['cf_cff'], v['cf_net'])
        chk(f'{p} cf ni', v['cf_ni'], v['ni_tot'])
        if v.get('bs_cash') is not None: chk(f'{p} cash vs bs', v['cf_end'], v['bs_cash'])
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
        chk(f'{p} assets', v['bs_cash'] + v['bs_ar'] + v['bs_inv'] + v['bs_der_a'] + v['bs_oca'] + v['bs_ppe'] + v['bs_ndt'] + v['bs_onca'], v['bs_ta'])
        chk(f'{p} liabilities', v['bs_ap'] + v['bs_accint'] + v['bs_der_l'] + v['bs_ocl'] + v['debt_st'] + v['bs_ltd'] + v['bs_pension'] + v['bs_aro'] + v['bs_dtl'] + v['bs_acl'] + v['bs_oncl'], v['bs_tl'])
        chk(f'{p} equity', v['bs_tl'] + v['bs_teq'], v['bs_tle'])
for y in range(2023, 2026):
    yy = str(y)[2:]
    # ng_items (category totals) is exempt: the S-1 (Q1-24) and the Q4-25 three-month column group interest / D&A / items slightly
    # differently from the year-to-date tables, so categories move by a few $m between quarters and the year; Adjusted EBITDA itself ties.
    for k in ('rev', 'oi', 'ni', 'adj_ebitda_pub', 'adj_fcf_pub', 'cf_cfo', 'cf_capex', 'seg_pjm', 'gen_twh', 'f_capex'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q', sum(qs), x(str(y)).get(k), 1.6 if k in ('adj_fcf_pub', 'adj_ebitda_pub', 'f_capex', 'seg_pjm') else 0.15)
        elif x(str(y)).get(k) is not None and not (y == 2023 and k in ('seg_pjm', 'gen_twh')):       # 2023 quarters: segment / generation data not published
            bad.append(f'FY{y} {k}: quarters missing {[i + 1 for i, q in enumerate(qs) if q is None]}')
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks, {len(bad)} issues')
