"""LECO model — reconciliations, cash flow, balance sheet, schedules, ratios, valuation."""
from leco_model import H, has, yoy, ratio, S, CFG, lay

CATL_OI = [
    ('rat', '(+) Rationalization & asset impairment net charges'),
    ('txn', '(+) Acquisition transaction & integration costs (in SG&A)'),
    ('inv', '(+) Amortization of step-up in value of acquired inventories (in COGS)'),
    ('pen', '(+/−) Pension settlement charges (gains) in operating income (to 2017)'),
    ('ven', '(+) Venezuela-related charges (devaluation, remeasurement, statutory severance; 2010–2015)'),
    ('gain', '(−) Gains on asset disposals / bargain purchase gains, net (2006 Ireland facility gain in SG&A)'),
    ('oth', '(+/−) Other company items'),
]
CATL_EB = [
    ('rat', '(+) Rationalization & asset impairment net charges'),
    ('txn', '(+) Acquisition transaction & integration costs'),
    ('inv', '(+) Amortization of step-up in value of acquired inventories'),
    ('pen', '(+/−) Pension settlement / termination net charges (gains) — other income from 2018'),
    ('ven', '(+) Venezuela-related charges (incl. 2015 deconsolidation)'),
    ('gain', '(−) Gains on asset disposals, bargain purchase & change-in-control gains, net'),
    ('oth', '(+/−) Other company items / definitional differences (balance to the published special-items total)'),
]


