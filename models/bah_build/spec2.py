"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, A1, QE3, B1

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2027E = Q1/27 actual + Q2–Q4 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=lambda: f'={A1("cf_ni")}+{QE3("is_ni")}')
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm1', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}', e26=lambda: f'={A1("cf_dda")}+{QE3("is_dda")}')
    S('cf_sbc', '  Stock-based compensation expense', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=lambda: f'={A1("cf_sbc")}+{QE3("is_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=lambda: f'={A1("cf_def")}+{3 * V0["def_q"]}', ae_in=V0['def_ae'],
      note='Annual: release cash-flow statement; quarters: XBRL (the quarterly releases fold deferred taxes into working capital). Forecast input.')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={A1("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_acc")}-{B1("bs_acc")})+({V("bs_ocl")}-{B1("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_oca")}-{P("bs_oca")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_acc")}-{P("bs_acc")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note=('History: net cash from operating activities − net income − D&A − stock-based compensation − deferred taxes (incl. noncash lease expense, gains and the '
            'working-capital lines). Forecast linked to the balance sheet: −Δ(receivables, other current assets) + Δ(payables & accrued, accrued compensation, other current liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of property, equipment and software', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2027E: FY27 guidance ~$220m, of which ~$105m for the new headquarters. 2028E+: revenue × capex %.')
    S('cf_acq', 'Payments for business acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True,
      e26=lambda: f'={A1("cf_acq")}-{V("ul_cons")}', ae=lambda: f'=-{V("m_spend")}',
      note='2027E = Q1 actual (Defy Security, $220m net of cash) + Ultra Mission Solutions ($720m, Q2). 2028E+: M&A lever.')
    S('cf_oinv', 'Other investing activities, net (strategic investments, divestitures; derived)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={A1("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Repurchases of common stock', 'line', 'm1', data='cf_bb', flow=True, e26=lambda: f'={A1("cf_bb")}-{CH(SC["bb27"])}', ae=lambda: f'=-{V("lev_bb")}',
      note=('2027E: Q1 actual + Q2–Q4 scenario input ($634m left on the $4,085m program at 30-Jun-2026). 2028E+ = leverage plug '
            '(surplus cash returned until net debt / adjusted EBITDA reaches the target). Includes shares withheld for taxes historically.'))
    S('cf_div', 'Cash dividends paid', 'line', 'm1', data='cf_div', flow=True,
      e26=lambda: f'={A1("cf_div")}-({Q2}{R["dps"]}*{Q2}{R["sh_basic"]}+{Q3}{R["dps"]}*{Q3}{R["sh_basic"]}+{Q4}{R["dps"]}*{Q4}{R["sh_basic"]})',
      ae=lambda: f'=-{V("dps")}*{V("bb_beg")}', note='Forecast = DPS × beginning shares (no circularity with plug-driven buybacks).')
    S('cf_eq', 'Proceeds from issuance of common stock & option exercises', 'line', 'm1', data='cf_stock', flow=True, e26=lambda: f'={A1("cf_eq")}+{3 * V0["eq_q"]}',
      ae_in=V0['eq_ae'])
    S('cf_debt', 'Net debt issuance / (repayment) (forecast; included in other financing historically)', 'line', 'm1',
      e26=lambda: f'={V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: $1.2bn notes issued 4-Aug-2026, Term Loan A-1 ($714m) repaid; term-loan amortization; maturities refinanced; revolver to minimum cash.')
    S('cf_ofin', 'Debt & other financing, net (derived historically)', 'line', 'm1', data='cf_ofin', flow=True, e26=lambda: f'={A1("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")},"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash and cash equivalents — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and cash equivalents — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF = ending cash (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<={TL()},0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<={TL()},0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: CFO − purchases of property, equipment and software)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm1', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("fcf_pub")}),IF(ABS({V("fcf")}-{V("fcf_pub")})<={TL()},0,ROUND({V("fcf")}-{V("fcf_pub")},1)),"n/p")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2028E+ input: headquarters build-out complete in FY27; FY2022–26 range 0.8–1.0% of revenue.')
    S('capex_dep', '  Capex / depreciation & other amortization (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2027E = Q2–Q4 from Class A shares outstanding at 30-Jun-2026; 2028E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2027E = Q2–Q4)', 'line', 'm', e26=lambda: f'={CH(SC["bb27"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_q3'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2027E begins from Class A shares outstanding at 30-Jun-2026 (120.28m, Q1 FY27 10-Q cover / balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q2/27 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed, as in the releases)', 'section',
      note='BS FORECAST — 2027E rolled forward from the 30-Jun-2026 balance sheet + Q2–Q4 flows; 2028E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable, net (billed & unbilled)', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_oca', '  Prepaid expenses & other current assets (derived)', 'line', 'm1', data='bs_oca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ocap")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property and equipment, net', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{A1("cf_capex")})-({QE3("d_dep")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation & other amortization (incl. software) + acquired PP&E.')
    S('bs_rou', '  Operating lease right-of-use assets', 'line', 'm1', data='bs_rou', bs=True, e26=lambda: f'={B1("bs_rou")}', ae=lambda: f'={P("bs_rou")}')
    S('bs_int', '  Intangible assets, net', 'line', 'm1', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-({QE3("d_acqam")})+{V("ul_cons")}*{V("ul_intp")}',
      ae=lambda: f'={P("bs_int")}-{V("d_acqam")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − acquisition amortization + acquired intangibles (Ultra 2027E, M&A lever). Software amortization runs through PP&E in the model.')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, e26=lambda: f'={B1("bs_gw")}+{V("ul_cons")}*(1-{V("ul_intp")})',
      ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})',
      note='2027E: + Ultra consideration less acquired intangibles (assumption: no net working capital acquired). 2028E+: M&A lever.')
    S('bs_onca', '  Deferred tax assets & other long-term assets (derived)', 'line', 'm1', data='bs_onca', bs=True, e26=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_std', '  Current portion of long-term debt', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})',
      note='Revolver borrowings (none since FY2012) + notes / term-loan amortization due in the next fiscal year.')
    S('bs_ap', '  Accounts payable and other accrued expenses', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_acc', '  Accrued compensation and benefits', 'line', 'm1', data='bs_acc', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accp")}')
    S('bs_ocl', '  Operating lease liabilities (current) & other current liabilities (derived)', 'line', 'm1', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_std")}),SUM({V("bs_std")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt, net of current portion', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_lease', '  Operating lease liabilities, net of current portion', 'line', 'm1', data='bs_lease', bs=True, e26=lambda: f'={B1("bs_lease")}', ae=lambda: f'={P("bs_lease")}')
    S('bs_ol', '  Deferred tax liabilities & other long-term liabilities (derived)', 'line', 'm1', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{A1("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_std")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Stockholders' equity (attributable to common stockholders)", 'line', 'm1', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+({QE3("is_nic")})+({V("cf_div")}-{A1("cf_div")})+({V("cf_bb")}-{A1("cf_bb")})+({V("cf_sbc")}-{A1("cf_sbc")})'
                   f'+({V("cf_eq")}-{A1("cf_eq")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_nic")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_eq")}',
      note='+ net income − dividends − repurchases (treasury stock) + stock-based compensation + stock issuance (AOCI held flat).')
    S('bs_nci', '  Non-controlling interests (FY2022–25)', 'line', 'm1', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}', ae=lambda: f'={P("bs_nci")}')
    S('bs_teq', 'Total equity', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<={TL()},0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<={TL()},0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},1)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<={TL()},0,ROUND({V("bs_cash")}-{V("cf_end")},1)),"")')
    S('bs_shares', '  Memo: Class A shares outstanding at period end (m; XBRL from FY2017)', 'memo', 'm1', data='bs_shares', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input); revenue basis (Booz Allen has no inventories)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'],
      note=V0['wc']['dso_note'])
    S('wc_ocap', '  Other current assets % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', e26_in=V0['wc']['oca'], ae_in=V0['wc']['oca'])
    S('wc_app', '  Accounts payable & accrued expenses % of revenue (FY2027E: solved to the FCF guidance)', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_rev")},"")',
      e26=lambda: f'=({CH(SC["out_fcf"])}-{V("wc_fcf_pre")}+{B1("bs_ap")})/{V("wc_rev")}', ae=lambda: f'={P("wc_app")}',
      note=('FY2027E: solved so that FY27 free cash flow = the guidance end-point for the active scenario (one working-capital plug, closed form; Q1/27 10.6% incl. '
            '$172m of accrued expenses acquired with Defy, FY2026 year end 8.1%). 2028E+: held at the FY2027E level.'))
    S('wc_fcf_pre', '  FY2027E free cash flow before the payables calibration (helper: all CFO lines except Δ payables & accrued + capex)', 'line', 'm1',
      e26=lambda: (f'={V("cf_ni")}+{V("cf_dda")}+{V("cf_sbc")}+{V("cf_def")}+{A1("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_oca")}-{B1("bs_oca")})'
                   f'+({V("bs_acc")}-{B1("bs_acc")})+({V("bs_ocl")}-{B1("bs_ocl")})+{V("cf_capex")}'))
    S('wc_fcf_chk', '  Check: FY27 free cash flow vs guidance end-point (should be 0)', 'check', 'm1', e26=lambda: f'=ROUND({V("fcf")}-{CH(SC["out_fcf"])},1)')
    S('wc_accp', '  Accrued compensation & benefits % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_acc")}/{V("wc_rev")},"")', e26_in=V0['wc']['acc'], ae_in=V0['wc']['acc'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables & accrued − accrued compensation − other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_acc")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-period column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration (net of cash acquired)'), ('nwc', 'Receivables & other net working capital acquired (net)'),
                   ('intang', 'Intangible assets (customer contracts, technology)'), ('gw', 'Goodwill'), ('oth', 'Other net assets / (liabilities)')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', ppa=k)
    S('ppa_chk', '  Check: net assets acquired − consideration (should be 0; ±0.15, ±0.6 from Q4 FY25)', 'check', 'm1',
      all=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_nwc")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_oth")})-{V("ppa_cons")},1),"")'))
    S('ppa_names', '  Deal closed in the period', 'text', 'gen', ppa='names', textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & RSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.07)
    S('ds_h', 'Debt schedule (senior notes and term loans repaid / refinanced at maturity; revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current portion + long-term debt, carrying value)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_06_30'])
    S('ds_notes', '  Senior notes & term loans (carrying value)', 'sched', 'm1', hist=lambda: f'={V("ds_total")}',
      e26=lambda: f'={B1("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm1', e26_in=V0['iss_notes'][2027], ae_in={y: V0['iss_notes'][y] for y in range(2028, 2032)},
      note=MAN['debt']['new_notes'] + ' 2029E+: maturing notes and the Term Loan A-2 balloon assumed refinanced with new notes (assumption).')
    S('ds_repay', '  Notes / term loans repaid (input)', 'sched', 'm1', e26_in=V0['repay'][2027], ae_in={y: V0['repay'][y] for y in range(2028, 2032)}, note=V0['repay_note'])
    S('ds_mat', '  Maturities in the following fiscal year (current portion)', 'sched', 'm1', e26_in=V0['mat'][2027], ae_in={y: V0['mat'][y] for y in range(2028, 2032)})
    S('ds_pre', '  Cash before revolver draws / repayments (opening cash + CFO + CFI + buybacks, dividends, equity, other financing − notes repaid + issued)', 'sched', 'm1',
      e26=lambda: (f'={B1("bs_cash")}+({V("cf_cfo")}-{A1("cf_cfo")})+({V("cf_cfi")}-{A1("cf_cfi")})+({V("cf_bb")}-{A1("cf_bb")})+({V("cf_div")}-{A1("cf_div")})'
                   f'+({V("cf_eq")}-{A1("cf_eq")})+({V("cf_ofin")}-{A1("cf_ofin")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_eq")}+{V("cf_ofin")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'], note=V0['min_cash_note'])
    S('ds_rev', '  Revolving credit facility (year end)', 'sched', 'm1',
      e26=lambda: f'=MAX(0,N({B1("ds_rev")})+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$1.5bn revolving credit facility (undrawn at 30-Jun-2026). Shortfalls below the minimum cash balance are drawn; surplus repays the revolver.')
    S('ds_head', '  Memo: revolver headroom vs the $1.5bn commitment (negative = would need other financing)', 'memo_calc', 'm1',
      e26=lambda: f'=1500-{V("ds_rev")}', ae=lambda: f'=1500-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes & term loans %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=0.055, note='Term SOFR + 1.00–1.63% (Eleventh Amendment); assumption ~5.5%.')
    S('ds_fees', '  Commitment fees & amortization of debt issuance costs ($m)', 'sched', 'm1', ae_in=6.0)
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.03, note='Netted in interest expense, net from Q4 FY2025. Assumption ~3%.')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2028E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_eq")}-{V("cf_ofin")}')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (adjusted EBITDA − total D&A)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.25)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. current debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable to common stockholders', 'line', 'm1', ann=True, all=lambda: f'={V("is_nic")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x) — company "net leverage ratio" basis', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q1}{R["sh_dil"]}-{Q1}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Non-controlling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBITA', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebita")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted diluted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
