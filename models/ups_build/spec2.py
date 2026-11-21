"""Row specification part 2 (UPS): cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QEc, B1

def build_spec2(V0):
    S = add
    def e26f(key, q4):          # 2026E flow = 9M actual (Q1-Q3/26) + Q4/26E estimate
        return lambda: f'={ACT(key)}+{q4()}'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'STATEMENTS OF CONSOLIDATED CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 9M 2026 actual + Q4 estimate; quarters = discrete, derived from the year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=e26f('cf_ni', lambda: QEc('is_ni')))
    S('cf_adj', 'Adjustments to reconcile net income to net cash from operating activities:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm', data='cf_da', flow=True, fc=lambda: f'={V("is_dda")}', e26=e26f('cf_dda', lambda: QEc('is_dda')))
    S('cf_pen', '  Pension and postretirement benefit expense, net of contributions', 'line', 'm', data='cf_pen', flow=True,
      e26=lambda: f'={ACT("cf_pen")}+{PT("pt_pen")}', ae_in=V0['pen_ae'],
      note=('Expense less contributions (two cash-flow lines, netted). 2026E: 9M actual + Q4 estimate (FY26 contributions guided at $1.3bn; $450m of the Aug-2026 notes was contributed '
            'in kind in Q3). 2027E+: input (assumption: contributions exceed expense).'))
    S('cf_penc', '    Memo: pension and postretirement benefit contributions', 'memo', 'm', data='cf_pen_contrib', flow=True)
    S('cf_def', '  Deferred tax (benefit) expense', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_q4"]}', ae_in=V0['def_ae'])
    S('cf_sbc', '  Stock compensation expense', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=e26f('cf_sbc', lambda: QEc('is_sbc')))
    S('cf_wc', '  Changes in assets and liabilities & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_wages")}-{B1("bs_wages")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_wages")}-{P("bs_wages")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operating activities − the lines above (self-insurance, other gains / losses and working-capital changes). '
            'Forecast linked to the balance sheet: −Δ receivables + Δ(payables, accrued wages, other current liabilities).'))
    S('cf_cfo', 'Net cash from operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'={V("cf_ni")}+{V("cf_dda")}+{V("cf_pen")}+{V("cf_def")}+{V("cf_sbc")}+{V("cf_wc")}')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: FY26 guidance ~$3.0bn. 2027E+: revenue × capex %.')
    S('cf_disp', 'Proceeds from disposals of property, plant and equipment', 'line', 'm', data='cf_disp', flow=True, e26=lambda: f'={ACT("cf_disp")}', ae_in=V0['disp_ae'],
      note='From Q2-2021 the cash-flow line also includes business disposals; those proceeds are shown on the next row (cash-flow line less the PP&E disposals in the free-cash-flow reconciliation). 2027E+: input.')
    S('cf_divest', 'Proceeds from disposals of businesses (UPS Freight Q2-2021; Coyote Q3-2024)', 'line', 'm', data='cf_divest', flow=True, e26=lambda: f'={ACT("cf_divest")}', ae_in=0.0)
    S('cf_acq', 'Acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='2026E = 9M actual. 2027E+: M&A lever.')
    S('cf_ms', 'Marketable securities, net (purchases less sales and maturities)', 'line', 'm', data='cf_ms', flow=True, e26=lambda: f'={ACT("cf_ms")}', ae_in=0.0)
    S('cf_oinv', 'Finance receivables & other investing activities, net (derived)', 'line', 'm', data='cf_oinv2', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt', 'Net change in debt (short-term debt, borrowings, repayments)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+{V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid at maturity and refinanced; commercial paper drawn or repaid to the minimum cash balance. (Q3-2026 excludes the $450m of notes contributed in kind to the pension plans.)')
    S('cf_bb', 'Purchases of common stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: 9M actual (nil) + Q4 scenario input ($1.3bn left on the 2023 authorization). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target).')
    S('cf_iss', 'Issuances of common stock', 'line', 'm', data='cf_iss', flow=True, e26=lambda: f'={ACT("cf_iss")}+{V0["iss_q4_cash"]}', ae_in=V0['iss_ae_cash'])
    S('cf_div', 'Dividends', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{QEc("dps")}*{QEc("sh_basic")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Forecast = dividends per share × beginning shares (no circularity with buybacks). Part of each dividend is settled in class A shares (not modelled).')
    S('cf_ofin', 'Other financing activities (derived)', 'line', 'm', data='cf_ofin', flow=True, e26=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash used in financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash, cash equivalents and restricted cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net increase (decrease) in cash, cash equivalents and restricted cash', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_hfs', '  Memo: cash reclassified to / from assets held for sale (Coyote: −$10m Q2-2024, +$10m Q3-2024)', 'memo', 'm', data='cf_hfs', flow=True, e26=lambda: '=0', ae=lambda: '=0')
    S('cf_beg', 'Cash, cash equivalents and restricted cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash, cash equivalents and restricted cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change + held-for-sale memo = ending cash (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}+N({V("cf_hfs")})-{V("cf_end")})<=1.5,0,ROUND({V("cf_beg")}+{V("cf_net")}+N({V("cf_hfs")})-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS({V("cf_ni")}+{V("cf_dda")}+N({V("cf_pen")})+N({V("cf_def")})+N({V("cf_sbc")})+{V("cf_wc")}-{V("cf_cfo")})<=1.5,0,'
                   f'ROUND({V("cf_ni")}+{V("cf_dda")}+N({V("cf_pen")})+N({V("cf_def")})+N({V("cf_sbc")})+{V("cf_wc")}-{V("cf_cfo")},0)),"")'))
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf_oth', '  Net change in finance receivables + other investing activities (as presented; in the company free-cash-flow definition)', 'memo', 'm', data='fcf_oth', flow=True,
      e26=lambda: f'={ACT("fcf_oth")}', ae=lambda: '=0')
    S('fcf', 'Free cash flow (company definition: CFO − capital expenditures + PP&E disposal proceeds ± finance receivables ± other investing)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+N({V("cf_disp")})+N({V("fcf_oth")}),"")',
      note='Rebuilt from the filed cash-flow statements on the definition in the release ("Reconciliation of Free Cash Flow").')
    S('fcf_pub', '  Company-published free cash flow (release; year to date differenced for quarters)', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_diff', '  Model (filed statements) less company-published free cash flow — information', 'memo_calc', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),ROUND({V("fcf")}-{V("fcf_pub")},0),"n/p")',
      note='The release reconciliations before 2016 are marked "preliminary … subject to reclassification" and differ from the filed cash-flow statements; from 2016 the only difference is Q1-2025 / FY2025 ($10m of other investing reclassified in the 10-Q).')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('fcf_div', '  Dividends paid / FCF %', 'pct', 'pct', all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),ISNUMBER({V("cf_div")})),IFERROR(-{V("cf_div")}/{V("fcf")},""),"")')
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input (FY26 guidance ~$3.0bn = 3.2% of revenue; 2021–25 4.2–5.7%). Assumption: returning to ~4.4% (at or above D&A) as the network reconfiguration completes.')
    S('capex_dep', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_da")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = Q4 from shares issued at 30-Sep-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans and dividends settled in shares (m)', 'driver', 'm2', e26_in=V0['iss_q4'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from class A + class B shares issued at 30-Sep-2026 (balance sheet; 100m + 751m).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4/26 (m)', 'memo', 'm', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEETS (condensed)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Sep-2026 balance sheet + Q4 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_restr")}')
    S('bs_ms', '  Marketable securities', 'line', 'm', data='bs_ms', bs=True, e26=lambda: f'={B1("bs_ms")}', ae=lambda: f'={P("bs_ms")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Other current assets (derived)', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant and equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})-({QEc("d_da")}-{V("d_amort")}/4)',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("bs_sw")}-({V("d_da")}-{V("d_amort")}-N({V("m_amort")}))-{V("cf_disp")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior + capex (less capitalized software, booked in intangibles) − depreciation (D&A less amortization of intangibles) − disposal proceeds + acquired PP&E.')
    S('bs_rou', '  Operating lease right-of-use assets (from 2019, ASC 842)', 'line', 'm', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}', ae=lambda: f'={P("bs_rou")}')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-{V("d_amort")}/4', ae=lambda: f'={P("bs_int")}-{V("d_amort")}-N({V("m_amort")})+{V("m_spend")}*{V("m_intp")}+{V("bs_sw")}',
      note='Roll-forward: prior − amortization + acquired intangibles + capitalized software (input; the same amount is taken out of the PP&E roll-forward).')
    S('bs_onca', '  Investments, deferred income tax assets & other non-current assets (derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND SHAREOWNERS' EQUITY", 'sub', 'gen')
    S('bs_cdebt', '  Current maturities of long-term debt, commercial paper and finance leases', 'line', 'm', data='bs_cdebt', bs=True,
      fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_clease', '  Current maturities of operating leases', 'line', 'm', data='bs_clease', bs=True, e26=lambda: f'={B1("bs_clease")}', ae=lambda: f'={P("bs_clease")}')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_wages', '  Accrued wages and withholdings', 'line', 'm', data='bs_wages', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_wgp")}')
    S('bs_ocl', '  Self-insurance reserves, accrued benefit contributions & other current liabilities (derived)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_cdebt")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt and finance leases', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cdebt")}')
    S('bs_nclease', '  Non-current operating leases', 'line', 'm', data='bs_nclease', bs=True, e26=lambda: f'={B1("bs_nclease")}', ae=lambda: f'={P("bs_nclease")}')
    S('bs_pension', '  Pension and postretirement benefit obligations', 'line', 'm', data='bs_pension', bs=True,
      e26=lambda: f'={B1("bs_pension")}+({V("cf_pen")}-{ACT("cf_pen")})', ae=lambda: f'={P("bs_pension")}+{V("cf_pen")}',
      note='Roll-forward: prior + expense − contributions (no remeasurement / mark-to-market forecast).')
    S('bs_dtl', '  Deferred income tax liabilities', 'line', 'm', data='bs_dtl', bs=True,
      e26=lambda: f'={B1("bs_dtl")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_ol', '  Self-insurance reserves & other non-current liabilities (derived)', 'line', 'm', data='bs_ol', bs=True, e26=lambda: f'={B1("bs_ol")}', ae=lambda: f'={P("bs_ol")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', '  Total equity for controlling interests', 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QEc("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QEc("d_sbc")}+({V("cf_iss")}-{ACT("cf_iss")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_iss")}',
      note='+ net income − dividends − repurchases + stock compensation + issuances (other comprehensive income held flat).')
    S('bs_nci', '  Noncontrolling interests', 'line', 'm', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}', ae=lambda: f'={P("bs_nci")}')
    S('bs_teq', "Total shareowners' equity", 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND SHAREOWNERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1.5,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1.5,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_restr', '  Memo: restricted cash included in cash-flow cash (cash-flow ending cash − balance-sheet cash; 2018–Q3/19, Q1/24)', 'memo', 'm', data='bs_restr', bs=True,
      e26=lambda: f'={B1("bs_restr")}', ae=lambda: f'={P("bs_restr")}')
    S('bs_chk_cash', '  Check: BS cash + restricted cash memo vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+N({V("bs_restr")})-{V("cf_end")})<=1.5,0,ROUND({V("bs_cash")}+N({V("bs_restr")})-{V("cf_end")},0)),"")')
    S('bs_shares', '  Memo: shares issued at period end — class A + class B (m)', 'memo', 'm', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_sha', '    of which class A (10 votes; converts to class B on sale)', 'memo', 'm', data='bs_sh_a', bs=True)
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); UPS has no cost of goods sold, so payables and accruals run on revenue')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_app', '  Accounts payable % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")', e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'])
    S('wc_wgp', '  Accrued wages and withholdings % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_wages")}/{V("wc_rev")},"")', e26_in=V0['wc']['wg'], ae_in=V0['wc']['wg'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables − accrued wages − other current liabilities)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_wages")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count, pricing & capitalized software', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & restricted units)', 'sched', 'm', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.06)
    S('bs_sw', '  Capitalized software added to intangible assets (part of capital expenditures; input)', 'sched', 'm', ae=lambda: f'={V("d_amort")}',
      note='Assumption: software capitalized each year = amortization of intangibles, so the intangible balance is stable before acquisitions; the same amount is deducted from the PP&E roll-forward through D&A.')
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current maturities + long-term debt and finance leases)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_cdebt")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_09_30'])
    S('ds_notes', '  Senior notes, debentures, finance leases & other debt (excl. commercial paper)', 'sched', 'm', data='debt_x',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=V0['iss_notes'][FYC], ae_in={y: V0['iss_notes'].get(y, 0.0) for y in range(FYC + 1, FYL + 1)},
      note='2026E (Q4): none assumed after the Aug-2026 issues. 2027E+: maturities refinanced with new notes, plus $1.5bn (2028E, 2029E) and $2.0bn (2030E) of additional notes so that leverage-target buybacks are not funded with commercial paper beyond the $3.0bn credit commitments (financing assumption; see the headroom memo).')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note=MAN['debt']['maturities_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial-paper draws / repayments (opening cash + CFO + CFI + buybacks, dividends, issuances, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("cf_end")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_iss")}-{ACT("cf_iss")})+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_iss")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note='Assumption (cash and cash equivalents $4.7–6.8bn at the 2025–26 quarter ends).')
    S('ds_rev', '  Commercial paper / revolving credit (period end)', 'sched', 'm', data='debt_cp',
      e26=lambda: f'=MAX(0,N({B1("ds_rev")})+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note=MAN['debt']['credit_facilities'] + ' Shortfalls below the minimum cash balance are drawn as commercial paper; surplus repays it.')
    S('ds_head', '  Memo: headroom vs the $3.0bn revolving credit commitments backing commercial paper (negative = other financing needed)', 'memo_calc', 'm',
      e26=lambda: f'=3000-{V("ds_rev")}', ae=lambda: f'=3000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes, leases & other debt %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.04, note='Assumption (short-term rates).')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{P("bs_ms")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_iss")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_pen', '  Memo: pension & postretirement obligations + operating lease liabilities (not included in net debt)', 'memo_calc', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_pension")}),{V("bs_pension")}+N({V("bs_clease")})+N({V("bs_nclease")}),"")')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on non-GAAP adjusted operating profit)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (= non-GAAP adjusted operating profit)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.23)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − marketable securities', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_ms")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_cdebt")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', 'Total equity for controlling interests', 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash − marketable securities', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', '(Total debt + pension & postretirement obligations + operating leases) / adjusted EBITDA (x) — model proxy for the company\'s adjusted-debt leverage', 'line', 'x2', ann=True,
      all=lambda: f'=IFERROR(({V("ds_total")}+{V("hr_pen")})/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm', e26=lambda: f'={V("bb_end")}+({Q3}{R["sh_dil"]}-{Q3}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
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
