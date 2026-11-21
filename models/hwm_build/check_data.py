"""Consistency checks on the normalised Howmet data: statement arithmetic, segment sums, adjusted-measure bridges vs the published
figures, EPS, end-market sums, cash-flow and balance-sheet tie-outs, quarters vs years, and a cross-check of the release figures
against the XBRL company facts (10-K / 10-Q). Releases are in whole USD millions, so sums tolerate rounding (stated per check)."""
import normalize, xbrl
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=0.6):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
SEG = normalize.SEGK
for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    q = not p.isdigit()
    chk(f'{p} oi', v['rev'] - v['cogs'] - v['sga'] - v['rd'] - v['da'] - v['restr'], v['oi'], 1.6)
    chk(f'{p} ebt', v['oi'] - v['int'] - v['loss_debt'] - v['oth'], v['ebt'], 1.6)
    chk(f'{p} cont', v['ebt'] - v['tax'], v['cont'], 1.1)
    chk(f'{p} ni', v['cont'] + v['disc'], v['ni'], 1.1)
    chk(f'{p} eps', (v['ni'] - (0.5 if q else 2.0) * (p < 'Q4-25' if q else int(p) < 2026)) / v['sh_d'], v['eps_d'], 0.0201 if p == '2019' else 0.0101)   # 2019: per-share amounts computed independently for continuing / discontinued operations
    chk(f'{p} seg sales', sum(v[f'{g}_rev'] for g in SEG), v['rev'], 8.0 if p == '2019' else 2.1)
    chk(f'{p} seg ebitda total', v['seg_ebitda_tot'], v.get('seg_ebitda_tot_pub'), 2.1)
    chk(f'{p} adj oi + d&a - items in d&a = adj ebitda', (v['adj_oi_pub'] + v['da'] - v['sp_in_da']) if v.get('adj_oi_pub') is not None else None, v.get('adj_ebitda_pub'), 0.01)
    if abs(v['sp_in_da']) > 1.01: bad.append(f'{p}: special items in D&A {v["sp_in_da"]} (documented: Q2-20 only)') if p != 'Q2-20' else None
    chk(f'{p} adj ni bridge', v['cont'] + v['sp_restr'] + v['sp_oth_op'] + v['sp_nonop'] + v['sp_tax'], v['adj_ni_pub'], 0.01)
    if v.get('adj_eps_pub') is not None: chk(f'{p} adj eps', v['adj_ni_pub'] / (v.get('adj_sh') or v['sh_d']), v['adj_eps_pub'], 0.0201 if p == '2019' else 0.0101)
    if v.get('em_tot') is not None:
        chk(f'{p} end markets', n(v.get('em_ca')) + n(v.get('em_df')) + v['em_ct'] + v['em_io'], v['em_tot'], 20.0 if p in ('2019', '2020', 'Q3-20', 'Q1-20') else 2.1)
        chk(f'{p} end-market total vs sales', v['em_tot'], v['rev'], 8.0 if p in ('2019', '2020', 'Q1-20') else 0.6)
    if v.get('cf_cfo') is not None:
        chk(f'{p} cash', v['cf_beg'] + v['cf_net'], v['cf_end'], 1.6)
        if v.get('fcf_pub') is not None and p >= 'Q' or (p.isdigit() and v.get('fcf_pub') is not None):
            chk(f'{p} fcf', v['cf_cfo'] + v['cf_capex'] + v['cf_soldrec'] + n(v.get('fcf_oth')), v['fcf_pub'], 0.01)
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'], 0.01)
        chk(f'{p} bs liabilities + equity', v['bs_tl'] + v['bs_teq'], v['bs_tle'], 0.01)
        chk(f'{p} restricted cash', v['bs_restricted'], 1.0, 3.1)
for y in range(2020, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'cogs', 'sga', 'rd', 'da', 'restr', 'oi', 'int', 'tax', 'cont', 'ni', 'ep_rev', 'fs_rev', 'es_rev', 'fw_rev', 'ep_ebitda', 'fs_ebitda', 'es_ebitda',
              'fw_ebitda', 'adj_ni_pub', 'adj_ebitda_pub', 'cf_cfo', 'cf_capex', 'cf_bb', 'cf_div', 'cf_cfi', 'cf_cff', 'em_ca', 'em_df', 'em_ct', 'em_io'):
        qs = [x(f'Q{q}-{yy}').get(k) for q in (1, 2, 3, 4)]
        fy = x(str(y)).get(k)
        if all(q is not None for q in qs) and fy is not None: chk(f'FY{y} {k} sum-q', sum(qs), fy, 4.1 if (y == 2020 and k.startswith(('cf_', 'em_'))) else 2.1)
# ---- XBRL cross-check (as first filed; periods on the post-separation basis)
XB = [('rev', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'D'), ('oi', 'OperatingIncomeLoss', 'D'), ('ni', 'NetIncomeLoss', 'D'),
      ('eps_d', 'EarningsPerShareDiluted', 'D'), ('bs_ta', 'Assets', 'I'), ('bs_cash', 'CashAndCashEquivalentsAtCarryingValue', 'I')]
nx = 0
for p in normalize.periods():
    v = x(p)
    if p in ('2019', 'Q1-20'): continue
    y = int(p) if p.isdigit() else int('20' + p[-2:]); q = None if p.isdigit() else int(p[1])
    for k, tag, kind in XB:
        if q == 4 and kind == 'D': continue           # Q4 is not tagged in the 10-K
        xv = xbrl.value(tag, y, 'I' if kind == 'I' else ('FY' if q is None else 'Q'), q or 4, pick='first')
        if xv is None or v.get(k) is None: continue
        nx += 1; chk(f'{p} XBRL {tag}', v[k], xv, 0.011 if k == 'eps_d' else 0.6)
    if q is None or q < 4:
        xv = xbrl.value('NetCashProvidedByUsedInOperatingActivities', y, 'YTD', q or 4, pick='first')
        ytd = sum(n(x(f'Q{i}-{str(y)[2:]}').get('cf_cfo')) for i in range(1, (q or 4) + 1)) if q else v.get('cf_cfo')
        if xv is not None and not (y == 2020 and q == 2): nx += 1; chk(f'{p} XBRL CFO ytd', ytd, xv, 0.6)
print('\n'.join(bad) or 'all checks pass')
print(f'{ok[0]} checks ({nx} vs XBRL), {len(bad)} issues')
