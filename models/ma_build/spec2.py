"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, QQ, B1, E26a, QCHK

def build_spec2(V0):
    S = add
    def e26f(key, h2):          # FY2026E flow = H1-26 actual + Q3/Q4-26E estimates
        return lambda: f'={ACT(key)}+{h2()}'
    def d(key, base):           # change in a balance vs a base reference
        return f'({V(key)}-{base})'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = H1-26 actual + H2 estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (incl. non-controlling interests)', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_nit")}', e26=e26f('cf_ni', lambda: QQ('is_nit')))
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dda', '  Depreciation and amortization', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_da")}', e26=e26f('cf_dda', lambda: QQ('is_da')))
    S('cf_sbc', '  Share-based compensation', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("d_sbc")}', e26=e26f('cf_sbc', lambda: QQ('d_sbc')))
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={ACT("cf_def")}+{V0["def_h2"]}', ae_in=V0['def_ae'],
      note='Cash-flow statement. Forecast input.')
    S('cf_eqgl', '  (Gains) losses on equity investments & impairments', 'line', 'm', data='cf_eqgl', flow=True, e26=lambda: f'={ACT("cf_eqgl")}', ae_in=0.0)
    S('cf_wc', '  Customer incentives, working capital & other operating items, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={ACT("cf_wc")}-{d("bs_ar", B1("bs_ar"))}-{d("bs_set_a", B1("bs_set_a"))}-{d("bs_oca", B1("bs_oca"))}-{d("bs_onca", B1("bs_onca"))}'
                   f'+{d("bs_ap", B1("bs_ap"))}+{d("bs_set_l", B1("bs_set_l"))}+{d("bs_litl", B1("bs_litl"))}+{d("bs_accr", B1("bs_accr"))}+{d("bs_ocl", B1("bs_ocl"))}'
                   f'+{d("bs_ol", B1("bs_ol"))}-({V("cf_def")}-{ACT("cf_def")})'),
      ae=lambda: (f'=-{d("bs_ar", P("bs_ar"))}-{d("bs_set_a", P("bs_set_a"))}-{d("bs_oca", P("bs_oca"))}-{d("bs_onca", P("bs_onca"))}'
                  f'+{d("bs_ap", P("bs_ap"))}+{d("bs_set_l", P("bs_set_l"))}+{d("bs_litl", P("bs_litl"))}+{d("bs_accr", P("bs_accr"))}+{d("bs_ocl", P("bs_ocl"))}'
                  f'+{d("bs_ol", P("bs_ol"))}-{V("cf_def")}'),
      note=('History: net cash provided by operating activities − net income − D&A − share-based compensation − deferred taxes − equity-investment items. Includes the amortization '
            'of customer incentives net of incentive prepayments (prepaid expenses), settlement balances and accruals. Forecast linked to the balance sheet: −Δ operating assets + Δ operating '
            'liabilities (deferred taxes sit in other liabilities).'))
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchases of property and equipment & capitalized software', 'line', 'm', data='cf_capex', flow=True,
      e26=lambda: f'={ACT("cf_capex")}-{PT("pt_capex_h2")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='Property & equipment plus capitalized software (the company\'s capital expenditures). 2026E: H1 actual + H2 point estimate; 2027E+: net revenue × capex %.')
    S('cf_acq', 'Acquisition of businesses, net of cash acquired', 'line', 'm', data='cf_acq', flow=True,
      e26=lambda: f'={ACT("cf_acq")}-{V("bv_cons")}', ae=lambda: f'=-{V("m_spend")}',
      note='Vocalink 2017, Nets account-to-account 2021, Finicity 2020, Ekata 2021, Recorded Future Dec-2024; 2026E: BVNK $1.5bn (switch); 2027E+: M&A lever.')
    S('cf_oinv', 'Investment securities, equity investments & other investing, net (derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_bb', 'Purchases of treasury stock', 'line', 'm', data='cf_bb', flow=True, e26=lambda: f'={ACT("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E: H1 actual + H2 scenario input ($7.8bn authorization remaining at 27-Jul-2026; new program usually approved in December). 2027E+ = leverage plug.')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cf_div', flow=True,
      e26=lambda: f'={ACT("cf_div")}-{Q2}{R["dps"]}*{Q3E}{R["sh_basic"]}-{Q3E}{R["dps"]}*{Q4E}{R["sh_basic"]}',
      ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='Paid one quarter after declaration: 2026E H2 = the Q2 and Q3 declared dividends × shares. 2027E+: DPS declared × beginning shares (no circularity with buybacks).')
    S('cf_debt', 'Proceeds from / (payment of) debt, net (incl. commercial paper)', 'line', 'm', data='cf_debt', flow=True,
      e26=lambda: f'={ACT("cf_debt")}+{V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: notes repaid at maturity and refinanced (input), commercial paper drawn or repaid to the minimum cash balance.')
    S('cf_ofin', 'Tax withholdings on share-based payments, employee stock plans & other financing, net (derived)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={ACT("cf_ofin")}+{V0["ofin_h2"]}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash used in financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_bb")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash, cash equivalents and restricted cash', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period (from 2018 incl. restricted cash and restricted security deposits held for customers)', 'line_b', 'm', data='cf_end',
      fc=lambda: f'={V("cf_beg")}+{V("cf_net")}', note='ASU 2016-18 from 2018 (2017 comparatives recast in the 2018 releases; earlier years: cash and cash equivalents only). Q1-26: 10-Q figure (release typo, see comment).')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1.1,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},0)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=1.1,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},0)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model: CFO − property & equipment − capitalized software; Mastercard publishes no FCF in its releases)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('fcf_ret', '  Capital returned (buybacks + dividends) % of FCF', 'pct', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("fcf")}),ISNUMBER({V("cf_bb")})),IFERROR(-({V("cf_bb")}+{V("cf_div")})/{V("fcf")},""),"")')
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex (incl. capitalized software) % of net revenue', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")', ae_in=V0['capex_pct'],
      note='2027E+ input: FY2023–25 3.4–4.0% of net revenue; H1-26 4.6% (property additions).')
    S('capex_dep', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_da")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E = H2 from shares outstanding at 30-Jun-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2026E = H2)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net (m)', 'driver', 'm2', e26_in=V0['iss_h2'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from Class A + Class B shares outstanding at 30-Jun-2026 (877.2m, Q2-26 10-Q Note 10).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q3/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (condensed from the releases)', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + H2 flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}-{V("bs_rcash")}-{V("bs_rsd")}-N({V("bs_rco")})')
    S('bs_rcash', '  Restricted cash (litigation escrow to 2017; restricted cash & equivalents)', 'line', 'm', data='bs_rcash', bs=True,
      e26=lambda: f'={B1("bs_rcash")}', ae=lambda: f'={P("bs_rcash")}')
    S('bs_rsd', '  Restricted security deposits held for customers', 'line', 'm', data='bs_rsd', bs=True, e26=lambda: f'={B1("bs_rsd")}', ae=lambda: f'={P("bs_rsd")}',
      note='Held flat (offset by the matching liability).')
    S('bs_inv', '  Investments', 'line', 'm', data='bs_inv', bs=True, e26=lambda: f'={B1("bs_inv")}', ae=lambda: f'={P("bs_inv")}')
    S('bs_ar', '  Accounts receivable', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_set_a', '  Settlement assets', 'line', 'm', data='bs_set_a', bs=True, fc=lambda: f'={V("k_gdv")}*{V("wc_set")}')
    S('bs_oca', '  Prepaid expenses & other current assets (incl. customer-incentive prepayments; derived)', 'line', 'm', data='bs_oca', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, equipment and right-of-use assets, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B1("bs_ppe")}-({V("cf_capex")}-{ACT("cf_capex")})*{V("ppe_share")}-{QQ("is_da")}*{V("ppe_dshare")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}*{V("ppe_share")}-({V("is_da")}-N({V("bv_amort")})-N({V("m_amort")}))*{V("ppe_dshare")}',
      note='Roll-forward of the property & equipment share of capex and D&A (the capitalized-software share sits in intangible assets).')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True,
      e26=lambda: f'={B1("bs_gw")}+{V("bv_cons")}*(1-{V("bv_intp")})', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_intp")})')
    S('bs_int', '  Other intangible assets, net (incl. capitalized software)', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B1("bs_int")}-({V("cf_capex")}-{ACT("cf_capex")})*(1-{V("ppe_share")})-{QQ("is_da")}*(1-{V("ppe_dshare")})+{V("bv_cons")}*{V("bv_intp")}',
      ae=lambda: (f'={P("bs_int")}-{V("cf_capex")}*(1-{V("ppe_share")})-({V("is_da")}-N({V("bv_amort")})-N({V("m_amort")}))*(1-{V("ppe_dshare")})'
                  f'-N({V("bv_amort")})-N({V("m_amort")})+{V("m_spend")}*{V("m_intp")}'),
      note='Roll-forward: + capitalized software − its amortization + acquired intangibles − acquired-intangible amortization.')
    S('bs_onca', '  Deferred taxes, long-term customer-incentive prepayments, equity investments & other assets (derived)', 'line', 'm', data='bs_onca', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ap")}')
    S('bs_set_l', '  Settlement obligations', 'line', 'm', data='bs_set_l', bs=True, fc=lambda: f'={V("k_gdv")}*{V("wc_setl")}')
    S('bs_rsdl', '  Restricted security deposits held for customers (liability)', 'line', 'm', data='bs_rsdl', bs=True, fc=lambda: f'={V("bs_rsd")}')
    S('bs_litl', '  Accrued litigation (current; incl. obligations under litigation settlements to 2012)', 'line', 'm', data='bs_litl', bs=True,
      e26=lambda: f'={B1("bs_litl")}', ae=lambda: f'={P("bs_litl")}', note='Held flat: forecast provisions are assumed paid in the year.')
    S('bs_accr', '  Accrued expenses (incl. customer incentives payable)', 'line', 'm', data='bs_accr', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accr")}')
    S('bs_std', '  Short-term debt (commercial paper + notes due within 12 months)', 'line', 'm', data='bs_std', bs=True, fc=lambda: f'={V("ds_rev")}+MIN({V("ds_notes")},{V("ds_mat")})')
    S('bs_ocl', '  Other current liabilities (derived)', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_std")}')
    S('bs_ol', '  Deferred income taxes & other liabilities (incl. noncurrent litigation obligations, long-term taxes, leases; derived)', 'line', 'm', data='bs_ol', bs=True,
      e26=lambda: f'={B1("bs_ol")}+({V("cf_def")}-{ACT("cf_def")})', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_mez', '  Redeemable non-controlling interests (2019–23) / minority interest (2006–08)', 'line', 'm', data='bs_mez', bs=True, fc=lambda: '=0')
    S('bs_eq', "  Mastercard Incorporated stockholders' equity", 'line', 'm', data='bs_eq', bs=True,
      e26=lambda: (f'={B1("bs_eq")}+{QQ("is_ni")}+({V("cf_div")}-{ACT("cf_div")})+({V("cf_bb")}-{ACT("cf_bb")})+{QQ("d_sbc")}+({V("cf_ofin")}-{ACT("cf_ofin")})'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_ofin")}',
      note=('+ net income − dividends paid − repurchases + share-based compensation + employee-plan / withholding flows (AOCI held flat; the dividend payable is held in other '
            'current liabilities). Repurchased shares are held as Class A treasury stock.'))
    S('bs_nci', '  Non-controlling interests', 'line', 'm', data='bs_nci', bs=True, e26=lambda: f'={B1("bs_nci")}', ae=lambda: f'={P("bs_nci")}')
    S('bs_teq', 'Total equity', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+N({V("bs_mez")})+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=1.1,0,ROUND({V("bs_ta")}-{V("bs_tle")},0)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=1.1,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},0)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_rco', '  Memo: restricted cash held in prepaid / other assets (in cash-flow cash 2018–Q3-24; derived = CF cash − BS lines)', 'memo', 'm', data='bs_rc_oth', bs=True,
      fc=lambda: '=0', note='Mastercard\'s cash-flow cash includes restricted cash that the balance sheet carried inside prepaid / other assets until Q3-24 (separate line from Q4-24).')
    S('bs_chk_cash', '  Check: BS cash (+ restricted cash and security deposits from 2018, + memo) vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: (f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}+IF(ISNUMBER({V("bs_rco")}),{V("bs_rcash")}+{V("bs_rsd")}+{V("bs_rco")},0)-{V("cf_end")})<=1.1,0,'
                   f'ROUND({V("bs_cash")}+IF(ISNUMBER({V("bs_rco")}),{V("bs_rcash")}+{V("bs_rsd")}+{V("bs_rco")},0)-{V("cf_end")},0)),"")'))
    S('bs_shares', '  Memo: Class A + Class B shares outstanding at period end (m; equity captions; to 2013 not parsed)', 'memo', 'm1', data='bs_shares', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & BALANCE-SHEET DRIVERS', 'section', note='WORKING CAPITAL — forecast drivers (blue = input, at FY2025 year-end levels)')
    S('wc_rev', '  Net revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    for k, lab, bsk, base, key in (('wc_dso', '  DSO — receivables / net revenue × 365', 'bs_ar', 'wc_rev', 'dso'),):
        S(k, lab, 'line', 'd', hist=lambda bsk=bsk, base=base: f'=IFERROR({V(bsk)}/{V(base)}*365,"")', e26_in=V0['wc'][key], ae_in=V0['wc'][key])
    S('wc_set', '  Settlement assets ÷ GDV (USD m per USD bn of period GDV)', 'line', 'm2', hist=lambda: f'=IFERROR({V("bs_set_a")}/{V("k_gdv")},"")',
      e26_in=V0['wc']['set'], ae_in=V0['wc']['set'])
    S('wc_setl', '  Settlement obligations ÷ GDV', 'line', 'm2', hist=lambda: f'=IFERROR({V("bs_set_l")}/{V("k_gdv")},"")', e26_in=V0['wc']['setl'], ae_in=V0['wc']['setl'])
    for k, lab, bsk, key in (('wc_oca', '  Prepaid & other current assets % of net revenue', 'bs_oca', 'oca'),
                             ('wc_onca', '  Other noncurrent assets % of net revenue', 'bs_onca', 'onca'),
                             ('wc_ap', '  Accounts payable % of net revenue', 'bs_ap', 'ap'),
                             ('wc_accr', '  Accrued expenses % of net revenue', 'bs_accr', 'accr'),
                             ('wc_ocl', '  Other current liabilities % of net revenue', 'bs_ocl', 'ocl')):
        S(k, lab, 'pct', 'pct', hist=lambda bsk=bsk: f'=IFERROR({V(bsk)}/{V("wc_rev")},"")', e26_in=V0['wc'][key], ae_in=V0['wc'][key],
          note=V0['wc']['note'] if k == 'wc_oca' else None)
    S('wc_nwc', '  Operating NWC (receivables + settlement assets + prepaid & other − payables − settlement obligations − accrued − other current)', 'line', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_set_a")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_set_l")}-{V("bs_accr")}-{V("bs_ocl")},"")'))
    S('wc_nwc_p', '  NWC % of net revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    S('ppe_share', '  Property & equipment share of capex (rest = capitalized software)', 'driver', 'pct', e26_in=V0['ppe_share'], ae_in=V0['ppe_share'])
    S('ppe_dshare', '  Depreciation share of organic D&A (rest = amortization of capitalized software / intangibles)', 'driver', 'pct', e26_in=V0['ppe_dshare'], ae_in=V0['ppe_dshare'],
      note='FY2025: amortization of intangible assets $760m (10-K) of $1,1xx m D&A; assumption held.')
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & RSUs)', 'sched', 'm1', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.09)
    S('ds_h', 'Debt schedule (senior notes repaid at maturity and refinanced; commercial paper drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + long-term debt)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}', note=MAN['debt']['at_2026_06_30'])
    S('ds_notes', '  Senior notes (carrying amount)', 'sched', 'm',
      e26=lambda: f'={B1("ds_total")}-{V0["cp_jun"]}-{V("ds_repay")}+{V("ds_iss")}', ae=lambda: f'={P("ds_notes")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_iss', '  New notes issued (input)', 'sched', 'm', e26_in=V0['iss_notes'][FYC], ae_in={y: V0['iss_notes'][y] for y in range(FYC + 1, FYL + 1)},
      note='2026E H2: none (the $5.0bn June-2026 issue is in H1). 2027E+: maturities refinanced plus incremental issuance (assumption, gross debt rising with EBITDA).')
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=V0['repay'][FYC], ae_in={y: V0['repay'][y] for y in range(FYC + 1, FYL + 1)},
      note=MAN['debt']['maturity_note'])
    S('ds_mat', '  Maturities in the following year (current portion)', 'sched', 'm', e26_in=V0['mat'][FYC], ae_in={y: V0['mat'][y] for y in range(FYC + 1, FYL + 1)})
    S('ds_pre', '  Cash before commercial-paper draws / repayments (opening cash + CFO + CFI + buybacks, dividends, other financing + FX − notes repaid + issued)', 'sched', 'm',
      e26=lambda: (f'={B1("cf_end")}+({V("cf_cfo")}-{ACT("cf_cfo")})+({V("cf_cfi")}-{ACT("cf_cfi")})+({V("cf_bb")}-{ACT("cf_bb")})+({V("cf_div")}-{ACT("cf_div")})'
                   f'+({V("cf_ofin")}-{ACT("cf_ofin")})+({V("cf_fx")}-{ACT("cf_fx")})-{V("ds_repay")}+{V("ds_iss")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_ofin")}+{V("cf_fx")}-{V("ds_repay")}+{V("ds_iss")}')
    S('ds_min', '  Minimum cash balance (cash-flow basis: incl. restricted cash and security deposits)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'],
      note=V0['min_cash_note'])
    S('ds_rev', '  Commercial paper / revolver (year end)', 'sched', 'm',
      e26=lambda: f'=MAX(0,{V0["cp_jun"]}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note='$8bn commercial-paper program backed by the $8bn revolver (Nov-2030; undrawn); $710m CP at 30-Jun-2026. Shortfalls below the minimum cash balance are drawn; surplus repays CP.')
    S('ds_head', '  Memo: CP / revolver headroom vs the $8.0bn facility (negative = would need other financing)', 'memo_calc', 'm',
      e26=lambda: f'=8000-{V("ds_rev")}', ae=lambda: f'=8000-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{B1("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on opening notes %', 'sched', 'pct', ae_in=V0['r_notes'], note=MAN['debt']['coupon_note'])
    S('ds_r_rev', '  Interest rate on opening commercial paper %', 'sched', 'pct', ae_in=0.040, note='CP at 3.84% weighted average at 30-Jun-2026.')
    S('ds_fees', '  Discount / issuance-cost amortization, hedges & other interest ($m)', 'sched', 'm', ae_in=40.0)
    S('ds_r_cash', '  Investment income yield on opening cash & investments %', 'sched', 'pct', ae_in=0.028,
      note='H1-26 investment income $169m on ~$13–14bn average cash and investments (~2.5% annualised); held at 2.8% then flat (assumption).')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}+{P("bs_rcash")}+{P("bs_rsd")}-{P("bs_inv")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}-{V("cf_fx")}',
      note='Same net-debt definition as the leverage ratio (total debt − unrestricted cash − investments); restricted cash and security deposits held flat.')
    S('lev_tgt', '  Target net debt = target leverage × adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  D&A % of net revenue', 'pct', 'pct', all=ratio('is_da', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    S('hr_lit', '  Litigation provisions (special items) % of net revenue', 'pct', 'pct', all=ratio('d_lit', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted operating income, full-cost)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (= adjusted operating income, full-cost)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (adjusted)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,0.2)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity (incl. redeemable NCI)', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")}+N({V("bs_mez")}),"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash & investments (unrestricted)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-{V("bs_inv")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. short-term debt)', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable to Mastercard', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Mastercard stockholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity (year end; equity reduced by buybacks)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash & investments', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / adjusted EBITDA (x)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Non-controlling interests (USDm)', 'line', 'm', e26=lambda: f'={V("bs_nci")}+N({V("bs_mez")})', ae=lambda: f'={V("bs_nci")}+N({V("bs_mez")})')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating income', lambda: f'=IFERROR({V("v_ev")}/{V("o_aoi")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
