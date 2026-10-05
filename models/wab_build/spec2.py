"""Row specification part 2: cash flow, buybacks, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def h26(key):   # 1H/26 actual for a flow row
    return f'(BW{R[key]}+BX{R[key]})'

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (incl. noncontrolling interest)', 'line', 'm', data='cfq.net_income', flow=True, cf=True, fc=lambda: f'={V("is_nitot")}',
      e26=lambda: f'={h26("cf_ni")}+BY{R["is_nitot"]}+BZ{R["is_nitot"]}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm', data='cfq.dda', flow=True, cf=True, fc=lambda: f'={V("is_dda")}',
      e26=lambda: f'={h26("cf_dda")}+BY{R["is_dda"]}+BZ{R["is_dda"]}', note='2026E = 1H/26 actual (incl. deferred debt-cost amortization) + 2H/26 model D&A.')
    S('cf_sbc', '  Stock-based compensation', 'line', 'm', data='cfq.sbc', flow=True, cf=True, fc=lambda: f'={V("is_sbc")}',
      e26=lambda: f'={h26("cf_sbc")}+BY{R["is_sbc"]}+BZ{R["is_sbc"]}')
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cfq.deferred_tax', flow=True, cf=True,
      e26=lambda: f'={h26("cf_def")}', ae_in=V0['def_tax_ae'],
      note='2027E+: deferred tax benefit as acquired-intangible amortization (book) exceeds tax amortization (input).')
    S('cf_oth', '  (Gains) losses, impairments & other operating items, net (derived)', 'line', 'm', data='cfq.oth', flow=True, cf=True,
      e26=lambda: f'={h26("cf_oth")}', ae_in=0.0)
    S('cf_wc', '  Changes in operating assets & liabilities (working capital), net', 'line', 'm', data='cfq.wc_change', flow=True, cf=True,
      e26=lambda: (f'={h26("cf_wc")}-({V("bs_ar")}-BX{R["bs_ar"]})-({V("bs_inv")}-BX{R["bs_inv"]})+({V("bs_ap")}-BX{R["bs_ap"]})'
                   f'+({V("bs_cdep")}-BX{R["bs_cdep"]})+({V("bs_acc")}-BX{R["bs_acc"]})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})+({V("bs_ap")}-{P("bs_ap")})'
                  f'+({V("bs_cdep")}-{P("bs_cdep")})+({V("bs_acc")}-{P("bs_acc")})'),
      note='Linked to the balance sheet: −Δ(receivables incl. unbilled, inventories) + Δ(payables, customer deposits, accrued compensation). 2026E = 1H/26 actual + 2H balance-sheet change from 30-Jun-26.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cfq.cfo', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchase of property, plant & equipment', 'line', 'm', data='cfq.capex', flow=True, cf=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: FY26 capex point estimate. 2027E+: net sales × capex %.')
    S('cf_acq', 'Acquisitions of businesses, net of cash acquired', 'line', 'm', data='cfq.acquisitions', flow=True, cf=True,
      e26=lambda: f'={h26("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='2026E = 1H/26 actual (2026 bolt-ons); no further deals assumed in 2H. 2027E+: M&A lever.')
    S('cf_disp', 'Proceeds from disposal of assets & businesses', 'line', 'm', data='cfq.proceeds_disp', flow=True, cf=True,
      e26=lambda: f'={h26("cf_disp")}', ae_in=0.0)
    S('cf_oinv', 'Other investing activities, net (derived)', 'line', 'm', data='cfq.oinv', flow=True, cf=True,
      e26=lambda: f'={h26("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used for investing activities', 'line_b', 'm', data='cfq.cfi', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_borrow', 'Proceeds from debt (notes, credit facilities, commercial paper)', 'line', 'm', data='cfq.debt_proceeds', flow=True, cf=True,
      e26=lambda: f'={h26("cf_borrow")}+MAX(0,{V("ds_fac")}-BX{R["ds_fac"]})+{V("ds_refi")}',
      ae=lambda: f'={V("ds_refi")}+MAX(0,{V("ds_fac")}-{P("ds_fac")})')
    S('cf_repay', 'Payments of debt', 'line', 'm', data='cfq.debt_repay', flow=True, cf=True,
      e26=lambda: f'={h26("cf_repay")}+MIN(0,{V("ds_fac")}-BX{R["ds_fac"]})+{V("ds_mat")}',
      ae=lambda: f'={V("ds_mat")}+MIN(0,{V("ds_fac")}-{P("ds_fac")})',
      note='Net issuance / (repayment) = change in total debt per the debt schedule (scheduled note maturities, refinancing, prepayable facilities).')
    S('cf_div', 'Cash dividends paid', 'line', 'm', data='cfq.dividends', flow=True, cf=True,
      e26=lambda: f'={h26("cf_div")}-(BY{R["dps"]}*BY{R["sh_basic"]}+BZ{R["dps"]}*BZ{R["sh_basic"]})',
      ae=lambda: f'=-{V("dps")}*{V("bb_beg")}',
      note='2027E+: dividends per share × beginning shares outstanding (avoids circularity with buybacks).')
    S('cf_bb', 'Stock repurchases', 'line', 'm', data='cfq.buyback', flow=True, cf=True,
      e26=lambda: f'={h26("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E = 1H/26 actual + 2H scenario amount; 2027E+ = leverage plug (surplus cash returned via buybacks once net debt / Adj. EBITDA reaches the scenario floor).')
    S('cf_ofin', 'Stock option proceeds, tax withholding, NCI & other financing, net (derived)', 'line', 'm', data='cfq.ofin', flow=True, cf=True,
      e26=lambda: f'={h26("cf_ofin")}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash provided by (used for) financing activities', 'line_b', 'm', data='cfq.cff', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_borrow")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of changes in currency exchange rates', 'line', 'm', data='cfq.fx', flow=True, cf=True,
      e26=lambda: f'={h26("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net increase (decrease) in cash', 'line', 'm', data='cfq.net_change', flow=True, cf=True,
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cfq.cash_begin', cf=True, e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cfq.cash_end', cf=True, fc=lambda: f'={V("cf_beg")}+{V("cf_net")}',
      note='Cash basis per the statement in force: cash & equivalents to 2017; incl. restricted cash from 2018 (ASU 2016-18).')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0; ±0.1 rounding)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),IF(ABS({V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})-{V("cf_net")})<=0.15,0,ROUND({V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")})-{V("cf_net")},1)),"")')
    S('cf_chk2', '  Check: beginning cash + change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_beg")}),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.35,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (operating cash flow − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")',
      note='Model definition = CFO − purchases of PP&E (Wabtec reports operating cash flow conversion rather than free cash flow).')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('ocf_conv', '  Operating cash flow conversion % (company: CFO ÷ (net income + D&A))', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),IFERROR({V("cf_cfo")}/({V("cf_ni")}+{V("cf_dda")}),""),"")')
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+: input (FY26 guidance ~2% of sales; 2019–25 1.5–2.5%).')
    S('capex_dda', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ BUYBACKS
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E starts from shares outstanding at 30-Jun-2026; 2H/26 buyback per scenario')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})',
      note='2026E = current share price (valuation input); appreciates with the share-price input.')
    S('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}',
      note='2026E row = 2H/26 buyback only (1H/26 repurchases already in the Q1/Q2 share counts).')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', fc=lambda: None, e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)',
      ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=0.2, ae_in=0.6)
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'=BX{R["bs_shares"]}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Jun-2026 (10-Q).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', fc=lambda: None,
      e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet (Q2/26) + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs.cash', bs=True, fc=lambda: f'={V("cf_end")}-N({V("bs_rcash")})')
    S('bs_rcash', '  Restricted cash / deposits in escrow (where separate)', 'line', 'm', data='bs.restricted_cash', bs=True,
      e26=lambda: f'=N(BX{R["bs_rcash"]})', ae=lambda: f'=N({P("bs_rcash")})')
    S('bs_ar', '  Receivables, net (incl. unbilled)', 'line', 'm', data='bsx.ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365',
      note='Receivables = net sales × DSO / 365.')
    S('bs_inv', '  Inventories, net', 'line', 'm', data='bs.inventories', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other current assets (derived)', 'line', 'm', data='bsx.oca', bs=True, e26=lambda: f'=BX{R["bs_oca"]}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant & equipment, net', 'line', 'm', data='bs.ppe', bs=True,
      e26=lambda: f'=BX{R["bs_ppe"]}-({V("cf_capex")}-{h26("cf_capex")})-(BY{R["d_dep"]}+BZ{R["d_dep"]})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}',
      note='PP&E roll-forward: prior − capex (negative cash flow) − depreciation + acquired PP&E (M&A lever).')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs.goodwill', bs=True, e26=lambda: f'=BX{R["bs_gw"]}',
      ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Other intangible assets, net', 'line', 'm', data='bs.intangibles', bs=True,
      e26=lambda: f'=BX{R["bs_int"]}-(BY{R["is_amort"]}+BZ{R["is_amort"]})',
      ae=lambda: f'={P("bs_int")}-{V("is_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Intangibles roll-forward: prior − amortization + acquired intangibles (M&A lever).')
    S('bs_onca', '  Other noncurrent assets (incl. ROU, deferred taxes; derived)', 'line', 'm', data='bsx.onca', bs=True,
      e26=lambda: f'=BX{R["bs_onca"]}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs.ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_cdep', '  Customer deposits / contract liabilities', 'line', 'm', data='bs.customer_deposits', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_depp")}')
    S('bs_acc', '  Accrued compensation', 'line', 'm', data='bs.accrued_comp', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_accp")}')
    S('bs_war', '  Accrued warranty', 'line', 'm', data='bs.accrued_warranty', bs=True, e26=lambda: f'=BX{R["bs_war"]}', ae=lambda: f'={P("bs_war")}')
    S('bs_cdebt', '  Current portion of long-term debt & short-term borrowings', 'line', 'm', data='bs.current_debt', bs=True,
      e26=lambda: f'=MIN({V("ds_total")},-CB{R["ds_mat"]})', ae=lambda: (f'=MIN({V("ds_total")},-{nextc()}{R["ds_mat"]})'),
      note='Forecast: next year\'s scheduled note maturities.')
    S('bs_ocl', '  Other current liabilities (derived)', 'line', 'm', data='bsx.ocl', bs=True, e26=lambda: f'=BX{R["bs_ocl"]}', ae=lambda: f'={P("bs_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt', 'line', 'm', data='bs.ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cdebt")}')
    S('bs_pen', '  Accrued postretirement & pension benefits', 'line', 'm', data='bs.pension', bs=True,
      e26=lambda: f'=BX{R["bs_pen"]}', ae=lambda: f'={P("bs_pen")}')
    S('bs_dtl', '  Deferred income taxes', 'line', 'm', data='bs.deferred_tax', bs=True,
      e26=lambda: f'=BX{R["bs_dtl"]}+({V("cf_def")}-{h26("cf_def")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_oncl', '  Other noncurrent liabilities (incl. lease liabilities, warranty; derived)', 'line', 'm', data='bsx.oncl', bs=True,
      e26=lambda: f'=BX{R["bs_oncl"]}', ae=lambda: f'={P("bs_oncl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_e', "Shareholders' equity:", 'sub', 'gen')
    S('bs_cap', '  Common stock & additional paid-in capital', 'line', 'm', data='bsx.cap', bs=True,
      e26=lambda: f'=BX{R["bs_cap"]}+({V("cf_sbc")}-{h26("cf_sbc")})+({V("cf_ofin")}-{h26("cf_ofin")})',
      ae=lambda: f'={P("bs_cap")}+{V("cf_sbc")}+{V("cf_ofin")}', note='+ stock-based compensation + net option proceeds / withholding.')
    S('bs_treas', '  Treasury stock', 'line', 'm', data='bs.treasury', bs=True,
      e26=lambda: f'=BX{R["bs_treas"]}+({V("cf_bb")}-{h26("cf_bb")})', ae=lambda: f'={P("bs_treas")}+{V("cf_bb")}',
      note='Wabtec holds repurchased shares in treasury: + repurchases (negative).')
    S('bs_re', '  Retained earnings', 'line', 'm', data='bs.retained', bs=True,
      e26=lambda: f'=BX{R["bs_re"]}+BY{R["is_ni"]}+BZ{R["is_ni"]}+({V("cf_div")}-{h26("cf_div")})',
      ae=lambda: f'={P("bs_re")}+{V("is_ni")}+{V("cf_div")}', note='+ net income attributable − dividends.')
    S('bs_aoci', '  Accumulated other comprehensive income (loss)', 'line', 'm', data='bs.aoci', bs=True,
      e26=lambda: f'=BX{R["bs_aoci"]}+({V("cf_fx")}-{h26("cf_fx")})', ae=lambda: f'={P("bs_aoci")}')
    S('bs_weq', "Total Wabtec shareholders' equity", 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cap")}),SUM({V("bs_cap")}:{V("bs_aoci")}),"")')
    S('bs_nci', '  Noncontrolling interest', 'line', 'm', data='bs.nci', bs=True,
      e26=lambda: f'=N(BX{R["bs_nci"]})+BY{R["is_nci"]}+BZ{R["is_nci"]}', ae=lambda: f'=N({P("bs_nci")})+N({V("is_nci")})')
    S('bs_teq', 'Total equity', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_weq")}),{V("bs_weq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E; ±0.1 rounding)', 'check', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.15,0,ROUND({V("bs_ta")}-{V("bs_tle")},1)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},1),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs.total_assets', bs=True)
    S('bs_chk_cash', '  Check: BS cash (+ restricted cash where in the cash-flow basis) vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}+N({V("bs_rcf")})-{V("cf_end")},1),"")')
    S('bs_rcf', '  Memo: restricted cash included in the cash-flow cash basis', 'memo', 'm', data='bsx.rcf', bs=True,
      fc=lambda: f'=N({V("bs_rcash")})')
    S('bs_shares', '  Memo: common shares outstanding at period end (m)', 'memo', 'm1', data='bs.shares_outstanding_end', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables (incl. unbilled) / sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")',
      e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")',
      e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")',
      e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_depp', '  Customer deposits % of sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_cdep")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['dep'], ae_in=V0['wc']['dep'])
    S('wc_accp', '  Accrued compensation % of sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_acc")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['acc'], ae_in=V0['wc']['acc'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories − payables − deposits − accrued comp.)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}-{V("bs_ap")}-N({V("bs_cdep")})-N({V("bs_acc")}),"")')
    S('wc_nwc_p', '  NWC % of sales', 'pct', 'pct', all=lambda: f'=IFERROR({V("wc_nwc")}/{V("wc_rev")},"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IFERROR({V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', '2025–26 acquisitions — consideration & preliminary purchase-price allocation (closing-quarter column)', 'sub', 'gen')
    for k, lab in [('cons', 'Cash consideration (incl. debt repaid at closing)'), ('cashacq', 'Cash acquired'),
                   ('ar', 'Receivables acquired'), ('inv', 'Inventories acquired (at fair value)'), ('oca', 'Other current assets acquired'),
                   ('ppe', 'Property, plant & equipment'), ('intang', 'Intangible assets (customer relationships, technology, trade names, backlog)'),
                   ('gw', 'Goodwill'), ('onca', 'Other noncurrent assets (incl. ROU)'), ('cl', 'Current liabilities assumed'),
                   ('ncl', 'Noncurrent liabilities assumed (incl. leases, pensions)'), ('dtl', 'Deferred income taxes, net'), ('nci', 'Noncontrolling interest')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm', data=f'ppa.{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_cashacq")})+N({V("ppa_ar")})+N({V("ppa_inv")})+N({V("ppa_oca")})+N({V("ppa_ppe")})'
                    f'+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})-N({V("ppa_cl")})-N({V("ppa_ncl")})-N({V("ppa_dtl")})-N({V("ppa_nci")})-{V("ppa_cons")},0),"")'))
    S('ppa_names', '  Deal(s) closed in the quarter', 'text', 'gen', data='ppa.names', ppa=True, textdata=True)
    S('rf_h', 'Asset roll-forwards & non-cash items', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares)', 'sched', 'm1', ae_in=0.6)
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.07)
    S('ds_h', 'Debt schedule (scheduled note maturities + prepayable facilities to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current + long-term)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_cdebt")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_fac")}',
      note=V0['debt_note'])
    S('ds_mat', '  Scheduled note maturities (input, negative)', 'sched', 'm', e26_in=V0['mat'][2026], ae_in={y: V0['mat'][y] for y in (2027, 2028, 2029, 2030)},
      note=V0['mat_note'])
    S('ds_refp', '  % of scheduled maturities refinanced (input)', 'sched', 'pct', e26_in=V0['refi_pct'][2026], ae_in={y: V0['refi_pct'][y] for y in (2027, 2028, 2029, 2030)},
      note='100% = maturity refinanced with new notes at the refinancing rate; otherwise repaid from cash / facilities.')
    S('ds_refi', '  Refinancing issuance', 'sched', 'm', fc=lambda: None, e26=lambda: f'=-{V("ds_mat")}*{V("ds_refp")}', ae=lambda: f'=-{V("ds_mat")}*{V("ds_refp")}')
    S('ds_notes', '  Senior notes & term debt outstanding (year end)', 'sched', 'm', data='x.notes', bs=True,
      e26=lambda: f'=BX{R["ds_notes"]}+{V("ds_mat")}+{V("ds_refi")}', ae=lambda: f'={P("ds_notes")}+{V("ds_mat")}+{V("ds_refi")}')
    S('ds_pre', '  Cash before prepayable facilities (opening cash + CFO + CFI + non-debt financing + FX + scheduled debt flows)', 'sched', 'm',
      e26=lambda: (f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_fx")}'
                   f'+{h26("cf_borrow")}+{h26("cf_repay")}+{V("ds_mat")}+{V("ds_refi")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_fx")}+{V("ds_mat")}+{V("ds_refi")}')
    S('ds_min', '  Minimum cash balance (incl. restricted)', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_fac', '  Prepayable facilities outstanding: revolver, commercial paper, receivables securitization (year end)', 'sched', 'm', data='x.fac', bs=True,
      e26=lambda: f'=MAX(0,BX{R["ds_fac"]}+{V("ds_min")}-{V("ds_pre")})',
      ae=lambda: f'=MAX(0,{P("ds_fac")}+{V("ds_min")}-{V("ds_pre")})',
      note='Drawn / repaid so that cash = minimum balance; surplus cash first repays revolver / CP, then accumulates (or funds buybacks via the leverage plug).')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', fc=lambda: None, e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")',
      ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on notes & term debt (opening balance) %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_fac', '  Interest rate on prepayable facilities %', 'sched', 'pct', ae_in=0.045)
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.02)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a minimum net debt / Adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Minimum net debt / Adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: (f'={P("ds_notes")}+{P("ds_fac")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_ofin")}-{V("cf_fx")}'))
    S('lev_tgt', '  Target minimum net debt = min. leverage × Adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to minimum leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage floor is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization % of net sales', 'pct', 'pct', all=ratio('is_amort', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBIT)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (Adjusted EBITDA − D&A)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (actual)', 'line', 'pct', ann=True, all=lambda: f'={V("is_etr")}')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity incl. NCI', 'line', 'm', ann=True, all=lambda: f'={V("bs_teq")}')
    S('ra_nd', '  Net debt = Total debt − Cash (incl. restricted)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_rcash")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − effective tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & acquired intangible assets', 'line', 'm', ann=True, all=lambda: f'=-({V("bs_gw")}+{V("bs_int")})')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm', ann=True, all=lambda: f'=-({V("bs_tcl")}-N({V("bs_cdebt")}))')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=SUM({V("rn_ta")}:{V("rn_nibcl")})')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income attributable to Wabtec', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Wabtec shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_weq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (company definition; EBITDA where no adjusted figure was published)', 'line', 'm', ann=True,
      all=lambda: f'=IF(ISNUMBER({V("r_adj")}),{V("r_adj")},{V("r_ebitda")})')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+(BX{R["sh_dil"]}-BX{R["sh_basic"]})',
      ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interest (USDm)', 'line', 'm', e26=lambda: f'=N({V("bs_nci")})', ae=lambda: f'=N({V("bs_nci")})')
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")',
      ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted income from operations', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        nf = 'pct' if k in ('v_fcfy', 'v_dy') else 'x'
        S(k, lab, 'line', nf, e26=f, ae=f)

_NEXT = {'CA': 'CB', 'CB': 'CC', 'CC': 'CD', 'CD': 'CE', 'CE': None}
def nextc():
    n = _NEXT.get(CTX.col.c)
    return n or 'CE'
