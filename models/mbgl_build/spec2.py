"""Row specification part 2: cash flow, share schedule, balance sheet, working capital, schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def h26(key): return f'({Q1}{R[key]}+{Q2}{R[key]})'          # 1H/26 actual (flow rows)
def h2e(key): return f'({Q3}{R[key]}+{Q4}{R[key]})'          # 2H/26 estimate (Model P&L rows)
def B2(key): return f'{Q2}{R[key]}'                          # 30-Jun-2026 balance

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'COMBINED / CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note=('CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate). Quarters: Q1 as filed, Q2 = 1H − Q1 (10-Q); '
            'Q3-25 / Q4-25 not published (FY2025 only); 2023–24 annual only.'))
    S('cf_ni', 'Net income', 'line', 'm', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=lambda: f'={h26("cf_ni")}+{h2e("is_ni")}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dda', '  Depreciation & amortization of intangibles', 'line', 'm', data='cf_dda', flow=True, fc=lambda: f'={V("is_dda")}',
      e26=lambda: f'={h26("cf_dda")}+{h2e("is_dda")}')
    S('cf_sbc', '  Stock-based compensation', 'line', 'm', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=lambda: f'={h26("cf_sbc")}+{h2e("is_sbc")}')
    S('cf_def', '  Deferred income taxes', 'line', 'm', data='cf_def', flow=True, e26=lambda: f'={h26("cf_def")}+{V0["def_2h"]}', ae_in=V0['def_ae'],
      note=V0['def_note'])
    S('cf_oth', '  Provision for losses on receivables, restructuring & other non-cash (incl. debt-cost accretion)', 'line', 'm', data='cf_oth', flow=True,
      e26=lambda: f'={h26("cf_oth")}+{V("ds_accr")}', ae=lambda: f'={V("ds_accr")}')
    S('cf_wc', '  Changes in operating assets & liabilities, net (derived)', 'line', 'm', data='cf_wc', flow=True,
      e26=lambda: (f'={h26("cf_wc")}-({V("bs_ar")}-{B2("bs_ar")})-({V("bs_oca")}-{B2("bs_oca")})+({V("bs_ap")}-{B2("bs_ap")})'
                   f'+({V("bs_unearned")}-{B2("bs_unearned")})+({V("bs_ocl")}-{B2("bs_ocl")})'),
      ae=lambda: (f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ap")}-{P("bs_ap")})'
                  f'+({V("bs_unearned")}-{P("bs_unearned")})+({V("bs_ocl")}-{P("bs_ocl")})'),
      note='History: CFO − the lines above (incl. related-party balances). Forecast: −Δ(receivables, other current assets) + Δ(payables, unearned revenue, accrued & other).')
    S('cf_cfo', 'Cash provided by operating activities', 'line_b', 'm', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_wc")})')
    S('cf_capex', 'Capital expenditures', 'line', 'm', data='cf_capex', flow=True, e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: point estimate (1H/26 $12m). 2027E+: revenue × capex %.')
    S('cf_acq', 'Acquisitions, net of cash acquired', 'line', 'm', data='cf_acq', flow=True, e26=lambda: f'={h26("cf_acq")}', ae=lambda: f'=-{V("m_spend")}',
      note='FY2023: Market Scan (Feb-2023). 2027E+: M&A lever.')
    S('cf_oinv', 'Equity investments, related-party loans, dispositions (derived)', 'line', 'm', data='cf_oinv', flow=True, e26=lambda: f'={h26("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Cash used for investing activities', 'line_b', 'm', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_par', 'Net transfers to Parent (carve-out; 1H/26 incl. the $2.0bn separation dividend to S&P Global)', 'line', 'm', data='cf_par', flow=True,
      e26=lambda: f'={h26("cf_par")}', ae_in=0.0)
    S('cf_notes', 'Proceeds from issuance of senior notes', 'line', 'm', data='cf_notes', flow=True, e26=lambda: f'={h26("cf_notes")}', ae_in=0.0,
      note='$2.0bn notes issued 29-May-2026 (net proceeds $1,986m, released from escrow 30-Jun-2026).')
    S('cf_debt', 'Net debt issuance / (repayment) — revolver and refinancing (forecast)', 'line', 'm',
      e26=lambda: f'={V("ds_rev")}-{B2("ds_rev")}+{V("ds_iss")}-{V("ds_repay")}', ae=lambda: f'={V("ds_rev")}-{P("ds_rev")}+{V("ds_iss")}-{V("ds_repay")}')
    S('cf_div', 'Dividends paid', 'line', 'm', e26=lambda: f'=-({Q3}{R["dps"]}*{Q3}{R["sh_basic"]}+{Q4}{R["dps"]}*{Q4}{R["sh_basic"]})',
      ae=lambda: f'=-{V("dps")}*{V("bb_beg")}', note='Quarterly $0.06 from Q3-26. 2027E+: DPS × beginning shares (no circularity with buybacks).')
    S('cf_bb', 'Repurchases of common stock', 'line', 'm', e26=lambda: f'=-{CH(SC["bb26"])}', ae=lambda: f'=-{V("lev_bb")}',
      note='No repurchase program announced. 2027E+ = leverage plug (surplus cash returned once net debt / Adjusted EBITDA is at the scenario target).')
    S('cf_ofin', 'Related-party loan payments, contingent consideration & other financing (derived)', 'line', 'm', data='cf_ofin', flow=True,
      e26=lambda: f'={h26("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Cash provided by (used for) financing activities', 'line_b', 'm', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_par")}:{V("cf_ofin")})')
    S('cf_fx', 'Effect of exchange rate changes on cash', 'line', 'm', data='cf_fx', flow=True, e26=lambda: f'={h26("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+N({V("cf_fx")}),"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}+{V("cf_fx")}')
    S('cf_beg', 'Cash — beginning of period', 'line', 'm', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Cash — end of period', 'line_b', 'm', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}')
    S('cf_chk1', '  Check: beginning cash + CFO + CFI + CFF + FX = ending cash (should be 0; ±1 rounding)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}-{V("cf_end")})<=1,0,{V("cf_beg")}+{V("cf_net")}-{V("cf_end")}),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),ROUND(SUM({V("cf_ni")}:{V("cf_wc")})-{V("cf_cfo")},1),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (company definition: cash from operations − capital expenditures)', 'total', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")},"")')
    S('fcf_pub', '  Company-published free cash flow', 'memo', 'm', data='fcf_pub', flow=True)
    S('fcf_chk', '  Check: model vs company-published free cash flow (should be 0; ±1 rounding)', 'check', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("fcf_pub")}),ISNUMBER({V("fcf")})),IF(ABS({V("fcf")}-{V("fcf_pub")})<=1,0,{V("fcf")}-{V("fcf_pub")}),"")')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted share ($)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / Adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input (FY2023–25: 1.2% / 0.9% / 1.4%; capitalized software included).')
    S('capex_dep', '  Capex / depreciation (x)', 'line', 'x2', all=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("d_dep")})),IFERROR(-{V("cf_capex")}/{V("d_dep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE BUYBACK SCHEDULE', 'section', note='SHARES — 2026E starts from the 294.8m shares distributed on 1-Jul-2026; 2027E+ buybacks via the leverage plug')
    S('bb_px', '  Avg buyback price ($)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_cash', '  Buyback cash deployed (USDm)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'=-{V("cf_bb")}')
    S('bb_sh', '  Implied shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued under equity plans (m)', 'driver', 'm2', e26_in=V0['iss_2h'], ae_in=V0['iss_ae'])
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B2("bs_shares")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from 294,821,320 shares outstanding at 1-Jul-2026 (10-Q cover).')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since the spin (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'COMBINED / CONSOLIDATED BALANCE SHEET (condensed)', 'section',
      note=('BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from the prior year end. Published balance sheets: '
            '31-Dec-2023 (Form 10 draft), 31-Dec-2024 / 2025 (Form 10), 31-Mar-2026 (Form 10), 30-Jun-2026 (10-Q).'))
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Accounts receivable, net', 'line', 'm', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365', note='Receivables = revenue × DSO / 365.')
    S('bs_oca', '  Due from related parties, prepaid & other current assets', 'line', 'm', data='bs_oca', bs=True, e26=lambda: f'={B2("bs_oca")}', ae=lambda: f'={P("bs_oca")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_ppe', '  Property and equipment, net', 'line', 'm', data='bs_ppe', bs=True,
      e26=lambda: f'={B2("bs_ppe")}-({V("cf_capex")}-{h26("cf_capex")})-{h2e("d_dep")}', ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("d_dep")}',
      note='Roll-forward: prior − capex (negative cash flow; capitalized software included here) − depreciation.')
    S('bs_gw', '  Goodwill', 'line', 'm', data='bs_gw', bs=True, e26=lambda: f'={B2("bs_gw")}', ae=lambda: f'={P("bs_gw")}+{V("m_spend")}*(1-{V("m_intp")})')
    S('bs_int', '  Other intangible assets, net', 'line', 'm', data='bs_int', bs=True,
      e26=lambda: f'={B2("bs_int")}-{h2e("d_amort")}', ae=lambda: f'={P("bs_int")}-{V("d_amort")}+{V("m_spend")}*{V("m_intp")}',
      note='Roll-forward: prior − amortization + acquired intangibles (M&A lever).')
    S('bs_onca', '  Right-of-use assets & other non-current assets (incl. related-party loans; derived)', 'line', 'm', data='bs_onca', bs=True,
      e26=lambda: f'={B2("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_ppe")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_ap', '  Accounts payable', 'line', 'm', data='bs_ap', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_app")}')
    S('bs_unearned', '  Unearned revenue', 'line', 'm', data='bs_unearned', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_uep")}')
    S('bs_ocl', '  Accrued compensation, due to related parties & other current liabilities', 'line', 'm', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ltd', '  Long-term debt (senior notes, net of discount & issuance costs; revolver)', 'line', 'm', data='bs_ltd', bs=True, fc=lambda: f'={V("ds_total")}')
    S('bs_dtl', '  Deferred tax liability, net', 'line', 'm', data='bs_dtl', bs=True,
      e26=lambda: f'={B2("bs_dtl")}+({V("cf_def")}-{h26("cf_def")})', ae=lambda: f'={P("bs_dtl")}+{V("cf_def")}')
    S('bs_oncl', '  Operating lease liabilities, due to related parties (non-current) & other', 'line', 'm', data='bs_oncl', bs=True,
      e26=lambda: f'={B2("bs_oncl")}', ae=lambda: f'={P("bs_oncl")}',
      note='To 31-Mar-2026 includes the Canada Carfax related-party loan ($227–305m), settled at the separation.')
    S('bs_tl', 'Total liabilities', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ltd")}:{V("bs_oncl")}),"")')
    S('bs_eq', "Total equity (parent company investment + AOCI to 30-Jun-2026; common stock, APIC, retained earnings & AOCI after the spin)", 'line_b', 'm',
      data='bs_eq', bs=True,
      e26=lambda: f'={B2("bs_eq")}+{h2e("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{h2e("d_sbc")}+({V("cf_fx")}-{h26("cf_fx")})',
      ae=lambda: f'={P("bs_eq")}+{V("is_ni")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_sbc")}+{V("cf_fx")}',
      note='+ net income − dividends − repurchases + stock-based compensation (FX translation flows through AOCI).')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_eq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E)', 'check', 'm', all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),ROUND({V("bs_ta")}-{V("bs_tle")},1),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),ROUND({V("bs_ta")}-{V("bs_ta_pub")},1),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm', data='bs_ta', bs=True)
    S('bs_chk_cash', '  Check: BS cash vs cash-flow ending cash (should be 0)', 'check', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),ROUND({V("bs_cash")}-{V("cf_end")},1),"")')
    S('bs_shares', '  Memo: shares outstanding at period end (m)', 'memo', 'm1', data='bs_shares', bs=True, e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input; set at fiscal-year-end 31-Dec-2025 levels)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IF(ISNUMBER({V("bs_ar")}),IFERROR({V("bs_ar")}/{V("wc_rev")}*365,""),"")',
      e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_app', '  Accounts payable % of revenue', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("bs_ap")}),IFERROR({V("bs_ap")}/{V("wc_rev")},""),"")',
      e26_in=V0['wc']['ap'], ae_in=V0['wc']['ap'])
    S('wc_uep', '  Unearned revenue % of revenue', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("bs_unearned")}),IFERROR({V("bs_unearned")}/{V("wc_rev")},""),"")',
      e26_in=V0['wc']['ue'], ae_in=V0['wc']['ue'])
    S('wc_oclp', '  Accrued & other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IF(ISNUMBER({V("bs_ocl")}),IFERROR({V("bs_ocl")}/{V("wc_rev")},""),"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Operating NWC (receivables + other current assets − payables − unearned − accrued & other)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_oca")}-{V("bs_ap")}-{V("bs_unearned")}-{V("bs_ocl")},"")')
    S('wc_nwc_p', '  NWC % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m shares; RSUs & options)', 'sched', 'm1', ae_in=V0['dil_ae'], note='Assumption (spin-date replacement and new awards).')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    S('ds_h', 'Debt schedule (senior notes repaid / refinanced at maturity; $500m revolver drawn or repaid to a minimum cash balance)', 'sub', 'gen')
    S('ds_face', '  Senior notes — principal (5.050% 2029 $650m; 5.450% 2031 $650m; 6.050% 2036 $700m)', 'sched', 'm',
      e26=lambda: f'={sum(n["face"] for n in MAN["debt"]["notes"])}', ae=lambda: f'={P("ds_face")}+{V("ds_iss")}-{V("ds_repay")}', note=MAN['debt']['src'])
    S('ds_iss', '  New notes issued (refinancing; input)', 'sched', 'm', e26_in=0.0, ae_in=V0['iss_notes'])
    S('ds_repay', '  Notes repaid at maturity (input)', 'sched', 'm', e26_in=0.0, ae_in=V0['repay'], note=V0['repay_note'])
    S('ds_accr', '  Accretion of discount & issuance costs (non-cash; in interest expense)', 'sched', 'm', e26_in=V0['accr_2h'], ae_in=V0['accr_ae'],
      note='$19m unamortized at 30-Jun-2026 (OID $3m + issuance costs $16m) over ~6 years weighted life.')
    S('ds_notes', '  Senior notes — carrying value', 'sched', 'm', hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),{V("bs_ltd")},"")',
      e26=lambda: f'={B2("ds_notes")}+{V("ds_accr")}+{V("ds_iss")}-{V("ds_repay")}', ae=lambda: f'={P("ds_notes")}+{V("ds_accr")}+{V("ds_iss")}-{V("ds_repay")}')
    S('ds_pre', '  Cash before revolver draws / repayments', 'sched', 'm',
      e26=lambda: (f'={B2("bs_cash")}+({V("cf_cfo")}-{h26("cf_cfo")})+({V("cf_cfi")}-{h26("cf_cfi")})+{V("cf_div")}+{V("cf_bb")}+({V("cf_par")}-{h26("cf_par")})'
                   f'+({V("cf_ofin")}-{h26("cf_ofin")})+({V("cf_fx")}-{h26("cf_fx")})+{V("ds_iss")}-{V("ds_repay")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_par")}+{V("cf_ofin")}+{V("cf_fx")}+{V("ds_iss")}-{V("ds_repay")}')
    S('ds_min', '  Minimum cash balance', 'sched', 'm', e26_in=V0['min_cash'], ae_in=V0['min_cash'],
      note='Form 10: notes proceeds sized for ~$200m of cash at the separation.')
    S('ds_rev', '  Revolving credit facility (year end)', 'sched', 'm', hist=lambda: '=0' if (CTX.col.year, CTX.col.q or 4) >= (2026, 2) else None,
      e26=lambda: f'=MAX(0,{B2("ds_rev")}+{V("ds_min")}-{V("ds_pre")})', ae=lambda: f'=MAX(0,{P("ds_rev")}+{V("ds_min")}-{V("ds_pre")})',
      note=MAN['debt']['revolver'])
    S('ds_head', '  Memo: revolver headroom vs the $500m commitment', 'memo_calc', 'm', e26=lambda: f'=500-{V("ds_rev")}', ae=lambda: f'=500-{V("ds_rev")}')
    S('ds_total', '  Total debt (carrying value)', 'sched', 'm', hist=lambda: f'=IF(ISNUMBER({V("bs_ltd")}),{V("bs_ltd")},"")',
      fc=lambda: f'={V("ds_notes")}+{V("ds_rev")}')
    S('ds_net', '  Net issuance / (repayment) incl. accretion', 'sched', 'm', e26=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")', ae=lambda: f'=IFERROR({V("ds_total")}-{P("ds_total")},"")')
    S('ds_r_notes', '  Weighted coupon on opening notes principal %', 'sched', 'pct', ae_in=V0['r_notes'], note=V0['r_notes_note'])
    S('ds_r_rev', '  Interest rate on opening revolver %', 'sched', 'pct', ae_in=0.055, note='SOFR + 1.0–1.625% (rating grid); assumption ~5.5%.')
    S('ds_fees', '  Commitment fees & facility-cost amortization ($m)', 'sched', 'm', ae_in=1.0, note='Assumption: ~10–15bp on the undrawn $500m + $3m facility costs over 5 years.')
    S('ds_r_cash', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=0.03, note='Assumption.')
    S('lev_h', 'Leverage-targeted buybacks (repurchases plug to a target net debt / Adjusted EBITDA, 2027E+)', 'sub', 'gen')
    S('lev_min', '  Target net debt / Adjusted EBITDA (x) (scenario)', 'sched', 'x', ae=lambda: '=' + CH(SC['LEV']), note=V0['lev_note'])
    S('lev_pre', '  Net debt before buybacks (year end)', 'sched', 'm',
      ae=lambda: (f'={P("ds_total")}+{V("ds_accr")}-{P("cf_end")}-{V("cf_cfo")}-{V("cf_cfi")}-{V("cf_div")}-{V("cf_par")}-{V("cf_ofin")}-{V("cf_fx")}'))
    S('lev_tgt', '  Target net debt = target leverage × Adjusted EBITDA', 'sched', 'm', ae=lambda: f'={V("lev_min")}*{V("r_adj")}')
    S('lev_bb', '  Share repurchases: plug to target leverage', 'sched', 'm', ae=lambda: f'=MAX(0,{V("lev_tgt")}-{V("lev_pre")})',
      note='Surplus cash beyond the leverage target is returned via buybacks; feeds the cash-flow repurchase line.')
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of revenue', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_amort', '  Amortization of intangibles % of revenue', 'pct', 'pct', all=ratio('d_amort', 'is_rev'))
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBIT, full-cost: after all D&A; SBC added back per the company definition)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT, full-cost (Adjusted EBITDA − total D&A)', 'line', 'm', ann=True, all=lambda: f'={V("r_ebit_adj")}')
    S('ra_t', 'Effective tax rate', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("e_rate")}+0,IFERROR(MIN(0.4,MAX(0.15,{V("is_etr")})),0.27))')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_eq")}),{V("bs_eq")},"n/a")')
    S('ra_nd', '  Net debt = Total debt − Cash (pre-spin: related-party loan excluded)', 'line', 'm', ann=True, all=lambda: f'=IFERROR({V("ds_total")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_gw', '  − Goodwill & intangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-({V("bs_gw")}+{V("bs_int")}),"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities', 'line', 'm', ann=True, all=lambda: f'=IFERROR(-{V("bs_tcl")},"n/a")')
    S('rn_nta', '  = Net tangible assets', 'line', 'm', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / NTA', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', 'Total equity', 'line', 'm', ann=True, all=lambda: f'={V("ra_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt = Total debt − cash', 'line', 'm', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA', 'line', 'm', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x) (covenant: total net leverage ≤ 3.50x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price ($) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}')
    S('v_sh', 'Diluted shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+{V0["dil_q"]}', ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (USDm)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (USDm)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_nci', 'Noncontrolling interests (USDm; none)', 'line', 'm', e26_in=0.0, ae_in=0.0)
    S('v_ev', 'Enterprise value (USDm)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")', ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted operating profit', lambda: f'=IFERROR({V("v_ev")}/{V("o_adj")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (GAAP diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted EPS, model definition)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
