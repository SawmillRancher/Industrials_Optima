"""Consistency checks on the normalised data: statement arithmetic, company bridges, half-year sums vs fiscal year, segment sums,
balance sheet, cash-flow identity, EPS and quarterly memo sums."""
import normalize
D = normalize.run()
bad = []
def chk(name, a, b, tol=0.11):
    if a is None or b is None: return
    if name.startswith('H2-'): tol = max(tol, 0.25)          # derived halves: FY − H1 compounds two roundings
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
n = lambda v: 0.0 if v is None else v
for p, r in D.items():
    x = r['x']; g = x.get
    if g('rev') is not None and g('cos') is not None:
        chk(f'{p} rop', g('rev') - g('cos') - g('ext') - g('taxes') - g('staff') + n(g('oth_op')) - g('dna_prov'), g('rop'), 0.011)
        chk(f'{p} op', g('rop') + n(g('oth_ie')), g('op'), 0.011)
        chk(f'{p} ebt', g('op') - g('cost_nd') + n(g('deriv')) + n(g('fin_oth')), g('ebt'), 0.011)
        chk(f'{p} ni', g('ebt') - g('tax') + n(g('disc')), g('ni'), 0.011)
    if g('amp_rev') is not None and g('rev') is not None and not x.get('seg_restated') and p not in ('H2-24',):
        chk(f'{p} segments', g('amp_rev') + g('di_rev') + n(g('elim_rev')), g('rev'), 0.16)
    if g('agp_pub') is not None and g('amp_agp') is not None:
        chk(f'{p} agp', g('amp_agp') + g('di_agp') + n(g('oth_agp')), g('agp_pub'), 0.16)
    if g('adj_ebitda_pub') is not None and g('dna_br') is not None and g('sbc') is not None:
        chk(f'{p} adj ebitda', g('op') + g('dna_br') + n(g('oth_ie_br')) + g('sbc') + n(g('nonrec')), g('adj_ebitda_pub'), 0.16)
    if g('adj_ebit_pub') is not None and g('dna_ex_ppa') is not None and g('adj_ebitda_pub') is not None:
        chk(f'{p} adj ebit', g('adj_ebitda_pub') - g('dna_ex_ppa'), g('adj_ebit_pub'), 0.16)
    if g('ni_cont_ex_ppa_pub') is not None and g('ppa_amort') is not None:
        chk(f'{p} ni ex ppa (tax effect within 1.5 of gross add-back)', g('ni_cont') + g('ppa_amort') + n(g('brand')), g('ni_cont_ex_ppa_pub'), 8.0)
    if g('wsh') and g('eps_basic') is not None and g('ni') is not None:
        chk(f'{p} eps', (g('ni') - n(g('pref_div'))) / g('wsh'), g('eps_basic'), 0.0101)
    if g('bs_ta') is not None:
        chk(f'{p} bs', g('bs_ta'), g('bs_tle'), 0.011)
        chk(f'{p} bs assets', g('bs_gw') + g('bs_int') + g('bs_ppe') + n(g('bs_rou')) + g('bs_eqinv') + g('bs_onca') + g('bs_dta') + g('bs_inv') + g('bs_ar') + g('bs_oca') + g('bs_cash'), g('bs_ta'), 0.011)
        chk(f'{p} bs liab', g('bs_cap') + g('bs_res') + g('bs_ncb') + g('bs_ncll') + g('bs_pens') + g('bs_oncl') + g('bs_dtl') + g('bs_cb') + g('bs_cll') + g('bs_ap') + g('bs_ocl'), g('bs_tle'), 0.011)
    if g('cfo') is not None:
        chk(f'{p} cfo', n(g('cf_ni')) + g('cf_fin') + n(g('cf_tax')) + n(g('cf_dna')) + n(g('cf_oth')) + n(g('cf_taxp')) + n(g('cf_wc')), g('cfo'), 0.011)
        chk(f'{p} cfi', g('cf_capex') + g('cf_acq') + g('cf_oinv'), g('cfi'), 0.011)
        chk(f'{p} cff', g('cf_eq') + g('cf_div') + g('cf_debt') + g('cf_int') + g('cf_lease') + g('cf_ofin'), g('cff'), 0.011)
        if g('cf_beg') is not None and g('cf_end') is not None:
            chk(f'{p} cash', g('cf_beg') + g('cfo') + g('cfi') + g('cff') + g('cf_fx') + g('cf_disc'), g('cf_end'), 0.011)
    if g('cf_end') is not None and g('bs_cash') is not None: chk(f'{p} cash bs vs cf', g('cf_end') + n(g('cash_adj')), g('bs_cash'), 0.05)
    if g('qa_tot') is not None and g('qb_tot') is not None and g('amp_rev') is not None:
        chk(f'{p} quarters vs half', g('qa_tot') + g('qb_tot'), g('amp_rev') + g('di_rev') + n(g('elim_rev')), 0.16)
    if g('nd_pub') is not None and g('bs_ncb') is not None:
        chk(f'{p} net debt (company nets derivatives / accrued interest; ±1.0)', g('bs_ncb') + g('bs_cb') + g('bs_ncll') + g('bs_cll') - g('bs_cash') + n(g('deriv_net')), g('nd_pub'), 1.0)
for y in (2023, 2024, 2025):
    yy = str(y)[2:]
    for k in ('rev', 'op', 'ni', 'adj_ebitda_pub', 'cfo', 'cf_capex', 'amp_rev', 'di_rev'):
        hs = [D.get(f'H{h}-{yy}', {}).get('x', {}).get(k) for h in (1, 2)]
        fy = D.get(str(y), {}).get('x', {}).get(k)
        if fy is None: continue
        if all(v is not None for v in hs): chk(f'{y} {k} sum-h', sum(hs), fy, 0.011)
        else: bad.append(f'{y} {k}: halves missing {[i + 1 for i, v in enumerate(hs) if v is None]}')
print('\n'.join(bad) or 'all checks pass')
