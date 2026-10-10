"""Consistency checks on the normalised data: statement arithmetic, non-IFRS bridges, quarter sums vs fiscal year, sales splits,
balance sheet, cash-flow identity and EPS on Class A-equivalent shares."""
import normalize
D = normalize.run()
bad = []
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
for p, r in D.items():
    x = r['x']; g = x.get
    if g('cogs') is not None:
        chk(f'{p} gp', g('rev') - g('cogs'), g('gp'))
        chk(f'{p} op', g('gp') - g('sga'), g('op'))
        chk(f'{p} ebt', g('op') + g('fin_inc') - g('fin_exp') + g('fx'), g('ebt'))
        chk(f'{p} ni', g('ebt') - g('tax'), g('ni'))
    if g('adj_pub') is not None:
        chk(f'{p} adj ebitda', g('op') + g('dna') + g('sbc') + g('etc', 0), g('adj_pub'), 0.11)
    if g('adj_ni_pub') is not None:
        chk(f'{p} adj ni', g('ni') + g('ani_sbc') + g('ani_etc') + g('ani_tax'), g('adj_ni_pub'), 0.11)
        chk(f'{p} ani ni vs is', g('ani_ni'), g('ni'), 0.11)
        if g('sh_dil'): chk(f'{p} adj eps', g('adj_ni_pub') / g('sh_dil'), g('adj_eps_pub'), 0.0101)
    if g('sh_basic') and g('eps_a') is not None: chk(f'{p} eps', g('ni') / g('sh_basic'), g('eps_a'), 0.0101)
    if g('ch_whs') is not None: pass
    if g('rg_emea') is not None: chk(f'{p} regions', g('rg_emea') + g('rg_am') + g('rg_apac'), g('rev'), 0.25)
    if g('pr_shoes') is not None: chk(f'{p} products', g('pr_shoes') + g('pr_apparel') + g('pr_acc'), g('rev'), 0.25)
    if g('bs_ta') is not None:
        chk(f'{p} bs', g('bs_ta'), g('bs_tle'))
        chk(f'{p} bs assets', g('bs_cash') + g('bs_ar') + g('bs_inv') + g('bs_oca') + g('bs_ppe') + g('bs_rou') + g('bs_int') + g('bs_dta'), g('bs_ta'), 0.25)
        chk(f'{p} bs liab', g('bs_ap') + g('bs_cfl') + g('bs_ocl') + g('bs_ncfl') + g('bs_oncl') + g('bs_cap') + g('bs_ores') + g('bs_re'), g('bs_tle'), 0.35)
    if g('cf_cfo') is not None and g('cf_end') is not None and g('cf_beg') is not None:
        chk(f'{p} cf', g('cf_beg') + g('cf_net') + g('cf_fx'), g('cf_end'), 0.25)
    if g('cf_end') is not None and g('bs_cash') is not None: chk(f'{p} cash bs vs cf', g('cf_end'), g('bs_cash') - g('overdraft', 0), 0.15)
for y in range(2021, 2026):
    yy = str(y)[2:]
    for k in ('rev', 'gp', 'op', 'ni', 'adj_pub', 'dna', 'sbc', 'ch_whs', 'rg_am', 'rg_emea', 'rg_apac', 'pr_shoes', 'pr_apparel', 'cf_cfo', 'cf_capex', 'cf_lease'):
        qs = [D.get(f'Q{q}-{yy}', {}).get('x', {}).get(k) for q in (1, 2, 3, 4)]
        fy = D.get(str(y), {}).get('x', {}).get(k)
        if fy is None: continue
        if all(v is not None for v in qs): chk(f'{y} {k} sum-q', sum(qs), fy, 0.25)
        else: bad.append(f'{y} {k}: quarters missing {[i + 1 for i, v in enumerate(qs) if v is None]}')
print('\n'.join(bad) or 'all checks pass')
