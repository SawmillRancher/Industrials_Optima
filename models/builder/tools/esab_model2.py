"""ESAB model — income statement, bridges, cash flow, balance sheet, schedules, ratios, valuation."""
from esab_model import H, has, yoy, ratio, S, CFG, lay


def build_rest(M):
    D = CFG['debt']; E = CFG['eddyfi']
    Q2 = lambda k: f'[{k}@$Q2/26]'
    H1 = lambda k: f'([{k}@$Q1/26]+[{k}@$Q2/26])'
    hcf = has('cf_cfo'); hbs = has('bs_total_assets')
    # ================================================================ INCOME STATEMENT
    M.add(style='section', label='CONSOLIDATED STATEMENT OF OPERATIONS (US GAAP; continuing operations as reported)', note='CONSOLIDATED IS — forecast logic')
    M.add('is_sales', 'Net sales', 'total', 'num', hist=H('is_net_sales'), fc='=[g_sales]', cagr='growth', note='Forecast linked to the segment build.',
          comment='Source: ESAB Forms 10-K / 10-Q, Form 10 (10-12B/A, 17-Mar-2022; carve-out combined financial statements 2019–2021) and Form 8-K earnings releases (Ex. 99.1); SEC EDGAR CIK 0001877322.')
    M.add('is_sales_g', '  Net sales y/y %', 'pct', 'pct', hist=yoy('is_sales'), fc='=IFERROR([is_sales]/[is_sales@py]-1,"")')
    M.add('is_cogs', 'Cost of sales', 'line', 'num', hist=H('is_cogs'), fc='=[is_sales]-[is_gp]')
    M.add('is_gp', 'Gross profit', 'sub', 'num', hist='=[is_sales]-[is_cogs]', fc='=[is_oi]+[is_sga]+[is_restr]+[is_othop]', cagr='growth',
          note='Forecast = operating income + SG&A + restructuring + other operating items (backed out of the adjusted EBITDA build).')
    M.add('is_gm', '  Gross margin %', 'pctline', 'pct', hist=ratio('is_gp', 'is_sales'), fc='=IFERROR([is_gp]/[is_sales],"")', cagr='avg')
    M.add('is_sga', 'Selling, general & administrative expense', 'line', 'num', hist=H('is_sga'),
          qfc='=[is_sales]*[sga_pct]', afc=lambda c: '=SUMQ[is_sga]' if c.year == 2026 else '=[is_sales]*[sga_pct]')
    M.add('is_restr', 'Restructuring and other related charges', 'line', 'num', hist=H('is_restructuring'),
          qfc=lambda c: CFG['restr_q'][c.label], afc=lambda c: '=SUMQ[is_restr]' if c.year == 2026 else CFG['restr_fc'][str(c.year)], note=CFG['notes']['restr'])
    M.add('is_othop', 'Other operating items (charge = +)', 'line', 'num', hist=H('is_othop'), fc=0)
    M.add('is_oi', 'Operating income', 'total', 'num', hist='=[is_gp]-[is_sga]-[is_restr]-[is_othop]',
          qfc='=[g_aebitda]-[da_oth]-[amort]-[txn]-[perf]-[is_restr]',
          afc=lambda c: '=SUMQ[is_oi]' if c.year == 2026 else '=[g_aebitda]-[da_oth]-[amort]-[txn]-[perf]-[is_restr]', cagr='growth',
          note='Forecast = adjusted EBITDA − depreciation & other amortization − acquired-intangible amortization & step-up − transaction costs − performance options − restructuring.')
    M.add('chk_oi', '  Check: operating income vs reported (should be 0)', 'check', 'num', hist=lambda c: '=IF(ISNUMBER([is_oi_rep]),ROUND([is_oi]-[is_oi_rep],1),"")')
    M.add('is_oi_rep', '  Memo: operating income as reported', 'pub', 'num', hist=H('is_operating_income'), outline=2)
    M.add('is_int', 'Interest expense and other, net (incl. pension & other non-operating)', 'line', 'num', hist=H('is_interest_expense_other_net'),
          qfc=lambda c: CFG['int_q'][c.label], afc=lambda c: '=SUMQ[is_int]' if c.year == 2026 else '=[dsch_notes@py]*[r_notes]+[dsch_tl@py]*[r_tl]+[dsch_fac@py]*[r_fac]-[bs_cash@py]*[r_cash]+[int_oth]',
          note=CFG['notes']['int'])
    M.add('is_pen', 'Pension settlement (gain) loss & other non-operating items (below operating income)', 'line', 'num', hist=H('is_nonop_oth'), fc=0)
    M.add('is_pretax', 'Income from continuing operations before income taxes', 'sub', 'num', hist='=[is_oi]-[is_int]-N([is_pen])', fc='=[is_oi]-[is_int]-N([is_pen])', cagr='growth')
    M.add('is_tax', 'Income tax expense', 'line', 'num', hist=H('is_income_taxes'), qfc='=[is_pretax]*[is_etr]', afc=lambda c: '=SUMQ[is_tax]' if c.year == 2026 else '=[is_pretax]*[is_etr]')
    M.add('is_etr', '  Effective tax rate', 'pctline', 'pct', hist=ratio('is_tax', 'is_pretax'), qfc='=SCEN(TAX26)',
          afc=lambda c: '=IFERROR([is_tax]/[is_pretax],"")' if c.year == 2026 else CFG['etr'], cagr='avg')
    M.add('is_nic', 'Net income from continuing operations', 'sub', 'num', hist='=[is_pretax]-[is_tax]', fc='=[is_pretax]-[is_tax]')
    M.add('is_disc', 'Income (loss) from discontinued operations, net of taxes (legacy asbestos)', 'line', 'num', hist=H('is_disc_ops'),
          qfc='=' + H1('is_disc') + '/2', afc=lambda c: '=SUMQ[is_disc]' if c.year == 2026 else CFG['disc_fc'],
          note='Asbestos-related activity of divested Colfax businesses (expected settlements, legal & administrative costs). Q3/Q4-26E: 1H run-rate; 2027E+: input.')
    M.add('is_nit', 'Net income', 'sub', 'num', hist='=[is_nic]+[is_disc]', fc='=[is_nic]+[is_disc]')
    M.add('is_nci', '  Less: income attributable to noncontrolling interest', 'line', 'num', hist=H('is_nci_income'),
          qfc='=' + H1('is_nci') + '/2', afc=lambda c: '=SUMQ[is_nci]' if c.year == 2026 else '=[is_nci@py]*(1+[gm_sales])')
    M.add('is_ni', 'Net income attributable to ESAB Corporation', 'total', 'num', hist='=[is_nit]-[is_nci]', fc='=[is_nit]-[is_nci]', cagr='growth')
    M.add('chk_ni', '  Check: net income attributable vs reported (should be 0; ±0.1 rounding tolerated)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([is_ni_rep]),ROUND([is_ni]-[is_ni_rep],1),"")')
    M.add('is_ni_rep', '  Memo: net income attributable to ESAB as reported', 'pub', 'num', hist=H('is_ni_attrib'), outline=2)
    M.add('is_mcps', '  Less: mandatory convertible preferred stock (MCPS) dividends', 'line', 'num', hist=H('is_mcps_dividends'),
          qfc=f'={E["mcps"]}*{E["mcps_rate"]}/4', afc=lambda c: '=SUMQ[is_mcps]' if c.year == 2026 else CFG['mcps_div'][str(c.year)],
          note='$175m 6.50% Series A MCPS issued Jun-2026 (Eddyfi financing): $11.4m p.a.; mandatory conversion ~Jun-2029 into 7.1806–8.2576 shares per $1,000.')
    M.add('is_nicom', 'Net income attributable to common stockholders', 'sub', 'num', hist='=[is_ni]-N([is_mcps])', fc='=[is_ni]-N([is_mcps])')
    M.add('is_nic_attr', '  Memo: net income from continuing operations attributable to ESAB common (start of the adjusted-NI bridge)', 'line', 'num',
          hist='=[is_nic]-[is_nci]-N([is_mcps])', fc='=[is_nic]-[is_nci]-N([is_mcps])')
    M.add('is_da', '  Memo: depreciation & amortization (total; cash-flow statement)', 'line', 'num', hist=H('cf_da'),
          qfc='=[da_oth]+[amort]-[edd_step]', afc=lambda c: '=SUMQ[is_da]' if c.year == 2026 else '=[da_oth]+[amort]', outline=2)
    M.add('is_sbc', '  Memo: stock-based compensation', 'line', 'num', hist=H('cf_sbc'), qfc='=[is_sales]*[sbc_pct]+[perf]',
          afc=lambda c: '=SUMQ[is_sbc]' if c.year == 2026 else '=[is_sales]*[sbc_pct]+[perf]', outline=2)
    M.add(None, '(Earnings per share)', 'label')
    M.add('sh_b', '  Weighted-average basic shares (m)', 'line', 'num1', hist=H('is_shares_basic'),
          qfc=lambda c: f'=[sh_out@$Q2/26]-[bb_sh@$2026E]*{0.25 if c.q == 3 else 0.75}',
          afc=lambda c: '=AVERAGE([sh_b@-4],[sh_b@-3],[sh_b@-2],[sh_b@-1])' if c.year == 2026 else '=AVERAGE([sh_beg],[sh_end])',
          note='Q3/Q4-26E: shares outstanding at 3-Jul-2026 (incl. the Eddyfi common private placement) less 2H buybacks. 2027E+: average of beginning and ending shares.')
    M.add('sh_d', '  Weighted-average diluted shares (m)', 'line', 'num1', hist=H('is_shares_diluted'),
          qfc='=[sh_b]+([sh_d@$Q2/26]-[sh_b@$Q2/26])', afc=lambda c: '=AVERAGE([sh_d@-4],[sh_d@-3],[sh_d@-2],[sh_d@-1])' if c.year == 2026 else '=[sh_b]+[dil]')
    M.add('eps_c', 'EPS – diluted, continuing operations ($)', 'sub', 'eps', hist=lambda c: '=IFERROR(([is_nic]-[is_nci]-N([is_mcps]))/[sh_d],"")' if c.label in S.get('is_shares_diluted', {}) else None,
          qfc='=IFERROR(([is_nic]-[is_nci]-N([is_mcps]))/[sh_d],"")', afc=lambda c: '=SUMQ[eps_c]' if c.year == 2026 else '=IFERROR(([is_nic]-[is_nci]-N([is_mcps]))/[sh_d],"")', cagr='growth',
          note='Two-class / if-converted mechanics may cause ±$0.01–0.02 differences vs reported. 2026E = sum of quarters.')
    M.add('eps_c_rep', '  Memo: EPS – diluted, continuing operations as reported ($)', 'pub', 'eps', hist=H('is_eps_diluted_cont'), outline=2)
    M.add('eps_d', 'EPS – diluted, net income attributable to common ($)', 'line', 'eps', hist=lambda c: '=IFERROR([is_nicom]/[sh_d],"")' if c.label in S.get('is_shares_diluted', {}) else None,
          fc='=IFERROR([is_nicom]/[sh_d],"")')
    M.add('eps_d_rep', '  Memo: EPS – diluted as reported ($)', 'pub', 'eps', hist=H('is_eps_diluted'), outline=2)
    M.add('dps', '  Dividends declared per share ($)', 'line', 'eps', hist=H('is_dps_declared'), qfc=lambda c: '=[dps@$Q2/26]',
          afc=lambda c: '=SUMQ[dps]' if c.year == 2026 else '=[dps@py]*(1+[dps_g])', cagr='growth',
          note=f'Q3/Q4-26E: Q2/26 quarterly dividend held. 2027E+: +{CFG["dps_g"]:.0%} p.a.')
    M.add('dps_g', '  Dividend per share growth %', 'pct', 'pct', hist=yoy('dps', has('is_dps_declared')), afc=lambda c: '=IFERROR([dps]/[dps@py]-1,"")' if c.year == 2026 else CFG['dps_g'])
    M.blank()

    # ================================================================ RECON A — ADJUSTED EBITDA
    M.add(style='section', label='RECONCILIATION A: NET INCOME (CONTINUING OPS) → EBITDA → ADJUSTED EBITDA → CORE ADJUSTED EBITDA (company definition)',
          note="ADJUSTED EBITDA — per ESAB earnings-release reconciliations ('Reconciliation of GAAP to non-GAAP financial measures'); core = ex-Russia")
    hb = has('pub_adj_ebitda')
    M.add('rA_nic', 'Net income from continuing operations (GAAP)', 'sub', 'num', hist='=[is_nic]', fc='=[is_nic]')
    M.add('rA_tax', '  (+) Income tax expense', 'line', 'num', hist='=[is_tax]', fc='=[is_tax]')
    M.add('rA_int', '  (+) Interest expense and other, net', 'line', 'num', hist='=[is_int]', fc='=[is_int]')
    M.add('rA_pen', '  (+/−) Pension settlement (gain) loss & other non-operating items', 'line', 'num', hist='=N([is_pen])', fc='=N([is_pen])')
    M.add('rA_oi', '  = Operating income', 'sub', 'num', hist='=[rA_nic]+[rA_tax]+[rA_int]+[rA_pen]', fc='=[rA_nic]+[rA_tax]+[rA_int]+[rA_pen]')
    M.add('rA_da', '  (+) Depreciation & other amortization', 'line', 'num', hist=lambda c: '=[da_oth]' if hb(c) else None, fc='=[da_oth]')
    M.add('rA_am', '  (+) Amortization of acquired intangibles & fair-value step-up on acquired inventories', 'line', 'num',
          hist=lambda c: '=[amort]' if hb(c) else None, fc='=[amort]')
    M.add('ebitda', '  = EBITDA (model)', 'total', 'num', hist=lambda c: '=[rA_oi]+[rA_da]+[rA_am]' if hb(c) else None, fc='=[rA_oi]+[rA_da]+[rA_am]', cagr='growth')
    M.add('rA_restr', '  (+) Restructuring and other related charges', 'line', 'num', hist=lambda c: '=[is_restr]' if hb(c) else None, fc='=[is_restr]')
    M.add('rA_txn', '  (+) Acquisition transaction, due-diligence & integration expenses', 'line', 'num', hist=lambda c: '=[txn]' if hb(c) else None, fc='=[txn]')
    M.add('rA_perf', '  (+) Performance option awards compensation (2026)', 'line', 'num', hist=lambda c: '=[perf]' if hb(c) else None, fc='=[perf]')
    M.add('rA_sep', '  (+) Separation costs (spin-off from Colfax, 2022–2023)', 'line', 'num', hist=H('br_sep'), fc=0)
    M.add('rA_oth', '  (+/−) Other company items / definitional differences', 'line', 'num', hist=H('br_oth'), fc=0,
          note='2019–2020: balance between the Form 10 printed components and published adjusted EBITDA (carve-out allocations); 2021+: company "Other" line.')
    M.add('rA_items', '  Total adjusting items', 'sub', 'num', hist=lambda c: '=N([rA_restr])+N([rA_txn])+N([rA_perf])+N([rA_sep])+N([rA_oth])' if hb(c) else None,
          fc='=N([rA_restr])+N([rA_txn])+N([rA_perf])+N([rA_sep])+N([rA_oth])')
    M.add('aebitda', '  = Adjusted EBITDA (model bridge)', 'total', 'num', hist=lambda c: '=[ebitda]+[rA_items]' if hb(c) else None, fc='=[ebitda]+[rA_items]', cagr='growth',
          note='Historical bridge rebuilt from the company reconciliation in each period; forecast = segment build (check row in the Group block).')
    M.add('aebitda_m', '  Adjusted EBITDA margin %', 'pctline', 'pct', hist=ratio('aebitda', 'is_sales', hb), fc='=IFERROR([aebitda]/[is_sales],"")', cagr='avg')
    M.add('pub_aebitda', '  Company-published adjusted EBITDA', 'pub', 'num', hist=H('pub_adj_ebitda'))
    M.add('chk_aebitda', '  Check: model bridge vs company-published (should be 0; ±0.2 in 2021 quarters = release rounding)', 'check', 'num', hist=lambda c: '=IF(ISNUMBER([pub_aebitda]),ROUND([aebitda]-[pub_aebitda],1),"n/p")' if hb(c) else None)
    M.add('rA_ru', '  (−) Adjusted EBITDA attributable to Russia', 'line', 'num', hist=lambda c: '=-[ru_ebitda]' if c.label in S.get('pub_russia_ebitda', {}) else None, fc='=-[ru_ebitda]')
    M.add('cebitda', '  = Core adjusted EBITDA (ex-Russia)', 'total', 'num', hist=lambda c: '=[aebitda]+[rA_ru]' if c.label in S.get('pub_russia_ebitda', {}) else None,
          fc='=[aebitda]+[rA_ru]', cagr='growth')
    M.add('pub_cebitda', '  Company-published core adjusted EBITDA', 'pub', 'num', hist=H('pub_core_ebitda'))
    M.add('chk_cebitda', '  Check: model vs company-published core adjusted EBITDA (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([pub_cebitda]),ROUND([cebitda]-[pub_cebitda],1),"n/p")' if c.label in S.get('pub_russia_ebitda', {}) else None)
    M.add('def_eb', '  Definition basis (company adjusted EBITDA definition in force)', 'def', 'gen', hist=CFG['def_ebitda'])
    M.add(None, 'To adjusted EBITA:', 'label')
    M.add('rA_less_da', '  (−) Depreciation & other amortization', 'line', 'num', hist=lambda c: '=-[da_oth]' if hb(c) else None, fc='=-[da_oth]')
    M.add('aebita', '  = Adjusted EBITA (model; adjusted EBITDA − depreciation & other amortization)', 'sub', 'num',
          hist=lambda c: '=[aebitda]+[rA_less_da]' if hb(c) else None, fc='=[aebitda]+[rA_less_da]', cagr='growth')
    M.add('aebita_m', '  Adjusted EBITA margin %', 'pctline', 'pct', hist=ratio('aebita', 'is_sales', hb), fc='=IFERROR([aebita]/[is_sales],"")')
    M.add('aebitda_pf', '  Memo: adjusted EBITDA pro forma — Eddyfi full year (2026E), for leverage & valuation', 'line', 'num',
          afc=lambda c: f'=[aebitda]+[edd_rr]*[edd_m]*151/365' if c.year == 2026 else '=[aebitda]',
          note='2026E adds Eddyfi pre-closing days (1-Jan to 31-May) at the 2026E standalone margin (company pro forma basis).')
    M.blank()

    # ================================================================ RECON B — ADJUSTED NI / EPS
    M.add(style='section', label='RECONCILIATION B: GAAP NET INCOME / DILUTED EPS (CONTINUING OPS) → ADJUSTED & CORE ADJUSTED NET INCOME / EPS',
          note='ADJUSTED EPS — company definition: excludes restructuring, acquisition-amortization & other, performance options; tax-effected; excludes discrete tax items; MCPS on an if-converted basis')
    hn = has('pub_adj_ni')
    M.add('rB_ni', 'Net income from continuing operations attributable to ESAB common (GAAP)', 'sub', 'num', hist='=[is_nic_attr]', fc='=[is_nic_attr]')
    M.add('rB_restr', '  (+) Restructuring and other related charges — pretax', 'line', 'num', hist=lambda c: '=[is_restr]' if hn(c) else None, fc='=[is_restr]')
    M.add('rB_acq', '  (+) Acquisition-amortization & other related charges — pretax (transaction costs + amortization & step-up)', 'line', 'num',
          hist=lambda c: '=[txn]+[amort]' if hn(c) else None, fc='=[txn]+[amort]')
    M.add('rB_sep', '  (+) Separation costs — pretax (2022–2023)', 'line', 'num', hist=lambda c: '=N([rA_sep])' if hn(c) else None, fc=0)
    M.add('rB_nonop', '  (+/−) Pension settlements & other pre-tax items outside operating income (incl. Eddyfi bridge-loan fees)', 'line', 'num', hist=H('an_nonop'), fc=0)
    M.add('rB_perf', '  (+) Performance option awards compensation', 'line', 'num', hist=lambda c: '=[perf]' if hn(c) else None, fc='=[perf]')
    M.add('rB_taxeff', '  (−) Tax effect of adjusting items', 'line', 'num', hist=H('an_taxeff'), fc='=-([rB_restr]+[rB_acq]+N([rB_sep])+[rB_nonop]+[rB_perf])*[rB_rate]')
    M.add('rB_rate', '  Tax rate applied to adjusting items', 'pctline', 'pct',
          hist=lambda c: '=IFERROR(-[rB_taxeff]/([rB_restr]+[rB_acq]+N([rB_sep])+[rB_nonop]+[rB_perf]),"")' if hn(c) else None, fc=CFG['adj_tax'],
          note=f'Forecast: {CFG["adj_tax"]:.0%} (ESAB overall estimated effective rate applied to adjustments).')
    M.add('rB_disc', '  (+/−) Discrete tax adjustments', 'line', 'num', hist=H('an_discrete'), fc=0)
    M.add('rB_mcps', '  (+) MCPS dividends (if-converted method)', 'line', 'num', hist=lambda c: '=N([is_mcps])' if hn(c) else None, fc='=N([is_mcps])')
    M.add('rB_oth', '  (+/−) Other company items / rounding', 'line', 'num', hist=H('an_oth'), fc=0)
    M.add('adj_ni', '  = Adjusted net income from continuing operations (model)', 'total', 'num',
          hist=lambda c: '=[rB_ni]+N([rB_restr])+N([rB_acq])+N([rB_sep])+N([rB_nonop])+N([rB_perf])+N([rB_taxeff])+N([rB_disc])+N([rB_mcps])+N([rB_oth])' if hn(c) else None,
          fc='=[rB_ni]+N([rB_restr])+N([rB_acq])+N([rB_sep])+N([rB_nonop])+N([rB_perf])+N([rB_taxeff])+N([rB_disc])+N([rB_mcps])+N([rB_oth])', cagr='growth')
    M.add('pub_adj_ni', '  Company-published adjusted net income from continuing operations', 'pub', 'num', hist=H('pub_adj_ni'))
    M.add('chk_adj_ni', '  Check: model vs company-published (should be 0; ±0.1 rounding)', 'check', 'num', hist=lambda c: '=IF(ISNUMBER([pub_adj_ni]),ROUND([adj_ni]-[pub_adj_ni],1),"n/p")' if hn(c) else None)
    M.add('rB_ru', '  (−) Adjusted net income attributable to Russia', 'line', 'num', hist=H('pub_russia_ni', -1.0),
          qfc='=-[ru_ebitda]*' + str(CFG['ru_ni_conv']), afc=lambda c: '=SUMQ[rB_ru]' if c.year == 2026 else '=-[ru_ebitda]*%s' % CFG['ru_ni_conv'])
    M.add('core_adj_ni', '  = Core adjusted net income (ex-Russia)', 'sub', 'num', hist=lambda c: '=[adj_ni]+[rB_ru]' if c.label in S.get('pub_russia_ni', {}) else None,
          fc='=[adj_ni]+[rB_ru]', cagr='growth')
    M.add('pub_core_adj_ni', '  Company-published core adjusted net income', 'pub', 'num', hist=H('pub_core_adj_ni'))
    M.add('chk_core_adj_ni', '  Check: model vs company-published core adjusted net income (should be 0; ±0.1)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([pub_core_adj_ni]),ROUND([core_adj_ni]-[pub_core_adj_ni],1),"n/p")' if c.label in S.get('pub_russia_ni', {}) else None)
    M.add('rB_sh', '  Weighted-average diluted shares, if-converted (m)', 'line', 'num1', hist='=[sh_d]',
          fc=lambda c: '=[sh_d]+[mcps_conv_sh]' if c.year < 2030 else '=[sh_d]', note='Adds the MCPS if-converted shares until the mandatory conversion (~Jun-2029).')
    M.add('adj_eps', 'Adjusted diluted EPS — continuing operations ($) (model)', 'total', 'eps',
          hist=lambda c: '=IFERROR([adj_ni]/[rB_sh],"")' if hn(c) else None, qfc='=IFERROR([adj_ni]/[rB_sh],"")',
          afc=lambda c: '=SUMQ[adj_eps]' if c.year == 2026 else '=IFERROR([adj_ni]/[rB_sh],"")', cagr='growth')
    M.add('pub_adj_eps', '  Company-published adjusted diluted EPS ($)', 'pub', 'eps', hist=H('pub_adj_eps'))
    M.add('chk_adj_eps', '  Check: model vs company-published adjusted EPS (should be 0.00; ±0.01–0.03: company builds adjusted EPS from rounded per-share items)', 'check', 'eps',
          hist=lambda c: '=IF(ISNUMBER([pub_adj_eps]),ROUND([adj_eps]-[pub_adj_eps],2),"n/p")' if hn(c) else None)
    M.add('core_adj_eps', 'Core adjusted diluted EPS ($) (model)', 'total', 'eps',
          hist=lambda c: '=IFERROR([core_adj_ni]/[rB_sh],"")' if c.label in S.get('pub_russia_ni', {}) else None, qfc='=IFERROR([core_adj_ni]/[rB_sh],"")',
          afc=lambda c: '=SUMQ[core_adj_eps]' if c.year == 2026 else '=IFERROR([core_adj_ni]/[rB_sh],"")', cagr='growth',
          note='Company headline EPS measure; FY26 outlook $5.40–5.50.')
    M.add('pub_core_adj_eps', '  Company-published core adjusted diluted EPS ($)', 'pub', 'eps', hist=H('pub_core_adj_eps'))
    M.add('chk_core_adj_eps', '  Check: model vs company-published core adjusted EPS (should be 0.00; ±0.01–0.03 per-share rounding)', 'check', 'eps',
          hist=lambda c: '=IF(ISNUMBER([pub_core_adj_eps]),ROUND([core_adj_eps]-[pub_core_adj_eps],2),"n/p")' if c.label in S.get('pub_russia_ni', {}) else None)
    M.add('def_eps', '  Definition basis (company adjusted EPS)', 'def', 'gen', hist=CFG['def_eps'])
    M.blank()

    # ================================================================ GROWTH & MARGINS
    M.add(style='section', label='GROWTH & MARGINS', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    M.add('gm_sales', '  Net sales y/y %', 'pct', 'pct', hist=yoy('is_sales'), fc='=IFERROR([is_sales]/[is_sales@py]-1,"")', cagr='avg')
    M.add('gm_org', '  Organic sales growth % (company)', 'pctline', 'pct', hist=H('sc_TOT_organic_pct'),
          fc='=IFERROR(([AM_dorg]+[EA_dorg])/[is_sales@py],"")', cagr='avg')
    M.add('gm_core_org', '  Core organic growth % (company; ex-Russia)', 'pctline', 'pct', hist='=[core_org]', fc='=[core_org]')
    M.add('gm_acq', '  Acquisitions % (incl. Eddyfi & future M&A)', 'pctline', 'pct', hist=H('sc_TOT_acquisitions_pct'),
          fc='=IFERROR(([AM_dacq]+[EA_dacq]+N([edd_rev])-N([edd_rev@py])+N([ma_rev])-N([ma_rev@py]))/[is_sales@py],"")')
    M.add('gm_fx', '  Foreign currency %', 'pctline', 'pct', hist=H('sc_TOT_fx_pct'), fc='=IFERROR(([AM_dfx]+[EA_dfx])/[is_sales@py],"")')
    M.add('gm_aebitda_g', '  Adjusted EBITDA y/y %', 'pct', 'pct', hist=yoy('aebitda', has('pub_adj_ebitda')), fc='=IFERROR([aebitda]/[aebitda@py]-1,"")')
    M.add('gm_oi_g', '  Operating income y/y %', 'pct', 'pct', hist=yoy('is_oi'), fc='=IFERROR([is_oi]/[is_oi@py]-1,"")')
    M.add('gm_ni_g', '  Net income attributable y/y %', 'pct', 'pct', hist=yoy('is_ni'), fc='=IFERROR([is_ni]/[is_ni@py]-1,"")')
    M.add('gm_eps_g', '  Core adjusted EPS y/y %', 'pct', 'pct', hist=yoy('core_adj_eps', has('pub_russia_ni')), fc='=IFERROR([core_adj_eps]/[core_adj_eps@py]-1,"")')
    M.add('gm_gm', '  Gross margin %', 'pctline', 'pct', hist='=[is_gm]', fc='=[is_gm]')
    M.add('gm_aebitda_m', '  Adjusted EBITDA margin %', 'pctline', 'pct', hist=lambda c: '=[aebitda_m]' if has('pub_adj_ebitda')(c) else None, fc='=[aebitda_m]')
    M.add('gm_core_m', '  Core adjusted EBITDA margin %', 'pctline', 'pct', hist=lambda c: '=[core_m]' if has('russia_sales')(c) and has('seg_AM_net_sales')(c) else None, fc='=[core_m]')
    M.add('gm_inc', '  Incremental adjusted EBITDA margin (ΔEBITDA / Δnet sales)', 'pctline', 'pct',
          hist=lambda c: '=IFERROR(([aebitda]-[aebitda@py])/([is_sales]-[is_sales@py]),"")' if lay.py(c) and has('pub_adj_ebitda')(c) and has('pub_adj_ebitda')(lay.py(c)) else None,
          fc='=IFERROR(([aebitda]-[aebitda@py])/([is_sales]-[is_sales@py]),"")')
    M.add('gm_op_m', '  Operating margin (GAAP) %', 'pctline', 'pct', hist=ratio('is_oi', 'is_sales'), fc='=IFERROR([is_oi]/[is_sales],"")', cagr='avg')
    M.add('gm_net_m', '  Net margin %', 'pctline', 'pct', hist=ratio('is_ni', 'is_sales'), fc='=IFERROR([is_ni]/[is_sales],"")', cagr='avg')
    M.add('gm_sga', '  SG&A % of net sales', 'pctline', 'pct', hist='=[sga_pct]', fc='=[sga_pct]')
    M.blank()

    # ================================================================ CASH FLOW
    M.add(style='section', label='CONSOLIDATED STATEMENT OF CASH FLOWS',
          note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    M.add('cf_ni', 'Net income (incl. discontinued operations & NCI)', 'line', 'num', hist=H('cf_net_income'), afc='=[is_nit]',
          comment='Source: Forms 10-K / 10-Q / Form 10 statements of cash flows (year-to-date); discrete quarters derived.')
    M.add(None, 'Adjustments:', 'label')
    M.add('cf_da', '  Depreciation & amortization', 'line', 'num', hist=H('cf_da'), afc='=[is_da]')
    M.add('cf_sbc', '  Stock-based compensation', 'line', 'num', hist=H('cf_sbc'), afc='=[is_sbc]')
    M.add('cf_def', '  Deferred income taxes', 'line', 'num', hist=H('cf_deferred_taxes'), afc=lambda c: '=' + H1('cf_def') + '-[edd_amort]*0.25*0' if c.year == 2026 else 0)
    M.add('cf_ratg', '  Non-cash restructuring, impairment & (gains) losses', 'line', 'num', hist=H('cf_noncash_restructuring_impairment_gains'), afc=lambda c: '=' + H1('cf_ratg') if c.year == 2026 else 0)
    M.add('cf_oth', '  Other non-cash items & discontinued-operations cash, net (derived)', 'line', 'num', hist=H('cf_oth'),
          afc=lambda c: '=' + H1('cf_oth') if c.year == 2026 else 0,
          note='Includes asbestos payments net of insurance recoveries (discontinued operations). The 2H/26 inventory step-up is non-cash but runs through the inventory (working-capital) line in the forecast.')
    M.add('cf_wc', '  Changes in operating assets & liabilities, net', 'line', 'num', hist=H('cf_wc'),
          afc=lambda c: ('=' + H1('cf_wc') + '-([bs_ar]-[bs_ar@$Q2/26])-([bs_inv]-[bs_inv@$Q2/26])+([bs_ap]-[bs_ap@$Q2/26])+([bs_accr]-[bs_accr@$Q2/26])') if c.year == 2026
          else '=-([bs_ar]-[bs_ar@py])-([bs_inv]-[bs_inv@py])+([bs_ap]-[bs_ap@py])+([bs_accr]-[bs_accr@py])')
    M.add('cfo', 'Net cash provided by operating activities', 'sub', 'num', hist=H('cf_cfo'), afc='=SUM({c}%d:{c}%d)' % (M.rows['cf_ni'], M.rows['cf_wc']), cagr='growth')
    M.add('capex', 'Purchases of property, plant & equipment', 'line', 'num', hist=H('cf_capex'),
          afc=lambda c: '=-SCEN(CAPEX26)' if c.year == 2026 else '=-[is_sales]*[capex_pct]')
    M.add('cf_acq', 'Acquisitions, net of cash received', 'line', 'num', hist=H('cf_acquisitions'),
          afc=lambda c: '=' + H1('cf_acq') if c.year == 2026 else '=-[ma_spend]', note='2026E: 1H/26 actual (incl. Eddyfi ~$1.4bn net of cash). 2027E+: M&A lever.')
    M.add('cf_proc', 'Proceeds from sale of property, plant & equipment', 'line', 'num', hist=H('cf_proceeds_asset_sales'), afc=lambda c: '=' + H1('cf_proc') if c.year == 2026 else 0)
    M.add('cf_oinv', 'Other investing activities, net (derived)', 'line', 'num', hist=H('cf_oinv'), afc=lambda c: '=' + H1('cf_oinv') if c.year == 2026 else 0)
    M.add('cfi', 'Net cash used in investing activities', 'sub', 'num', hist=H('cf_cfi'), afc='=[capex]+[cf_acq]+[cf_proc]+[cf_oinv]')
    M.add('cf_dp', 'Proceeds from borrowings (senior notes, term loans)', 'line', 'num', hist=H('cf_debt_proceeds'),
          afc=lambda c: '=' + H1('cf_dp') if c.year == 2026 else '=[dsch_refi]')
    M.add('cf_dr', 'Repayments of borrowings', 'line', 'num', hist=H('cf_debt_repayments'),
          afc=lambda c: '=' + H1('cf_dr') + '+[dsch_mat]' if c.year == 2026 else '=[dsch_mat]')
    M.add('cf_rev', 'Revolving credit facility, net', 'line', 'num', hist=H('cf_revolver_net'),
          afc=lambda c: '=' + H1('cf_rev') + f'+([dsch_fac]-{D["fac_q2_26"]})' if c.year == 2026 else '=[dsch_fac]-[dsch_fac@py]',
          note='Forecast = change in the revolver per the debt schedule.')
    M.add('cf_div', 'Dividends paid (common & MCPS)', 'line', 'num', hist=H('cf_dividends_paid'),
          afc=lambda c: '=' + H1('cf_div') + '-([dps@$Q3/26E]*[sh_b@$Q3/26E]+[dps@$Q4/26E]*[sh_b@$Q4/26E])-([is_mcps@$Q3/26E]+[is_mcps@$Q4/26E])' if c.year == 2026 else '=-[dps]*[sh_beg]-N([is_mcps])')
    M.add('cf_bb', 'Repurchases of common stock', 'line', 'num', hist=H('cf_buybacks'),
          afc=lambda c: '=' + H1('cf_bb') + '-SCEN(BB26)' if c.year == 2026 else '=-[bb_plug]')
    M.add('cf_eq', 'Equity issuance (MCPS & common private placement 2026; stock plans)', 'line', 'num', hist=H('cf_equity_issuance'),
          afc=lambda c: '=' + H1('cf_eq') if c.year == 2026 else 0)
    M.add('cf_parent', 'Net transfers (to) from former parent (pre-spin)', 'line', 'num', hist=H('cf_net_transfers_to_parent'), afc=0)
    M.add('cf_ofin', 'Other financing activities, net (derived)', 'line', 'num', hist=lambda c: (S['cf_ofin'].get(c.label, 0) - (S.get('cf_net_transfers_to_parent', {}).get(c.label) or 0)) if c.label in S.get('cf_ofin', {}) else None,
          afc=lambda c: '=' + H1('cf_ofin') if c.year == 2026 else 0)
    M.add('cff', 'Net cash provided by (used in) financing activities', 'sub', 'num', hist=H('cf_cff'), afc='=[cf_dp]+[cf_dr]+[cf_rev]+[cf_div]+[cf_bb]+[cf_eq]+[cf_parent]+[cf_ofin]')
    M.add('cf_fx', 'Effect of foreign exchange rates on cash', 'line', 'num', hist=H('cf_fx_effect'), afc=lambda c: '=' + H1('cf_fx') if c.year == 2026 else 0)
    M.add('cf_net', 'Net increase (decrease) in cash', 'line', 'num', hist=H('cf_net_change_cash'), afc='=[cfo]+[cfi]+[cff]+[cf_fx]')
    M.add('cf_beg', 'Cash — beginning of period', 'line', 'num', hist=H('cf_cash_begin'), afc='=[cf_end@py]')
    M.add('cf_end', 'Cash — end of period (incl. restricted cash where reported)', 'sub', 'num', hist=H('cf_cash_end'), afc='=[cf_beg]+[cf_net]')
    M.add('chk_cf1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([cfo]),ROUND([cfo]+[cfi]+[cff]+[cf_fx]-[cf_net],1),"")' if hcf(c) else None, afc='=ROUND([cfo]+[cfi]+[cff]+[cf_fx]-[cf_net],1)')
    M.add('chk_cf2', '  Check: beginning cash + change = ending cash (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([cf_end]),ROUND([cf_beg]+[cf_net]-[cf_end],1),"")' if hcf(c) else None, afc='=ROUND([cf_beg]+[cf_net]-[cf_end],1)')
    M.add(None, '(Memo)', 'label')
    M.add('fcf', 'Free cash flow (operating cash flow − capital expenditures)', 'total', 'num', hist=lambda c: '=[cfo]+[capex]' if hcf(c) else None, afc='=[cfo]+[capex]', cagr='growth')
    M.add('pub_afcf', '  Memo: company-published adjusted free cash flow (excl. discontinued ops & acquisition-related payments)', 'pub', 'num', hist=H('pub_adj_fcf'), outline=2)
    M.add('fcf_g', '  FCF y/y %', 'pct', 'pct', hist=yoy('fcf', hcf), afc='=IFERROR([fcf]/[fcf@py]-1,"")')
    M.add('fcf_pct', '  FCF % of net sales', 'pctline', 'pct', hist=lambda c: '=IFERROR([fcf]/[is_sales],"")' if hcf(c) else None, afc='=IFERROR([fcf]/[is_sales],"")', cagr='avg')
    M.add('fcf_conv', '  FCF / adjusted net income conversion %', 'pctline', 'pct', hist=lambda c: '=IFERROR([fcf]/[adj_ni],"")' if hcf(c) and hn(c) else None, afc='=IFERROR([fcf]/[adj_ni],"")', cagr='avg')
    M.add('fcf_ps', '  FCF per diluted share ($)', 'line', 'eps', hist=lambda c: '=IFERROR([fcf]/[sh_d],"")' if hcf(c) else None, afc='=IFERROR([fcf]/[sh_d],"")')
    M.add(None, 'Capex ratios', 'label')
    M.add('capex_pct', '  Capex % of net sales', 'pctline', 'pct', hist=lambda c: '=IFERROR(-[capex]/[is_sales],"")' if hcf(c) else None,
          afc=lambda c: '=IFERROR(-[capex]/[is_sales],"")' if c.year == 2026 else CFG['capex_pct'], cagr='avg', note=CFG['notes']['capex_pct'])
    M.add('capex_da', '  Capex / depreciation & other amortization (x)', 'line', 'x2', hist=lambda c: '=IFERROR(-[capex]/[da_oth],"")' if hcf(c) and has('br_da')(c) else None, afc='=IFERROR(-[capex]/[da_oth],"")')
    M.blank()

    # ================================================================ BUYBACKS
    M.add(style='section', label='SHARE BUYBACK SCHEDULE', note='SHARES — 2026E = 2H/26 only; MCPS converts ~Jun-2029')
    M.add('bb_px', '  Avg buyback price ($)', 'line', 'eps', afc=lambda c: '=[val_px]' if c.year == 2026 else '=[bb_px@py]*(1+[px_app])')
    M.add('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'num', afc=lambda c: '=SCEN(BB26)' if c.year == 2026 else '=-[cf_bb]')
    M.add('bb_sh', '  Implied shares repurchased (m)', 'line', 'num1', afc='=IFERROR([bb_cash]/[bb_px],0)')
    M.add('bb_iss', '  Shares issued under equity plans (m)', 'line', 'num1', afc=lambda c: 0.1 if c.year == 2026 else 0.3)
    M.add('mcps_conv_sh', '  MCPS conversion shares (m; if-converted until Jun-2029, issued at conversion)', 'line', 'num1',
          afc=lambda c: E['mcps_conv_shares'] if c.year <= 2029 else 0, note=f'175,000 MCPS × {E["mcps_conv_rate"]} shares (mid of 7.1806–8.2576) = {E["mcps_conv_shares"]:.2f}m shares.')
    M.add('sh_beg', '  Beginning shares outstanding (m)', 'line', 'num1', afc=lambda c: '=[sh_out@$Q2/26]' if c.year == 2026 else '=[sh_end@py]')
    M.add('sh_end', '  Ending shares outstanding (m)', 'sub', 'num1', afc=lambda c: '=[sh_beg]-[bb_sh]+[bb_iss]+[mcps_conv_sh]' if c.year == 2029 else '=[sh_beg]-[bb_sh]+[bb_iss]')
    M.add('bb_pct', '  % of shares repurchased', 'pctline', 'pct', afc='=IFERROR([bb_sh]/[sh_beg],"")')
    M.blank()

    # ================================================================ BALANCE SHEET
    M.add(style='section', label='CONSOLIDATED BALANCE SHEET', note='BS FORECAST — 2026E rolled forward from the 3-Jul-2026 balance sheet (Q2/26, post-Eddyfi) + 2H flows; 2027E+ from prior year end')
    M.add(None, 'ASSETS', 'label')
    M.add('bs_cash', '  Cash and cash equivalents', 'line', 'num', hist=H('bs_cash'), afc='=[cf_end]')
    M.add('bs_ar', '  Trade receivables, net', 'line', 'num', hist=H('bs_ar'), afc='=[wc_sales]*[dso]/365')
    M.add('bs_inv', '  Inventories, net', 'line', 'num', hist=H('bs_inventories'), afc='=[wc_cogs]*[dio]/365')
    M.add('bs_oca', '  Prepaid expenses & other current assets (derived)', 'line', 'num', hist=H('bs_oca'), afc=lambda c: '=' + Q2('bs_oca') if c.year == 2026 else '=[bs_oca@py]')
    M.add('bs_tca', 'Total current assets', 'sub', 'num', hist=lambda c: '=[bs_cash]+[bs_ar]+[bs_inv]+[bs_oca]' if hbs(c) else None, afc='=[bs_cash]+[bs_ar]+[bs_inv]+[bs_oca]')
    M.add('bs_ppe', '  Property, plant & equipment, net', 'line', 'num', hist=H('bs_ppe_net'),
          afc=lambda c: ('=' + Q2('bs_ppe') + '-([capex]-[capex@$Q1/26]-[capex@$Q2/26])-([da_oth@$Q3/26E]+[da_oth@$Q4/26E])') if c.year == 2026
          else '=[bs_ppe@py]-[capex]-[da_oth]+[ma_spend]*[ma_ppe_pct]')
    M.add('bs_gw', '  Goodwill', 'line', 'num', hist=H('bs_goodwill'), afc=lambda c: '=' + Q2('bs_gw') if c.year == 2026 else '=[bs_gw@py]+[ma_spend]*(1-[ma_ppe_pct]-[ma_int_pct])')
    M.add('bs_int', '  Intangible assets, net', 'line', 'num', hist=H('bs_intangibles_net'),
          afc=lambda c: ('=' + Q2('bs_int') + '-([amort@$Q3/26E]+[amort@$Q4/26E]-[edd_step@$Q3/26E]-[edd_step@$Q4/26E])') if c.year == 2026
          else '=[bs_int@py]-([amort]-[edd_step])+[ma_spend]*[ma_int_pct]',
          note='Intangibles roll-forward: − amortization (legacy + Eddyfi PPA; the inventory step-up runs through inventories) + acquired intangibles (M&A lever).')
    M.add('bs_onca', '  Other noncurrent assets (derived; incl. ROU assets, asbestos insurance assets, deferred taxes)', 'line', 'num', hist=H('bs_onca'),
          afc=lambda c: '=' + Q2('bs_onca') if c.year == 2026 else '=[bs_onca@py]')
    M.add('bs_ta', 'TOTAL ASSETS', 'total', 'num', hist=lambda c: '=[bs_tca]+[bs_ppe]+[bs_gw]+[bs_int]+[bs_onca]' if hbs(c) else None,
          afc='=[bs_tca]+[bs_ppe]+[bs_gw]+[bs_int]+[bs_onca]')
    M.add(None, 'LIABILITIES AND EQUITY', 'label')
    M.add('bs_std', '  Current portion of long-term debt', 'line', 'num', hist=H('bs_current_debt'), afc='=[dsch_cur]')
    M.add('bs_ap', '  Accounts payable', 'line', 'num', hist=H('bs_ap'), afc='=[wc_cogs]*[dpo]/365')
    M.add('bs_accr', '  Accrued liabilities', 'line', 'num', hist=H('bs_accrued_liabilities'), afc='=[wc_sales]*[accr_pct]')
    M.add('bs_ocl', '  Other current liabilities (derived)', 'line', 'num', hist=H('bs_ocl'), afc=lambda c: '=' + Q2('bs_ocl') if c.year == 2026 else '=[bs_ocl@py]')
    M.add('bs_tcl', 'Total current liabilities', 'sub', 'num', hist=lambda c: '=N([bs_std])+[bs_ap]+[bs_accr]+N([bs_ocl])' if hbs(c) else None, afc='=N([bs_std])+[bs_ap]+[bs_accr]+N([bs_ocl])')
    M.add('bs_ltd', '  Long-term debt', 'line', 'num', hist=H('bs_long_term_debt'), afc='=[dsch_total]-[dsch_cur]')
    M.add('bs_oncl', '  Other liabilities (derived; incl. asbestos, pensions, lease liabilities, deferred taxes)', 'line', 'num', hist=H('bs_oncl'),
          afc=lambda c: '=' + Q2('bs_oncl') if c.year == 2026 else '=[bs_oncl@py]')
    M.add('bs_tl', 'Total liabilities', 'sub', 'num', hist=lambda c: '=[bs_tcl]+N([bs_ltd])+[bs_oncl]' if hbs(c) else None, afc='=[bs_tcl]+N([bs_ltd])+[bs_oncl]')
    M.add(None, 'Equity:', 'label')
    M.add('bs_mcps', '  6.50% Series A mandatory convertible preferred stock', 'line', 'num', hist=H('bs_mcps'),
          afc=lambda c: ('=' + Q2('bs_mcps')) if c.year == 2026 else ('=[bs_mcps@py]' if c.year < 2029 else 0),
          note='Converts into common stock ~Jun-2029 (reclassified to common stock & APIC).')
    M.add('bs_cs', '  Common stock & additional paid-in capital', 'line', 'num', hist=H('bs_common_stock_apic'),
          afc=lambda c: ('=' + Q2('bs_cs') + '+([cf_sbc]-[cf_sbc@$Q1/26]-[cf_sbc@$Q2/26])+([cf_bb]-[cf_bb@$Q1/26]-[cf_bb@$Q2/26])') if c.year == 2026
          else ('=[bs_cs@py]+[cf_sbc]+[cf_bb]' + ('+[bs_mcps@py]' if c.year == 2029 else '')), note='+ stock-based compensation − repurchases (+ MCPS conversion in 2029E).')
    M.add('bs_re', '  Retained earnings (net parent investment pre-spin; derived balance)', 'line', 'num', hist=H('bs_re'),
          afc=lambda c: ('=' + Q2('bs_re') + '+[is_ni@$Q3/26E]+[is_ni@$Q4/26E]-([is_mcps@$Q3/26E]+[is_mcps@$Q4/26E])-([dps@$Q3/26E]*[sh_b@$Q3/26E]+[dps@$Q4/26E]*[sh_b@$Q4/26E])') if c.year == 2026
          else '=[bs_re@py]+[is_ni]+[cf_div]')
    M.add('bs_aoci', '  Accumulated other comprehensive loss', 'line', 'num', hist=H('bs_aoci'), afc=lambda c: '=' + Q2('bs_aoci') if c.year == 2026 else '=[bs_aoci@py]')
    M.add('bs_le', "Total ESAB Corporation equity", 'sub', 'num', hist=lambda c: '=N([bs_mcps])+[bs_cs]+[bs_re]+[bs_aoci]' if hbs(c) else None,
          afc='=N([bs_mcps])+[bs_cs]+[bs_re]+[bs_aoci]')
    M.add('bs_nci', '  Noncontrolling interest', 'line', 'num', hist=H('bs_nci_equity'), afc=lambda c: ('=' + Q2('bs_nci') + '+[is_nci@$Q3/26E]+[is_nci@$Q4/26E]') if c.year == 2026 else '=[bs_nci@py]+[is_nci]')
    M.add('bs_te', 'Total equity', 'sub', 'num', hist=lambda c: '=[bs_le]+N([bs_nci])' if hbs(c) else None, afc='=[bs_le]+N([bs_nci])')
    M.add('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'num', hist=lambda c: '=[bs_tl]+[bs_te]' if hbs(c) else None, afc='=[bs_tl]+[bs_te]')
    M.add('chk_bs', 'BS tie-out check (TA − TL&E)', 'check', 'num', hist=lambda c: '=IF(ISNUMBER([bs_ta]),ROUND([bs_ta]-[bs_tle],1),"")' if hbs(c) else None, afc='=ROUND([bs_ta]-[bs_tle],1)')
    M.add('chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'num', hist=lambda c: '=IF(ISNUMBER([bs_ta_rep]),ROUND([bs_ta]-[bs_ta_rep],1),"")' if hbs(c) else None)
    M.add('bs_ta_rep', '  Memo: total assets as reported', 'pub', 'num', hist=H('bs_total_assets'), outline=2)
    M.add('chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0; restricted cash differences noted)', 'check', 'num',
          hist=lambda c: '=IF(AND(ISNUMBER([bs_cash]),ISNUMBER([cf_end])),ROUND([bs_cash]-[cf_end],1),"")' if hbs(c) and hcf(c) else None, afc='=ROUND([bs_cash]-[cf_end],1)')
    M.add('bs_asb_a', '  Memo: asbestos insurance assets (within other assets)', 'line', 'num', hist=H('bs_asbestos_insurance_assets'), outline=2)
    M.add('bs_asb_l', '  Memo: asbestos liabilities (current + long-term)', 'line', 'num', hist=H('bs_asbestos_liabilities_total'), outline=2)
    M.add('sh_out', '  Memo: common shares outstanding at period end (m)', 'line', 'num1', hist=H('bs_shares_outstanding_period_end'), afc='=[sh_end]')
    M.blank()

    # ================================================================ WORKING CAPITAL
    M.add(style='section', label='WORKING CAPITAL & CASH CONVERSION', note='WORKING CAPITAL — forecast drivers (blue = input)')
    M.add('wc_sales', '  Net sales — pro forma full-year basis (2026E incl. Eddyfi pre-closing)', 'line', 'num', hist='=[is_sales]',
          afc=lambda c: '=[is_sales]+[edd_rr]*151/365' if c.year == 2026 else '=[is_sales]',
          note='2026E adds Eddyfi sales for the pre-closing days so year-end working capital is sized on a full-year run-rate.')
    M.add('wc_cogs', '  Cost of sales — pro forma basis', 'line', 'num', hist='=[is_cogs]', afc=lambda c: '=[is_cogs]*[wc_sales]/[is_sales]')
    days = lambda c: '91.25' if c.is_q else '365'
    M.add('dso', '  DSO — receivables / net sales × 365', 'line', 'days', hist=lambda c: f'=IFERROR([bs_ar]/[wc_sales]*{days(c)},"n/a")' if hbs(c) else None, afc=CFG['dso'], cagr='avg',
          note=f'Forecast inputs (DSO {CFG["dso"]}d, inventory {CFG["dio"]}d, payables {CFG["dpo"]}d, accrued {CFG["accr_pct"]:.1%}): FY25 levels adjusted for Eddyfi (higher-margin, longer-cycle inspection business).')
    M.add('dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'days', hist=lambda c: f'=IFERROR([bs_inv]/[wc_cogs]*{days(c)},"n/a")' if hbs(c) else None, afc=CFG['dio'], cagr='avg')
    M.add('dpo', '  Payable days — payables / cost of sales × 365', 'line', 'days', hist=lambda c: f'=IFERROR([bs_ap]/[wc_cogs]*{days(c)},"n/a")' if hbs(c) else None, afc=CFG['dpo'], cagr='avg')
    M.add('accr_pct', '  Accrued liabilities % of net sales (annualised)', 'pctline', 'pct',
          hist=lambda c: f'=IFERROR([bs_accr]/([wc_sales]*{"4" if c.is_q else "1"}),"n/a")' if hbs(c) else None, afc=CFG['accr_pct'])
    M.add('nwc', '  Operating NWC (receivables + inventories − payables − accrued liabilities)', 'sub', 'num',
          hist=lambda c: '=IF(ISNUMBER([bs_ar]),[bs_ar]+[bs_inv]-[bs_ap]-[bs_accr],"n/a")' if hbs(c) else None, afc='=[bs_ar]+[bs_inv]-[bs_ap]-[bs_accr]')
    M.add('nwc_pct', '  NWC % of net sales (annualised)', 'pctline', 'pct', hist=lambda c: f'=IFERROR([nwc]/([wc_sales]*{"4" if c.is_q else "1"}),"n/a")' if hbs(c) else None,
          afc='=IFERROR([nwc]/[wc_sales],"n/a")', cagr='avg')
    M.add('dnwc', '  ΔNWC (y/y)', 'line', 'num', hist=lambda c: '=IFERROR([nwc]-[nwc@py],"")' if hbs(c) and lay.py(c) else None, afc='=IFERROR([nwc]-[nwc@py],"")')
    M.blank()

    # ================================================================ SCHEDULES
    M.add(style='section', label='BALANCE SHEET FORECAST SCHEDULES', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    M.add(style='block', label=E['ppa_title'], note=None)
    for k, lbl, v in E['ppa_rows']:
        M.add(f'ppa_{k}', '  ' + lbl, 'line', 'num', afc=lambda c, v=v: v if c.year == 2026 else None)
    M.add('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'num',
          afc=lambda c: E['ppa_check_formula'] if c.year == 2026 else None)
    M.add(style='block', label='Asset roll-forwards & non-cash items', note=None)
    M.add('dil', '  Dilutive securities (m shares)', 'line', 'num1', afc=lambda c: None if c.year == 2026 else '=[sh_d@$Q2/26]-[sh_b@$Q2/26]')
    M.add('px_app', '  Share-price appreciation % (buyback pricing)', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else 0.08)
    M.add('int_oth', '  Other non-operating expense in "interest expense and other, net" (pension, FX, other; USDm)', 'line', 'num',
          afc=lambda c: None if c.year == 2026 else CFG['int_oth'])
    M.add(style='block', label='Debt schedule (senior notes & term loan with scheduled maturities + revolver to a minimum cash balance)', note=None)
    M.add('dsch_total', '  Total debt (current + long-term)', 'sub', 'num', hist=lambda c: '=N([bs_std])+N([bs_ltd])' if hbs(c) else None,
          afc='=[dsch_notes]+[dsch_tl]+[dsch_fac]+[dsch_adj]', note=D['note_total'])
    M.add('dsch_adj', '  Other debt less unamortized deferred financing fees (carrying adjustment at 3-Jul-26, held)', 'line', 'num',
          afc=lambda c: f'=([bs_std@$Q2/26]+[bs_ltd@$Q2/26])-({D["notes_ye"]["2026"]}+{D["tl_q2_26"]}+{D["fac_q2_26"]})' if c.year == 2026 else '=[dsch_adj@py]')
    M.add('dsch_mat', '  Scheduled maturities / amortization (input, negative)', 'line', 'num', afc=lambda c: D['mat'][str(c.year)], note=D['note_mat'])
    M.add('dsch_refi_pct', '  % of scheduled maturities refinanced (input)', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else D['refi_pct'][str(c.year)])
    M.add('dsch_refi', '  Refinancing issuance', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=-[dsch_mat]*[dsch_refi_pct]')
    M.add('dsch_notes', '  Senior notes outstanding (face, year end)', 'line', 'num', afc=lambda c: D['notes_ye'][str(c.year)] if str(c.year) in D['notes_ye'] else '=[dsch_notes@py]+[dsch_refi]+[dsch_mat_notes]')
    M.add('dsch_mat_notes', '  of which: note maturities (negative)', 'line', 'num', afc=lambda c: D['mat_notes'][str(c.year)])
    M.add('dsch_tl', '  Term loan A outstanding (year end)', 'line', 'num', afc=lambda c: f'={D["tl_q2_26"]}+[dsch_mat]-[dsch_mat_notes]' if c.year == 2026 else '=[dsch_tl@py]+([dsch_mat]-[dsch_mat_notes])')
    M.add('dsch_cur', '  Current portion (next year\'s scheduled maturities)', 'line', 'num', afc=lambda c: '=-[dsch_mat@+1]' if c.year < 2030 else 0)
    M.add('dsch_pre', '  Cash before revolver (opening cash + CFO + CFI + non-revolver financing)', 'line', 'num',
          afc=lambda c: ('=[cf_beg]+[cfo]+[cfi]+[cf_div]+[cf_bb]+[cf_eq]+[cf_parent]+[cf_ofin]+[cf_fx]+[cf_dp]+[cf_dr]+([cf_rev@$Q1/26]+[cf_rev@$Q2/26])') if c.year == 2026
          else '=[cf_beg]+[cfo]+[cfi]+[cf_div]+[cf_bb]+[cf_eq]+[cf_parent]+[cf_ofin]+[cf_fx]+[cf_dp]+[cf_dr]')
    M.add('dsch_min', '  Minimum cash balance', 'line', 'num', afc=D['min_cash'])
    M.add('dsch_fac', '  Revolving credit facility outstanding (year end)', 'line', 'num',
          afc=lambda c: f'=MAX(0,{D["fac_q2_26"]}+[dsch_min]-[dsch_pre])' if c.year == 2026 else '=MAX(0,[dsch_fac@py]+[dsch_min]-[dsch_pre])',
          note='Drawn/repaid so that cash = minimum balance; surplus cash repays the revolver first (deleveraging).')
    M.add('dsch_net', '  Net issuance / (repayment)', 'line', 'num', hist=lambda c: '=IFERROR([dsch_total]-[dsch_total@py],"")' if hbs(c) and lay.py(c) else None, afc='=IFERROR([dsch_total]-[dsch_total@py],"")')
    M.add('r_notes', '  Interest rate on senior notes %', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else D['r_notes'], note=D['note_rates'])
    M.add('r_tl', '  Interest rate on term loan %', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else D['r_tl'])
    M.add('r_fac', '  Interest rate on revolver %', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else D['r_fac'])
    M.add('r_cash', '  Interest income yield on opening cash %', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else D['r_cash'])
    M.add(style='block', label='Leverage-targeted buybacks (repurchases plug to a minimum net debt / Adjusted EBITDA)', note=None)
    M.add('lev_min', '  Minimum net debt / Adjusted EBITDA (x) (scenario)', 'line', 'x2', afc=lambda c: None if c.year == 2026 else '=SCEN(LEV)')
    M.add('nd_pre', '  Net debt before buybacks (year end)', 'line', 'num',
          afc=lambda c: None if c.year == 2026 else '=[dsch_notes@py]+[dsch_tl@py]+[dsch_fac@py]-[bs_cash@py]-[cfo]-[cfi]-[cf_div]-[cf_eq]-[cf_parent]-[cf_ofin]-[cf_fx]')
    M.add('nd_target', '  Target minimum net debt = min. leverage × Adjusted EBITDA', 'line', 'num', afc=lambda c: None if c.year == 2026 else '=[lev_min]*[aebitda]')
    M.add('bb_plug', '  Share repurchases: plug to minimum leverage', 'sub', 'num', afc=lambda c: None if c.year == 2026 else '=MAX(0,[nd_target]-[nd_pre])')
    M.blank()

    # ================================================================ RATIOS
    A = lambda c: c.is_a and (c.is_fc or hbs(c))
    af = lambda f: (lambda c: f if A(c) else None)
    M.add(style='section', label='RATIO ANALYSIS', note='RETURNS — annual columns (NOPAT on adjusted EBITA)')
    M.add(style='block', label='DuPont decomposition of ROIC', note=None)
    M.add('r_aebita', 'Adjusted EBITA (adjusted EBITDA − depreciation & other amortization)', 'line', 'num', hist=lambda c: '=[aebita]' if A(c) and has('pub_adj_ebitda')(c) else None, fc=af('=[aebita]'))
    M.add('r_etr', 'Effective tax rate (actual)', 'pctline', 'pct', hist=af('=[is_etr]'), fc=af('=[is_etr]'))
    M.add('nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'sub', 'num', hist=af('=IFERROR([r_aebita]*(1-[r_etr]),"n/a")'), fc=af('=IFERROR([r_aebita]*(1-[r_etr]),"n/a")'))
    M.add('ic', 'Invested capital (IC) = Equity + Net debt', 'sub', 'num', hist=af('=IFERROR([r_te]+[r_nd],"n/a")'), fc=af('=IFERROR([r_te]+[r_nd],"n/a")'))
    M.add('r_te', '  Total equity incl. NCI & MCPS', 'line', 'num', hist=af('=[bs_te]'), fc=af('=[bs_te]'))
    M.add('r_nd', '  Net debt = Total debt − Cash', 'line', 'num', hist=af('=[dsch_total]-[bs_cash]'), fc=af('=[dsch_total]-[bs_cash]'))
    M.add('roic', 'ROIC = NOPAT / IC', 'total', 'pct', hist=af('=IFERROR([nopat]/[ic],"n/a")'), fc=af('=IFERROR([nopat]/[ic],"n/a")'), cagr='avg')
    M.add('roic_m', '  Margin = Adjusted EBITA / Net sales', 'pctline', 'pct', hist=af('=IFERROR([r_aebita]/[is_sales],"n/a")'), fc=af('=IFERROR([r_aebita]/[is_sales],"n/a")'))
    M.add('roic_t', '  Capital turnover = Net sales / IC', 'line', 'x2', hist=af('=IFERROR([is_sales]/[ic],"n/a")'), fc=af('=IFERROR([is_sales]/[ic],"n/a")'))
    M.add('roic_tb', '  Tax burden = (1 − effective tax rate)', 'pctline', 'pct', hist=af('=IFERROR(1-[r_etr],"n/a")'), fc=af('=IFERROR(1-[r_etr],"n/a")'))
    M.add('chk_roic', '  Check: Margin × Turnover × Tax burden = ROIC', 'check', 'pct', hist=af('=IFERROR(ROUND([roic_m]*[roic_t]*[roic_tb]-[roic],6),"n/a")'), fc=af('=IFERROR(ROUND([roic_m]*[roic_t]*[roic_tb]-[roic],6),"n/a")'))
    M.add(style='block', label='RONTA decomposition', note=None)
    M.add('ronta_nopat', 'NOPAT = Adjusted EBITA × (1 − tax rate)', 'line', 'num', hist=af('=[nopat]'), fc=af('=[nopat]'))
    M.add('ronta_ta', '  Total assets', 'line', 'num', hist=af('=[bs_ta]'), fc=af('=[bs_ta]'))
    M.add('ronta_gw', '  − Goodwill & acquired intangible assets', 'line', 'num', hist=af('=-([bs_gw]+[bs_int])'), fc=af('=-([bs_gw]+[bs_int])'))
    M.add('ronta_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'num', hist=af('=-([bs_tcl]-N([bs_std]))'), fc=af('=-([bs_tcl]-N([bs_std]))'))
    M.add('nta', '  = Net tangible assets', 'sub', 'num', hist=af('=[ronta_ta]+[ronta_gw]+[ronta_nibcl]'), fc=af('=[ronta_ta]+[ronta_gw]+[ronta_nibcl]'))
    M.add('ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', hist=af('=IFERROR([ronta_nopat]/[nta],"n/a")'), fc=af('=IFERROR([ronta_nopat]/[nta],"n/a")'), cagr='avg')
    M.add(style='block', label='Return on Equity (ROE)', note=None)
    M.add('roe_ni', 'Net income attributable to ESAB', 'line', 'num', hist=af('=[is_ni]'), fc=af('=[is_ni]'))
    M.add('roe_eq', 'ESAB Corporation equity', 'line', 'num', hist=af('=[bs_le]'), fc=af('=[bs_le]'))
    M.add('roe', 'ROE = Net income / Equity', 'total', 'pct', hist=af('=IFERROR([roe_ni]/[roe_eq],"n/a")'), fc=af('=IFERROR([roe_ni]/[roe_eq],"n/a")'), cagr='avg')
    M.add(style='block', label='Leverage', note=None)
    M.add('lev_nd', 'Net debt = Total debt − cash', 'line', 'num', hist=af('=[r_nd]'), fc=af('=[r_nd]'))
    M.add('lev_ebitda', 'Adjusted EBITDA (2026E pro forma for Eddyfi full year)', 'line', 'num', hist=af('=[aebitda]'),
          fc=lambda c: ('=[aebitda_pf]' if c.year == 2026 else '=[aebitda]') if A(c) else None)
    M.add('lev', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', hist=af('=IFERROR([lev_nd]/[lev_ebitda],"n/a")'), fc=af('=IFERROR([lev_nd]/[lev_ebitda],"n/a")'))
    M.blank()

    # ================================================================ VALUATION
    M.add(style='section', label='VALUATION', note=f'VALUATION — share price input ${CFG["share_price"]:.2f} ({CFG["share_price_note"]})')
    M.add('val_px', 'Share price ($) — current', 'val', 'eps', afc=lambda c: CFG['share_price'] if c.year == 2026 else '=[val_px@py]')
    M.add('val_sh', 'Diluted shares at period end (m; incl. MCPS if-converted shares)', 'line', 'num1',
          afc=lambda c: '=[sh_end]+([sh_d]-[sh_b])' + ('+[mcps_conv_sh]' if c.year < 2029 else ''))
    M.add('val_mcap', 'Market capitalisation (USDm)', 'line', 'num', afc='=IFERROR([val_px]*[val_sh],"n/a")')
    M.add('val_nd', 'Net debt (USDm)', 'line', 'num', afc='=[r_nd]')
    M.add('val_nci', 'Noncontrolling interest (USDm)', 'line', 'num', afc='=N([bs_nci])')
    M.add('val_asb', 'Asbestos liabilities net of insurance assets (USDm; debt-like)', 'line', 'num',
          afc=f'={CFG["asbestos_net"]}', note='Net asbestos exposure at 3-Jul-2026 held flat (cash costs run through discontinued operations).')
    M.add('val_ev', 'Enterprise value (USDm)', 'sub', 'num', afc='=IFERROR([val_mcap]+[val_nd]+[val_nci]+[val_asb],"n/a")')
    M.add(None, 'Multiples', 'label')
    M.add('val_evs', '  EV / Net sales', 'line', 'x2', afc='=IFERROR([val_ev]/[is_sales],"n/a")')
    M.add('val_evebitda', '  EV / Adjusted EBITDA (2026E pro forma)', 'line', 'x', afc='=IFERROR([val_ev]/[lev_ebitda],"n/a")')
    M.add('val_evebita', '  EV / Adjusted EBITA', 'line', 'x', afc='=IFERROR([val_ev]/[aebita],"n/a")')
    M.add('val_evic', '  EV / IC', 'line', 'x2', afc='=IFERROR([val_ev]/[ic],"n/a")')
    M.add('val_pe', '  P / E (GAAP diluted, continuing ops)', 'line', 'x', afc='=IFERROR([val_px]/[eps_c],"n/a")')
    M.add('val_pe_adj', '  P / E (core adjusted EPS)', 'line', 'x', afc='=IFERROR([val_px]/[core_adj_eps],"n/a")')
    M.add('val_fcfy', '  FCF yield', 'pctline', 'pct', afc='=IFERROR([fcf]/[val_mcap],"n/a")')
    M.add('val_dy', '  Dividend yield', 'pctline', 'pct', afc='=IFERROR([dps]/[val_px],"n/a")')