def build_rest(M):
    D = CFG['debt']
    # ------------------------------------------------------------------ RECONCILIATION A
    M.add(style='section', label='RECONCILIATION A: OPERATING INCOME → ADJUSTED OPERATING INCOME (company definition)',
          note='ADJUSTED OPERATING INCOME — per Lincoln Electric earnings-release reconciliations ("Non-GAAP Financial Measures"); special items as defined by the company in each period')
    M.add('rA_oi', 'Operating income (GAAP)', 'sub', 'num', hist='=[is_oi]', fc='=[is_oi]')
    for c, lbl in CATL_OI:
        if c == 'rat':
            fc = '=[is_rat]'
        elif c == 'txn':
            fc = None
        else:
            fc = 0
        kw = {}
        if c == 'txn':
            kw = dict(qfc='=([oi_txn@$Q1/26]+[oi_txn@$Q2/26])/2',
                      afc=lambda col: '=SUMQ[oi_txn]' if col.year == 2026 else '=MAX(2,[ma_spend]*0.01)',
                      note='Q3/Q4-26E: 1H/26 run-rate. 2027E+: ~1% of acquisition spend (min. $2m p.a.).')
        elif c == 'rat':
            kw = dict(fc=fc, note='Forecast = rationalization line of the income statement.')
        else:
            kw = dict(fc=fc)
        M.add(f'oi_{c}', '  ' + lbl, 'line', 'num', hist=H(f'oi_{c}'), outline=0, **kw)
    M.add('oi_sp', '  Total special items in operating income', 'sub', 'num',
          hist=lambda c: ('=' + '+'.join(f'N([oi_{k}])' for k, _ in CATL_OI)) if c.label in S.get('oi_rat', {}) else None,
          fc='=' + '+'.join(f'N([oi_{k}])' for k, _ in CATL_OI))
    M.add('adj_oi', '  = Adjusted operating income (model bridge)', 'total', 'num',
          hist=lambda c: '=[rA_oi]+[oi_sp]' if c.label in S.get('oi_rat', {}) else None, fc='=[rA_oi]+[oi_sp]', cagr='growth',
          note='Historical bridge rebuilt from the company reconciliation in each period; forecast = operating income + rationalization + transaction costs.')
    M.add('adj_oi_m', '  Adjusted operating income margin %', 'pctline', 'pct', hist=ratio('adj_oi', 'is_sales', has('oi_rat')),
          fc='=IFERROR([adj_oi]/[is_sales],"")', cagr='avg')
    M.add('pub_adj_oi', '  Company-published adjusted operating income', 'pub', 'num', hist=H('pub_adj_oi'),
          comment='Source: earnings releases (Form 8-K Ex. 99.1), "Adjusted operating income" reconciliation. 2006–2008: not tabulated by the company (only described in release text) → n/p.')
    M.add('chk_adj_oi', '  Check: model bridge vs company-published (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([pub_adj_oi]),ROUND([adj_oi]-[pub_adj_oi],1),"n/p")' if c.label in S.get('oi_rat', {}) or c.label in S.get('pub_adj_oi', {}) else None)
    M.add('nonop_adj', '  Memo: adjusted non-operating income (adjusted EBIT − adjusted operating income)', 'line', 'num',
          hist=lambda c: '=IF(AND(ISNUMBER([aebit]),ISNUMBER([adj_oi])),[aebit]-[adj_oi],"")' if c.label in S.get('oi_rat', {}) else None,
          fc='=[is_eq]+[is_oth]', outline=2,
          note='Other income + equity earnings excluding special items in non-operating lines (pension settlements, disposal gains).')
    M.blank()

    # ------------------------------------------------------------------ RECONCILIATION B
    M.add(style='section', label='RECONCILIATION B: NET INCOME → EBIT → ADJUSTED EBIT → ADJUSTED EBITDA',
          note="ADJUSTED EBIT — LECO's segment profit measure (\"EBIT, as adjusted\" to 2019, \"Adjusted EBIT\" from 2020); EBIT = operating income + other income (+ equity earnings while reported)")
    heb = has('eb_rat')
    M.add('rB_ni', 'Net income attributable to Lincoln Electric (GAAP)', 'sub', 'num', hist='=[is_ni]', fc='=[is_ni]')
    M.add('rB_nci', '  (+) Net income attributable to noncontrolling interests', 'line', 'num', hist='=[is_nci]', fc='=[is_nci]')
    M.add('rB_tax', '  (+) Income taxes', 'line', 'num', hist='=[is_tax]', fc='=[is_tax]')
    M.add('rB_int', '  (+) Interest expense, net of interest income', 'line', 'num', hist='=[is_int_net]', fc='=[is_int_net]')
    M.add('ebit', '  = EBIT (operating income + equity earnings + other income)', 'total', 'num',
          hist='=[rB_ni]+[rB_nci]+[rB_tax]+[rB_int]', fc='=[rB_ni]+[rB_nci]+[rB_tax]+[rB_int]', cagr='growth')
    M.add('pub_ebit', '  Company-published EBIT (consolidated segment table)', 'pub', 'num', hist=H('pub_ebit'))
    M.add('chk_ebit', '  Check: model EBIT vs company-published (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([pub_ebit]),ROUND([ebit]-[pub_ebit],1),"n/p")')
    for c, lbl in CATL_EB:
        M.add(f'eb_{c}', '  ' + lbl, 'line', 'num', hist=H(f'eb_{c}'), fc=f'=[oi_{c}]',
              note=('Forecast = special items in operating income (no non-operating special items assumed).' if c == 'rat' else None))
    M.add('sp_total', '  Total special items (pre-tax)', 'sub', 'num',
          hist=lambda c: ('=' + '+'.join(f'N([eb_{k}])' for k, _ in CATL_EB)) if heb(c) else None,
          fc='=' + '+'.join(f'N([eb_{k}])' for k, _ in CATL_EB))
    M.add('aebit', '  = Adjusted EBIT (model bridge)', 'total', 'num',
          hist=lambda c: '=[ebit]+[sp_total]' if heb(c) else '=[ebit]', fc='=[ebit]+[sp_total]', cagr='growth',
          note='Historical bridge rebuilt from the company special-items disclosure; forecast = segment-build adjusted EBIT (check row in the Group block).')
    M.add('aebit_m', '  Adjusted EBIT margin %', 'pctline', 'pct', hist=ratio('aebit', 'is_sales'), fc='=IFERROR([aebit]/[is_sales],"")', cagr='avg')
    M.add('pub_adj_ebit', '  Company-published adjusted EBIT ("EBIT, as adjusted" to 2019)', 'pub', 'num', hist=H('pub_adj_ebit'),
          comment='Source: earnings-release segment table (Consolidated column) / adjusted EBIT reconciliation (2020+). 2006–2008: segment profit after special items per the 10-K segment note / Q4-08 release.')
    M.add('chk_aebit', '  Check: model bridge vs company-published (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([pub_adj_ebit]),ROUND([aebit]-[pub_adj_ebit],1),"n/p")')
    M.add('def_eb', '  Definition basis (company EBIT definition in force)', 'def', 'gen',
          hist={'2006': 'Segment profit = income before interest & taxes', 'Q1/13': 'EBIT = OI + equity earnings + other income', 'Q1/20': 'Adjusted EBIT (renamed)', 'Q1/23': 'EBIT = OI + other income (interest net)'})
    M.add(None, 'To adjusted EBITDA:', 'label')
    M.add('rB_da', '  (+) Depreciation & amortization', 'line', 'num', hist='=[da]', fc='=[da]')
    M.add('aebitda', '  = Adjusted EBITDA (model; LECO does not publish an adjusted EBITDA measure)', 'total', 'num',
          hist='=[aebit]+[rB_da]', fc='=[aebit]+[rB_da]', cagr='growth',
          note='Model measure for leverage and EV/EBITDA; LECO reports EBITDA only in its credit-covenant definitions.')
    M.add('aebitda_m', '  Adjusted EBITDA margin %', 'pctline', 'pct', hist=ratio('aebitda', 'is_sales'), fc='=IFERROR([aebitda]/[is_sales],"")', cagr='avg')
    M.add('ebitda', '  Memo: EBITDA (GAAP EBIT + D&A)', 'line', 'num', hist='=[ebit]+[rB_da]', fc='=[ebit]+[rB_da]', outline=2)
    M.blank()

    # ------------------------------------------------------------------ RECONCILIATION C
    M.add(style='section', label='RECONCILIATION C: GAAP NET INCOME / DILUTED EPS → ADJUSTED NET INCOME / ADJUSTED EPS',
          note='ADJUSTED EPS — LECO publishes adjusted net income and adjusted diluted EPS every quarter; special items pre-tax per bridge B, tax effect as published (derived where the company disclosed after-tax items only)')
    hni = has('pub_adj_ni')
    M.add('rC_ni', 'Net income attributable to Lincoln Electric (GAAP)', 'sub', 'num', hist='=[is_ni]', fc='=[is_ni]')
    M.add('rC_sp', '  (+) Special items, pre-tax (as in the adjusted EBIT bridge)', 'line', 'num',
          hist=lambda c: '=[sp_total]' if heb(c) else None, fc='=[sp_total]')
    M.add('rC_taxeff', '  (−) Tax effect of special items', 'line', 'num', hist=H('eps_taxeff'), fc='=-[rC_sp]*[rC_rate]',
          comment='As published ("Tax effect of special items"). Periods in which LECO disclosed special items only after tax (2006–Q1/18 releases) → tax effect derived as published adjusted net income − net income − pre-tax special items − discrete tax items − NCI share.')
    M.add('rC_rate', '  Tax rate applied to special items', 'pctline', 'pct',
          hist=lambda c: '=IF(ABS(N([rC_sp]))>1,IFERROR(-[rC_taxeff]/[rC_sp],""),"n/m")' if heb(c) and c.label in S.get('eps_taxeff', {}) else None,
          fc=CFG['etr'], note=f'Forecast: {CFG["etr"]:.1%} (blended statutory rate on rationalization and transaction costs).')
    M.add('rC_taxonly', '  (+/−) Discrete tax items (US tax reform, audit settlements, valuation-allowance changes)', 'line', 'num', hist=H('eps_taxonly'), fc=0)
    M.add('rC_nci', '  (+/−) Noncontrolling-interest share of special items', 'line', 'num', hist=H('eps_nci'), fc=0)
    M.add('adj_ni', '  = Adjusted net income (model)', 'total', 'num',
          hist=lambda c: '=[rC_ni]+N([rC_sp])+N([rC_taxeff])+N([rC_taxonly])+N([rC_nci])' if hni(c) else None,
          fc='=[rC_ni]+N([rC_sp])+N([rC_taxeff])+N([rC_taxonly])+N([rC_nci])', cagr='growth')
    M.add('pub_adj_ni', '  Company-published adjusted net income', 'pub', 'num', hist=H('pub_adj_ni'))
    M.add('chk_adj_ni', '  Check: model vs company-published adjusted net income (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([pub_adj_ni]),ROUND([adj_ni]-[pub_adj_ni],1),"n/p")' if hni(c) else None)
    M.add('rC_sh', '  Weighted-average diluted shares (m)', 'line', 'num1', hist='=[sh_d]', fc='=[sh_d]')
    M.add('adj_eps', 'Adjusted diluted EPS ($) (model)', 'total', 'eps',
          hist=lambda c: '=IF(AND(ISNUMBER([adj_ni]),ISNUMBER([rC_sh])),IFERROR([adj_ni]/[rC_sh],""),"")' if hni(c) else None,
          qfc='=IFERROR([adj_ni]/[rC_sh],"")',
          afc=lambda c: '=SUMQ[adj_eps]' if c.year == 2026 else '=IFERROR([adj_ni]/[rC_sh],"")', cagr='growth',
          note='2026E = sum of quarters (company convention).')
    M.add('pub_adj_eps', '  Company-published adjusted diluted EPS ($)', 'pub', 'eps', hist=H('pub_adj_eps'),
          comment='Source: earnings releases. 2006–2010 restated for the 2-for-1 split (May-2011).')
    M.add('chk_adj_eps', '  Check: model vs company-published adjusted EPS (should be 0.00; ±0.01–0.02 share rounding)', 'check', 'eps',
          hist=lambda c: '=IF(ISNUMBER([pub_adj_eps]),ROUND([adj_eps]-[pub_adj_eps],2),"n/p")' if hni(c) else None)
    M.add('pub_sp_ps', '  Memo: company-published special items per share ($)', 'pub', 'eps', hist=H('pub_sp_ps'), outline=2)
    M.add('def_eps', '  Definition basis (company adjusted EPS)', 'def', 'gen',
          hist={'2006': 'After-tax special items (tax effect derived)', 'Q2/18': 'Pre-tax items + published tax effect'})
    M.blank()

    # ------------------------------------------------------------------ GROWTH & MARGINS
    M.add(style='section', label='GROWTH & MARGINS', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    M.add('gm_sales', '  Net sales y/y %', 'pct', 'pct', hist=yoy('is_sales'), fc='=IFERROR([is_sales]/[is_sales@py]-1,"")', cagr='avg')
    M.add('gm_org', '  Organic sales growth % (volume + price)', 'pctline', 'pct', hist=lambda c: '=[cons_org]' if c.label in S.get('sc_CONS_volume_pct', {}) else None, fc='=[cons_org]', cagr='avg')
    M.add('gm_vol', '  Volume % (company)', 'pctline', 'pct', hist=lambda c: '=[cons_volume]' if c.label in S.get('sc_CONS_volume_pct', {}) else None, fc='=[cons_volume]')
    M.add('gm_price', '  Price % (company)', 'pctline', 'pct', hist=lambda c: '=[cons_price]' if c.label in S.get('sc_CONS_volume_pct', {}) else None, fc='=[cons_price]')
    M.add('gm_aoi_g', '  Adjusted operating income y/y %', 'pct', 'pct', hist=yoy('adj_oi', has('oi_rat')), fc='=IFERROR([adj_oi]/[adj_oi@py]-1,"")')
    M.add('gm_aebit_g', '  Adjusted EBIT y/y %', 'pct', 'pct', hist=yoy('aebit'), fc='=IFERROR([aebit]/[aebit@py]-1,"")')
    M.add('gm_ni_g', '  Net income attributable y/y %', 'pct', 'pct', hist=yoy('is_ni'), fc='=IFERROR([is_ni]/[is_ni@py]-1,"")')
    M.add('gm_eps_g', '  Adjusted EPS y/y %', 'pct', 'pct', hist=yoy('adj_eps', hni), fc='=IFERROR([adj_eps]/[adj_eps@py]-1,"")')
    M.add('gm_gm', '  Gross margin %', 'pctline', 'pct', hist='=[is_gm]', fc='=[is_gm]')
    M.add('gm_aoi_m', '  Adjusted operating income margin %', 'pctline', 'pct', hist=lambda c: '=[adj_oi_m]' if c.label in S.get('oi_rat', {}) else None, fc='=[adj_oi_m]')
    M.add('gm_aebit_m', '  Adjusted EBIT margin %', 'pctline', 'pct', hist='=[aebit_m]', fc='=[aebit_m]')
    M.add('gm_aebitda_m', '  Adjusted EBITDA margin %', 'pctline', 'pct', hist='=[aebitda_m]', fc='=[aebitda_m]')
    M.add('gm_inc', '  Incremental adjusted EBIT margin (Δ adj. EBIT / Δ net sales)', 'pctline', 'pct',
          hist=lambda c: '=IFERROR(([aebit]-[aebit@py])/([is_sales]-[is_sales@py]),"")' if lay.py(c) else None,
          fc='=IFERROR(([aebit]-[aebit@py])/([is_sales]-[is_sales@py]),"")')
    M.add('gm_op_m', '  Operating margin (GAAP) %', 'pctline', 'pct', hist=ratio('is_oi', 'is_sales'), fc='=IFERROR([is_oi]/[is_sales],"")', cagr='avg')
    M.add('gm_net_m', '  Net margin %', 'pctline', 'pct', hist=ratio('is_ni', 'is_sales'), fc='=IFERROR([is_ni]/[is_sales],"")', cagr='avg')
    M.add('gm_sga', '  SG&A % of net sales', 'pctline', 'pct', hist='=[sga_pct]', fc='=[sga_pct]')
    M.blank()

    # ------------------------------------------------------------------ CASH FLOW
    M.add(style='section', label='CONSOLIDATED STATEMENT OF CASH FLOWS',
          note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    hcf = has('cf_cfo')
    H1 = lambda k: f'([{k}@$Q1/26]+[{k}@$Q2/26])'
    M.add('cf_ni', 'Net income (incl. noncontrolling interests)', 'line', 'num', hist=H('cf_net_income_incl_nci'), afc='=[is_nici]',
          comment='Source: Forms 10-K / 10-Q statements of cash flows (year-to-date); discrete quarters derived (Q2 = 6M − 3M, Q3 = 9M − 6M, Q4 = FY − 9M).')
    M.add(None, 'Adjustments:', 'label')
    M.add('cf_da', '  Depreciation & amortization', 'line', 'num', hist=H('cf_da'), afc='=[da]')
    M.add('cf_sbc', '  Stock-based compensation', 'line', 'num', hist=H('cf_sbc'), afc='=[is_sbc]')
    M.add('cf_ratg', '  Non-cash rationalization & impairment charges, (gains) losses on disposals', 'line', 'num', hist=H('cf_ratg'),
          afc=lambda c: '=' + H1('cf_ratg') if c.year == 2026 else 0)
    M.add('cf_def', '  Deferred income taxes', 'line', 'num', hist=H('cf_deferred_taxes'), afc=lambda c: '=' + H1('cf_def') if c.year == 2026 else 0,
          note='2026E = 1H/26 actual; none forecast thereafter.')
    M.add('cf_oth', '  Other non-cash items, net (derived; incl. pension contributions, equity earnings)', 'line', 'num', hist=H('cf_oth'),
          afc=lambda c: '=' + H1('cf_oth') if c.year == 2026 else 0)
    M.add('cf_wc', '  Changes in operating assets & liabilities, net', 'line', 'num', hist=H('cf_wc'),
          afc=lambda c: ('=' + H1('cf_wc') + '-([bs_ar]-[bs_ar@$Q2/26])-([bs_inv]-[bs_inv@$Q2/26])+([bs_ap]-[bs_ap@$Q2/26])+([bs_accr]-[bs_accr@$Q2/26])') if c.year == 2026
          else '=-([bs_ar]-[bs_ar@py])-([bs_inv]-[bs_inv@py])+([bs_ap]-[bs_ap@py])+([bs_accr]-[bs_accr@py])',
          note='Linked to the balance sheet: −Δ(receivables, inventories) + Δ(payables, accrued compensation); 2026E = 1H actual + 2H change vs 30-Jun-26.')
    M.add('cfo', 'Net cash provided by operating activities', 'sub', 'num', hist=H('cf_cfo'), afc='=SUM([cf_ni]:[cf_wc])'.replace('[cf_ni]:[cf_wc]', '{c}%d:{c}%d' % (M.rows['cf_ni'], M.rows['cf_wc'])), cagr='growth')
    M.add('capex', 'Capital expenditures', 'line', 'num', hist=H('cf_capex'),
          afc=lambda c: '=-SCEN(CAPEX26)' if c.year == 2026 else '=-[is_sales]*[capex_pct]',
          note='2026E: FY26 capex assumption $110–130m (scenario end-point). 2027E+: net sales × capex %.')
    M.add('cf_acq', 'Acquisition of businesses, net of cash acquired', 'line', 'num', hist=H('cf_acquisitions'),
          afc=lambda c: '=' + H1('cf_acq') if c.year == 2026 else '=-[ma_spend]', note='2026E: 1H/26 actual (Alloy Steel true-up); 2027E+: M&A lever.')
    M.add('cf_proc', 'Proceeds from sale of property, plant & equipment / businesses', 'line', 'num', hist=H('cf_proceeds'),
          afc=lambda c: '=' + H1('cf_proc') if c.year == 2026 else 0)
    M.add('cf_oinv', 'Other investing activities, net (derived)', 'line', 'num', hist=H('cf_oinv'), afc=lambda c: '=' + H1('cf_oinv') if c.year == 2026 else 0)
    M.add('cfi', 'Net cash used by investing activities', 'sub', 'num', hist=H('cf_cfi'), afc='=[capex]+[cf_acq]+[cf_proc]+[cf_oinv]')
    M.add('cf_std', 'Short-term borrowings, net (revolver / amounts due banks)', 'line', 'num', hist=H('cf_st_borrowings_net'),
          afc=lambda c: ('=' + H1('cf_std') + f'+([dsch_fac]-{D["fac_q2_26"]})') if c.year == 2026 else '=[dsch_fac]-[dsch_fac@py]',
          note='Forecast = change in prepayable facilities per the debt schedule.')
    M.add('cf_ltb', 'Proceeds from long-term borrowings', 'line', 'num', hist=H('cf_lt_borrowings'),
          afc=lambda c: '=' + H1('cf_ltb') if c.year == 2026 else '=[dsch_refi]')
    M.add('cf_ltr', 'Payments on long-term borrowings', 'line', 'num', hist=H('cf_lt_repayments'),
          afc=lambda c: '=' + H1('cf_ltr') + '+[dsch_mat]' if c.year == 2026 else '=[dsch_mat]')
    M.add('cf_div', 'Cash dividends paid to shareholders', 'line', 'num', hist=H('cf_dividends_paid'),
          afc=lambda c: '=' + H1('cf_div') + '-([dps@$Q3/26E]*[sh_b@$Q3/26E]+[dps@$Q4/26E]*[sh_b@$Q4/26E])' if c.year == 2026 else '=-[dps]*[sh_beg]',
          note='2027E+: dividends per share × beginning shares outstanding (avoids circularity with buybacks).')
    M.add('cf_bb', 'Purchase of shares for treasury', 'line', 'num', hist=H('cf_buybacks'),
          afc=lambda c: '=' + H1('cf_bb') + '-SCEN(BB26)' if c.year == 2026 else '=-[bb_plug]',
          note='2026E = 1H/26 actual + 2H scenario amount; 2027E+ = leverage plug (surplus cash returned once net debt / adj. EBITDA reaches the scenario floor).')
    M.add('cf_opt', 'Proceeds from exercise of stock options', 'line', 'num', hist=H('cf_options_proceeds'),
          afc=lambda c: '=' + H1('cf_opt') if c.year == 2026 else 0)
    M.add('cf_ofin', 'Other financing activities, net (derived; incl. NCI transactions)', 'line', 'num', hist=H('cf_ofin'),
          afc=lambda c: '=' + H1('cf_ofin') if c.year == 2026 else 0)
    M.add('cff', 'Net cash used by financing activities', 'sub', 'num', hist=H('cf_cff'),
          afc='=[cf_std]+[cf_ltb]+[cf_ltr]+[cf_div]+[cf_bb]+[cf_opt]+[cf_ofin]')
    M.add('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'num', hist=H('cf_fx_effect'), afc=lambda c: '=' + H1('cf_fx') if c.year == 2026 else 0)
    M.add('cf_net', 'Net increase (decrease) in cash', 'line', 'num', hist=H('cf_net_change_cash'), afc='=[cfo]+[cfi]+[cff]+[cf_fx]')
    M.add('cf_beg', 'Cash — beginning of period', 'line', 'num', hist=H('cf_cash_begin'), afc='=[cf_end@py]')
    M.add('cf_end', 'Cash — end of period', 'sub', 'num', hist=H('cf_cash_end'), afc='=[cf_beg]+[cf_net]')
    M.add('chk_cf1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([cfo]),ROUND([cfo]+[cfi]+[cff]+[cf_fx]-[cf_net],1),"")' if hcf(c) else None,
          afc='=ROUND([cfo]+[cfi]+[cff]+[cf_fx]-[cf_net],1)')
    M.add('chk_cf2', '  Check: beginning cash + change = ending cash (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([cf_end]),ROUND([cf_beg]+[cf_net]-[cf_end],1),"")' if hcf(c) else None,
          afc='=ROUND([cf_beg]+[cf_net]-[cf_end],1)')
    M.add(None, '(Memo)', 'label')
    M.add('fcf', 'Free cash flow (operating cash flow − capital expenditures; company definition)', 'total', 'num',
          hist=lambda c: '=[cfo]+[capex]' if hcf(c) else None, afc='=[cfo]+[capex]', cagr='growth',
          note='LECO defines free cash flow as CFO − capital expenditures and cash conversion as FCF / adjusted net income.')
    M.add('fcf_g', '  FCF y/y %', 'pct', 'pct', hist=yoy('fcf', hcf), afc='=IFERROR([fcf]/[fcf@py]-1,"")')
    M.add('fcf_pct', '  FCF % of net sales', 'pctline', 'pct', hist=lambda c: '=IFERROR([fcf]/[is_sales],"")' if hcf(c) else None, afc='=IFERROR([fcf]/[is_sales],"")', cagr='avg')
    M.add('cash_conv', '  Cash conversion — FCF / adjusted net income % (company definition)', 'pctline', 'pct',
          hist=lambda c: '=IFERROR([fcf]/[adj_ni],"")' if hcf(c) and hni(c) else None, afc='=IFERROR([fcf]/[adj_ni],"")', cagr='avg')
    M.add('pub_cashconv', '  Memo: company-published cash conversion %', 'pub', 'pct', hist=H('pub_cashconv'), outline=2)
    M.add('conv_tgt', '  Memo: FY26 cash conversion target (company ~100%)', 'pctline', 'pct', afc=lambda c: '=SCEN(CONV26)' if c.year == 2026 else None,
          note='Company targets ~100% cash conversion. Model 2026E sits below it because receivables / inventories are held at FY25 days on ~11% sales growth; lower the inventory-days input to close the gap.')
    M.add('fcf_ps', '  FCF per diluted share ($)', 'line', 'eps', hist=lambda c: '=IFERROR([fcf]/[sh_d],"")' if hcf(c) else None, afc='=IFERROR([fcf]/[sh_d],"")')
    M.add(None, 'Capex ratios', 'label')
    M.add('capex_pct', '  Capex % of net sales', 'pctline', 'pct', hist=lambda c: '=IFERROR(-[capex]/[is_sales],"")' if hcf(c) else None,
          afc=lambda c: '=IFERROR(-[capex]/[is_sales],"")' if c.year == 2026 else CFG['capex_pct'], cagr='avg',
          note=f'2027E+: {CFG["capex_pct"]:.1%} input (FY26 assumption ~2.5%; FY25 3.0% incl. capacity projects; 10-yr avg ~2.5%).')
    M.add('capex_da', '  Capex / D&A (x)', 'line', 'x2', hist=lambda c: '=IFERROR(-[capex]/[da],"")' if hcf(c) else None, afc='=IFERROR(-[capex]/[da],"")')
    M.blank()

    # ------------------------------------------------------------------ BUYBACKS
    M.add(style='section', label='SHARE BUYBACK SCHEDULE', note='SHARES — 2026E = 2H/26 only (1H/26 repurchases already in the Q1/Q2 share counts)')
    M.add('bb_px', '  Avg buyback price ($)', 'line', 'eps', afc=lambda c: '=[val_px]' if c.year == 2026 else '=[bb_px@py]*(1+[px_app])',
          note='2026E = current share price (valuation input); appreciates with the share-price input.')
    M.add('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'num', afc=lambda c: '=SCEN(BB26)' if c.year == 2026 else '=-[cf_bb]',
          note='2026E row = 2H/26 buyback only.')
    M.add('bb_sh', '  Implied shares repurchased (m)', 'line', 'num1', afc='=IFERROR([bb_cash]/[bb_px],0)')
    M.add('bb_iss', '  Shares issued under equity plans (m)', 'line', 'num1', afc=lambda c: 0.1 if c.year == 2026 else 0.3,
          note='~0.3m shares p.a. issued on option exercises / RSU vesting (2023–25 avg).')
    M.add('sh_beg', '  Beginning shares outstanding (m)', 'line', 'num1', afc=lambda c: '=[sh_out@$Q2/26]' if c.year == 2026 else '=[sh_end@py]',
          note='2026E begins from shares outstanding at 30-Jun-2026 (54.51m, Q2-26 10-Q cover).')
    M.add('sh_end', '  Ending shares outstanding (m)', 'sub', 'num1', afc='=[sh_beg]-[bb_sh]+[bb_iss]')
    M.add('bb_pct', '  % of shares repurchased', 'pctline', 'pct', afc='=IFERROR([bb_sh]/[sh_beg],"")')
    M.add('bb_cum', '  Memo: cumulative shares repurchased since 2H/26 (m)', 'line', 'num1', afc=lambda c: '=[bb_sh]' if c.year == 2026 else '=[bb_cum@py]+[bb_sh]')
    M.blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    M.add(style='section', label='CONSOLIDATED BALANCE SHEET',
          note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet (Q2/26) + 2H flows; 2027E+ from prior year end')
    hbs = has('bs_ta_rep')
    Q2 = lambda k: f'[{k}@$Q2/26]'
    M.add(None, 'ASSETS', 'label')
    M.add('bs_cash', '  Cash and cash equivalents', 'line', 'num', hist=H('bs_cash'), afc='=[cf_end]',
          comment='Source: Forms 10-K / 10-Q balance sheets (10-Q balance sheets are condensed: goodwill / intangibles / accrued compensation not always shown separately → captured in the "other" lines).')
    M.add('bs_ar', '  Accounts receivable, net', 'line', 'num', hist=H('bs_ar'), afc='=[wc_sales]*[dso]/365', note='Receivables = net sales × DSO / 365.')
    M.add('bs_inv', '  Inventories', 'line', 'num', hist=H('bs_inv'), afc='=[wc_cogs]*[dio]/365')
    M.add('bs_oca', '  Other current assets (derived; incl. prepaid, assets held for sale)', 'line', 'num', hist=H('bs_oca'),
          afc=lambda c: '=' + Q2('bs_oca') if c.year == 2026 else '=[bs_oca@py]')
    M.add('bs_tca', 'Total current assets', 'sub', 'num', hist=lambda c: '=[bs_cash]+[bs_ar]+[bs_inv]+[bs_oca]' if hbs(c) else None,
          afc='=[bs_cash]+[bs_ar]+[bs_inv]+[bs_oca]')
    M.add('bs_ppe', '  Property, plant & equipment, net', 'line', 'num', hist=H('bs_ppe'),
          afc=lambda c: ('=' + Q2('bs_ppe') + '-([capex]-[capex@$Q1/26]-[capex@$Q2/26])-([da@$Q3/26E]+[da@$Q4/26E]-[amort]/2)') if c.year == 2026
          else '=[bs_ppe@py]-[capex]-([da]-[amort]-[ma_amort])+[ma_spend]*[ma_ppe_pct]',
          note='PP&E roll-forward: prior + capex − depreciation (total D&A less intangible amortization) + acquired PP&E (M&A lever).')
    M.add('bs_gw', '  Goodwill', 'line', 'num', hist=H('bs_gw'),
          afc=lambda c: '=' + Q2('bs_gw') if c.year == 2026 else '=[bs_gw@py]+[ma_spend]*(1-[ma_ppe_pct]-[ma_int_pct])')
    M.add('bs_onca', '  Other noncurrent assets (derived; incl. intangibles, ROU assets, deferred taxes, pension)', 'line', 'num', hist=H('bs_onca'),
          afc=lambda c: ('=' + Q2('bs_onca') + '-[amort]/2') if c.year == 2026 else '=[bs_onca@py]-[amort]-[ma_amort]+[ma_spend]*[ma_int_pct]',
          note='Intangibles roll-forward inside other assets: − amortization (legacy per the FY2025 10-K schedule) + acquired intangibles (M&A lever).')
    M.add('bs_ta', 'TOTAL ASSETS', 'total', 'num', hist=lambda c: '=[bs_tca]+[bs_ppe]+N([bs_gw])+[bs_onca]' if hbs(c) else None,
          afc='=[bs_tca]+[bs_ppe]+N([bs_gw])+[bs_onca]')
    M.add(None, 'LIABILITIES AND EQUITY', 'label')
    M.add('bs_std', '  Short-term debt & current portion of long-term debt', 'line', 'num', hist=H('bs_std'), afc='=[dsch_fac]+[dsch_cur]')
    M.add('bs_ap', '  Trade accounts payable', 'line', 'num', hist=H('bs_ap'), afc='=[wc_cogs]*[dpo]/365')
    M.add('bs_accr', '  Accrued employee compensation & benefits', 'line', 'num', hist=H('bs_accr'), afc='=[wc_sales]*[accr_pct]')
    M.add('bs_ocl', '  Other current liabilities (derived; incl. accrued taxes, contract liabilities, current lease)', 'line', 'num', hist=H('bs_ocl'),
          afc=lambda c: '=' + Q2('bs_ocl') if c.year == 2026 else '=[bs_ocl@py]')
    M.add('bs_tcl', 'Total current liabilities', 'sub', 'num', hist=lambda c: '=N([bs_std])+[bs_ap]+N([bs_accr])+[bs_ocl]' if hbs(c) else None,
          afc='=N([bs_std])+[bs_ap]+N([bs_accr])+[bs_ocl]')
    M.add('bs_ltd', '  Long-term debt, less current portion', 'line', 'num', hist=H('bs_ltd'), afc='=[dsch_notes]-[dsch_cur]')
    M.add('bs_oncl', '  Other noncurrent liabilities (derived; incl. pensions, deferred taxes, lease liabilities)', 'line', 'num', hist=H('bs_oncl'),
          afc=lambda c: '=' + Q2('bs_oncl') if c.year == 2026 else '=[bs_oncl@py]')
    M.add('bs_tl', 'Total liabilities', 'sub', 'num', hist=lambda c: '=[bs_tcl]+N([bs_ltd])+[bs_oncl]' if hbs(c) else None, afc='=[bs_tcl]+N([bs_ltd])+[bs_oncl]')
    M.add(None, "Shareholders' equity:", 'label')
    M.add('bs_cs', '  Common shares & additional paid-in capital', 'line', 'num', hist=H('bs_cs'),
          afc=lambda c: ('=' + Q2('bs_cs') + '+([cf_sbc]-[cf_sbc@$Q1/26]-[cf_sbc@$Q2/26])+([cf_opt]-[cf_opt@$Q1/26]-[cf_opt@$Q2/26])') if c.year == 2026 else '=[bs_cs@py]+[cf_sbc]+[cf_opt]',
          note='+ stock-based compensation + option proceeds.')
    M.add('bs_re', '  Retained earnings', 'line', 'num', hist=H('bs_re'),
          afc=lambda c: ('=' + Q2('bs_re') + '+[is_ni@$Q3/26E]+[is_ni@$Q4/26E]-([dps@$Q3/26E]*[sh_b@$Q3/26E]+[dps@$Q4/26E]*[sh_b@$Q4/26E])') if c.year == 2026 else '=[bs_re@py]+[is_ni]+[cf_div]',
          note='+ net income − dividends.')
    M.add('bs_aoci', '  Accumulated other comprehensive loss', 'line', 'num', hist=H('bs_aoci'), afc=lambda c: '=' + Q2('bs_aoci') if c.year == 2026 else '=[bs_aoci@py]')
    M.add('bs_treas', '  Treasury shares, at cost', 'line', 'num', hist=H('bs_treas'),
          afc=lambda c: ('=' + Q2('bs_treas') + '+([cf_bb]-[cf_bb@$Q1/26]-[cf_bb@$Q2/26])') if c.year == 2026 else '=[bs_treas@py]+[cf_bb]',
          note='Lincoln Electric holds repurchased shares in treasury (44.1m shares at 30-Jun-26).')
    M.add('bs_le', "Total Lincoln Electric shareholders' equity", 'sub', 'num',
          hist=lambda c: '=[bs_cs]+[bs_re]+[bs_aoci]+[bs_treas]' if hbs(c) else None, afc='=[bs_cs]+[bs_re]+[bs_aoci]+[bs_treas]')
    M.add('bs_nci', '  Noncontrolling interests', 'line', 'num', hist=H('bs_nci'), afc=lambda c: '=' + Q2('bs_nci') if c.year == 2026 else '=[bs_nci@py]')
    M.add('bs_te', 'Total equity', 'sub', 'num', hist=lambda c: '=[bs_le]+N([bs_nci])' if hbs(c) else None, afc='=[bs_le]+N([bs_nci])')
    M.add('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'num', hist=lambda c: '=[bs_tl]+[bs_te]' if hbs(c) else None, afc='=[bs_tl]+[bs_te]')
    M.add('chk_bs', 'BS tie-out check (TA − TL&E)', 'check', 'num', hist=lambda c: '=IF(ISNUMBER([bs_ta]),ROUND([bs_ta]-[bs_tle],1),"")' if hbs(c) else None,
          afc='=ROUND([bs_ta]-[bs_tle],1)')
    M.add('chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([bs_ta_rep]),ROUND([bs_ta]-[bs_ta_rep],1),"")' if hbs(c) else None)
    M.add('bs_ta_rep', '  Memo: total assets as reported', 'pub', 'num', hist=H('bs_ta_rep'), outline=2)
    M.add('chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(AND(ISNUMBER([bs_cash]),ISNUMBER([cf_end])),ROUND([bs_cash]-[cf_end],1),"")' if hbs(c) and hcf(c) else None,
          afc='=ROUND([bs_cash]-[cf_end],1)')
    M.add('sh_out', '  Memo: common shares outstanding at period end (m)', 'line', 'num1', hist=H('sh_out'), afc='=[sh_end]')
    M.blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    M.add(style='section', label='WORKING CAPITAL & CASH CONVERSION', note='WORKING CAPITAL — forecast drivers (blue = input)')
    M.add('wc_sales', '  Net sales (period)', 'line', 'num', hist='=[is_sales]', afc='=[is_sales]')
    M.add('wc_cogs', '  Cost of goods sold (period)', 'line', 'num', hist='=[is_cogs]', afc='=[is_cogs]')
    days = lambda c: '91.25' if c.is_q else '365'
    M.add('dso', '  DSO — receivables / net sales × 365', 'line', 'days',
          hist=lambda c: f'=IFERROR([bs_ar]/[wc_sales]*{days(c)},"n/a")' if hbs(c) else None, afc=CFG['dso'], cagr='avg',
          note=f'Forecast inputs set at FY2025 levels (DSO {CFG["dso"]}d, inventory {CFG["dio"]}d, payables {CFG["dpo"]}d, accrued {CFG["accr_pct"]:.1%}).')
    M.add('dio', '  Inventory days — inventories / COGS × 365', 'line', 'days',
          hist=lambda c: f'=IFERROR([bs_inv]/[wc_cogs]*{days(c)},"n/a")' if hbs(c) else None, afc=CFG['dio'], cagr='avg')
    M.add('dpo', '  Payable days — payables / COGS × 365', 'line', 'days',
          hist=lambda c: f'=IFERROR([bs_ap]/[wc_cogs]*{days(c)},"n/a")' if hbs(c) else None, afc=CFG['dpo'], cagr='avg')
    M.add('accr_pct', '  Accrued employee compensation % of net sales (annualised)', 'pctline', 'pct',
          hist=lambda c: f'=IFERROR([bs_accr]/([wc_sales]*{"4" if c.is_q else "1"}),"n/a")' if hbs(c) and c.label in S.get('bs_accr', {}) else None,
          afc=CFG['accr_pct'])
    M.add('nwc', '  Operating NWC (receivables + inventories − payables − accrued compensation)', 'sub', 'num',
          hist=lambda c: '=IF(ISNUMBER([bs_ar]),[bs_ar]+[bs_inv]-[bs_ap]-N([bs_accr]),"n/a")' if hbs(c) else None,
          afc='=[bs_ar]+[bs_inv]-[bs_ap]-N([bs_accr])')
    M.add('nwc_pct', '  NWC % of net sales (annualised)', 'pctline', 'pct',
          hist=lambda c: f'=IFERROR([nwc]/([wc_sales]*{"4" if c.is_q else "1"}),"n/a")' if hbs(c) else None, afc='=IFERROR([nwc]/[wc_sales],"n/a")', cagr='avg')
    M.add('dnwc', '  ΔNWC (y/y)', 'line', 'num', hist=lambda c: '=IFERROR([nwc]-[nwc@py],"")' if hbs(c) and lay.py(c) else None, afc='=IFERROR([nwc]-[nwc@py],"")')
    M.blank()

    # ------------------------------------------------------------------ SCHEDULES
    M.add(style='section', label='BALANCE SHEET FORECAST SCHEDULES', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    M.add(style='block', label='Asset roll-forwards & non-cash items', note=None)
    am = CFG['amort']
    M.add('amort', '  Amortization of acquired intangibles — legacy (USDm)', 'line', 'num1', afc=lambda c: am[str(c.year)],
          note='FY2025 10-K expected amortization: $33.7m (2026), $31.5m (2027), $30.1m (2028), $26.0m (2029), $22.0m (2030).')
    M.add('dil', '  Dilutive securities (m shares)', 'line', 'num1', afc=lambda c: None if c.year == 2026 else '=[sh_d@$Q2/26]-[sh_b@$Q2/26]')
    M.add('px_app', '  Share-price appreciation % (buyback pricing)', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else 0.07)
    M.add(style='block', label='Debt schedule (senior notes with scheduled maturities + revolver / amounts due banks to a minimum cash balance)', note=None)
    M.add('dsch_total', '  Total debt (short-term + long-term)', 'sub', 'num', hist=lambda c: '=N([bs_std])+N([bs_ltd])' if hbs(c) else None,
          afc='=[dsch_notes]+[dsch_fac]',
          note='Debt at 30-Jun-26 $1,150m: senior notes $1,150m face (2015 Notes B 3.35% 2030 $100m, C 3.61% 2035 $50m, D 4.02% 2045 $100m; 2016 Notes A 2.75% 2028 $100m, B 3.03% 2033 $100m, C 3.27% 2037 $100m, D 3.52% 2041 $50m; 2024 Notes A 5.55% 2029 $75m, B 5.62% 2031 $75m, C 5.74% 2034 $400m); $1.0bn revolver (SOFR + 1.10%, Jun-2029) undrawn.')
    M.add('dsch_mat', '  Scheduled note maturities (input, negative)', 'line', 'num', afc=lambda c: D['mat'][str(c.year)],
          note='2028: 2016 Notes Series A ($100m); 2029: 2024 Notes Series A ($75m); 2030: 2015 Notes Series B ($100m).')
    M.add('dsch_refi_pct', '  % of scheduled maturities refinanced (input)', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else 1.0)
    M.add('dsch_refi', '  Refinancing issuance', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=-[dsch_mat]*[dsch_refi_pct]')
    M.add('dsch_notes', '  Senior notes outstanding (face, year end)', 'line', 'num',
          afc=lambda c: f'={D["notes_q2_26"]}+[dsch_mat]+[dsch_refi]' if c.year == 2026 else '=[dsch_notes@py]+[dsch_mat]+[dsch_refi]')
    M.add('dsch_cur', '  Current portion (next year\'s scheduled maturities)', 'line', 'num',
          afc=lambda c: (f'=-[dsch_mat@+1]' if c.year < 2030 else 0))
    M.add('dsch_pre', '  Cash before prepayable facilities (opening cash + CFO + CFI + non-facility financing)', 'line', 'num',
          afc=lambda c: ('=[cf_beg]+[cfo]+[cfi]+[cf_div]+[cf_bb]+[cf_opt]+[cf_ofin]+[cf_fx]+([cf_ltb@$Q1/26]+[cf_ltb@$Q2/26])+([cf_ltr@$Q1/26]+[cf_ltr@$Q2/26])+[dsch_mat]+([cf_std@$Q1/26]+[cf_std@$Q2/26])') if c.year == 2026
          else '=[cf_beg]+[cfo]+[cfi]+[cf_div]+[cf_bb]+[cf_opt]+[cf_ofin]+[cf_fx]+[dsch_mat]+[dsch_refi]')
    M.add('dsch_min', '  Minimum cash balance', 'line', 'num', afc=D['min_cash'],
          note='LECO typically holds $200–400m of cash (largely outside the US).')
    M.add('dsch_fac', '  Revolver / amounts due banks outstanding (year end)', 'line', 'num',
          afc=lambda c: f'=MAX(0,{D["fac_q2_26"]}+[dsch_min]-[dsch_pre])' if c.year == 2026 else '=MAX(0,[dsch_fac@py]+[dsch_min]-[dsch_pre])',
          note='Drawn/repaid so that cash = minimum balance; surplus cash first repays the revolver, then accumulates (or funds buybacks via the leverage plug).')
    M.add('dsch_net', '  Net issuance / (repayment)', 'line', 'num', hist=lambda c: '=IFERROR([dsch_total]-[dsch_total@py],"")' if hbs(c) and lay.py(c) else None,
          afc='=IFERROR([dsch_total]-[dsch_total@py],"")')
    M.add('r_notes', '  Interest rate on senior notes (opening balance) % (historical = net interest / opening total debt)', 'pctline', 'pct',
          hist=lambda c: '=IFERROR([is_int_net]/[dsch_total@py],"")' if c.kind == 'A' and lay.py(c) else None,
          afc=lambda c: None if c.year == 2026 else D['r_notes'],
          note='Weighted-average effective rate on the senior notes 4.16% at 30-Jun-26 (incl. terminated swaps) + fees; drifts up as 2028–30 maturities refinance at ~5.5%.')
    M.add('r_fac', '  Interest rate on revolver %', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else D['r_fac'],
          note='SOFR (~3.9%) + 1.10% margin.')
    M.add('r_cash', '  Interest income yield on opening cash %', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else D['r_cash'])
    M.add(style='block', label='Leverage-targeted buybacks (repurchases plug to a minimum net debt / Adjusted EBITDA)', note=None)
    M.add('lev_min', '  Minimum net debt / Adjusted EBITDA (x) (scenario)', 'line', 'x2', afc=lambda c: None if c.year == 2026 else '=SCEN(LEV)',
          note='Surplus cash above the leverage floor is returned through repurchases (LECO returned ~100% of FCF in 2023–25).')
    M.add('nd_pre', '  Net debt before buybacks (year end)', 'line', 'num',
          afc=lambda c: None if c.year == 2026 else '=[dsch_notes@py]+[dsch_fac@py]-[bs_cash@py]-[cfo]-[cfi]-[cf_div]-[cf_opt]-[cf_ofin]-[cf_fx]')
    M.add('nd_target', '  Target minimum net debt = min. leverage × Adjusted EBITDA', 'line', 'num', afc=lambda c: None if c.year == 2026 else '=[lev_min]*[aebitda]')
    M.add('bb_plug', '  Share repurchases: plug to minimum leverage', 'sub', 'num', afc=lambda c: None if c.year == 2026 else '=MAX(0,[nd_target]-[nd_pre])',
          note='Feeds the cash-flow repurchase line.')
    M.add(style='block', label='Historical reference (driver context)', note=None)
    M.add('ref_da', '  Total D&A % of net sales', 'pctline', 'pct', hist=ratio('da', 'is_sales'), afc='=IFERROR([da]/[is_sales],"")')
    M.add('ref_capex', '  Capex % of net sales', 'pctline', 'pct', hist=lambda c: '=IFERROR(-[capex]/[is_sales],"")' if hcf(c) else None, afc='=IFERROR(-[capex]/[is_sales],"")')
    M.blank()

    # ------------------------------------------------------------------ RATIOS
    A = lambda c: c.is_a
    M.add(style='section', label='RATIO ANALYSIS', note='RETURNS — annual columns (NOPAT on adjusted EBIT)')
    M.add(style='block', label='DuPont decomposition of ROIC', note=None)
    M.add('r_aebit', 'Adjusted EBIT', 'line', 'num', hist=lambda c: '=[aebit]' if A(c) else None, fc=lambda c: '=[aebit]' if A(c) else None)
    M.add('r_etr', 'Effective tax rate (actual)', 'pctline', 'pct', hist=lambda c: '=[is_etr]' if A(c) else None, fc=lambda c: '=[is_etr]' if A(c) else None)
    M.add('nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'sub', 'num', hist=lambda c: '=IFERROR([r_aebit]*(1-[r_etr]),"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([r_aebit]*(1-[r_etr]),"n/a")' if A(c) else None)
    M.add('ic', 'Invested capital (IC) = Equity + Net debt', 'sub', 'num', hist=lambda c: '=IFERROR([r_te]+[r_nd],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([r_te]+[r_nd],"n/a")' if A(c) else None)
    M.add('r_te', '  Total equity incl. NCI', 'line', 'num', hist=lambda c: '=[bs_te]' if A(c) else None, fc=lambda c: '=[bs_te]' if A(c) else None)
    M.add('r_nd', '  Net debt = Total debt − Cash', 'line', 'num', hist=lambda c: '=[dsch_total]-[bs_cash]' if A(c) else None,
          fc=lambda c: '=[dsch_total]-[bs_cash]' if A(c) else None)
    M.add('roic', 'ROIC = NOPAT / IC', 'total', 'pct', hist=lambda c: '=IFERROR([nopat]/[ic],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([nopat]/[ic],"n/a")' if A(c) else None, cagr='avg')
    M.add('roic_m', '  Margin = Adjusted EBIT / Net sales', 'pctline', 'pct', hist=lambda c: '=IFERROR([r_aebit]/[is_sales],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([r_aebit]/[is_sales],"n/a")' if A(c) else None)
    M.add('roic_t', '  Capital turnover = Net sales / IC', 'line', 'x2', hist=lambda c: '=IFERROR([is_sales]/[ic],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([is_sales]/[ic],"n/a")' if A(c) else None)
    M.add('roic_tb', '  Tax burden = (1 − effective tax rate)', 'pctline', 'pct', hist=lambda c: '=IFERROR(1-[r_etr],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR(1-[r_etr],"n/a")' if A(c) else None)
    M.add('chk_roic', '  Check: Margin × Turnover × Tax burden = ROIC', 'check', 'pct',
          hist=lambda c: '=IFERROR(ROUND([roic_m]*[roic_t]*[roic_tb]-[roic],6),"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR(ROUND([roic_m]*[roic_t]*[roic_tb]-[roic],6),"n/a")' if A(c) else None)
    M.add('pub_roic', '  Memo: company-published adjusted ROIC (rolling 12 months; adjusted NOPAT / period-end invested capital)', 'pub', 'pct',
          hist=lambda c: (S.get('pub_adj_roic', {}).get(c.label) if S.get('pub_adj_roic', {}).get(c.label) is not None else S.get('pub_roic', {}).get(c.label)) if A(c) else None)
    M.add(style='block', label='RONTA decomposition', note=None)
    M.add('ronta_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'num', hist=lambda c: '=[nopat]' if A(c) else None, fc=lambda c: '=[nopat]' if A(c) else None)
    M.add('ronta_ta', '  Total assets', 'line', 'num', hist=lambda c: '=[bs_ta]' if A(c) else None, fc=lambda c: '=[bs_ta]' if A(c) else None)
    M.add('ronta_gw', '  − Goodwill', 'line', 'num', hist=lambda c: '=-N([bs_gw])' if A(c) else None, fc=lambda c: '=-N([bs_gw])' if A(c) else None,
          note='Acquired intangibles sit inside other noncurrent assets (not deducted; ~$250m at FY25).')
    M.add('ronta_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'num',
          hist=lambda c: '=-([bs_tcl]-N([bs_std]))' if A(c) else None, fc=lambda c: '=-([bs_tcl]-N([bs_std]))' if A(c) else None)
    M.add('nta', '  = Net tangible assets', 'sub', 'num', hist=lambda c: '=[ronta_ta]+[ronta_gw]+[ronta_nibcl]' if A(c) else None,
          fc=lambda c: '=[ronta_ta]+[ronta_gw]+[ronta_nibcl]' if A(c) else None)
    M.add('ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', hist=lambda c: '=IFERROR([ronta_nopat]/[nta],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([ronta_nopat]/[nta],"n/a")' if A(c) else None, cagr='avg')
    M.add(style='block', label='Return on Equity (ROE)', note=None)
    M.add('roe_ni', 'Net income attributable to Lincoln Electric', 'line', 'num', hist=lambda c: '=[is_ni]' if A(c) else None, fc=lambda c: '=[is_ni]' if A(c) else None)
    M.add('roe_eq', "Lincoln Electric shareholders' equity", 'line', 'num', hist=lambda c: '=[bs_le]' if A(c) else None, fc=lambda c: '=[bs_le]' if A(c) else None)
    M.add('roe', 'ROE = Net income / Equity', 'total', 'pct', hist=lambda c: '=IFERROR([roe_ni]/[roe_eq],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([roe_ni]/[roe_eq],"n/a")' if A(c) else None, cagr='avg')
    M.add(style='block', label='Leverage', note=None)
    M.add('lev_nd', 'Net debt = Total debt − cash', 'line', 'num', hist=lambda c: '=[r_nd]' if A(c) else None, fc=lambda c: '=[r_nd]' if A(c) else None)
    M.add('lev_ebitda', 'Adjusted EBITDA', 'line', 'num', hist=lambda c: '=[aebitda]' if A(c) else None, fc=lambda c: '=[aebitda]' if A(c) else None)
    M.add('lev', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', hist=lambda c: '=IFERROR([lev_nd]/[lev_ebitda],"n/a")' if A(c) else None,
          fc=lambda c: '=IFERROR([lev_nd]/[lev_ebitda],"n/a")' if A(c) else None)
    M.blank()

    # ------------------------------------------------------------------ VALUATION
    M.add(style='section', label='VALUATION', note=f'VALUATION — share price input ${CFG["share_price"]:.2f} ({CFG["share_price_note"]})')
    V = lambda c: c.kind == 'AE'
    M.add('val_px', 'Share price ($) — current', 'val', 'eps', afc=lambda c: CFG['share_price'] if c.year == 2026 else '=[val_px@py]')
    M.add('val_sh', 'Diluted shares at period end (m)', 'line', 'num1', afc='=[sh_end]+([sh_d]-[sh_b])')
    M.add('val_mcap', 'Market capitalisation (USDm)', 'line', 'num', afc='=IFERROR([val_px]*[val_sh],"n/a")')
    M.add('val_nd', 'Net debt (USDm)', 'line', 'num', afc='=[r_nd]')
    M.add('val_nci', 'Noncontrolling interests (USDm)', 'line', 'num', afc='=N([bs_nci])')
    M.add('val_ev', 'Enterprise value (USDm)', 'sub', 'num', afc='=IFERROR([val_mcap]+[val_nd]+[val_nci],"n/a")')
    M.add(None, 'Multiples', 'label')
    M.add('val_evs', '  EV / Net sales', 'line', 'x2', afc='=IFERROR([val_ev]/[is_sales],"n/a")')
    M.add('val_evebitda', '  EV / Adjusted EBITDA', 'line', 'x', afc='=IFERROR([val_ev]/[aebitda],"n/a")')
    M.add('val_evebit', '  EV / Adjusted EBIT', 'line', 'x', afc='=IFERROR([val_ev]/[aebit],"n/a")')
    M.add('val_evic', '  EV / IC', 'line', 'x2', afc='=IFERROR([val_ev]/[ic],"n/a")')
    M.add('val_pe', '  P / E (GAAP diluted)', 'line', 'x', afc='=IFERROR([val_px]/[eps_d],"n/a")')
    M.add('val_pe_adj', '  P / E (adjusted EPS)', 'line', 'x', afc='=IFERROR([val_px]/[adj_eps],"n/a")')
    M.add('val_fcfy', '  FCF yield', 'pctline', 'pct', afc='=IFERROR([fcf]/[val_mcap],"n/a")')
    M.add('val_dy', '  Dividend yield', 'pctline', 'pct', afc='=IFERROR([dps]/[val_px],"n/a")')
