"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules (Ultra Maritime PPA, debt, pension
liability, leverage-targeted buybacks), ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, QEa, B1

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    def e26q(key):              # 2026E flow = 9M actual + the Q4/26E cell of the same row
        return lambda: f'={ACT(key)}+{QEc(key)}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M 2026 actual + Q4/26E estimate, Q4 lines in the Q4/26E column; history: quarters derived from the year-to-date statements, as originally reported)')
    S('cf_ni', 'Net earnings (as reported in the cash-flow statement)', 'line', 'm', data='cf_ni', flow=True, qe_ok=True, qe=lambda: f'={QEc("is_ni")}', fc=lambda: f'={V("is_ni")}', e26=e26q('cf_ni'))
    S('cf_basis', '  Memo: basis difference — statement net earnings (re-presented basis) − cash-flow net earnings (as reported)', 'memo_calc', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("cf_ni")}),ISNUMBER({V("is_ni")})),IF(ABS({V("is_ni")}-{V("cf_ni")})<=0.6,0,{V("is_ni")}-{V("cf_ni")}),"")',
      note='Non-zero only where the income statement is on a re-presented basis (2017 ASC 606: $1,963m vs $2,002m reported; Q1/Q2-16 continuing operations vs reported incl. IS&GS).')
    S('cf_adj', 'Adjustments for non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm', data='cf_dda', flow=True, qe_ok=True, qe=lambda: f'={QEc("is_dda")}', fc=lambda: f'={V("is_dda")}', e26=e26q('cf_dda'))
    S('cf_sbc', '  Stock-based compensation', 'line', 'm', data='cf_sbc', flow=True, qe_ok=True, qe=lambda: f'={QEc("is_sbc")}', fc=lambda: f'={V("is_sbc")}', e26=e26q('cf_sbc'))
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, qe_ok=True, qe=lambda: f'={PT("pt_def")}', e26=e26q('cf_def'), ae_in=V0['def_ae'],
      note='9M 2026 $1,114m (large: tax-law changes on R&D expensing / bonus depreciation). Q4/26E point estimate; 2027E+ input (assumption).')
    S('cf_chg', '  Severance / impairment charges, pension settlement charges, reach-forward losses (non-cash)', 'line', 'm', data='cf_chg', flow=True, qe_ok=True, qe=lambda: f'=-{QEc("ua_sev")}', e26=e26q('cf_chg'), fc=lambda: f'=-{V("ua_sev")}')
    S('cf_pens', '  Qualified defined benefit pension plans (FAS expense − cash contributions)', 'line', 'm', data='cf_pens', flow=True, qe_ok=True,
      qe=lambda: f'=-({V("pn_fas", E26)}-{ACT("pn_fas_q")})-({V("pn_contrib", E26)}-{ACT("pn_contrib_q")})', e26=e26q('cf_pens'),
      ae=lambda: f'=-{V("pn_fas")}-{V("pn_contrib")}',
      note='History: cash-flow line ("postretirement benefit plans" to 2015). Forecast = −FAS pension expense (non-cash; negative sign = expense) − contributions. Q4/26E: 2026 outlook FAS expense $(370)m less the 9M accrual.')
    S('pn_fas_q', '  Memo: FAS pension expense accrual in the quarter (service + non-service; helper)', 'memo_calc', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("is_nonsvc")}),{V("is_nonsvc")}+{V("pn_svc", ANN[CTX.col.year].c)}/4,"")' if CTX.col.q and CTX.col.year >= 2018 else None), qe_ok=True,
      qe=lambda: f'={QEc("is_nonsvc")}+{V("pn_svc", E26)}/4')
    S('pn_contrib_q', '  Memo: pension contributions in the quarter (helper; 2026 none expected)', 'memo_calc', 'm', qe_ok=True, qe=lambda: '=0',
      all=lambda: ('=0' if CTX.col.q and CTX.col.year == 2026 else None))
    S('cf_wc_h', 'Changes in operating assets and liabilities:', 'sub', 'gen')
    S('cf_ar', '  Receivables, net', 'line', 'm', data='cf_ar', flow=True, qe_ok=True, qe=lambda: f'={PT("pt_wc_ar")}', e26=e26q('cf_ar'), ae=lambda: f'=-({V("bs_ar")}-{P("bs_ar")})')
    S('cf_ca', '  Contract assets (unbilled receivables inside "receivables" before 2018)', 'line', 'm', data='cf_ca', flow=True, qe_ok=True,
      qe=lambda: f'={V("cal_cfo", E26)}-{ACT("cf_cfo")}-({QEc("cf_ni")}+{QEc("cf_dda")}+{QEc("cf_sbc")}+{QEc("cf_def")}+{QEc("cf_chg")}+{QEc("cf_pens")}+{QEc("cf_ar")}+{QEc("cf_inv")}+{QEc("cf_ap")}+{QEc("cf_cl")}+{QEc("cf_tax")}+{QEc("cf_oth")})',
      e26=e26q('cf_ca'), ae=lambda: f'=-({V("bs_ca")}-{P("bs_ca")})',
      note='Q4/26E = calibration plug: the contract-asset change that makes 2026E cash from operations equal the guidance end-point (the swing item in LMT working capital; contract assets rose $3.9bn in 9M 2026). 2027E+: balance-sheet driver.')
    S('cf_inv', '  Inventories', 'line', 'm', data='cf_inv', flow=True, qe_ok=True, qe=lambda: f'={PT("pt_wc_inv")}', e26=e26q('cf_inv'), ae=lambda: f'=-({V("bs_inv")}-{P("bs_inv")})')
    S('cf_ap', '  Accounts payable', 'line', 'm', data='cf_ap', flow=True, qe_ok=True, qe=lambda: f'={PT("pt_wc_ap")}', e26=e26q('cf_ap'), ae=lambda: f'={V("bs_ap")}-{P("bs_ap")}')
    S('cf_cl', '  Contract liabilities (customer advances and amounts in excess of costs incurred before 2018)', 'line', 'm', data='cf_cl', flow=True, qe_ok=True,
      qe=lambda: f'={PT("pt_wc_cl")}', e26=e26q('cf_cl'), ae=lambda: f'={V("bs_cl")}-{P("bs_cl")}')
    S('cf_tax', '  Income taxes', 'line', 'm', data='cf_tax', flow=True, qe_ok=True, qe=lambda: f'={PT("pt_wc_tax")}', e26=e26q('cf_tax'), ae_in=0.0)
    S('cf_oth', '  Other, net (derived: cash from operations less the itemised lines)', 'line', 'm', data='cf_oth', flow=True, qe_ok=True, qe=lambda: f'={PT("pt_wc_oth")}', e26=e26q('cf_oth'),
      ae=lambda: f'=({V("bs_sal")}-{P("bs_sal")})+({V("bs_ocl")}-{P("bs_ocl")})-({V("bs_oca")}-{P("bs_oca")})',
      note='History: residual (incl. items such as tax-matter resolutions, discontinued-operations adjustments). Forecast: Δ salaries & benefits + Δ other current liabilities − Δ other current assets.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, qe_ok=True, qe=lambda: f'=SUM({V("cf_ni")},{V("cf_dda")}:{V("cf_pens")},{V("cf_ar")}:{V("cf_oth")})',
      fc=lambda: f'=SUM({V("cf_ni")},{V("cf_dda")}:{V("cf_pens")},{V("cf_ar")}:{V("cf_oth")})')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True, qe_ok=True, qe=lambda: f'=-{PT("pt_capex")}-{ACT("cf_capex")}', e26=e26q('cf_capex'),
      ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: outlook $2.1-2.3bn (point estimate $2.2bn; 9M $1,268m). 2027E+: net sales × capex %.')
    S('cf_acq', 'Acquisitions of businesses, net of cash acquired', 'line', 'm', data='cf_acq', flow=True, qe_ok=True, qe=lambda: f'=-{V("um_cons", E26)}*{V("um_sw", E26)}', e26=e26q('cf_acq'),
      ae=lambda: f'=-{V("m_spend")}-{V("um_cons")}*{V("um_sw")}',
      note='Q4/26E: Ultra Maritime $3.45bn (cash on hand; closing assumed 31-Dec-2026). 2015: Sikorsky $9.0bn. 2027E+: M&A lever.')
    S('cf_divest', 'Proceeds from divestitures (2016 IS&GS cash; 2006 / 2010-11 businesses)', 'line', 'm', data='cf_divest', flow=True, qe_ok=True, qe=lambda: '=0', e26=e26q('cf_divest'), ae_in=0.0)
    S('cf_oinv', 'Other investing, net (derived)', 'line', 'm', data='cf_oinv', flow=True, qe_ok=True, qe=lambda: '=0', e26=e26q('cf_oinv'), ae_in=0.0)
    S('cf_cfi', 'Net cash used for investing activities', 'line_b', 'm', data='cf_cfi', flow=True, qe_ok=True, qe=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})', fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt_iss', 'Issuance of long-term debt, net of related costs', 'line', 'm', data='cf_debt_iss', flow=True, qe_ok=True, qe=lambda: f'={V("ds_iss", E26)}', e26=e26q('cf_debt_iss'), ae=lambda: f'={V("ds_iss")}')
    S('cf_debt_rep', 'Repayments of long-term debt', 'line', 'm', data='cf_debt_rep', flow=True, qe_ok=True, qe=lambda: f'=-{V("ds_repay", E26)}', e26=e26q('cf_debt_rep'), ae=lambda: f'=-{V("ds_repay")}',
      note='Per the debt schedule: notes repaid at maturity (2026: $1,168m repaid in 9M), refinanced per the refinancing % input.')
    S('cf_cp', 'Commercial paper / revolver, net (forecast plug to the minimum cash balance)', 'line', 'm', qe_ok=True, qe=lambda: f'={V("ds_rev", E26)}-{B1("ds_rev")}', e26=lambda: f'={QEc("cf_cp")}',
      ae=lambda: f'={V("ds_rev")}-{P("ds_rev")}', note='Historically inside "other, net" (no commercial paper outstanding since 2019).')
    S('cf_bb', 'Repurchases of common stock', 'line', 'm', data='cf_bb', flow=True, qe_ok=True, qe=lambda: f'=-{CH(SC["bb26"])}', e26=e26q('cf_bb'), ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: none in 9M (cash preserved for Ultra Maritime); Q4 scenario input. 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target), floored at the minimum programme.')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cf_div', flow=True, qe_ok=True, qe=lambda: f'=-{QEc("dps")}*{QEc("sh_basic")}', e26=e26q('cf_div'), ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Forecast = DPS × beginning shares (no circularity with the buyback plug).')
    S('cf_eq', 'Issuances of common stock (equity plans; shown separately to 2015)', 'line', 'm', data='cf_stock', flow=True, qe_ok=True, qe=lambda: '=0', e26=e26q('cf_eq'), ae_in=0.0,
      note='Nil from 2016 (share issuances under equity plans are netted in other, net / withholding).')
    S('cf_ofin', 'Other financing, net (derived historically: withholding taxes on awards, ESOP, debt costs)', 'line', 'm', data='cf_ofin', flow=True, qe_ok=True, qe=lambda: f'={PT("pt_ofin")}', e26=e26q('cf_ofin'), ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash used for financing activities', 'line_b', 'm', data='cf_cff', flow=True, qe_ok=True, qe=lambda: f'=SUM({V("cf_debt_iss")}:{V("cf_ofin")})', fc=lambda: f'=SUM({V("cf_debt_iss")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, qe_ok=True, qe=lambda: '=0', e26=e26q('cf_fx'), ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True, qe_ok=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      qe=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}', fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash and cash equivalents — beginning of period', 'line', 'm', data='cf_beg', qe_ok=True, qe=lambda: f'={B1("cf_end")}', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and cash equivalents — end of period', 'line_b', 'm', data='cf_end', qe_ok=True, qe=lambda: f'={V("cf_beg")}+{V("cf_net")}', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.6,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: cash from operations = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")},{V("cf_dda")}:{V("cf_pens")},{V("cf_ar")}:{V("cf_oth")})-{V("cf_cfo")})<=0.6,0,ROUND(SUM({V("cf_ni")},{V("cf_dda")}:{V("cf_pens")},{V("cf_ar")}:{V("cf_oth")})-{V("cf_cfo")},0)),"")')
    S('cf_wc_tot', '  Memo: change in operating assets and liabilities (Σ working-capital lines)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ar")}),SUM({V("cf_ar")}:{V("cf_oth")}),"")', qe_ok=True, qe=lambda: f'=SUM({V("cf_ar")}:{V("cf_oth")})')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: cash from operations − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow (summary tables, from 2018)', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<=0.6,0,ROUND({V("fcf")}-{V("fcf_pub")},0)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net earnings conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: 2.6% of sales (2023-25: 2.2-2.5%; 2026 outlook ~2.7%; munitions capacity expansion).')
    S('capex_dep', '  Capex / depreciation & other amortization (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 27-Sep-2026; 2027E+ buybacks via the leverage plug (floored at the minimum programme)')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'], note='~1m shares a year issued under stock-based awards and defined-contribution plans (2025: 229m → 230m before repurchases of 6.6m).')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from the 230m shares outstanding at 27-Sep-2026 (statement of earnings).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 27-Sep-2026 balance sheet + Q4 flows (incl. Ultra Maritime purchase accounting); 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Receivables, net (billed; incl. unbilled before 2018)', 'line', 'm', data='bs_ar', bs=True, e26=lambda: f'={B1("bs_ar")}-{QEc("cf_ar")}', ae=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_ca', '  Contract assets (from 2018, ASC 606)', 'line', 'm', data='bs_ca', bs=True, e26=lambda: f'={B1("bs_ca")}-{QEc("cf_ca")}', ae=lambda: f'={V("wc_rev")}*{V("wc_ca")}')
    S('bs_inv', '  Inventories', 'line', 'm', data='bs_inv', bs=True, e26=lambda: f'={B1("bs_inv")}-{QEc("cf_inv")}', ae=lambda: f'={V("wc_rev")}*{V("wc_inv")}')
    S('bs_oca', '  Other current assets (incl. current deferred taxes to 2015; derived)', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={V("wc_rev")}*{V("wc_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant and equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-{QEc("cf_capex")}-{QEc("d_dep")}+{V("um_cons")}*{V("um_sw")}*{V("um_ppe")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation & other amortization + acquired PP&E.')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}+{V("um_cons")}*{V("um_sw")}*(1-{V("um_ppe")}-{V("um_intp")})',
      ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net (shown separately from 2015; inside other noncurrent assets before)', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{QEc("d_amort")}+{V("um_cons")}*{V("um_sw")}*{V("um_intp")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − intangible amortization + acquired intangibles (Ultra Maritime 2026E; M&A lever).')
    S('bs_dta', '  Deferred income taxes (noncurrent asset)', 'line', 'm', data='bs_dta', bs=True, e26=lambda: f'={B1("bs_dta")}-{QEc("cf_def")}', ae=lambda: f'={P("bs_dta")}-{V("cf_def")}',
      note='Roll-forward: prior − deferred tax expense (cash-flow add-back).')
    S('bs_onca', '  Other noncurrent assets (incl. ULA investment, prepaid pension, lease ROU; derived)', 'line', 'm', data='bs_onca', bs=True, e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, e26=lambda: f'={B1("bs_ap")}+{QEc("cf_ap")}', ae=lambda: f'={V("wc_cos")}*{V("wc_dpo")}/365')
    S('bs_sal', '  Salaries, benefits and payroll taxes', 'line', 'm', data='bs_sal', bs=True, e26=lambda: f'={B1("bs_sal")}', ae=lambda: f'={V("wc_rev")}*{V("wc_sal")}')
    S('bs_cl', '  Contract liabilities (customer advances and amounts in excess of costs incurred before 2018)', 'line', 'm', data='bs_cl', bs=True,
      e26=lambda: f'={B1("bs_cl")}+{QEc("cf_cl")}', ae=lambda: f'={V("wc_rev")}*{V("wc_cl")}')
    S('bs_std', '  Current maturities of long-term debt / commercial paper', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Forecast = commercial paper / revolver (plug) + notes maturing in the following year.')
    S('bs_ocl', '  Other current liabilities (derived)', 'line', 'm', data='bs_ocl', bs=True, e26=lambda: f'={B1("bs_ocl")}+{QEc("cf_oth")}+{QEc("cf_tax")}', ae=lambda: f'={V("wc_rev")}*{V("wc_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt, net', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_pens', '  Accrued pension liabilities', 'line', 'm', data='bs_pens', bs=True, e26=lambda: f'={B1("bs_pens")}+{QEc("cf_pens")}', ae=lambda: f'={P("bs_pens")}+{V("cf_pens")}',
      note='Roll-forward: prior + FAS expense − contributions (the cash-flow pension line); actuarial gains / losses through OCI are not forecast. $13.9bn at YE2016 → $3.9bn at Sep-2026 after annuity transfers and asset returns.')
    S('bs_oncl', '  Other noncurrent liabilities (incl. OPEB, leases, deferred taxes; derived)', 'line', 'm', data='bs_oncl', bs=True, e26=lambda: f'={B1("bs_oncl")}', ae=lambda: f'={P("bs_oncl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_eq', "  Stockholders' equity (common stock, APIC, retained earnings, accumulated OCI)", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: f'={B1("bs_eq")}+{QEc("is_ni")}+{QEc("cf_div")}+{QEc("cf_bb")}+{QEc("d_sbc")}+{QEc("cf_eq")}+{QEc("cf_ofin")}',
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_eq")}+{V("cf_ofin")}',
      note='+ net earnings − dividends − repurchases + stock-based compensation + issuances + other financing (tax withholding on vested awards, ESOP; equity-settled). OCI / pension remeasurement held flat. Equity was $1.0bn at YE2011 (pension losses in AOCI).')
    S('bs_nci', '  Noncontrolling interests (none)', 'line', 'm', data='bs_nci', bs=True, e26=lambda: '=0', ae=lambda: '=0')
    S('bs_teq', 'Total equity', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.6,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=0.6,0,ROUND({V("bs_cash")}-{V("cf_end")},0)),"")')
    S('bs_shares', '  Memo: common shares outstanding at period end (m; statement of earnings)', 'memo', 'm1', data='sh_end', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input, set at the YE2025 / Sep-2026 levels)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cos', '  Cost of sales — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cos")}),{V("is_cos")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / net sales × 365 (billed only from 2018)', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', ae_in=V0['wc']['dso'])
    S('wc_ca', '  Contract assets % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ca")}/{V("wc_rev")},"")', ae_in=V0['wc']['ca'],
      note='YE2025 17.3%; 27-Sep-2026 20.4% (F-35 Lot 20 pre-contract costs; the Q4/26E plug brings 2026E back toward the guided cash flow). 2027E+ input: normalising from ~20.5% at YE2026E to the YE2025 level by 2030E as the Lot 20+ contracts are definitized (assumption).')
    S('wc_inv', '  Inventories % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_rev")},"")', ae_in=V0['wc']['inv'])
    S('wc_oca', '  Other current assets % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', ae_in=V0['wc']['oca'])
    S('wc_dpo', '  Payable days — accounts payable / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cos")}*365,"")', ae_in=V0['wc']['dpo'])
    S('wc_sal', '  Salaries, benefits & payroll taxes % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_sal")}/{V("wc_rev")},"")', ae_in=V0['wc']['sal'])
    S('wc_cl', '  Contract liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_cl")}/{V("wc_rev")},"")', ae_in=V0['wc']['cl'],
      note='Customer advances: 15.2% at YE2025 (Dec-2025 $11.4bn; Sep-2026 $12.6bn). Input.')
    S('wc_ocl', '  Other current liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")', ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + contract assets + inventories + other CA − payables − salaries − contract liabilities − other CL)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_ca")}+{V("bs_inv")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_sal")}-{V("bs_cl")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Ultra Maritime purchase-price allocation (2026E column; MODEL ASSUMPTIONS — no PPA has been filed)', 'sub', 'gen')
    S('ppa_cons', '  Consideration (cash)', 'sched', 'm', e26=lambda: f'={V("um_cons")}*{V("um_sw")}')
    S('ppa_ppe', '  Property, plant & equipment', 'sched', 'm', e26=lambda: f'={V("ppa_cons")}*{V("um_ppe")}')
    S('ppa_intang', '  Intangible assets (customer relationships, technology, backlog)', 'sched', 'm', e26=lambda: f'={V("ppa_cons")}*{V("um_intp")}')
    S('ppa_gw', '  Goodwill', 'sched', 'm', e26=lambda: f'={V("ppa_cons")}-{V("ppa_ppe")}-{V("ppa_intang")}')
    S('ppa_chk', '  Check: assets acquired − consideration (should be 0; working capital and liabilities assumed nil)', 'check', 'm',
      e26=lambda: f'=ROUND({V("ppa_ppe")}+{V("ppa_intang")}+{V("ppa_gw")}-{V("ppa_cons")},0)')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; RSUs, PSUs, options)', 'sched', 'm1', ae_in=V0['dil'], note='Diluted − basic weighted shares: ~1.0m in 2026 (Q3/26: 231.5m vs 230.5m).')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.06)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced per the refinancing %; commercial paper / revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current maturities / commercial paper + long-term debt, net)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['src'])
    S('ds_notes', '  Senior notes (book value, incl. current portion)', 'sched', 'm', data='debt_tot',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}',
      note='Book value ($20.5bn at 27-Sep-2026 = $21.7bn face less $1.2bn unamortized discounts and issuance costs; maturities are repaid at face — the discount accretion (~$50m p.a.) is not modelled).')
    S('ds_mat', '  Notes maturing in the following year (10-K Note 10 ladder; input)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)}, note=MAN['debt']['ladder_note'])
    S('ds_repay', '  Notes repaid at maturity (input; 2026 = $1,168m repaid in 9M)', 'sched', 'm', e26_in=V0['repay'][FYC], ae=lambda: f'={P("ds_mat")}')
    S('ds_refi', '  Refinancing % of maturities (input)', 'sched', 'pct', ae_in=V0['refi'], note='Investment-grade issuer (A-/Baa1); maturities assumed refinanced with new notes (100%). Set lower to deleverage.')
    S('ds_iss', '  New notes issued (refinancing × maturities + other issuance input)', 'sched', 'm', e26_in=V0['iss_notes'][FYC], ae=lambda: f'={V("ds_repay")}*{V("ds_refi")}+{V("ds_iss_x")}')
    S('ds_iss_x', '  Other new issuance (input)', 'sched', 'm', ae_in=0.0)
    S('ds_pre', '  Cash before commercial paper (opening cash + CFO + CFI + buybacks, dividends, equity, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("bs_cash")}+{QEc("cf_cfo")}+{QEc("cf_cfi")}+{QEc("cf_bb")}+{QEc("cf_div")}+{QEc("cf_eq")}+{QEc("cf_ofin")}+{QEc("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_eq")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note='Cash held $2.5-4.1bn at recent year ends; $6.0bn at Sep-2026 ahead of the $3.45bn Ultra Maritime payment.')
    S('ds_rev', '  Commercial paper / revolver drawn (year end)', 'sched', 'm', data='debt_st',
      e26=lambda: f'=MAX(0,{B1("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note=MAN['debt']['revolver'] + ' Shortfalls below the minimum cash balance are drawn; surplus repays.')
    S('ds_head', '  Memo: revolving-credit headroom vs the $6.0bn of facilities (negative = would need other financing)', 'memo_calc', 'm', e26=lambda: f'=6000-{V("ds_rev")}', ae=lambda: f'=6000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=MAN['debt']['interest'] + ' Input ~5.2% (2025 coupons 4.15-5.00% on new issues; legacy 3.55-5.90%).')
    S('ds_r_rev', '  Interest rate on opening commercial paper / revolver %', 'sched', 'pct', ae_in=0.045)
    S('ds_r_cash', '  Interest income yield on opening cash % (in other non-operating income)', 'sched', 'pct', ae_in=0.035, note='9M 2026 other non-operating income $179m on ~$4-6bn of cash (~4% annualised).')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+; floored at a minimum programme)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_floor', '  Minimum annual repurchase programme ($m; input)', 'sched', 'm', ae_in=V0['bb_min'], note='Repurchases every year since 2006 ($1.1-7.9bn; 2025 $3.0bn; 2026 paused for Ultra Maritime). Input $1.0bn.')
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_eq")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage (≥ minimum programme)', 'sched', 'm', ae=lambda: f'=MAX({V("lev_floor")},{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost, incl. the FAS/CAS operating adjustment)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (model; full-cost)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(MAX({V("is_etr")}+0,0.1),0.4),0.17)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")',
      note="Book equity is depressed by pension losses in accumulated OCI (equity $1.0bn at YE2011), so book ROIC is very high; see RONTA and EV/IC.")
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. current debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net earnings', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net earnings / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    S('lv_pens', 'Memo: net debt + accrued pension liabilities / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR(({V("lv_nd")}+{V("bs_pens")})/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")',
      note='Accrued pension liabilities ($3.9bn) are not added to EV (CAS recovery funds them); shown as a leverage memo.')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Business segment operating profit', lambda: f'=IFERROR({V("v_ev")}/{V("g_segop")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS, model)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
