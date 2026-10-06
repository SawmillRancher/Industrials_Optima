"""Row specification part 2: cash flow, share buyback schedule, balance sheet, working capital, lease (IFRS 16) schedule, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def h26(key):   # 1H/26 actual for a flow row
    return f'({Q1}{R[key]}+{Q2}{R[key]})'
def B2(key): return f'{Q2}{R[key]}'      # 30-Jun-2026 balance
def H2(key): return f'({Q3}{R[key]}+{Q4}{R[key]})'   # 2H/26E from the P&L quarters

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS', 'section',
      note='CASH FLOW — forecast logic (annual; 2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements)')
    S('cf_ni', 'Net income (loss)', 'line', 'm1', data='cf_ni', flow=True, fc=lambda: f'={V("is_ni")}', e26=lambda: f'={h26("cf_ni")}+{H2("is_ni")}')
    S('cf_adj', 'Adjustments:', 'sub', 'gen')
    S('cf_dna', '  Depreciation & amortization', 'line', 'm1', data='cf_dna', flow=True, fc=lambda: f'={V("is_dda")}', e26=lambda: f'={h26("cf_dna")}+{H2("is_dda")}')
    S('cf_sbc', '  Share-based compensation', 'line', 'm1', data='cf_sbc', flow=True, fc=lambda: f'={V("is_sbc")}', e26=lambda: f'={h26("cf_sbc")}+{H2("is_sbc")}')
    S('cf_oth', '  Income taxes, net interest, exchange differences, provisions & other non-cash items (derived)', 'line', 'm1', data='cf_oth', flow=True,
      e26=lambda: f'={h26("cf_oth")}+{H2("is_tax")}+{H2("is_fexp")}-{H2("is_finc")}', ae=lambda: f'={V("is_tax")}+{V("is_fexp")}-{V("is_finc")}',
      note='Add-back of P&L tax and net interest (paid / received below); forecast FX result treated as cash.')
    S('cf_wc', '  Change in working capital (trade receivables, inventories, trade payables, other current items)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: (f'={h26("cf_wc")}-({V("bs_ar")}-{B2("bs_ar")})-({V("bs_inv")}-{B2("bs_inv")})-({V("bs_oca")}-{B2("bs_oca")})'
                   f'+({V("bs_ap")}-{B2("bs_ap")})+({V("bs_ocl")}-{B2("bs_ocl")})'),
      ae=lambda: f'=-({V("bs_ar")}-{P("bs_ar")})-({V("bs_inv")}-{P("bs_inv")})-({V("bs_oca")}-{P("bs_oca")})+({V("bs_ap")}-{P("bs_ap")})+({V("bs_ocl")}-{P("bs_ocl")})',
      note='Linked to the balance sheet. 2026E = 1H/26 actual + 2H change from 30-Jun-26.')
    S('cf_taxp', '  Interest received and income taxes paid', 'line', 'm1', data='cf_taxp', flow=True,
      e26=lambda: f'={h26("cf_taxp")}-{H2("is_tax")}+{H2("is_finc")}', ae=lambda: f'=-{V("is_tax")}+{V("is_finc")}')
    S('cf_cfo', 'Cash flow from operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_taxp")})')
    S('cf_capex', 'Purchase of property, plant & equipment and intangible assets', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}', note='2026E: FY26 point estimate. 2027E+: net sales × capex % (stores, distribution centres, IT, LightSpray capacity).')
    S('cf_oinv', 'Other investing activities (disposals, contingent consideration, acquisitions)', 'line', 'm1', data='cf_oinv', flow=True, e26=lambda: f'={h26("cf_oinv")}', ae_in=0.0)
    S('cf_cfi', 'Cash flow from investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_lease', 'Payments of lease liabilities (principal)', 'line', 'm1', data='cf_lease', flow=True, e26=lambda: f'=-{PT("pt_lease")}', ae=lambda: f'=-{V("ls_rdep")}',
      note='2026E: FY26 point estimate. 2027E+: ≈ right-of-use depreciation (steady state; lease schedule below).')
    S('cf_eq', 'Proceeds from share issues / sale of treasury shares (equity plans; IPO 2021)', 'line', 'm1', data='cf_eq', flow=True,
      e26=lambda: f'={h26("cf_eq")}', ae_in=V0['eq_ae'], note='IPO Sep-2021 (net ~CHF 0.6bn); thereafter sale of treasury shares to employees.')
    S('cf_bb', 'Repurchase of Class A shares', 'line', 'm1', e26=lambda: f'=-{V("bb_cash")}', ae=lambda: f'=-{V("bb_cash")}',
      note='USD 1bn authorization (22-Sep-2026, to Dec-2029); CHF = USD × USD/CHF (buyback schedule).')
    S('cf_intp', 'Interest paid', 'line', 'm1', data='cf_intp', flow=True, e26=lambda: f'={h26("cf_intp")}-{H2("is_fexp")}', ae=lambda: f'=-{V("is_fexp")}')
    S('cf_ofin', 'Other financing (financial liabilities, equity transaction costs) (derived)', 'line', 'm1', data='cf_ofin', flow=True, e26=lambda: f'={h26("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Cash flow from financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_lease")}:{V("cf_ofin")})')
    S('cf_fx', 'Net impact of foreign exchange rate differences on cash', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={h26("cf_fx")}', ae_in=0.0)
    S('cf_net', 'Change in net cash and cash equivalents (excl. FX)', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")},"")',
      fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Net cash — beginning of period', 'line', 'm1', data='cf_beg', e26=lambda: f'={P("cf_end")}', ae=lambda: f'={P("cf_end")}')
    S('cf_end', 'Net cash — end of period (net of bank overdrafts)', 'line_b', 'm1', data='cf_end', fc=lambda: f'={V("cf_beg")}+{V("cf_net")}+{V("cf_fx")}')
    S('cf_chk1', '  Check: beginning + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}+{V("cf_fx")}-{V("cf_end")})<=0.25,0,ROUND({V("cf_beg")}+{V("cf_net")}+{V("cf_fx")}-{V("cf_end")},2)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_taxp")})-{V("cf_cfo")})<=0.015,0,ROUND(SUM({V("cf_ni")}:{V("cf_taxp")})-{V("cf_cfo")},2)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (CFO − capex − lease principal payments)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+{V("cf_lease")},"")',
      note='Model definition (rent-adjusted under IFRS 16). On lists "Free Cash Flow" among its Investor Day non-IFRS measures but does not reconcile it in the quarterly releases.')
    S('fcf_g', '  FCF y/y %', 'growth', 'pct', all=growth('fcf'))
    S('fcf_m', '  FCF % of net sales', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / adjusted net income conversion %', 'pct', 'pct', all=ratio('fcf', 'e_adjni'))
    S('fcf_ps', '  FCF per diluted Class A share (CHF)', 'line', 'ps', all=ratio('fcf', 'sh_dil'))
    S('fcf_eb', '  FCF / Adjusted EBITDA %', 'pct', 'pct', all=ratio('fcf', 'r_adj'))
    S('capex_h', 'Capex ratios', 'sub', 'gen')
    S('capex_pct', '  Capex % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input (2023–25: 2.6–2.8% of net sales; 1H/26 2.8%).')
    S('capex_dep', '  Capex / non-lease depreciation & amortization (x)', 'line', 'x2', all=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("ls_odep")})),IFERROR(-{V("cf_capex")}/{V("ls_odep")},""),"")')
    blank()

    # ------------------------------------------------------------------ SHARES / BUYBACK
    S('sec_bb', 'SHARE BUYBACK SCHEDULE (USD 1bn Class A authorization, Sep-2026 to Dec-2029)', 'section',
      note='SHARES — Class A-equivalent shares; buybacks in USD (scenario table) converted at the USD/CHF input; 2030E assumes a renewed programme')
    S('bb_usd', '  Buyback cash deployed (USD m)', 'line', 'm', e26=lambda: f'={CH(SC["bb26"])}', ae=lambda: f'={CH(SC["BB"][CTX.col.year])}',
      note='Base: authorization executed evenly over Q4-26–2029 (≈USD 77m in Q4-26, ≈USD 308m p.a.); Bull faster, Bear slower (scenario table).')
    S('bb_auth', '  Memo: remaining USD 1bn authorization (USD m, year end)', 'memo_calc', 'm',
      e26=lambda: f'={V0["auth"]}-{V("bb_usd")}', ae=lambda: (f'={P("bb_auth")}-{V("bb_usd")}' if CTX.col.year <= 2029 else None),
      note='Negative = spend beyond the current authorization (requires a new board authorization).')
    S('bb_fx', '  USD/CHF (CHF per USD)', 'line', 'm2', e26=lambda: f'={V("v_fx")}', ae=lambda: f'={P("bb_fx")}')
    S('bb_cash', '  Buyback cash deployed (CHF m)', 'line', 'm', e26=lambda: f'={V("bb_usd")}*{V("bb_fx")}', ae=lambda: f'={V("bb_usd")}*{V("bb_fx")}')
    S('bb_px', '  Avg buyback price (USD)', 'line', 'm2', e26=lambda: f'={V("v_pxu")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_sh', '  Implied Class A shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_usd")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_usd")}/{V("bb_px")},0)')
    S('bb_iss', '  Shares issued / delivered under equity plans (m)', 'driver', 'm2', e26_in=0.6, ae_in=1.2,
      note='Treasury shares delivered to employees (~1–2m Class A-equivalent shares p.a. 2023–25).')
    S('bb_beg', '  Beginning Class A-equivalent shares outstanding (m)', 'line', 'm1', e26=lambda: f'={B2("sh_basic")}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from the Q2-26 weighted basic Class A-equivalent shares (300.4m Class A + 335.3m Class B ÷ 10) as the 30-Jun-2026 proxy.')
    S('bb_end', '  Ending Class A-equivalent shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}+{V("bb_iss")}')
    S('bb_pct', '  % of shares repurchased', 'pct', 'pct', e26=ratio('bb_sh', 'bb_beg'), ae=ratio('bb_sh', 'bb_beg'))
    S('bb_cum', '  Memo: cumulative shares repurchased since Q4-26 (m)', 'memo', 'm1', e26=lambda: f'={V("bb_sh")}', ae=lambda: f'={P("bb_cum")}+{V("bb_sh")}')
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED BALANCE SHEET', 'section',
      note='BS FORECAST — 2026E rolled forward from the 30-Jun-2026 balance sheet + 2H flows; 2027E+ from prior year end. Quarter-end balance sheets from Q3-21 (FY2020 from the FY2021 release).')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}')
    S('bs_ar', '  Trade receivables', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365', note='Receivables = net sales × DSO / 365.')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other current financial & operating assets', 'line', 'm1', data='bs_oca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ocap")}')
    S('bs_tca', 'Total current assets', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_oca")}),"")')
    S('bs_fa', '  Property, plant & equipment and intangible assets', 'line', 'm1', data='bs_fa', bs=True,
      e26=lambda: f'={B2("bs_fa")}-({V("cf_capex")}-{h26("cf_capex")})-{H2("d_dna")}*(1-{V("ls_share")})',
      ae=lambda: f'={P("bs_fa")}-{V("cf_capex")}-{V("ls_odep")}', note='Roll-forward: prior + capex − non-lease D&A.')
    S('bs_rou', '  Right-of-use assets (IFRS 16)', 'line', 'm1', data='bs_rou', bs=True, fc=lambda: f'={V("wc_rev")}*{V("ls_rou_pct")}',
      note='Store, office and warehouse leases; forecast at a % of net sales (new leases = plug in the lease schedule).')
    S('bs_dta', '  Deferred tax assets', 'line', 'm1', data='bs_dta', bs=True, e26=lambda: f'={B2("bs_dta")}', ae=lambda: f'={P("bs_dta")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),{V("bs_tca")}+SUM({V("bs_fa")}:{V("bs_dta")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_ap', '  Trade payables', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_cfl', '  Current lease liabilities & other current financial liabilities', 'line', 'm1', data='bs_cfl', bs=True, fc=lambda: f'={V("ls_ll")}*{V("ls_cur")}',
      note='Lease liabilities shown separately from Q1-25; before, inside other financial liabilities (incl. Q1-22 bank overdraft CHF 25.8m).')
    S('bs_ocl', '  Other current operating liabilities, provisions & income tax liabilities', 'line', 'm1', data='bs_ocl', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_tcl', 'Total current liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),SUM({V("bs_ap")}:{V("bs_ocl")}),"")')
    S('bs_ncfl', '  Non-current lease liabilities & other non-current financial liabilities', 'line', 'm1', data='bs_ncfl', bs=True, fc=lambda: f'={V("ls_ll")}-{V("bs_cfl")}')
    S('bs_oncl', '  Employee benefit obligations, provisions & deferred tax liabilities', 'line', 'm1', data='bs_oncl', bs=True,
      e26=lambda: f'={B2("bs_oncl")}', ae=lambda: f'={P("bs_oncl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_ap")}),{V("bs_tcl")}+SUM({V("bs_ncfl")}:{V("bs_oncl")}),"")')
    S('bs_e', 'Equity:', 'sub', 'gen')
    S('bs_cap', '  Share capital, capital reserves & treasury shares', 'line', 'm1', data='bs_cap', bs=True,
      e26=lambda: f'={B2("bs_cap")}+({V("cf_sbc")}-{h26("cf_sbc")})+({V("cf_eq")}-{h26("cf_eq")})+{V("cf_bb")}',
      ae=lambda: f'={P("bs_cap")}+{V("cf_sbc")}+{V("cf_eq")}+{V("cf_bb")}', note='+ share-based compensation + treasury-share sales − repurchases (held as treasury shares).')
    S('bs_ores', '  Other reserves (translation, actuarial)', 'line', 'm1', data='bs_ores', bs=True,
      e26=lambda: f'={B2("bs_ores")}+({V("cf_fx")}-{h26("cf_fx")})', ae=lambda: f'={P("bs_ores")}+{V("cf_fx")}')
    S('bs_re', '  Retained earnings (accumulated losses)', 'line', 'm1', data='bs_re', bs=True,
      e26=lambda: f'={B2("bs_re")}+{H2("is_ni")}', ae=lambda: f'={P("bs_re")}+{V("is_ni")}', note='+ net income (no dividends).')
    S('bs_teq', 'Total equity', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cap")}),SUM({V("bs_cap")}:{V("bs_re")}),"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E; ±0.4 rounding of one-decimal lines)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.45,0,ROUND({V("bs_ta")}-{V("bs_tle")},2)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0; ±0.3 rounding)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.35,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},2)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_od', '  Memo: bank overdraft netted in cash-flow cash (Q1-22)', 'memo', 'm1', data='overdraft')
    S('bs_chk_cash', '  Check: BS cash − overdraft vs cash-flow ending net cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-N({V("bs_od")})-{V("cf_end")})<=0.15,0,ROUND({V("bs_cash")}-N({V("bs_od")})-{V("cf_end")},2)),"")')
    S('bs_shares', '  Memo: Class A-equivalent shares outstanding at period end (m; forecast)', 'memo', 'm1', e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'section', note='WORKING CAPITAL — forecast drivers (blue = input)')
    S('wc_rev', '  Net sales — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — trade receivables / net sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — trade payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_ocap', '  Other current assets % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', e26_in=V0['wc']['oca'], ae_in=V0['wc']['oca'])
    S('wc_oclp', '  Other current operating liabilities % of net sales', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Net working capital (company definition: trade receivables + inventories − trade payables)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}-{V("bs_ap")},"")')
    S('wc_nwc_p', '  NWC % of net sales (annualised)', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")')
    S('wc_dnwc', '  ΔNWC (y/y)', 'line', 'm1', all=lambda: (f'=IF(AND(ISNUMBER({V("wc_nwc")}),ISNUMBER({P("wc_nwc")})),{V("wc_nwc")}-{P("wc_nwc")},"")' if CTX.col.prior else None))
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('ls_h', 'Leases (IFRS 16) — right-of-use assets and lease liabilities', 'sub', 'gen')
    S('ls_share', '  Right-of-use depreciation % of total D&A', 'sched', 'pct', e26_in=V0['rou_share'], ae_in=V0['rou_share'],
      note=V0['rou_note'])
    S('ls_rdep', '  Right-of-use depreciation', 'sched', 'm1', e26=lambda: f'={V("d_dna")}*{V("ls_share")}', ae=lambda: f'={V("d_dna")}*{V("ls_share")}')
    S('ls_odep', '  Depreciation & amortization of PP&E and intangibles', 'sched', 'm1', e26=lambda: f'={V("d_dna")}-{V("ls_rdep")}', ae=lambda: f'={V("d_dna")}-{V("ls_rdep")}')
    S('ls_rou_pct', '  Right-of-use assets % of net sales', 'sched', 'pct', hist=lambda: f'=IFERROR({V("bs_rou")}/{V("wc_rev")},"")',
      e26_in=V0['rou_pct'], ae_in=V0['rou_pct'], note='30-Jun-26: 15.8% of annualised 1H/26 sales (DTC store roll-out).')
    S('ls_new', '  New leases (non-cash additions; plug = Δ right-of-use + RoU depreciation)', 'sched', 'm1',
      e26=lambda: f'={V("bs_rou")}-{B2("bs_rou")}+{H2("d_dna")}*{V("ls_share")}', ae=lambda: f'={V("bs_rou")}-{P("bs_rou")}+{V("ls_rdep")}')
    S('ls_ll', '  Lease & other financial liabilities (current + non-current)', 'sched', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_cfl")}),{V("bs_cfl")}+{V("bs_ncfl")},"")',
      e26=lambda: f'={B2("ls_ll")}+{V("ls_new")}+({V("cf_lease")}-{h26("cf_lease")})', ae=lambda: f'={P("ls_ll")}+{V("ls_new")}+{V("cf_lease")}',
      note='Roll-forward: prior + new leases − principal payments. No bank debt (CHF 700m revolving facility, undrawn).')
    S('ls_cur', '  Current portion %', 'sched', 'pct', hist=lambda: f'=IFERROR({V("bs_cfl")}/{V("ls_ll")},"")', e26_in=V0['ll_cur'], ae_in=V0['ll_cur'])
    S('ls_rate', '  Financial expense ÷ opening lease & financial liabilities %', 'sched', 'pct', ae_in=V0['ll_rate'],
      note='Lease interest plus facility / bank fees (FY25 financial expenses CHF 29m on ~CHF 0.5bn liabilities).')
    S('ls_yield', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=V0['cash_yield'], note='FY25 financial income ≈ 3.3% of average cash (USD / EUR deposits).')
    S('rf_h', 'Share count & pricing', 'sub', 'gen')
    S('ds_dil', '  Dilutive securities (m Class A-equivalent shares; options, RSUs, PSUs)', 'sched', 'm1', ae_in=2.0)
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.10)
    S('hr_h', 'Historical reference (driver context)', 'sub', 'gen')
    S('hr_dda', '  Total D&A % of net sales', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('hr_lease', '  Lease principal payments % of net sales', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_lease")}),IFERROR(-{V("cf_lease")}/{V("is_rev")},""),"")')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on Adjusted EBIT; invested capital incl. lease liabilities)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT (Adjusted EBITDA − D&A)', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (20% normalised where not meaningful)', 'line', 'pct', ann=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("is_etr")}),{V("is_etr")}>0.05,{V("is_etr")}<0.4),{V("is_etr")},0.2)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt (incl. leases)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = lease & financial liabilities − cash', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ls_ll")}-{V("bs_cash")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Net sales', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Net sales / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − effective tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_ta', '  Total assets', 'line', 'm1', ann=True, all=lambda: f'={V("bs_ta")}')
    S('rn_cash', '  − Cash', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(-{V("bs_cash")},"n/a")')
    S('rn_nibcl', '  − Non-interest-bearing current liabilities (trade payables & other operating)', 'line', 'm1', ann=True,
      all=lambda: f'=IFERROR(-({V("bs_ap")}+{V("bs_ocl")}),"n/a")')
    S('rn_nta', '  = Net operating assets (excl. cash)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR(SUM({V("rn_ta")}:{V("rn_nibcl")}),"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / net operating assets', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")',
      note='On has minimal goodwill / acquired intangibles, so tangible returns are measured on operating assets excluding cash.')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe_ni', 'Net income', 'line', 'm1', ann=True, all=lambda: f'={V("is_ni")}')
    S('roe_eq', 'Total equity', 'line', 'm1', ann=True, all=lambda: f'={V("ra_eq")}')
    S('roe', 'ROE = Net income / Equity', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("roe_ni")}/{V("roe_eq")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt incl. lease liabilities (negative = net cash)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (company definition)', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / Adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_pxu', 'Share price (USD, NYSE: ONON) — current', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_pxu")}')
    S('v_fx', 'USD/CHF (CHF per USD) — spot input', 'sched', 'm2', e26_in=V0['usdchf'], ae=lambda: f'={P("v_fx")}',
      note='Investor Day: "CHF 5.6 billion … approaching USD 7 billion" and USD 65m ≈ CHF 53m imply ~0.80–0.82.')
    S('v_px', 'Share price (CHF) = USD price × USD/CHF', 'sched', 'm2', e26=lambda: f'={V("v_pxu")}*{V("v_fx")}', ae=lambda: f'={V("v_pxu")}*{V("v_fx")}')
    S('v_sh', 'Diluted Class A-equivalent shares at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}+({Q2}{R["sh_dil"]}-{Q2}{R["sh_basic"]})',
      ae=lambda: f'={V("bb_end")}+N({V("ds_dil")})')
    S('v_mc', 'Market capitalisation (CHF m)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt incl. lease liabilities (CHF m)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_ndx', 'Net debt excl. lease liabilities (CHF m; DCF bridge — UFCF deducts lease payments)', 'line', 'm',
      e26=lambda: f'=-{V("bs_cash")}', ae=lambda: f'=-{V("bs_cash")}')
    S('v_nci', 'Noncontrolling interests (CHF m)', 'line', 'm', e26_in=0.0, ae_in=0.0)
    S('v_ev', 'Enterprise value (CHF m; IFRS 16 basis, incl. leases)', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")',
      ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_nd")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Net sales', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (IFRS diluted)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (adjusted diluted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
