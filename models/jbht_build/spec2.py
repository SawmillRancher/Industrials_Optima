"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    def dq4(key): return f'({V(key)}-{B1(key)})'          # change over Q4/26E (year-end 2026E less 30-Sep-2026)
    def dy(key): return f'({V(key)}-{P(key)})'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = nine months actual + Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net earnings', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Adjustments to reconcile net earnings to net cash provided by operating activities:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm1', data='cf_da', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_sbc', '  Share-based compensation', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_gain', '  (Gain) / loss on sale of revenue equipment and other', 'line', 'm1', data='cf_gain', flow=True, e26=lambda: f'={ACT("cf_gain")}', ae=lambda: '=0',
      note='Forecast nil: equipment assumed sold at book value.')
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}', ae_in=V0['def_ae'],
      note='Forecast input (FY2021–25 average ≈ $33m; bonus-depreciation timing).')
    S('cf_wc', '  Changes in operating assets and liabilities & other, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-{dq4("bs_ar")}-{dq4("bs_oca")}+{dq4("bs_ap")}+{dq4("bs_claims")}+{dq4("bs_oacc")}+{dq4("bs_oltl")}'),
      ae=lambda: f'=-{dy("bs_ar")}-{dy("bs_oca")}+{dy("bs_ap")}+{dy("bs_claims")}+{dy("bs_oacc")}+{dy("bs_oltl")}',
      note=('History: net cash from operations − net earnings − D&A − share-based compensation − gain / loss − deferred taxes (incl. impairments and other non-cash items). '
            'Forecast linked to the balance sheet: −Δ(receivables, prepaid & other) + Δ(payables, claims accruals, accrued expenses, other long-term liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Additions to property and equipment', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}-{V("cf_sale")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}/(1-{V("capex_sale")})',
      note='2026E: company outlook for net capital expenditures (~$700m) grossed up for equipment sale proceeds. 2027E+: revenue × net capex % ÷ (1 − sale-proceeds ratio).')
    S('cf_sale', 'Net proceeds from sale of equipment', 'line', 'm1', data='cf_sale', flow=True,
      e26=lambda: f'={ACT("cf_sale")}+{PT("pt_sale")}', ae=lambda: f'=-{V("cf_capex")}*{V("capex_sale")}')
    S('cf_acq', 'Business acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='Cory 1st Choice (Feb-2019), RDI Last Mile (Jan-2020), Zenith Freight Lines (Feb-2022), BNSF Logistics brokerage (Sep-2023). 2027E+: M&A lever.')
    S('cf_oinv', 'Other investing activities, net (derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae=lambda: '=0')
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Purchase of treasury stock', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: nine months actual + Q4 scenario input ($1bn authorization of Oct-2025; $619m remaining at 30-Sep-2026). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target).')
    S('cf_div', 'Dividends paid', 'line', 'm1', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}')
    S('cf_debt', 'Net debt issuance / (repayment) (forecast; inside the line below historically)', 'line', 'm1',
      e26=lambda: f'={V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: senior notes and term loans refinanced at maturity; revolver drawn or repaid to the minimum cash balance.')
    S('cf_ofin', 'Debt, stock-plan tax withholding & other financing, net (derived historically)', 'line', 'm1', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}', ae=lambda: '=0')
    S('cf_cff', 'Net cash used in financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")},"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF = change in cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.02,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.02,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('ncapex', 'Net capital expenditures (company term: additions to property and equipment − sale proceeds)', 'line', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("cf_sale")})),-({V("cf_capex")}+{V("cf_sale")}),"")',
      note='The measure J.B. Hunt quotes in its releases and outlook.')
    S('fcf', 'Free cash flow (model definition: CFO − net capital expenditures)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("ncapex")})),{V("cf_cfo")}-{V("ncapex")},"")',
      note='Model definition (the company publishes no free cash flow measure).')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net earnings conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Net capital expenditures % of revenue', 'pct', 'pct', all=ratio('ncapex', 'is_rev'), ae_in=V0['capex_pct'], note=V0['capex_pct_note'])
    S('capex_sale', '  Equipment sale proceeds % of gross additions', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_sale")}/{V("cf_capex")},""),"")', ae_in=V0['sale_pct'], note='FY2021–25: 7–21% of gross additions; input.')
    S('capex_dep', '  Net capital expenditures / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("ncapex")}),IFERROR({V("ncapex")}/{V("d_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares outstanding at 30-Sep-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net of withholding (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from actual shares outstanding at 30-Sep-2026 (release supplemental data), which already reflect nine-month repurchases.')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Prepaid expenses and other current assets (derived)', 'line', 'm1', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Net property and equipment', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: (f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({QEc("d_dda")}-{V("d_amort")}/4)-({V("cf_sale")}-{ACT("cf_sale")})'),
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-({V("d_dda")}-{V("d_amort")}-N({V("m_amort")}))-({V("cf_sale")}+{V("cf_gain")})+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior + additions − depreciation (D&A less intangible amortization) − book value of equipment sold + acquired PP&E.')
    S('bs_oa', '  Other assets, net (goodwill, intangibles, operating-lease right-of-use assets, other)', 'line', 'm1', data='bs_oa', bs=True,
      e26=lambda: f'={B1("bs_oa")}-{V("d_amort")}/4', ae=lambda: f'={P("bs_oa")}-{V("d_amort")}-N({V("m_amort")})+{V("m_spend")}*(1-{V("m_ppe")})',
      note='Roll-forward: prior − amortization of intangibles + acquired goodwill and intangibles (M&A lever).')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+{V("bs_ppe")}+{V("bs_oa")},"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_std', '  Current debt', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'=MIN({V("ds_notes")},{V("ds_mat")})',
      note='Senior notes / term loans maturing in the next year.')
    S('bs_ap', '  Trade accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dpo")}/365')
    S('bs_claims', '  Claims accruals (current)', 'line', 'm1', data='bs_claims', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_clp")}')
    S('bs_oacc', '  Accrued payroll and other accrued expenses (derived)', 'line', 'm1', data='bs_oacc', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_std")}:{V("bs_oacc")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_oltl', '  Long-term claims accruals and other long-term liabilities', 'line', 'm1', data='bs_oltl', bs=True, e26=lambda: f'={B1("bs_oltl")}', ae=lambda: f'={P("bs_oltl")}',
      note='Long-term claims accruals are shown separately from Q2-25 (inside other long-term liabilities before). Held flat in the forecast.')
    S('bs_dit', '  Deferred income taxes', 'line', 'm1', data='bs_dit', bs=True,
      e26=lambda: f'={B1("bs_dit")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_dit")}+{V("cf_def")}')
    S('bs_eq', "  Stockholders' equity", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}',
      note='+ net earnings − dividends − treasury-stock purchases + share-based compensation.')
    S('bs_nci', '  Noncontrolling interests (none)', 'line', 'm1', e26=lambda: '=0', ae=lambda: '=0')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+{V("bs_ltd")}+{V("bs_oltl")}+{V("bs_dit")}+{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.02,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.02,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=0.02,0,ROUND({V("bs_cash")}-{V("cf_end")},1)),"")')
    S('bs_shares', '  Memo: actual shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_gwint', '  Memo: goodwill and intangible assets, net (inside other assets; XBRL, from Dec-2018)', 'memo', 'm1', data='bs_gwint', bs=True)
    S('bs_gross', '  Memo: property and equipment, gross', 'memo', 'm1', data='bs_ppe_gross', bs=True)
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); revenue basis (no cost of goods sold)')
    S('wc_rev', '  Revenue — annualised (quarters × 4; 2026E = Q4/26E × 4)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")', qe=lambda: f'={V("is_rev")}*4',
      e26=lambda: f'={QEc("is_rev")}*4', ae=lambda: f'={V("is_rev")}',
      note='Year-end 2026E balances are sized on the Q4/26E run-rate, like the historical quarter-end ratios.')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dpo', '  Payable days — trade payables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_clp', '  Claims accruals (current) % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_claims")}/{V("wc_rev")},"")', e26_in=V0['wc']['cl'], ae_in=V0['wc']['cl'])
    S('wc_oclp', '  Accrued payroll and other accrued expenses % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oacc")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + prepaid & other − payables − claims accruals − accrued expenses)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_claims")}-{V("bs_oacc")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; restricted and performance share units)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes and term loans refinanced at maturity; revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current debt + long-term debt)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_09_30'])
    S('ds_notes', '  Senior notes & term loans (carrying amount)', 'sched', 'm1', data='debt_lt',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes / term loans issued (input)', 'sched', 'm1', e26_in=0.0, ae_in=V0['iss_notes'], note='Maturities assumed refinanced (assumption).')
    S('ds_repay', '  Notes / term loans repaid at maturity (input)', 'sched', 'm1', e26_in=0.0, ae_in=V0['repay'], note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following year (current debt)', 'sched', 'm1', e26_in=0.0, ae_in=V0['mat'])
    S('ds_pre', '  Cash before revolver draws / repayments (opening cash + CFO + CFI + buybacks, dividends, other financing − notes repaid + issued)', 'sched', 'm1',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_ofin")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note='J.B. Hunt runs minimal cash ($4m at 30-Sep-2026; $17m at year-end 2025) against its revolver.')
    S('ds_rev', '  Revolving line of credit (year end)', 'sched', 'm1', data='debt_st',
      e26=lambda: f'=MAX(0,{B1("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$1.0bn revolver expiring Nov-2030 ($81.9m drawn at 30-Sep-2026). Shortfalls below the minimum cash balance are drawn; surplus repays the revolver. Balances above the $1.0bn commitment (Bull case, where buybacks run to 1.0x leverage) are a financing assumption: new notes / term loans at the same rate — see the headroom memo.')
    S('ds_head', '  Memo: revolver headroom vs the $1.0bn commitment (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'=1000-{V("ds_rev")}', ae=lambda: f'=1000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_debt', '  Interest rate on opening total debt %', 'sched', 'pct', ae_in=V0['r_debt'], note=V0['r_debt_note'])
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.03)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow treasury-stock line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_int', '  Net interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_bv', '  Book value per share ($)', 'line', 'ps', all=lambda: f'=IF(AND(ISNUMBER({V("bs_eq")}),ISNUMBER({V("bs_shares")})),IFERROR({V("bs_eq")}/{V("bs_shares")},""),"")')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (adjusted EBITDA − total D&A)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (bounded 15–40%; FY2017 Tax Act year)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(MIN(0.4,MAX(0.15,{V("is_etr")}+0)),0.24)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets (where reported separately; history from Dec-2018)', 'line', 'm1', ann=True,
      hist=lambda: f'=-N({V("bs_gwint")})', fc=lambda: f'={P("rn_gw")}+{V("d_amort")}+N({V("m_amort")})-{V("m_spend")}*(1-{V("m_ppe")})')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. current debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net earnings', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net earnings / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
