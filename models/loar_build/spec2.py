"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def h26(key):   # 1H/26 actual for a flow row
    return f'({Q1}{R[key]}+{Q2}{R[key]})'
def B2(key): return f'{Q2}{R[key]}'      # 30-Jun-2026 balance
_NEXT = {'AK': 'AL', 'AL': 'AM', 'AM': 'AN', 'AN': 'AO', 'AO': 'AO'}

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements; 2022 quarters: prospectus summary lines only)')
    S('cf_ni', 'Net income (loss)', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=lambda: f'={h26("cf_ni")}+{Q3}{R["is_ni"]}+{Q4}{R["is_ni"]}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization of intangible and other long-term assets', 'line', 'm1', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}',
      e26=lambda: f'={h26("cf_dda")}+{Q3}{R["is_dda"]}+{Q4}{R["is_dda"]}')
    S('cf_sbc', '  Stock-based compensation', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}',
      e26=lambda: f'={h26("cf_sbc")}+{Q3}{R["is_sbc"]}+{Q4}{R["is_sbc"]}')
    S('cf_def', '  Deferred income taxes', 'line', 'm1', data='cf_def', flow=True, e26=lambda: f'={h26("cf_def")}', ae_in=V0['def_tax_ae'],
      note='2027E+: deferred tax benefit on book amortization of non-deductible acquired intangibles (LMB, SCHROTH) (input).')
    S('cf_oth', '  Debt-cost amortization, inventory step-up, lease & contingent-consideration items, other (derived)', 'line', 'm1', data='cf_oth', flow=True,
      e26=lambda: f'={h26("cf_oth")}+{Q3}{R["d_step"]}+{Q4}{R["d_step"]}+{Q3}{R["d_oth"]}+{Q4}{R["d_oth"]}+{V("ds_accr")}',
      ae=lambda: f'={V("d_step")}+{V("d_oth")}+{V("ds_accr")}', note='Debt issuance-cost amortization (~$1m a quarter, inside interest expense) + non-cash P&L items added back.')
    S('cf_wc', '  Changes in operating assets & liabilities (working capital), net', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={h26("cf_wc")}-({V("bs_ar")}-{B2("bs_ar")})-({V("bs_inv")}-{B2("bs_inv")})+({V("bs_ap")}-{B2("bs_ap")})'
                   f'+({V("bs_ocl")}-{B2("bs_ocl")})'),
      ae=lambda: f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ocl")}-{P("bs_ocl")})',
      note='Linked to the balance sheet: −Δ(receivables, inventories) + Δ(payables, accrued & other current liabilities). 2026E = 1H/26 actual + 2H change from 30-Jun-26.')
    S('cf_cfo', 'Net cash provided by operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Capital expenditures', 'line', 'm1', data='cf_capex', flow=True, e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: FY26 capex point estimate. 2027E+: net sales × capex %.')
    S('cf_acq', 'Payments for acquisitions, net of cash acquired', 'line', 'm1', data='cf_acq', flow=True, e26=lambda: f'={h26("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='2026E = 1H/26 actual (Harper Engineering $249.8m); no further deals assumed in 2H/26. 2027E+: M&A lever.')
    S('cf_oinv', 'Other investing activities, net (derived: asset sales, purchase-price adjustments)', 'line', 'm1', data='cf_oinv', flow=True,
      e26=lambda: f'={h26("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_eq', 'Net proceeds from issuance of common stock (IPO, follow-on, option exercises)', 'line', 'm1', data='cf_eq', flow=True,
      e26=lambda: f'={h26("cf_eq")}', ae_in=V0['opt_ae'], note='IPO Apr-2024 (net $325.7m) and follow-on Dec-2024 ($311.5m); option exercises thereafter.')
    S('cf_dbin', 'Proceeds from issuance of long-term debt', 'line', 'm1', data='cf_dbin', flow=True,
      e26=lambda: f'={h26("cf_dbin")}+MAX(0,{V("ds_fac")}-{B2("ds_fac")}-{V("ds_accr")})', ae=lambda: f'=MAX(0,{V("ds_fac")}-{P("ds_fac")}-{V("ds_accr")})')
    S('cf_dbout', 'Payments of long-term debt', 'line', 'm1', data='cf_dbout', flow=True,
      e26=lambda: f'={h26("cf_dbout")}+MIN(0,{V("ds_fac")}-{B2("ds_fac")}-{V("ds_accr")})', ae=lambda: f'=MIN(0,{V("ds_fac")}-{P("ds_fac")}-{V("ds_accr")})',
      note='Net borrowing / (repayment) = change in term loans per the debt schedule (voluntary prepayment at par with surplus cash; draws for M&A).')
    S('cf_bb', 'Repurchases of common stock', 'line', 'm1', qe_in={3: 0.0, 4: 0.0}, e26=lambda: f'=-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='No repurchase program to date. 2027E+ = leverage plug (surplus cash returned once net debt / Adjusted EBITDA reaches the scenario floor).')
    S('cf_ofin', 'Financing costs, finance-lease payments & other financing, net (derived)', 'line', 'm1', data='cf_ofin', flow=True,
      e26=lambda: f'={h26("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash provided by (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_eq")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of translation adjustments on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={h26("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net increase (decrease) in cash', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: CFO + CFI + CFF + FX = change in cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=0.015,0,ROUND({V("cf_beg")}+{V("cf_net")}-{V("cf_end")},2)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")})<=0.015,0,ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},2)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (operating cash flow − capital expenditures)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")', note='Model definition (Loar does not publish free cash flow).')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / Adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input (2022–25: 2.3–3.8% of net sales).')
    S('capex_dep', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E starts from shares outstanding at 30-Jun-2026; 2027E+ buybacks only via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=0.1, ae_in=0.3)
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B2("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from 93.68m shares outstanding at 30-Jun-2026 (Q2-26 balance sheet).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since 2H/26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end. Quarter-end balance sheets published from Q1-24 (FY2022-23 year ends from the prospectus).')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365', note='Receivables = net sales × DSO / 365.')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other current assets (incl. income taxes receivable)', 'line', 'm1', data='bs_oca', bs=True, e26=lambda: f'={B2("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property, plant & equipment, net', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B2("bs_ppe")}-({V("cf_capex")}-{h26("cf_capex")})-({Q3}{R["d_dep"]}+{Q4}{R["d_dep"]})',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}+{V("m_spend")}*{V("m_ppe")}', note='Roll-forward: prior − capex (negative cash flow) − depreciation + acquired PP&E.')
    S('bs_gw', '  Goodwill', 'line', 'm1', data='bs_gw', bs=True, e26=lambda: f'={B2("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_ppe")}-{V("m_intp")})')
    S('bs_int', '  Intangible assets, net', 'line', 'm1', data='bs_int', bs=True,
      e26=lambda: f'={B2("bs_int")}-({Q3}{R["d_amort"]}+{Q4}{R["d_amort"]})', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − amortization + acquired intangibles (M&A lever).')
    S('bs_onca', '  Lease right-of-use & other long-term assets (derived)', 'line', 'm1', data='bs_onca', bs=True, e26=lambda: f'={B2("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_cdebt', '  Current portion of long-term debt', 'line', 'm1', data='bs_cdebt', bs=True, e26=lambda: f'=MIN({V("ds_total")},{B2("bs_cdebt")})',
      ae=lambda: f'=MIN({V("ds_total")},{P("bs_cdebt")})', note='Held at the 30-Jun-2026 level (term-loan scheduled amortization).')
    S('bs_ocl', '  Accrued expenses, income taxes payable & current lease liabilities (derived)', 'line', 'm1', data='bs_ocl', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt, net', 'line', 'm1', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}-{V("bs_cdebt")}')
    S('bs_dtl', '  Deferred income taxes', 'line', 'm1', data='bs_dtl', bs=True,
      e26=lambda: f'={B2("bs_dtl")}+({V("cf_def")}-{h26("cf_def")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_oncl', '  Lease, environmental, contingent-consideration & other long-term liabilities (derived)', 'line', 'm1', data='bs_oncl', bs=True,
      e26=lambda: f'={B2("bs_oncl")}', ae=lambda: f'={P("bs_oncl")}', note='Includes the Harper Engineering contingent consideration ($16.6m at 30-Jun-2026; max $55m, 2026–31 targets).')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_e', "Stockholders' equity:", 'sub', 'gen')
    S('bs_cap', "  Common stock & additional paid-in capital (member's equity pre-IPO)", 'line', 'm1', data='bs_cap', bs=True,
      e26=lambda: f'={B2("bs_cap")}+({V("cf_sbc")}-{h26("cf_sbc")})+({V("cf_eq")}-{h26("cf_eq")})+({V("cf_bb")}-{h26("cf_bb")})',
      ae=lambda: f'={P("bs_cap")}+{V("cf_sbc")}+{V("cf_eq")}+{V("cf_bb")}',
      note="+ stock-based compensation + share issuance − repurchases (retired; Delaware). Pre-IPO (to Q1-24): member's equity of Loar Holdings, LLC.")
    S('bs_re', '  Retained earnings (accumulated deficit)', 'line', 'm1', data='bs_re', bs=True,
      e26=lambda: f'={B2("bs_re")}+{Q3}{R["is_ni"]}+{Q4}{R["is_ni"]}', ae=lambda: f'={P("bs_re")}+{V("is_ni")}', note='+ net income (no dividends).')
    S('bs_aoci', '  Accumulated other comprehensive income (loss)', 'line', 'm1', data='bs_aoci', bs=True,
      e26=lambda: f'={B2("bs_aoci")}+({V("cf_fx")}-{h26("cf_fx")})', ae=lambda: f'={P("bs_aoci")}')
    S('bs_teq', "Total stockholders' equity", 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cap")}),SUM({V("bs_cap")}:{V("bs_aoci")}),"")')
    S('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.015,0,ROUND({V("bs_ta")}-{V("bs_tle")},2)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},2),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}-{V("cf_end")},2),"")')
    S('bs_shares', '  Memo: common shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('bs_fl', '  Memo: finance lease liabilities (current + long-term; in net debt)', 'memo', 'm1', data='bs_fl', bs=True, e26=lambda: f'={B2("bs_fl")}', ae=lambda: f'={P("bs_fl")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_oclp', '  Accrued & other current liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + inventories − payables − accrued & other current liabilities)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}-{V("bs_ap")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ppa_h', 'Acquisitions — consideration & purchase-price allocation (closing-quarter column)', 'sub', 'gen')
    for k, lab in [('cons', 'Consideration — net assets acquired (cash paid incl. debt repaid; Harper incl. contingent consideration as a liability)'),
                   ('ca', 'Current assets acquired (incl. inventory at fair value)'), ('ppe', 'Property, plant & equipment'),
                   ('intang', 'Intangible assets (customer relationships, trade names, technology)'), ('gw', 'Goodwill'),
                   ('onca', 'Other noncurrent assets (incl. deferred tax assets)'), ('cl', 'Current liabilities assumed'),
                   ('ncl', 'Noncurrent liabilities assumed (incl. contingent consideration, leases)'), ('dtl', 'Deferred income taxes')]:
        S(f'ppa_{k}', f'  {lab}', 'sched', 'm1', data=f'ppa_{k}', ppa=True)
    S('ppa_chk', '  Check: assets acquired − liabilities assumed − consideration (should be 0)', 'check', 'm1',
      hist=lambda: (f'=IF(ISNUMBER({V("ppa_cons")}),ROUND(N({V("ppa_ca")})+N({V("ppa_ppe")})+N({V("ppa_intang")})+N({V("ppa_gw")})+N({V("ppa_onca")})'
                    f'-N({V("ppa_cl")})-N({V("ppa_ncl")})-N({V("ppa_dtl")})-{V("ppa_cons")},2),"")'))
    S('ppa_names', '  Deal(s) closed in the quarter', 'text', 'gen', data='ppa_names', ppa=True, textdata=True)
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; options & RSUs)', 'sched', 'm1', ae_in=1.9)
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (term loans prepayable at par: drawn / repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_total', '  Total debt, net of issuance costs (current + long-term)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),N({V("bs_cdebt")})+{V("bs_ltd")},"")', fc=lambda: f'={V("ds_notes")}+{V("ds_fac")}', note=MAN['debt'])
    S('ds_notes', '  Other debt — West Virginia EDA notes (forgivable; from Jul-2025)', 'sched', 'm1', e26_in=1.5, ae_in=1.5,
      hist=lambda: f'=IF(ISNUMBER({V("ds_total")}),{1.5 if (CTX.col.year, CTX.col.q or 4) >= (2025, 3) else 0},"")')
    S('ds_pre', '  Cash before term-loan draws / prepayments (opening cash + CFO + CFI + equity, buybacks & other financing + FX)', 'sched', 'm1',
      e26=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_eq")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_fx")}+{h26("cf_dbin")}+{h26("cf_dbout")}',
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_eq")}+{V("cf_bb")}+{V("cf_ofin")}+{V("cf_fx")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm1', e26_in=V0['min_cash'], ae_in=V0['min_cash'])
    S('ds_accr', '  Accretion of debt issuance costs (non-cash; in interest expense)', 'sched', 'm1', e26=lambda: f'={2 * V0["dcost_q"]}', ae=lambda: f'={4 * V0["dcost_q"]}',
      note='~$1m a quarter (1H/26 $1.9m): increases the term-loan carrying value; added back in operating cash flow.')
    S('ds_fac', '  Term loans (carrying value; prepayable at par, year end)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("ds_total")}),{V("ds_total")}-{V("ds_notes")},"")',
      e26=lambda: f'=MAX(0,{B2("ds_fac")}+{V("ds_min")}-{V("ds_pre")})+{V("ds_accr")}', ae=lambda: f'=MAX(0,{P("ds_fac")}+{V("ds_min")}-{V("ds_pre")})+{V("ds_accr")}',
      note='Surplus cash above the minimum balance prepays term loans (no premium); shortfalls (M&A) are drawn. Maturity 10-May-2030 assumed refinanced / extended.')
    S('ds_net', '  Net issuance / (repayment)', 'sched', 'm1', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_fac', '  Interest rate on term loans (opening balance; SOFR + 4.25% incl. debt-cost amortization) %', 'sched', 'pct', ae_in=V0['r_fac'], note=V0['r_fac_note'])
    S('ds_r_notes', '  Interest rate on other debt %', 'sched', 'pct', ae_in=0.0)
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.03)
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a minimum net debt / Adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Minimum net debt / Adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm1',
      ae=lambda: f'={P("ds_notes")}+{P("ds_fac")}+{P("bs_fl")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_eq")}-{V("cf_ofin")}-{V("cf_fx")}')
    S('lev_tgt', '  Target minimum net debt = min. leverage × Adjusted EBITDA', 'sched', 'm1', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to minimum leverage', 'sched', 'm1', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage floor is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization % of net sales', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    S('hr_int', '  Interest expense ÷ average total debt %', 'pct', 'pct',
      all=lambda: (f'=IFERROR({V("is_int")}*{4 if CTX.col.q else 1}/AVERAGE({V("ds_total")},{(CTX.col.prevq if CTX.col.q else CTX.col.prior)}{R["ds_total"]}),"")'
                   if (CTX.col.prevq if CTX.col.q else CTX.col.prior) else None))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBIT)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (Adjusted EBITDA − D&A)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (actual; 25% normalised before 2024)', 'line', 'pct', ann=True,
      all=lambda: f'={V("is_etr")}' if CTX.col.year >= 2024 else '=0.25')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', "  Total stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt + finance leases − Cash', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ds_total")}+N({V("bs_fl")})-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − effective tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & acquired intangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-({V("bs_tcl")}-N({V("bs_cdebt")})),"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', "Stockholders' equity", 'line', 'm1', ann=True, all=lambda: f'={V("ra_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt + finance leases − cash', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (company definition)', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm)', 'line', 'm', e26_in=0.0, ae_in=0.0)
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBITA', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (Adjusted EPS, current definition)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
