"""Cash flow, balance sheet, schedules, ratios and valuation rows."""
from spec import *

def CLr(k): return f'$CL${R[k]}'
def H2(k):  # 2H/26 portion of a 2026E flow = 2026E − 1H/26
    return f'({V(k)}-{CLr(k)})'

def build_spec2():
    S = add
    # ================================================================== CASH FLOW
    S('sec_cf', 'CONSOLIDATED CASH FLOW STATEMENT', 'section',
      note='CONSOLIDATED CASH FLOW STATEMENT — forecast logic (annual; 1H/26 = reported six months; 2026E = 1H/26 actual + 2H/26 forecast)')
    blank()
    S('cf_ne', 'Net earnings (incl. noncontrolling interests)', 'cf_line', 'm', data='cf.net_earnings', cfbs=True,
      fc_ann=lambda: f'={V("is_ne")}')
    S('cf_adj_hdr', 'Adjustments:', 'line', 'gen')
    S('cf_dda', '  Depreciation, depletion, accretion & amortization', 'cf_line', 'm', data='cf.dda', cfbs=True,
      fc_ann=lambda: f'={V("is_dda")}')
    S('cf_lease', '  Noncash operating lease expense', 'cf_line', 'm', data='cf.noncash_lease', cfbs=True,
      e26=lambda: f'={CLr("cf_lease")}', ae_input=0.0, note='2H/26 and 2027E+ set to zero (lease payments assumed equal to expense).')
    S('cf_gain', '  Net (gain) loss on sale of PP&E and businesses', 'cf_line', 'm', data='cf.gain_sale', cfbs=True,
      fc_ann=lambda: f'=-{V("is_gain")}')
    S('cf_pens', '  Contributions to pension plans', 'cf_line', 'm', data='cf.pension_contrib', cfbs=True,
      e26_input=-7.7, ae=lambda: f'={PV("cf_pens")}',
      note='2026E: 10-K expected contributions (funded $3.9m + nonqualified $3.8m). Reduces other noncurrent liabilities.')
    S('cf_sbc', '  Share-based compensation expense', 'cf_line', 'm', data='cf.sbc', cfbs=True, fc_ann=lambda: f'={V("is_sbc")}')
    S('cf_dtax', '  Deferred income taxes, net', 'cf_line', 'm', data='cf.deferred_tax', cfbs=True,
      e26=lambda: f'={CLr("cf_dtax")}', ae_input=0.0, note='2H/26 and 2027E+: no further deferred tax movement assumed (input).')
    S('cf_wc', '  Changes in operating assets and liabilities', 'cf_line', 'm', data='cf.wc_change', cfbs=True,
      e26=lambda: (f'={CLr("cf_wc")}-({V("bs_ar")}-{CLr("bs_ar")})-({V("bs_inv")}-{CLr("bs_inv")})-({V("bs_oca")}-{CLr("bs_oca")})'
                   f'+({V("bs_ap")}-{CLr("bs_ap")})+({V("bs_ocl")}-{CLr("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{PV("bs_ar")})-({V("bs_inv")}-{PV("bs_inv")})-({V("bs_oca")}-{PV("bs_oca")})'
                  f'+({V("bs_ap")}-{PV("bs_ap")})+({V("bs_ocl")}-{PV("bs_ocl")})'),
      note='Linked to BS: −Δ(receivables, inventories, other current assets) + Δ(payables & accruals, other current liabilities). 2026E = 1H/26 actual + 2H change vs 30-Jun-26.')
    S('cf_othop', '  Other operating items, net', 'cf_line', 'm', data='cf.other_op', cfbs=True,
      e26=lambda: f'={CLr("cf_othop")}', ae_input=0.0)
    S('cfo', 'Net cash provided by operating activities', 'cf_total', 'm', data='cf.cfo', cfbs=True,
      fc_ann=lambda: f'=SUM({V("cf_ne")}:{V("cf_othop")})')
    S('cf_capex', 'Purchases of property, plant & equipment', 'cf_line', 'm', data='cf.capex', cfbs=True,
      e26=lambda: f'=-$DD${SC["pt_capex"]}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: FY26 capex outlook mid-point ($750–800m). 2027E+: revenues × capex % input.')
    S('cf_pppe', 'Proceeds from sale of property, plant & equipment', 'cf_line', 'm', data='cf.proceeds_ppe', cfbs=True,
      e26=lambda: f'={CLr("cf_pppe")}', ae_input=0.0)
    S('cf_pbus', 'Proceeds from sale of businesses', 'cf_line', 'm', data='cf.proceeds_bus', cfbs=True,
      e26=lambda: f'={CLr("cf_pbus")}', ae_input=0.0, note='2026E = 1H/26 actual (California ready-mix sale).')
    S('cf_acq', 'Payment for businesses acquired, net of cash acquired', 'cf_line', 'm', data='cf.acquisitions', cfbs=True,
      e26=lambda: f'={CLr("cf_acq")}-{V("mna_spend")}', ae=lambda: f'=-{V("mna_spend")}',
      note='2026E = 1H/26 actual (no further 2026 M&A assumed). 2027E+ = M&A lever.')
    S('cf_othinv', 'Other investing activities, net', 'cf_line', 'm', data='cf.other_inv', cfbs=True,
      e26=lambda: f'={CLr("cf_othinv")}', ae_input=0.0)
    S('cfi', 'Net cash provided by (used for) investing activities', 'cf_total', 'm', data='cf.cfi', cfbs=True,
      fc_ann=lambda: f'=SUM({V("cf_capex")}:{V("cf_othinv")})')
    blank()
    S('cf_debtp', 'Proceeds from debt / short-term borrowings', 'cf_line', 'm', data='cf.debt_proceeds', cfbs=True,
      e26=lambda: f'={CLr("cf_debtp")}+{V("d_roll")}+MAX(0,{V("d_rev")}-N({CLr("bs_std")}))',
      ae=lambda: f'={V("d_roll")}+MAX(0,{V("d_rev")}-{PV("d_rev")})')
    S('cf_debtr', 'Repayment of debt (incl. short-term, current maturities, finance leases)', 'cf_line', 'm', data='cf.debt_repay', cfbs=True,
      e26=lambda: f'={CLr("cf_debtr")}+{V("d_mat")}+MIN(0,{V("d_rev")}-N({CLr("bs_std")}))',
      ae=lambda: f'={V("d_mat")}+MIN(0,{V("d_rev")}-{PV("d_rev")})',
      note='Net issuance / (repayment) = change in total debt per the debt schedule (row below).')
    S('cf_buyb', 'Purchases of common stock (share repurchases)', 'cf_line', 'm', data='cf.buyback', cfbs=True,
      e26=lambda: f'={CLr("cf_buyb")}-{CH(SC["BB26"])}', ae=lambda: f'=-{V("bl_plug")}',
      note='2026E = 1H/26 actual + 2H scenario amount; 2027E+ = leverage plug: surplus cash returned via buybacks so net debt / Adjusted EBITDA does not fall below the scenario floor.')
    S('cf_div', 'Dividends paid', 'cf_line', 'm', data='cf.dividends', cfbs=True,
      e26=lambda: f'={CLr("cf_div")}-({V("dps","CM")}+{V("dps","CN")})*{CLr("bs_shares")}',
      ae=lambda: f'=-{V("dps")}*{PV("bb_end")}',
      note='Dividends = DPS × opening shares outstanding (avoids a buyback ↔ dividend circularity).')
    S('cf_stock', 'Proceeds from issuance of common stock (option exercises)', 'cf_line', 'm', data='cf.stock_proceeds', cfbs=True,
      e26=lambda: f'=N({CLr("cf_stock")})', ae_input=0.0)
    S('cf_othfin', 'Other financing activities, net (shares withheld for taxes, NCI, debt costs)', 'cf_line', 'm', data='cf.other_fin', cfbs=True,
      e26=lambda: f'={CLr("cf_othfin")}', ae_input=-30.0)
    S('cff', 'Net cash provided by (used for) financing activities', 'cf_total', 'm', data='cf.cff', cfbs=True,
      fc_ann=lambda: f'=SUM({V("cf_debtp")}:{V("cf_othfin")})')
    blank()
    S('cf_chg', 'Net increase (decrease) in cash (and restricted cash from 2017)', 'cf_line', 'm', data='cf.net_change', cfbs=True,
      fc_ann=lambda: f'={V("cfo")}+{V("cfi")}+{V("cff")}')
    S('cf_begin', 'Cash — beginning of period', 'cf_line', 'm', data='cf.cash_begin', cfbs=True,
      e26=lambda: f'={V("cf_end","CI")}', ae=lambda: f'={PV("cf_end")}')
    S('cf_end', 'Cash — end of period', 'cf_line', 'm', data='cf.cash_end', cfbs=True,
      fc_ann=lambda: f'={V("cf_begin")}+{V("cf_chg")}',
      note='ASU 2016-18: restricted cash included in the cash-flow statement from FY2017.')
    S('cf_chk', '  Check: CFO + CFI + CFF = change in cash (should be 0)', 'check', 'm1',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("cfo")}),ROUND({V("cfo")}+{V("cfi")}+{V("cff")}-{V("cf_chg")},1),"")')
    S('cf_mhdr', '(Memo)', 'line', 'gen')
    S('fcf', 'Free cash flow (CFO − capital expenditures)', 'total', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("cfo")}),{V("cfo")}+N({V("cf_capex")}),"")',
      note='Vulcan does not publish a free cash flow measure in its releases; model definition = CFO − purchases of PP&E.')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', cfbs_f=lambda: f'=IFERROR({V("fcf")}/{PV("fcf")}-1,"")' if CTX.col.prev else None, ann_only_f=True)
    S('fcf_m', '  FCF % of revenues', 'pct', 'pct', cfbs_f=lambda: f'=IFERROR({V("fcf")}/{V("is_rev")},"")')
    S('fcf_conv', '  FCF / Adjusted net earnings (current definition) conversion %', 'pct', 'pct',
      cfbs_f=lambda: f'=IFERROR({V("fcf")}/{V("e_cur")},"")')
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', cfbs_f=lambda: f'=IFERROR({V("fcf")}/{V("sh_dil")},"")')
    S('cash_ret', '  Cash returned to shareholders (dividends + buybacks)', 'line', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("cfo")}),-N({V("cf_div")})-N({V("cf_buyb")}),"")')
    S('capex_hdr', 'Capex ratios', 'line', 'gen')
    S('capex_pct', '  Capex % of revenues', 'pct', 'pct', cfbs_f=lambda: f'=IFERROR(-N({V("cf_capex")})/{V("is_rev")},"")',
      ae_input=0.095)
    S('capex_dda', '  Capex / DDA&A (x)', 'line', 'x2', cfbs_f=lambda: f'=IFERROR(-N({V("cf_capex")})/{V("cf_dda")},"")')
    blank()

    # ================================================================== BUYBACKS
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARE BUYBACKS — 2026E row = 2H/26 only (1H/26 repurchases already in Q1/Q2 share counts)')
    S('bb_price', '  Avg buyback price ($)', 'line', 'ps', e26=lambda: f'={V("val_px")}',
      ae=lambda: f'={PV("bb_price")}*(1+{V("d_px_g")})',
      note='2026E = current share price ($243, valuation input); appreciates with the share-price input.')
    S('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'm', e26=lambda: f'=-({V("cf_buyb")}-{CLr("cf_buyb")})',
      ae=lambda: f'=-{V("cf_buyb")}')
    S('bb_shares', '  Implied shares repurchased (m)', 'line', 'm1', fc_ann=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_price")},0)')
    S('bb_issued', '  Shares issued under equity plans (m)', 'line', 'm1', e26_input=0.1, ae_input=0.3)
    S('bb_begin', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={CLr("bs_shares")}', ae=lambda: f'={PV("bb_end")}')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', fc_ann=lambda: f'={V("bb_begin")}-{V("bb_shares")}+{V("bb_issued")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', fc_ann=lambda: f'=IFERROR({V("bb_shares")}/{V("bb_begin")},"")')
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H/26 (m)', 'line', 'm1',
      e26=lambda: f'={V("bb_shares")}', ae=lambda: f'={PV("bb_cum")}+{V("bb_shares")}')
    blank()

    # ================================================================== BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET', 'section',
      note='BS FORECAST — first-principles roll-forward (2026E from the 30-Jun-26 balance sheet + 2H/26 flows; 2027E+ from prior year end)')
    blank()
    S('bs_ahdr', 'ASSETS', 'line', 'gen')
    S('bs_cahdr', 'Current assets:', 'line', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'bs_line', 'm', data='bs.cash', cfbs=True,
      fc_ann=lambda: f'={V("cf_end")}-{V("bs_rcash")}', note='Cash-flow ending cash (incl. restricted) less restricted cash.')
    S('bs_rcash', '  Restricted cash', 'bs_line', 'm', data='bs.restricted_cash', cfbs=True,
      e26=lambda: f'={CLr("bs_rcash")}', ae=lambda: f'={PV("bs_rcash")}')
    S('bs_ar', '  Accounts and notes receivable, net', 'bs_line', 'm', data='bs.ar_net', cfbs=True,
      fc_ann=lambda: f'={V("is_rev")}*{V("wc_dso")}/365', note='Receivables = revenues × DSO / 365.')
    S('bs_inv', '  Inventories', 'bs_line', 'm', data='bs.inventories', cfbs=True,
      fc_ann=lambda: f'={V("is_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other current assets (prepaids, current taxes, other)', 'bs_line', 'm', data='bs.other_current', cfbs=True,
      e26=lambda: f'={CLr("bs_oca")}', ae=lambda: f'={PV("bs_oca")}')
    S('bs_hfs', '  Assets held for sale', 'bs_line', 'm', data='bs.assets_held_for_sale', cfbs=True, e26_input=0.0, ae_input=0.0)
    S('bs_tca', 'Total current assets', 'line_b', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_hfs")}),"")')
    S('bs_invlt', '  Investments and long-term receivables', 'bs_line', 'm', data='bs.invest_lt_rec', cfbs=True,
      e26=lambda: f'={CLr("bs_invlt")}', ae=lambda: f'={PV("bs_invlt")}')
    S('bs_ppe', '  Property, plant & equipment, net', 'bs_line', 'm', data='bs.ppe_net', cfbs=True,
      e26=lambda: (f'={CLr("bs_ppe")}-{H2("cf_capex")}-({H2("is_dda")}-{V("sch_amort")}/2)-{H2("cf_pppe")}'
                   f'-{H2("cf_acq")}*{V("mna_ppe_pct","CP")}'),
      ae=lambda: f'={PV("bs_ppe")}-{V("cf_capex")}-({V("is_dda")}-{V("sch_amort")})-{V("cf_pppe")}-{V("cf_acq")}*{V("mna_ppe_pct")}',
      note='PP&E roll-forward: opening + capex − depreciation & depletion (DDA&A less intangible amortization) − disposals + acquired PP&E.')
    S('bs_rou', '  Operating lease right-of-use assets (2019+)', 'bs_line', 'm', data='bs.rou_assets', cfbs=True,
      e26=lambda: f'={CLr("bs_rou")}', ae=lambda: f'={PV("bs_rou")}')
    S('bs_gw', '  Goodwill', 'bs_line', 'm', data='bs.goodwill', cfbs=True,
      e26=lambda: f'={CLr("bs_gw")}-{H2("cf_acq")}*{V("mna_gw_pct","CP")}', ae=lambda: f'={PV("bs_gw")}-{V("cf_acq")}*{V("mna_gw_pct")}')
    S('bs_int', '  Other intangible assets, net', 'bs_line', 'm', data='bs.intangibles', cfbs=True,
      e26=lambda: f'={CLr("bs_int")}-{V("sch_amort")}/2-{H2("cf_acq")}*{V("mna_int_pct","CP")}',
      ae=lambda: f'={PV("bs_int")}-{V("sch_amort")}-{V("cf_acq")}*{V("mna_int_pct")}',
      note='Intangibles roll-forward: opening + acquired intangibles − amortization (schedule below).')
    S('bs_onca', '  Other noncurrent assets', 'bs_line', 'm', data='bs.other_noncurrent', cfbs=True,
      e26=lambda: f'={CLr("bs_onca")}', ae=lambda: f'={PV("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'bs_total', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_invlt")}:{V("bs_onca")}),"")')
    blank()
    S('bs_lhdr', "LIABILITIES AND EQUITY", 'line', 'gen')
    S('bs_clhdr', 'Current liabilities:', 'line', 'gen')
    S('bs_curmat', '  Current maturities of long-term debt', 'bs_line', 'm', data='bs.current_maturities', cfbs=True,
      fc_ann=lambda: (f'=-{V("d_mat", ANN[CTX.col.year + 1].c)}' if CTX.col.year < 2030 else '=0'),
      note="Next year's scheduled maturities (debt schedule).")
    S('bs_std', '  Short-term debt / commercial paper', 'bs_line', 'm', data='bs.short_term_debt', cfbs=True,
      fc_ann=lambda: f'={V("d_rev")}')
    S('bs_ap', '  Trade payables and accruals', 'bs_line', 'm', data='bs.payables', cfbs=True,
      fc_ann=lambda: f'={V("is_cogs")}*{V("wc_dpo")}/365')
    S('bs_ocl', '  Other current liabilities', 'bs_line', 'm', data='bs.other_current_liab', cfbs=True,
      fc_ann=lambda: f'={V("is_rev")}*{V("wc_ocl")}')
    S('bs_hfsl', '  Liabilities held for sale', 'bs_line', 'm', data='bs.liab_held_for_sale', cfbs=True, e26_input=0.0, ae_input=0.0)
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_curmat")}:{V("bs_hfsl")}),"")')
    S('bs_ltd', '  Long-term debt', 'bs_line', 'm', data='bs.ltd', cfbs=True,
      fc_ann=lambda: f'={V("d_total")}-{V("bs_curmat")}-{V("bs_std")}')
    S('bs_dtax', '  Deferred income taxes, net', 'bs_line', 'm', data='bs.deferred_tax', cfbs=True,
      e26=lambda: f'={CLr("bs_dtax")}+{H2("cf_dtax")}', ae=lambda: f'={PV("bs_dtax")}+{V("cf_dtax")}')
    S('bs_defrev', '  Deferred revenue (volumetric production payments)', 'bs_line', 'm', data='bs.deferred_revenue', cfbs=True,
      e26=lambda: f'={CLr("bs_defrev")}', ae=lambda: f'={PV("bs_defrev")}')
    S('bs_lease', '  Noncurrent operating lease liabilities', 'bs_line', 'm', data='bs.lt_lease', cfbs=True,
      e26=lambda: f'={CLr("bs_lease")}', ae=lambda: f'={PV("bs_lease")}')
    S('bs_oncl', '  Other noncurrent liabilities (pension, ARO, other)', 'bs_line', 'm', data='bs.other_noncurrent_liab', cfbs=True,
      e26=lambda: f'={CLr("bs_oncl")}+{H2("cf_pens")}', ae=lambda: f'={PV("bs_oncl")}+{V("cf_pens")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_eqhdr', 'Equity:', 'line', 'gen')
    S('bs_cs', '  Common stock ($1 par)', 'bs_line', 'm', data='bs.common_stock', cfbs=True,
      e26=lambda: f'={CLr("bs_cs")}', ae=lambda: f'={PV("bs_cs")}')
    S('bs_apic', '  Capital in excess of par value', 'bs_line', 'm', data='bs.capital_excess', cfbs=True,
      e26=lambda: f'={CLr("bs_apic")}+{H2("cf_sbc")}+N({V("cf_stock")})-N({CLr("cf_stock")})+{H2("cf_othfin")}',
      ae=lambda: f'={PV("bs_apic")}+{V("cf_sbc")}+{V("cf_stock")}+{V("cf_othfin")}',
      note='+ SBC + stock issued + other financing (shares withheld for taxes, NCI distributions).')
    S('bs_re', '  Retained earnings', 'bs_line', 'm', data='bs.retained_earnings', cfbs=True,
      e26=lambda: f'={CLr("bs_re")}+{H2("is_ni")}+{H2("cf_div")}+{H2("cf_buyb")}',
      ae=lambda: f'={PV("bs_re")}+{V("is_ni")}+{V("cf_div")}+{V("cf_buyb")}',
      note='+ net earnings attributable to Vulcan − dividends − share repurchases (Vulcan retires repurchased shares; model charges the cost to retained earnings).')
    S('bs_aoci', '  Accumulated other comprehensive income (loss)', 'bs_line', 'm', data='bs.aoci', cfbs=True,
      e26=lambda: f'={CLr("bs_aoci")}', ae=lambda: f'={PV("bs_aoci")}')
    S('bs_treas', '  Treasury stock (legacy, pre-2009)', 'bs_line', 'm', data='bs.treasury_stock', cfbs=True)
    S('bs_veq', "Total Vulcan shareholders' equity", 'line_b', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_re")}),SUM({V("bs_cs")}:{V("bs_treas")}),"")')
    S('bs_nci', '  Noncontrolling interest', 'bs_line', 'm', data='bs.nci', cfbs=True,
      e26=lambda: f'={CLr("bs_nci")}+{H2("is_nci")}', ae=lambda: f'={PV("bs_nci")}+{V("is_nci")}')
    S('bs_te', 'Total equity', 'line_b', 'm', cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_veq")}),{V("bs_veq")}+N({V("bs_nci")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'bs_total', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_te")},"")')
    blank()
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1', cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_ta")}),ROUND({V("bs_ta")}-{V("bs_tle")},1),"")')
    S('bs_ta_chk', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},1),"")', hist_only=True)
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs.total_assets', cfbs=True)
    S('bs_cash_chk', '  Check: BS cash (+ restricted from 2017) vs cash-flow ending cash (should be 0)', 'check', 'm1',
      cfbs_f=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}+N({V("bs_rcash")})*{1 if CTX.col.year >= 2017 else 0}-{V("cf_end")},1),"")')
    S('bs_shares', '  Memo: common shares outstanding at period end (m)', 'memo', 'm1', data='bs.shares_outstanding_end', cfbs=True,
      fc_ann=lambda: f'={V("bb_end")}')
    blank()

    # ================================================================== WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input)')
    S('wc_dso', '  DSO — receivables / revenues × 365', 'line', 'd',
      cfbs_f=lambda: f'=IFERROR({V("bs_ar")}/{V("is_rev")}*365*{0.5 if CTX.col.kind == "H" else 1},"n/a")', e26_input=46, ae_input=46)
    S('wc_dio', '  Inventory days — inventories / cost of revenues × 365', 'line', 'd',
      cfbs_f=lambda: f'=IFERROR({V("bs_inv")}/{V("is_cogs")}*365*{0.5 if CTX.col.kind == "H" else 1},"n/a")', e26_input=45, ae_input=45)
    S('wc_dpo', '  Payable days — trade payables & accruals / cost of revenues × 365', 'line', 'd',
      cfbs_f=lambda: f'=IFERROR({V("bs_ap")}/{V("is_cogs")}*365*{0.5 if CTX.col.kind == "H" else 1},"n/a")', e26_input=27, ae_input=27)
    S('wc_ocl', '  Other current liabilities % of revenues', 'pct', 'pct',
      cfbs_f=lambda: f'=IFERROR({V("bs_ocl")}/{V("is_rev")}*{0.5 if CTX.col.kind == "H" else 1},"n/a")', e26_input=0.055, ae_input=0.055)
    S('wc_nwc', '  Operating NWC (receivables + inventories + other CA − payables − other CL)', 'line', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}+N({V("bs_oca")})-{V("bs_ap")}-N({V("bs_ocl")}),"n/a")')
    S('wc_nwc_pct', '  NWC % of revenues', 'pct', 'pct', cfbs_f=lambda: f'=IFERROR({V("wc_nwc")}/{V("is_rev")},"n/a")', ann_only_f=True)
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', cfbs_f=lambda: f'=IFERROR({V("wc_nwc")}-{PV("wc_nwc")},"n/a")' if CTX.col.prev else None, ann_only_f=True)
    blank()

    # ================================================================== SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('sch_hdr1', 'Asset roll-forwards & non-cash items', 'line', 'gen')
    S('sch_amort', '  Amortization of intangible assets (within DDA&A, USDm)', 'driver', 'm', e26_input=95.0, ae_input=95.0,
      note='Contractual rights in place / customer relationships; ~$95m p.a. estimate from FY2025 intangible balance and 10-K amortization run-rate (input).')
    S('d_dilutive', '  Dilutive securities (m shares)', 'driver', 'm1', ae_input=0.5)
    S('d_px_g', '  Share-price appreciation % (buyback pricing)', 'driver', 'pct', ae_input=0.08)
    S('d_hdr', 'Debt schedule (scheduled note maturities + commercial paper / revolver to a minimum cash balance)', 'line', 'gen')
    S('d_total', '  Total debt (current maturities + short-term + long-term)', 'line_b', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_curmat")})+N({V("bs_std")})+{V("bs_ltd")},"")',
      e26=lambda: f'={CLr("d_total")}-N({CLr("bs_std")})+{V("d_mat")}+{V("d_roll")}+{V("d_rev")}',
      ae=lambda: f'={PV("d_total")}+{V("d_mat")}+{V("d_roll")}+{V("d_rev")}-{PV("d_rev")}',
      note='Notes at 30-Jun-26 (face $4,440m): 3.90% $400m due 2027, 4.95% $500m 2029, 3.50% $750m 2030, 5.35% $750m 2034, 7.15% $129m 2037, 4.50% $700m 2047, 4.70% $461m 2048, 5.70% $750m 2054; $1.6bn revolver / CP undrawn (Nov-2029).')
    S('d_mat', '  Scheduled maturities / repayments (input, negative)', 'driver', 'm',
      e26_input=0.0, ae_vals={2027: -400.0, 2028: 0.0, 2029: -500.0, 2030: -750.0},
      note='2026E = 2H/26 maturities only (none). 10-Q maturity ladder: 2027 $400m, 2029 $500m, 2030 $750m.')
    S('d_rollpct', '  % of scheduled maturities refinanced (input)', 'driver', 'pct', e26_input=1.0, ae_input=1.0,
      note='100% = each maturity refinanced with new notes at the refinancing rate; 0% = repaid from cash / CP.')
    S('d_roll', '  Refinancing issuance', 'line', 'm', fc_ann=lambda: f'=-{V("d_mat")}*{V("d_rollpct")}')
    S('d_refi', '  Refinanced debt outstanding (year end)', 'line', 'm', e26=lambda: f'={V("d_roll")}',
      ae=lambda: f'={PV("d_refi")}+{V("d_roll")}')
    S('d_cashpre', '  Cash before CP / revolver (opening cash + CFO + CFI + non-debt CFF + maturities + refinancing)', 'line', 'm',
      e26=lambda: (f'={V("cf_end","CI")}+{V("cfo")}+{V("cfi")}+{V("cf_buyb")}+{V("cf_div")}+{V("cf_stock")}+{V("cf_othfin")}'
                   f'+{CLr("cf_debtp")}+{CLr("cf_debtr")}+{V("d_mat")}+{V("d_roll")}-N({CLr("bs_std")})'),
      ae=lambda: f'={PV("cf_end")}+{V("cfo")}+{V("cfi")}+{V("cf_buyb")}+{V("cf_div")}+{V("cf_stock")}+{V("cf_othfin")}+{V("d_mat")}+{V("d_roll")}-{PV("d_rev")}')
    S('d_mincash', '  Minimum cash balance (incl. restricted)', 'driver', 'm', e26_input=250.0, ae_input=250.0)
    S('d_rev', '  Commercial paper / revolver outstanding (year end)', 'line', 'm',
      fc_ann=lambda: f'=MAX(0,{V("d_mincash")}-{V("d_cashpre")})',
      note='Draws when cash would fall below the minimum (e.g. Bull M&A); repaid from surplus cash.')
    S('d_netiss', '  Net issuance / (repayment)', 'line', 'm',
      cfbs_f=lambda: f'=IFERROR({V("d_total")}-{PV("d_total")},"")' if CTX.col.prev else None, ann_only_f=True,
      e26=lambda: f'={V("d_total")}-{V("d_total","CI")}')
    S('d_r_leg', '  Interest rate on legacy notes (opening balance) %', 'pct', 'pct',
      cfbs_f=lambda: f'=IFERROR({V("is_int")}/{PV("d_total")},"")' if CTX.col.prev else None, ann_only_f=True, ae_input=0.0505,
      note='Weighted-average effective rate on notes outstanding 5.04% (10-Q); historical = net interest / opening total debt.')
    S('d_r_cash', '  Interest income yield on opening cash %', 'pct', 'pct', ae_input=0.035)
    S('d_r_refi', '  Interest rate on refinanced debt %', 'pct', 'pct', ae_input=0.0525)
    S('d_r_rev', '  Interest rate on CP / revolver %', 'pct', 'pct', ae_input=0.0475)
    S('bl_hdr', 'Leverage-targeted buybacks (repurchases plug to a minimum net debt / Adjusted EBITDA)', 'line', 'gen')
    S('bl_min', '  Minimum net debt / Adjusted EBITDA (x) (scenario)', 'driver', 'x',
      ae=lambda: '=' + CH(SC['LEV']), note='Scenario-driven floor; Vulcan targets total debt / Adjusted EBITDA of 2.0–2.5x.')
    S('bl_ndpre', '  Net debt before buybacks (year end)', 'line', 'm',
      ae=lambda: (f'={PV("d_total")}+{V("d_mat")}+{V("d_roll")}-({PV("cf_end")}+{V("cfo")}+{V("cfi")}+{V("cf_div")}+{V("cf_stock")}'
                  f'+{V("cf_othfin")}+{V("d_mat")}+{V("d_roll")})'),
      note='Opening debt + maturities + refinancing − (opening cash + CFO + CFI + dividends + other financing + debt flows).')
    S('bl_tgt', '  Target minimum net debt = min. leverage × Adjusted EBITDA', 'line', 'm', ae=lambda: f'={V("bl_min")}*{V("r_cur")}')
    S('bl_plug', '  Share repurchases: plug to minimum leverage', 'line_b', 'm', ae=lambda: f'=MAX(0,{V("bl_tgt")}-{V("bl_ndpre")})',
      note='Zero when leverage is already at or above the floor (e.g. heavy M&A years).')
    S('sch_hdr2', 'Historical reference (driver context)', 'line', 'gen')
    S('sch_ddapct', '  Total DDA&A % of revenues', 'pct', 'pct', cfbs_f=lambda: f'=IFERROR({V("is_dda")}/{V("is_rev")},"")')
    S('sch_roic_pub', '  Memo: company-published ROIC (Adjusted EBITDA / average invested capital, TTM)', 'memo', 'pct',
      data='ngaap.roic_pub', annual_only=True)
    blank()

    # ================================================================== RATIOS
    S('sec_ratio', 'RATIO ANALYSIS', 'section')
    S('ra_hdr', 'DuPont decomposition of ROIC', 'line', 'gen')
    S('ra_ebit', 'Adjusted EBIT (model)', 'line', 'm', cfbs_f=lambda: f'={V("o_ebit")}')
    S('ra_etr', 'Effective tax rate (actual)', 'pct', 'pct', cfbs_f=lambda: f'={V("is_etr")}')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm',
      cfbs_f=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_etr")})*{2 if CTX.col.kind == "H" else 1},"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', cfbs_f=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity (incl. NCI)', 'line', 'm', cfbs_f=lambda: f'={V("bs_te")}')
    S('ra_nd', '  Net debt = Total debt − cash − restricted cash', 'line', 'm',
      cfbs_f=lambda: f'=IFERROR({V("d_total")}-{V("bs_cash")}-N({V("bs_rcash")}),"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'ratio_total', 'pct', cfbs_f=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")',
      note='1H/26 NOPAT annualised (×2).')
    S('ra_m', '  Margin = Adjusted EBIT / Revenues', 'pct', 'pct', cfbs_f=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_t', '  Capital turnover = Revenues / IC', 'line', 'x2',
      cfbs_f=lambda: f'=IFERROR({V("is_rev")}*{2 if CTX.col.kind == "H" else 1}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − effective tax rate)', 'pct', 'pct', cfbs_f=lambda: f'=IFERROR(1-{V("ra_etr")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'pct', 'pct',
      cfbs_f=lambda: f'=IFERROR({V("ra_m")}*{V("ra_t")}*{V("ra_tb")},"n/a")')
    blank()
    S('rn_hdr', 'RONTA decomposition', 'line', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', cfbs_f=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', cfbs_f=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & other intangible assets', 'line', 'm', cfbs_f=lambda: f'=-(N({V("bs_gw")})+N({V("bs_int")}))')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm',
      cfbs_f=lambda: f'=-({V("bs_tcl")}-N({V("bs_curmat")})-N({V("bs_std")}))')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', cfbs_f=lambda: f'=SUM({V("rn_ta")}:{V("rn_nibcl")})')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'ratio_total', 'pct', cfbs_f=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    blank()
    S('roe_hdr', 'Return on Equity (ROE)', 'line', 'gen')
    S('roe_ni', 'Net earnings attributable to Vulcan', 'line', 'm',
      cfbs_f=lambda: f'={V("is_ni")}*{2 if CTX.col.kind == "H" else 1}')
    S('roe_eq', "Vulcan shareholders' equity", 'line', 'm', cfbs_f=lambda: f'={V("bs_veq")}')
    S('roe', 'ROE = NI / Equity', 'ratio_total', 'pct', cfbs_f=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    blank()
    S('lev_hdr', 'Leverage', 'line', 'gen')
    S('lev_nd', 'Net debt = Total debt − cash − restricted cash (company definition)', 'line', 'm', cfbs_f=lambda: f'={V("ra_nd")}')
    S('lev_eb', 'Adjusted EBITDA (current definition)', 'line', 'm',
      cfbs_f=lambda: f'=IF(ISNUMBER({V("r_cur")}),{V("r_cur")}*{2 if CTX.col.kind == "H" else 1},"")')
    S('lev_x', 'Net debt / Adjusted EBITDA (x)', 'line_b', 'x2', cfbs_f=lambda: f'=IFERROR({V("lev_nd")}/{V("lev_eb")},"n/a")',
      note='1H/26 on annualised 1H EBITDA (company reports 1.7x on TTM Adjusted EBITDA).')
    S('lev_td', 'Total debt / Adjusted EBITDA (x)', 'line', 'x2', cfbs_f=lambda: f'=IFERROR({V("d_total")}/{V("lev_eb")},"n/a")')
    blank()

    # ================================================================== VALUATION
    S('sec_val', 'VALUATION', 'section', note='VALUATION — current share price input $243 (per user); applied to 2026E–2030E')
    S('val_px', 'Share price ($) — current', 'driver', 'ps', e26_input=243.0, ae=lambda: f'={PV("val_px")}',
      note='User input (4-Oct-2026).')
    S('val_sh', 'Diluted shares (m)', 'line', 'm1', fc_ann=lambda: f'={V("sh_dil")}')
    S('val_mc', 'Market capitalisation (USDm)', 'line', 'm', fc_ann=lambda: f'=IFERROR({V("val_px")}*{V("val_sh")},"n/a")')
    S('val_nd', 'Net debt (USDm)', 'line', 'm', fc_ann=lambda: f'={V("lev_nd")}')
    S('val_nci', 'Noncontrolling interests (USDm)', 'line', 'm', fc_ann=lambda: f'={V("bs_nci")}')
    S('val_ev', 'Enterprise value (USDm)', 'line_b', 'm', fc_ann=lambda: f'=IFERROR({V("val_mc")}+{V("val_nd")}+{V("val_nci")},"n/a")')
    S('val_hdr', 'Multiples', 'line', 'gen')
    S('val_evs', '  EV / Revenues', 'line', 'x2', fc_ann=lambda: f'=IFERROR({V("val_ev")}/{V("is_rev")},"n/a")')
    S('val_eveb', '  EV / Adjusted EBITDA', 'line', 'x2', fc_ann=lambda: f'=IFERROR({V("val_ev")}/{V("r_cur")},"n/a")')
    S('val_evebit', '  EV / Adjusted EBIT', 'line', 'x2', fc_ann=lambda: f'=IFERROR({V("val_ev")}/{V("o_ebit")},"n/a")')
    S('val_evic', '  EV / IC', 'line', 'x2', fc_ann=lambda: f'=IFERROR({V("val_ev")}/{V("ra_ic")},"n/a")')
    S('val_pe', '  P / E (GAAP diluted)', 'line', 'x2', fc_ann=lambda: f'=IFERROR({V("val_px")}/{V("eps_dil")},"n/a")')
    S('val_pea', '  P / E (Adjusted EPS, company definition)', 'line', 'x2', fc_ann=lambda: f'=IFERROR({V("val_px")}/{V("e_cur_eps")},"n/a")')
    S('val_fcfy', '  FCF yield', 'pct', 'pct', fc_ann=lambda: f'=IFERROR({V("fcf")}/{V("val_mc")},"n/a")')
    S('val_dy', '  Dividend yield', 'pct', 'pct', fc_ann=lambda: f'=IFERROR({V("dps")}/{V("val_px")},"n/a")')
