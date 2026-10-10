"""Row specification part 2 (ODFL): cash flow, buybacks, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def h26(key):   # 1H/26 actual for a flow row
    return f'(BW{R[key]}+BX{R[key]})'

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income', 'line', 'm', data='cfq.net_income', flow=True, cf=True, fc=lambda: f'={V("is_ni")}',
      e26=lambda: f'={h26("cf_ni")}+BY{R["is_ni"]}+BZ{R["is_ni"]}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization', 'line', 'm', data='cfq.dda', flow=True, cf=True, fc=lambda: f'={V("is_dda")}',
      e26=lambda: f'={h26("cf_dda")}+BY{R["is_dda"]}+BZ{R["is_dda"]}')
    S('cf_gain', '  (Gain) loss on disposal of property & equipment', 'line', 'm', data='cfq.gain_loss', flow=True, cf=True,
      e26=lambda: f'={h26("cf_gain")}', ae_in=0.0)
    S('cf_def', '  Deferred income taxes (10-K; within other in the condensed 10-Q statements)', 'line', 'm', data='cfq.deferred_tax', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_def")})', ae_in=V0['def_tax_ae'],
      note='2027E+: deferred tax expense from accelerated tax depreciation on the capex programme (input).')
    S('cf_sbc', '  Share-based compensation (where presented)', 'line', 'm', data='cfq.sbc', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_sbc")})+BY{R["is_sbc"]}+BZ{R["is_sbc"]}', ae=lambda: f'={V("is_sbc")}')
    S('cf_oth', '  Other non-cash items, net (derived; incl. non-cash lease expense)', 'line', 'm', data='cfq.oth', flow=True, cf=True,
      e26=lambda: f'={h26("cf_oth")}', ae_in=0.0)
    S('cf_wc', '  Changes in operating assets & liabilities (working capital), net', 'line', 'm', data='cfq.wc_change', flow=True, cf=True,
      e26=lambda: (f'=N({h26("cf_wc")})-({V("bs_ar")}-BX{R["bs_ar"]})+({V("bs_ap")}-BX{R["bs_ap"]})'
                   f'+({V("bs_comp")}-BX{R["bs_comp"]})+({V("bs_claims")}-BX{R["bs_claims"]})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_comp")}-{P("bs_comp")})+({V("bs_claims")}-{P("bs_claims")})'),
      note='Linked to the balance sheet: −Δ customer receivables + Δ(payables, compensation & benefits, claims & insurance accruals). '
           'Condensed 10-Q statements show a single "changes in operating assets and liabilities" or "other" line — quarterly split between WC and other is as presented.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm', data='cfq.cfo', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Purchase of property & equipment', 'line', 'm', data='cfq.capex', flow=True, cf=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: capex plan ~$380m (Q2-26 release: $180m real estate / service centers, $155m tractors & trailers, $45m IT & other). 2027E+: revenue × capex %.')
    S('cf_disp', 'Proceeds from sale of property & equipment', 'line', 'm', data='cfq.proceeds_disp', flow=True, cf=True,
      e26=lambda: f'={h26("cf_disp")}', ae=lambda: f'={V("is_rev")}*{V("disp_pct")}')
    S('cf_sti', 'Short-term investments, net (purchases − maturities / sales)', 'line', 'm', data='cfq.sti_net', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_sti")})', ae_in=0.0)
    S('cf_acq', 'Acquisition of business assets / service centers', 'line', 'm', data='cfq.acquisitions', flow=True, cf=True,
      e26=lambda: f'=N({h26("cf_acq")})', ae_in=0.0, note='e.g. UW Freight Line (2006), Priority Freight (2007), Bowman (2008), Arnold Transportation assets (2013), Yellow service centers (2023 — in capex).')
    S('cf_oinv', 'Other investing activities, net (derived)', 'line', 'm', data='cfq.oinv', flow=True, cf=True,
      e26=lambda: f'={h26("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm', data='cfq.cfi', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_borrow', 'Proceeds from debt (senior notes, revolving line of credit)', 'line', 'm', data='cfq.debt_proceeds', flow=True, cf=True,
      e26=lambda: f'={h26("cf_borrow")}+MAX(0,{V("ds_fac")}-BX{R["ds_fac"]})+{V("ds_refi")}',
      ae=lambda: f'={V("ds_refi")}+MAX(0,{V("ds_fac")}-{P("ds_fac")})')
    S('cf_repay', 'Principal payments on debt', 'line', 'm', data='cfq.debt_repay', flow=True, cf=True,
      e26=lambda: f'={h26("cf_repay")}+MIN(0,{V("ds_fac")}-BX{R["ds_fac"]})+{V("ds_mat")}',
      ae=lambda: f'={V("ds_mat")}+MIN(0,{V("ds_fac")}-{P("ds_fac")})',
      note='Net issuance / (repayment) = change in total debt per the debt schedule (Series B notes amortisation; revolver).')
    S('cf_div', 'Dividends paid', 'line', 'm', data='cfq.dividends', flow=True, cf=True,
      e26=lambda: f'={h26("cf_div")}-(BY{R["dps"]}*BY{R["sh_basic"]}+BZ{R["dps"]}*BZ{R["sh_basic"]})',
      ae=lambda: f'=-{V("dps")}*{V("bb_beg")}', note='2027E+: dividends per share × beginning shares outstanding (avoids circularity with buybacks).')
    S('cf_bb', 'Payments for share repurchases (incl. accelerated share repurchases)', 'line', 'm', data='cfq.buyback', flow=True, cf=True,
      e26=lambda: f'={h26("cf_bb")}-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='2026E = 1H/26 actual + 2H scenario amount; 2027E+ = cash plug (cash above the scenario target balance returned via buybacks).')
    S('cf_ofin', 'Other financing activities, net (derived; tax withholding on equity awards, debt costs)', 'line', 'm', data='cfq.ofin', flow=True, cf=True,
      e26=lambda: f'={h26("cf_ofin")}', ae_in=V0['ofin_ae'])
    S('cf_cff', 'Net cash used in financing activities', 'line_b', 'm', data='cfq.cff', flow=True, cf=True,
      fc=lambda: f'=SUM({V("cf_borrow")}:{V("cf_ofin")})')
    S('cf_net', 'Net increase (decrease) in cash & cash equivalents', 'line', 'm', data='cfq.net_change', flow=True, cf=True,
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash & cash equivalents — beginning of period', 'line', 'm', data='cfq.cash_begin', cf=True, e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash & cash equivalents — end of period', 'line_b', 'm', data='cfq.cash_end', cf=True, fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF = change in cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),ROUND({V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}-{V("cf_net")},1),"")')
    S('cf_chk2', '  Check: beginning cash + change = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_beg")}),ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},1),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (operating cash flow − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")',
      note='Model definition = CFO − purchases of property & equipment (gross; ODFL does not publish free cash flow).')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note=V0['capex_note'])
    S('ncapex_pct', '  Net capex (capex − disposal proceeds) % of revenue', 'pct', 'pct',
      all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-({V("cf_capex")}+N({V("cf_disp")}))/{V("is_rev")},""),"")')
    S('disp_pct', '  Disposal proceeds % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_disp")}),IFERROR({V("cf_disp")}/{V("is_rev")},""),"")',
      ae_in=V0['disp_pct'])
    S('capex_dda', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("cf_dda")},""),"")')
    blank()

    # ------------------------------------------------------------------ BUYBACKS
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E starts from shares outstanding at 30-Jun-2026; 2H/26 buyback per scenario')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})',
      note='2026E = current share price (valuation input); appreciates with the share-price input.')
    S('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}',
      note='2026E row = 2H/26 buyback only (1H/26 repurchases already in the Q1/Q2 share counts).')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)',
      ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=0.1, ae_in=0.3)
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'=BX{R["bs_shares"]}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from shares outstanding at 30-Jun-2026 (10-Q cover / balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1',
      e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'BALANCE SHEET', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet (Q2/26) + 2H flows; 2027E+ from prior year end')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs.cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_sti', '  Short-term investments', 'line', 'm', data='bs.sti', bs=True,
      e26=lambda: f'=N(BX{R["bs_sti"]})-({V("cf_sti")}-N({h26("cf_sti")}))', ae=lambda: f'=N({P("bs_sti")})-{V("cf_sti")}')
    S('bs_ar', '  Customer receivables, net', 'line', 'm', data='bs.receivables', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365',
      note='Receivables = revenue × DSO / 365.')
    S('bs_oca', '  Other current assets (derived; other receivables, prepaid, income taxes receivable, deferred taxes to 2015)', 'line', 'm', data='bsx.oca', bs=True,
      e26=lambda: f'=BX{R["bs_oca"]}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Net property & equipment', 'line', 'm', data='bs.ppe', bs=True,
      e26=lambda: f'=BX{R["bs_ppe"]}-({V("cf_capex")}-{h26("cf_capex")})-(BY{R["is_dda"]}+BZ{R["is_dda"]})-({V("cf_disp")}-{h26("cf_disp")})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("cf_dda")}-{V("cf_disp")}-{V("cf_acq")}',
      note='Roll-forward: prior + capex − D&A − net book value of disposals (= proceeds; no gains forecast).')
    S('bs_onca', '  Other assets (derived; goodwill & intangibles, operating lease ROU, deferred compensation investments)', 'line', 'm', data='bsx.onca', bs=True,
      e26=lambda: f'=BX{R["bs_onca"]}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+{V("bs_ppe")}+{V("bs_onca")},"")')
    S('bs_l', "LIABILITIES AND SHAREHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs.ap', bs=True, fc=lambda: f'={V("wc_opex")}*{V("wc_dpo")}/365')
    S('bs_comp', '  Compensation & benefits', 'line', 'm', data='bs.accrued_comp', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_comp")}')
    S('bs_claims', '  Claims & insurance accruals (current)', 'line', 'm', data='bs.claims_cur', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_claims")}')
    S('bs_cdebt', '  Current maturities of long-term debt', 'line', 'm', data='bs.current_debt', bs=True,
      e26=lambda: f'=MIN({V("ds_total")},-CB{R["ds_mat"]})', ae=lambda: f'=MIN({V("ds_total")},-{nextc()}{R["ds_mat"]})',
      note="Forecast: next year's scheduled note amortisation.")
    S('bs_ocl', '  Other current liabilities (derived; other accrued liabilities, income taxes payable, lease liabilities)', 'line', 'm', data='bsx.ocl', bs=True,
      e26=lambda: f'=BX{R["bs_ocl"]}', ae=lambda: f'={P("bs_ocl")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt (excluding current maturities)', 'line', 'm', data='bs.ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cdebt")}')
    S('bs_dtl', '  Deferred income taxes', 'line', 'm', data='bs.deferred_tax', bs=True,
      e26=lambda: f'=BX{R["bs_dtl"]}+({V("cf_def")}-N({h26("cf_def")}))', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_oncl', '  Other non-current liabilities (derived; claims & insurance, lease liabilities, deferred compensation)', 'line', 'm', data='bsx.oncl', bs=True,
      e26=lambda: f'=BX{R["bs_oncl"]}', ae=lambda: f'={P("bs_oncl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_e', "Shareholders' equity:", 'sub', 'gen')
    S('bs_cap', '  Common stock & capital in excess of par value', 'line', 'm', data='bsx.cap', bs=True,
      e26=lambda: f'=BX{R["bs_cap"]}+({V("cf_sbc")}-N({h26("cf_sbc")}))+({V("cf_ofin")}-{h26("cf_ofin")})',
      ae=lambda: f'={P("bs_cap")}+{V("cf_sbc")}+{V("cf_ofin")}', note='+ share-based compensation + other financing (net share settlement of awards).')
    S('bs_re', '  Retained earnings', 'line', 'm', data='bs.retained', bs=True,
      e26=lambda: f'=BX{R["bs_re"]}+BY{R["is_ni"]}+BZ{R["is_ni"]}+({V("cf_div")}-{h26("cf_div")})+({V("cf_bb")}-{h26("cf_bb")})',
      ae=lambda: f'={P("bs_re")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}',
      note='+ net income − dividends − repurchases (ODFL cancels repurchased shares; cost in excess of par charged mainly to retained earnings).')
    S('bs_teq', "Total shareholders' equity", 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cap")}),{V("bs_cap")}+{V("bs_re")},"")')
    S('bs_tle', "TOTAL LIABILITIES AND SHAREHOLDERS' EQUITY", 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),ROUND({V("bs_ta")}-{V("bs_tle")},1),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},1),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs.total_assets', bs=True)
    S('bs_chk_eq', "  Check: Σ equity components vs reported total shareholders' equity (should be 0)", 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_teq_pub")}),ROUND({V("bs_teq")}-{V("bs_teq_pub")},1),"")')
    S('bs_teq_pub', "  Memo: total shareholders' equity as reported", 'memo', 'm', data='bs.total_equity', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}-{V("cf_end")},1),"")')
    S('bs_shares', '  Memo: common shares outstanding at period end (m; split-adjusted)', 'memo', 'm1', data='bs.shares_outstanding_end', bs=True,
      e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_ppe_h', '  Memo: property & equipment at cost (10-K / 10-Q):', 'sub', 'gen', group=True)
    for k, lab in (('ppe_rev_equip', 'Revenue equipment'), ('ppe_land', 'Land & structures'), ('ppe_other', 'Other fixed assets'),
                   ('ppe_lease', 'Leasehold improvements'), ('ppe_gross', 'Total property & equipment (gross)'), ('accum_dep', 'Less: accumulated depreciation')):
        S(f'bs_{k}', f'    {lab}', 'memo', 'm', data=f'bs.{k}', bs=True, group=True)
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_opex', '  Operating expenses excl. D&A — annualised', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_opex")}),({V("is_opex")}-{V("is_dda")})*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — customer receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")',
      e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dpo', '  Payable days — payables / operating expenses excl. D&A × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_opex")}*365,"")',
      e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_comp', '  Compensation & benefits % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_comp")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['comp'], ae_in=V0['wc']['comp'])
    S('wc_claims', '  Claims & insurance accruals (current) % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_claims")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['claims'], ae_in=V0['wc']['claims'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables − payables − compensation − claims accruals)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}-{V("bs_ap")}-N({V("bs_comp")})-N({V("bs_claims")}),"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IFERROR({V("wc_nwc")}/{V("wc_rev")},"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IFERROR({V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing inputs', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares)', 'sched', 'm1', ae_in=1.0)
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (Series B senior notes amortisation + revolving line of credit to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt (current + long-term)', 'sched', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_cdebt")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_fac")}',
      note=V0['debt_note'])
    S('ds_mat', '  Scheduled note maturities (input, negative)', 'sched', 'm', e26_in=V0['mat'][2026], ae_in={y: V0['mat'][y] for y in (2027, 2028, 2029, 2030)},
      note=V0['mat_note'])
    S('ds_refp', '  % of scheduled maturities refinanced (input)', 'sched', 'pct', e26_in=0.0, ae_in=0.0)
    S('ds_refi', '  Refinancing issuance', 'sched', 'm', e26=lambda: f'=-{V("ds_mat")}*{V("ds_refp")}', ae=lambda: f'=-{V("ds_mat")}*{V("ds_refp")}')
    S('ds_notes', '  Senior notes outstanding (year end)', 'sched', 'm', data='bsx.debt', bs=True,
      e26=lambda: f'=BX{R["ds_notes"]}+{V("ds_mat")}+{V("ds_refi")}', ae=lambda: f'={P("ds_notes")}+{V("ds_mat")}+{V("ds_refi")}')
    S('ds_pre', '  Cash before revolver (opening cash + CFO + CFI + dividends + buybacks + other financing + scheduled note flows)', 'sched', 'm',
      e26=lambda: (f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}'
                   f'+{h26("cf_borrow")}+{h26("cf_repay")}+{V("ds_mat")}+{V("ds_refi")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_ofin")}+{V("ds_mat")}+{V("ds_refi")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_fac', '  Revolving line of credit outstanding ($400m facility to Mar-2028; year end)', 'sched', 'm', data='x.fac', bs=True,
      e26=lambda: f'=MAX(0,N(BX{R["ds_fac"]})+{V("ds_min")}-{V("ds_pre")})',
      ae=lambda: f'=MAX(0,N({P("ds_fac")})+{V("ds_min")}-{V("ds_pre")})',
      note='Drawn / repaid so that cash ≥ minimum balance (undrawn at 30-Jun-26; $368m available after letters of credit).')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")',
      ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Interest rate on senior notes (opening balance) %', 'sched', 'pct', ae_in=0.0279, note='Series B senior notes 2.79% (2020 Note Agreement with PGIM).')
    S('ds_r_fac', '  Interest rate on revolver %', 'sched', 'pct', ae_in=0.05, note='SOFR + 0.10% + 1.000–1.375% margin.')
    S('ds_r_cash', '  Interest income yield on opening cash & short-term investments %', 'sched', 'pct', ae_in=0.035)
    S('lev_h', 'Cash-return buybacks (repurchases plug: cash above the scenario target balance returned, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target cash balance (USDm) (scenario)', 'sched', 'm', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Cash before buybacks (year end)', 'sched', 'm',
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_ofin")}+{V("ds_mat")}+{V("ds_refi")}')
    S('lev_bb', '  Share repurchases: plug to the target cash balance', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_pre")}-{V("lev_min")})',
      note='Surplus cash beyond the target balance is returned via buybacks ($1.31bn authorisation remaining at 30-Jun-26 under the $3.0bn 2023 programme); feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_ppe', '  Net property & equipment % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("bs_ppe")}),IFERROR({V("bs_ppe")}/{V("wc_rev")},""),"")')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBIT)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (Adjusted EBITDA − D&A)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (actual)', 'line', 'pct', ann=True, all=lambda: f'={V("is_etr")}')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Total shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_teq")}')
    S('ra_nd', '  Net debt = Total debt − cash & short-term investments', 'line', 'm', ann=True,
      all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")}-N({V("bs_sti")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − effective tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangibles (within other assets; nil after 2020)', 'line', 'm', ann=True, all=lambda: f'=-N({V("x_gw")})')
    S('x_gw', '  Memo: goodwill & intangible assets (balance sheet, where separately presented)', 'memo', 'm', data='bsx.gwi', bs=True, ann=True)
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm', ann=True, all=lambda: f'=-({V("bs_tcl")}-N({V("bs_cdebt")}))')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'={V("rn_ta")}+{V("rn_gw")}+{V("rn_nibcl")}')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Shareholders' equity", 'line', 'm', ann=True, all=lambda: f'={V("bs_teq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash & short-term investments (negative = net cash)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (model)', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+(BX{R["sh_dil"]}-BX{R["sh_basic"]})',
      ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm; negative = net cash)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm; none)', 'line', 'm', e26_in=0.0, ae_in=0.0)
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")',
      ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
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
