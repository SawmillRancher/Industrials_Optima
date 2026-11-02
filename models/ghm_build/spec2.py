"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum, ACT, B1, ECa

def build_spec2(V0):
    S = add
    def rem(key):               # FY2027E balance roll: remaining flow (FY - Q1 actual)
        return f'({V(key)}-{ACT(key)})'
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2027E = full year with Q1 actual; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (loss)', 'line', 'm1', data='cf_ni', flow=True, ec=lambda: f'={V("is_ni")}', ae=lambda: f'={V("is_ni")}')
    S('cf_adj', 'Non-cash items:', 'sub', 'gen')
    S('cf_dep', '  Depreciation (FY2006–10: depreciation & amortization)', 'line', 'm1', data='cf_dep', flow=True, ec=lambda: f'={V("d_dep")}', ae=lambda: f'={V("d_dep")}')
    S('cf_amort', '  Amortization (intangibles, inventory step-up)', 'line', 'm1', data='cf_amort', flow=True, ec=lambda: f'={V("d_amort")}', ae=lambda: f'={V("d_amort")}')
    S('cf_pens', '  Amortization of actuarial losses / prior service cost (pension)', 'line', 'm1', data='cf_pens', flow=True, ec=lambda: f'={ACT("cf_pens")}', ae_in=0.0,
      note='Non-cash reclassification from other comprehensive income; forecast nil (assumption).')
    S('cf_sbc', '  Equity-based compensation', 'line', 'm1', data='cf_sbc', flow=True, ec=lambda: f'={V("d_sbc")}', ae=lambda: f'={V("d_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, ec=lambda: f'={ACT("cf_def")}', ae_in=V0['def_ae'])
    S('cf_oth', '  (Gain) loss on PP&E; change in fair value of contingent consideration', 'line', 'm1', data='cf_oth', flow=True,
      ec=lambda: f'={ACT("cf_oth")}', ae=lambda: f'={V("d_eo")}', note='2028E+: FlackTek earn-out fair-value accretion (non-cash; liability grows).')
    S('cf_wc', '  Working capital & other operating items, net (derived)', 'line', 'm1', data='cf_wc', flow=True,
      ec=lambda: (f'={ACT("cf_wc")}-({V("bs_ar")}-{B1("bs_ar")})-({V("bs_unb")}-{B1("bs_unb")})-({V("bs_inv")}-{B1("bs_inv")})'
                  f'+({V("bs_ap")}-{B1("bs_ap")})+({V("bs_accc")}-{B1("bs_accc")})+({V("bs_acco")}-{B1("bs_acco")})+({V("bs_dep")}-{B1("bs_dep")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_unb")}-{P("bs_unb")})-({V("bs_inv")}-{P("bs_inv")})'
                  f'+({V("bs_ap")}-{P("bs_ap")})+({V("bs_accc")}-{P("bs_accc")})+({V("bs_acco")}-{P("bs_acco")})+({V("bs_dep")}-{P("bs_dep")})'),
      note=('History: net cash from operations − the non-cash lines above (release cash-flow statements). Forecast linked to the balance sheet: '
            '−Δ(receivables, unbilled revenue, inventories) + Δ(payables, accrued compensation, accrued expenses, customer deposits).'))
    S('cf_cfo', 'Net cash provided (used) by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchase of property, plant & equipment, net of disposals', 'line', 'm1', data='cf_capex', flow=True,
      ec=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2027E: FY27 guidance mid-point ($18–22m). 2028E+: net sales × capex % (company framework: capex 7–10% of sales).')
    S('cf_acq', 'Acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True, ec=lambda: f'={ACT("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='FY2011 Energy Steel; FY2022 Barber-Nichols; FY2024 P3; FY2026 Xdot and FlackTek; Q1 FY27 FlackTek working-capital settlement (+$1.6m). 2028E+: M&A lever.')
    S('cf_invest', 'Purchases / redemptions of investments, net (FY2006–2021)', 'line', 'm1', data='cf_invest', flow=True, ec=lambda: f'={ACT("cf_invest")}', ae_in=0.0)
    S('cf_oinv', 'Other investing activities, net (derived)', 'line', 'm1', data='cf_oinv', flow=True, ec=lambda: f'={ACT("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used by investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt', 'Debt borrowings / (repayments), incl. finance leases, net', 'line', 'm1', data='cf_debt', flow=True,
      ec=lambda: f'={ACT("cf_debt")}+{V("ds_total")}-{B1("ds_total")}', ae=lambda: f'={V("ds_net")}',
      note='Per the debt schedule: revolver drawn or repaid to the minimum cash balance. Q1 FY27: $13.0m repaid from the PIPE proceeds.')
    S('cf_div', 'Dividends paid', 'line', 'm1', data='cf_div', flow=True, ec=lambda: f'={ACT("cf_div")}', ae=lambda: f'=-{V("dps")}*{V("bb_beg")}')
    S('cf_stock', 'Issuance of common stock, net of costs (FY2027: $50m PIPE)', 'line', 'm1', data='cf_stock', flow=True,
      ec=lambda: f'={ACT("cf_stock")}+{V0["stock_rem"]}', ae_in=V0['stock_ae'])
    S('cf_withhold', 'Tax withholdings on net share settlement of restricted stock units', 'line', 'm1', data='cf_withhold', flow=True,
      ec=lambda: f'={ACT("cf_withhold")}+{V0["withhold_rem"]}', ae_in=V0['withhold_ae'])
    S('cf_bb', 'Purchase of treasury stock (repurchase program)', 'line', 'm1', data='cf_bb', flow=True, ec=lambda: f'={ACT("cf_bb")}-{CH(SC["bb27"])}',
      ae=lambda: f'=-{V("lev_bb")}',
      note='$18m program authorized Jan-2015; no purchases FY2024–Q1 FY27. 2028E+: net-cash cap plug (surplus cash above the cap returned via buybacks).')
    S('cf_ofin', 'Other financing, net (derived)', 'line', 'm1', data='cf_ofin', flow=True, ec=lambda: f'={ACT("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided (used) by financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm1', data='cf_fx', flow=True, ec=lambda: f'={ACT("cf_fx")}', ae_in=0.0)
    S('cf_hfs', 'Change in cash classified within assets held for sale (FY2019–20, commercial nuclear business)', 'line', 'm1', data='cf_hfs', flow=True,
      ec=lambda: '=0', ae_in=0.0)
    S('cf_net', 'Net increase (decrease) in cash and cash equivalents', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})+N({V("cf_hfs")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}+{V("cf_hfs")}')
    S('cf_beg', 'Cash and cash equivalents — beginning of period', 'line', 'm1', data='cf_beg', ec=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash and cash equivalents — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + net change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.0015,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},3)),"")')
    S('cf_chk2', '  Check: CFO + CFI + CFF + FX (+ held-for-sale cash) = net change (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),IF(ABS({V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})+N({V("cf_hfs")})-{V("cf_net")})<=0.0015,0,ROUND({V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})+N({V("cf_hfs")})-{V("cf_net")},3)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (model definition: CFO − net capex; Graham publishes no FCF measure)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / Adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note=('2028E+ input stepping down from 6% to 4%: the FY2025–27 capacity programme (Navy facility, cryogenic test, Arvada and Batavia '
                                   'automation) is "nearing completion" (Q4 FY26 presentation); FY2006–22 capex was ~1–3% of sales. Company framework 7–10% for organic growth (assumption below it).'))
    S('capex_dep', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2027E from shares outstanding at 30-Jun-2026 (incl. the 600k-share PIPE); 2028E+ buybacks via the net-cash cap')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', ec=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm; 2027E = Q2–Q4)', 'line', 'm', ec=lambda: f'={CH(SC["bb27"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm3', ec=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans, net of shares withheld (m)', 'driver', 'm3', ec_in=V0['iss_rem'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm3', ec=lambda: f'={B1("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2027E begins from shares outstanding at 30-Jun-2026 (11.727m, 10-Q balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm3', ec=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', ec=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q2/27 (m)', 'memo', 'm3', ec=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET (as in the releases)', 'section',
      note='BS FORECAST — 2027E rolled forward from the 30-Jun-2026 balance sheet + Q2–Q4 flows; 2028E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_invest', '  Investments (fixed-income securities; to FY2021)', 'line', 'm1', data='bs_invest', bs=True, ec=lambda: f'={B1("bs_invest")}', ae=lambda: f'={P("bs_invest")}')
    S('bs_ar', '  Trade accounts receivable, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365')
    S('bs_unb', '  Unbilled revenue (contract assets)', 'line', 'm1', data='bs_unb', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_unb")}/365')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Prepaid expenses, income taxes receivable & other current assets (derived)', 'line', 'm1', data='bs_oca', bs=True,
      ec=lambda: f'={B1("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant & equipment, net', 'line', 'm1', data='bs_ppe', bs=True,
      ec=lambda: f'={B1("bs_ppe")}-{rem("cf_capex")}-{rem("d_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='Roll-forward: prior − capex (negative cash flow) − depreciation + acquired PP&E.')
    S('bs_pen', '  Prepaid pension asset', 'line', 'm1', data='bs_pen', bs=True, ec=lambda: f'={B1("bs_pen")}', ae=lambda: f'={P("bs_pen")}')
    S('bs_rou', '  Operating lease assets', 'line', 'm1', data='bs_rou', bs=True, ec=lambda: f'={B1("bs_rou")}', ae=lambda: f'={P("bs_rou")}')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, ec=lambda: f'={B1("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net (customer relationships, technology, tradenames, backlog)', 'line', 'm1', data='bs_int', bs=True,
      ec=lambda: f'={B1("bs_int")}-{rem("d_amort")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − amortization + acquired intangibles (M&A lever).')
    S('bs_onca', '  Deferred income tax asset & other assets (derived)', 'line', 'm1', data='bs_onca', bs=True, ec=lambda: f'={B1("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_std', '  Short-term debt & current portion of long-term debt / finance leases', 'line', 'm1', data='bs_std', bs=True, fc=lambda: f'={V("ds_fl")}')
    S('bs_ap', '  Accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_accc', '  Accrued compensation', 'line', 'm1', data='bs_accc', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accc")}')
    S('bs_acco', '  Accrued expenses & other current liabilities', 'line', 'm1', data='bs_acco', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_acco")}')
    S('bs_dep', '  Customer deposits (contract liabilities)', 'line', 'm1', data='bs_dep', bs=True, fc=lambda: f'={V("ob_bkl")}*{V("wc_depb")}',
      note='Forecast as % of backlog: advance billings on long-cycle Defense programs.')
    S('bs_opl', '  Operating lease liabilities — current', 'line', 'm1', data='bs_opl', bs=True, ec=lambda: f'={B1("bs_opl")}', ae=lambda: f'={P("bs_opl")}')
    S('bs_ocl', '  Income taxes payable & other current liabilities (derived)', 'line', 'm1', data='bs_ocl', bs=True, ec=lambda: f'={B1("bs_ocl")}', ae=lambda: f'={P("bs_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_std")}),SUM({V("bs_std")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt (revolving credit facility) & finance lease obligations', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_rev")}')
    S('bs_opln', '  Operating lease liabilities — non-current', 'line', 'm1', data='bs_opln', bs=True, ec=lambda: f'={B1("bs_opln")}', ae=lambda: f'={P("bs_opln")}')
    S('bs_ol', '  Deferred income taxes, pension & postretirement, earn-out & other liabilities (derived)', 'line', 'm1', data='bs_ol', bs=True,
      ec=lambda: f'={B1("bs_ol")}+{rem("cf_def")}+{rem("cf_oth")}', ae=lambda: f'={P("bs_ol")}+{V("cf_def")}+{V("cf_oth")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tcl")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_ol")}),"")')
    S('bs_eq', "  Total stockholders' equity", 'line', 'm1', data='bs_eq', bs=True,
      ec=lambda: (f'={B1("bs_eq")}+{rem("is_ni")}+{rem("cf_div")}+{rem("cf_bb")}+{rem("cf_sbc")}+{rem("cf_stock")}+{rem("cf_withhold")}'),
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_stock")}+{V("cf_withhold")}',
      note='+ net income − dividends − repurchases + equity-based compensation + stock issued − withholding (other comprehensive income held flat).')
    S('bs_nci', '  Noncontrolling interests (none)', 'line', 'm1', ec=lambda: '=0', ae=lambda: '=0')
    S('bs_teq', 'Total equity', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")}+N({V("bs_nci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.0015,0,ROUND({V("bs_ta")}-{V("bs_tle")},3)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.0015,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},3)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-{V("cf_end")})<=0.0015,0,ROUND({V("bs_cash")}-{V("cf_end")},3)),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m; XBRL, issued less treasury)', 'memo', 'm3', data='bs_shares', bs=True,
      ec=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input) at fiscal-year-end (31-Mar-2026) levels; year ends compared with year ends')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of products sold — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    W = V0['wc']
    S('wc_dso', '  DSO — receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', ec_in=W['dso'], ae_in=W['dso'])
    S('wc_unb', '  Unbilled revenue days — contract assets / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_unb")}/{V("wc_rev")}*365,"")', ec_in=W['unb'], ae_in=W['unb'])
    S('wc_dio', '  Inventory days — inventories / cost of products sold × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', ec_in=W['dio'], ae_in=W['dio'])
    S('wc_dpo', '  Payable days — payables / cost of products sold × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', ec_in=W['dpo'], ae_in=W['dpo'])
    S('wc_accc', '  Accrued compensation % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_accc")}/{V("wc_rev")},"")', ec_in=W['accc'], ae_in=W['accc'])
    S('wc_acco', '  Accrued expenses % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_acco")}/{V("wc_rev")},"")', ec_in=W['acco'], ae_in=W['acco'])
    S('wc_depb', '  Customer deposits % of backlog', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_dep")}/{V("ob_bkl")},"")', ec_in=W['depb'], ae_in=W['depb'],
      note=W['note'])
    S('wc_nwc', '  Operating NWC (receivables + unbilled + inventories − payables − accrued − customer deposits)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_unb")}+{V("bs_inv")}-{V("bs_ap")}-{V("bs_accc")}-{V("bs_acco")}-{V("bs_dep")},"")')
    S('wc_nwc_p', '  NWC % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-quarter column)', 'sub', 'gen')
    for k, lab in [('cons', 'Purchase price (cash + shares + earn-out at fair value)'),
                   ('ca', 'Current assets acquired (cash, receivables, unbilled, inventories, prepaid)'), ('ppe', 'Property, plant & equipment'),
                   ('intang', 'Intangible assets (customer relationships, technology, tradename, backlog)'), ('gw', 'Goodwill (tax-deductible)'),
                   ('onca', 'Operating lease & other non-current assets'), ('cl', 'Current liabilities assumed (incl. customer deposits)'), ('debt', 'Debt assumed'),
                   ('ncl', 'Operating lease & other non-current liabilities')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − purchase price (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_debt")})-N({V("ppa_ncl")})-{V("ppa_cons")},3),"")'))
    S('ppa_names', '  Deal closed in the quarter', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; RSUs / PSUs)', 'sched', 'm3', ae_in=V0['dil'])
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (finance leases held; Wells Fargo revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (short-term + long-term debt & finance leases)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_std")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_fl")}+{V("ds_rev")}', note=MAN['debt']['at_2026_06_30'])
    S('ds_fl', '  Current debt & finance leases (held at the 30-Jun-2026 level)', 'sched', 'm1', data='bs_std', ec=lambda: f'={B1("bs_std")}', ae=lambda: f'={P("ds_fl")}')
    S('ds_pre', '  Cash before revolver draws / repayments (opening cash + CFO + CFI + buybacks, dividends, equity, other financing + FX)', 'sched', 'm1',
      ec=lambda: (f'={B1("bs_cash")}+{rem("cf_cfo")}+{rem("cf_cfi")}+{rem("cf_bb")}+{rem("cf_div")}+{rem("cf_stock")}+{rem("cf_withhold")}'
                  f'+{rem("cf_ofin")}+{rem("cf_fx")}+{rem("cf_hfs")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_bb")}+{V("cf_div")}+{V("cf_stock")}+{V("cf_withhold")}+{V("cf_ofin")}+{V("cf_fx")}+{V("cf_hfs")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', ec_in=V0['min_cash'], ae_in=V0['min_cash'],
      note='Assumption: $15m (cash $6.6m at 31-Mar-2026 with $13m drawn; $21.6m at 31-Mar-2025).')
    S('ds_rev', '  Revolving credit facility & long-term finance leases (period end)', 'sched', 'm1', data='bs_ltd',
      ec=lambda: f'=MAX(0,{B1("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note=MAN['debt']['facility'] + ' Shortfalls below the minimum cash balance are drawn; surplus repays the revolver.')
    S('ds_head', '  Memo: revolver headroom vs the $80m commitment less ~$5.5m letters of credit (negative = other financing needed)', 'memo_calc', 'm1',
      ec=lambda: f'=80-5.52-{V("ds_rev")}', ae=lambda: f'=80-5.52-{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', ec=lambda: f'=IFERROR({V("ds_total")}-{B1("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=0.052, note='SOFR (3.68% at 31-Mar-2026) + 1.25–2.50% margin (assumption ~5.2%).')
    S('ds_fees', '  Unused commitment & letter-of-credit fees ($m)', 'sched', 'm1', ae_in=0.2, note='Unused fee 0.10–0.20% on $80m + LC fees at the SOFR margin on ~$5.5m.')
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.03, note='Assumption (money-market yields ~3–4%).')
    S('lev_h', 'Net-cash cap buybacks (repurchases plug to a target net debt / Adjusted EBITDA, 2028E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / Adjusted EBITDA (x) (scenario; negative = net cash cap)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_total")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_stock")}-{V("cf_withhold")}-{V("cf_ofin")}-{V("cf_fx")}-{V("cf_hfs")}')
    S('lev_tgt', '  Target net debt = target leverage × Adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to the net-cash cap', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Net cash above the cap is returned via buybacks (existing $18m authorization; assumption); feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('d_da', 'is_rev'))
    S('hr_amort', '  Amortization % of net sales', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_rd', '  Book-to-bill — trailing four quarters (x)', 'line', 'x2',
      all=lambda: (f'=IFERROR(SUM({QC[(CTX.col.year, 1)].c}{R["ob_ord"]}:{QC[(CTX.col.year, CTX.col.q)].c}{R["ob_ord"]})'
                   f'/SUM({QC[(CTX.col.year, 1)].c}{R["is_rev"]}:{QC[(CTX.col.year, CTX.col.q)].c}{R["is_rev"]}),"")') if CTX.col.q else None)
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBITA after SBC and cash adjusting costs)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'NOPAT base (Adjusted EBITA − SBC − cash adjusting costs)', 'line', 'm1', ann=True, all=lambda: f'={V("r_nopb")}')
    S('ra_t', 'Tax rate (effective rate, bounded 15–40%; 23% where not meaningful)', 'line', 'pct', ann=True,
      all=lambda: f'=IFERROR(IF(AND({V("is_etr")}>=0.15,{V("is_etr")}<=0.4),{V("is_etr")},0.23),0.23)')
    S('ra_nopat', 'NOPAT = NOPAT base × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − cash − investments', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_invest")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = NOPAT base / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_std")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("bs_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt (cash) = Total debt − cash − investments', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    S('lv_gx', 'Total debt / Adjusted EBITDA (x) — covenant ≤ 3.50x (bank definition differs)', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("ds_total")}/{V("r_adj")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', ec_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm3', ec=lambda: f'={V("bb_end")}+({Q1}{R["sh_dil"]}-{Q1}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', ec=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (cash) (USDm)', 'line', 'm', ec=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', ec=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', ec=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBITA', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebita")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_evbk', '  EV / Backlog', lambda: f'=IFERROR({V("v_ev")}/{V("ob_bkl")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', ec=f, ae=f)
