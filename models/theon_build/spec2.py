"""Row specification part 2: cash flow, debt schedule & leverage-floor buybacks, share schedule, balance sheet, working capital,
fixed-asset / intangible schedules, ratios, valuation."""
from fw import *
from spec import CH, PT, SC, ratio, growth, nsum

def h26(key):   # 1H/26 actual for a flow row
    return f'({Q1}{R[key]}+{Q2}{R[key]})'
def B2(key): return f'{Q2}{R[key]}'      # 30-Jun-2026 balance
def H2(key): return f'({Q3}{R[key]}+{Q4}{R[key]})'   # 2H/26E from the P&L quarters
def yr(): return CTX.col.year
def D(key):     # change in a balance vs the opening balance (2026E: vs 30-Jun-2026)
    return f'({V(key)}-{B2(key) if CTX.col.kind == "E26" else P(key)})'

def build_spec2(V0):
    S = add
    # ------------------------------------------------------------------ CASH FLOW
    S('sec_cf', 'CONSOLIDATED STATEMENT OF CASH FLOWS (condensed to the trading-update presentation)', 'section',
      note='CASH FLOW — forecast logic (2026E = 1H/26 actual + 2H estimate; quarters = discrete, derived from year-to-date statements; FY2021 not published)')
    S('cf_ni', 'Profit for the period after tax', 'line', 'm1', data='cf_ni', flow=True, e26=lambda: f'={h26("cf_ni")}+{H2("is_ni")}', ae=lambda: f'={V("is_ni")}')
    S('cf_nonc', '  Non-cash items (D&A, tax and net finance add-backs, fair-value gains, share of associates, impairments)', 'line', 'm1', data='cf_nonc', flow=True,
      e26=lambda: f'={h26("cf_nonc")}+{H2("d_dna")}+{H2("is_tax")}+{H2("is_fcost")}-{H2("is_finc")}-{H2("d_assoc")}',
      ae=lambda: f'={V("d_dna")}+{V("is_tax")}+{V("is_fcost")}-{V("is_finc")}-{V("d_assoc")}',
      note='As printed in the Q1 / 9M updates ("Non cash items"); for H1 / FY statements = cash generated before working capital − profit after tax (derived).')
    S('cf_wc', '  Change in working capital (inventories, receivables, prepayments, payables, contract liabilities)', 'line', 'm1', data='cf_wc', flow=True,
      e26=lambda: f'={h26("cf_wc")}-{D("bs_ar")}-{D("bs_inv")}-{D("bs_oca")}+{D("bs_ap")}+{D("bs_ocl")}',
      ae=lambda: f'=-{D("bs_ar")}-{D("bs_inv")}-{D("bs_oca")}+{D("bs_ap")}+{D("bs_ocl")}', note='Linked to the balance sheet. 2026E = 1H/26 actual + 2H change from 30-Jun-26.')
    S('cf_tax', '  Income tax paid', 'line', 'm1', data='cf_tax', flow=True, e26=lambda: f'={h26("cf_tax")}-{H2("is_tax")}', ae=lambda: f'=-{V("is_tax")}')
    S('cf_int', '  Interest paid', 'line', 'm1', data='cf_int', flow=True, e26=lambda: f'={h26("cf_int")}-{H2("is_fcost")}', ae=lambda: f'=-{V("is_fcost")}')
    S('cf_cfo', 'Net cash from operating activities', 'line_b', 'm1', data='cf_cfo', flow=True, fc=lambda: f'=SUM({V("cf_ni")}:{V("cf_int")})')
    S('cf_capex', 'Payments for property, plant & equipment, intangible assets and investment property', 'line', 'm1', data='cf_capex', flow=True,
      e26=lambda: f'=-{PT("pt_capex")}', ae=lambda: f'=-{V("is_rev")}*{V("capex_pct")}',
      note='2026E: company capex guidance EUR 30m (incl. the new Greek platform-products facility; unverified). 2027E+: revenue × capex % (mid-term target c.4% of revenue).')
    S('cf_acq', 'Acquisitions and investments (business combinations, associates, financial assets)', 'line', 'm1', data='cf_acq', flow=True,
      e26=lambda: f'={h26("cf_acq")}-{V("me_px")}', ae=lambda: f'=-{V("hg_ev")}-{V("ma_sp")}',
      note='1H/26: Exosens 9.8% (EUR 268.7m), Kappa (EUR 62.8m net of cash), associates. 2H/26E: MERIO (assumed price). 2027E: HGH EV; 2028E+: bolt-on lever.')
    S('cf_oinv', 'Other investing (interest and dividends received, term deposits, disposals, loans) (derived)', 'line', 'm1', data='cf_oinv', flow=True,
      e26=lambda: f'={h26("cf_oinv")}+{H2("is_finc")}', ae=lambda: f'={V("is_finc")}', note='Forecast: interest received = finance income (no fair-value changes forecast).')
    S('cf_cfi', 'Net cash used in investing activities', 'line_b', 'm1', data='cf_cfi', flow=True, fc=lambda: f'=SUM({V("cf_capex")}:{V("cf_oinv")})')
    S('cf_debt', 'Net proceeds from / (repayment of) borrowings', 'line', 'm1', data='cf_debt', flow=True,
      e26=lambda: f'={h26("cf_debt")}+{V("dt_tl")}+{V("dt_plug")}', ae=lambda: f'={V("dt_tl")}+{V("dt_plug")}')
    S('cf_lease', 'Lease payments (principal)', 'line', 'm1', data='cf_lease', flow=True, e26=lambda: f'=2*{h26("cf_lease")}',
      ae=lambda: f'={P("cf_lease")}*(1+{V("gm_rev")})')
    S('cf_eq', 'Proceeds from share capital increases (IPO Feb-2024; rights issue Dec-2025)', 'line', 'm1', data='cf_eq', flow=True,
      e26=lambda: f'={h26("cf_eq")}', ae_in=0.0)
    S('cf_bb', 'Treasury shares and share buy-back agreement payments', 'line', 'm1', data='cf_bb', flow=True,
      e26=lambda: f'={h26("cf_bb")}', ae=lambda: f'=-{V("bb_cash")}')
    S('cf_div', 'Dividends paid', 'line', 'm1', data='cf_div', flow=True, e26=lambda: f'={h26("cf_div")}', ae=lambda: f'=-{P("dps")}*{P("bb_end")}',
      note='Paid in June on the prior year: 2026E = EUR 24.07m paid (FY2025 EUR 0.31/share). 2027E+: prior-year DPS × prior year-end shares.')
    S('cf_ofin', 'Other financing (derived)', 'line', 'm1', data='cf_ofin', flow=True, e26=lambda: f'={h26("cf_ofin")}', ae_in=0.0)
    S('cf_cff', 'Net cash from / (used in) financing activities', 'line_b', 'm1', data='cf_cff', flow=True, fc=lambda: f'=SUM({V("cf_debt")}:{V("cf_ofin")})')
    S('cf_net', 'Net change in cash and cash equivalents', 'line', 'm1', data='cf_net', flow=True,
      hist=lambda: f'=IF(ISNUMBER({V("cf_cfo")}),{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")},"")', fc=lambda: f'={V("cf_cfo")}+{V("cf_cfi")}+{V("cf_cff")}')
    S('cf_beg', 'Cash and cash equivalents — beginning of period (cash-flow basis)', 'line', 'm1', data='cf_beg', e26=lambda: f'={Q1}{R["cf_beg"]}', ae=lambda: f'={P("cf_end")}',
      note='2026E begins from the opening cash used by the 2026 statements (EUR 256.820m; the FY2025 cash-flow statement netted a EUR 0.007m overdraft).')
    S('cf_fx', 'Foreign exchange differences', 'line', 'm1', data='cf_fx', flow=True, e26=lambda: f'={h26("cf_fx")}', ae_in=0.0)
    S('cf_end', 'Cash and cash equivalents — end of period (cash-flow basis, net of overdrafts)', 'line_b', 'm1', data='cf_end',
      fc=lambda: f'={V("cf_beg")}+{V("cf_net")}+{V("cf_fx")}')
    S('cf_chk1', '  Check: beginning + CFO + CFI + CFF + FX = ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_beg")}),ISNUMBER({V("cf_cfo")})),IF(ABS({V("cf_beg")}+{V("cf_net")}+{V("cf_fx")}-{V("cf_end")})<=0.002,0,ROUND({V("cf_beg")}+{V("cf_net")}+{V("cf_fx")}-{V("cf_end")},3)),"")')
    S('cf_chk2', '  Check: CFO = sum of operating lines (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("cf_ni")}),IF(ABS(SUM({V("cf_ni")}:{V("cf_int")})-{V("cf_cfo")})<=0.002,0,ROUND(SUM({V("cf_ni")}:{V("cf_int")})-{V("cf_cfo")},3)),"")')
    S('cf_memo', '(Memo)', 'sub', 'gen')
    S('fcf', 'Free cash flow (CFO − capex − lease payments; model definition)', 'total', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("cf_cfo")}),ISNUMBER({V("cf_capex")})),{V("cf_cfo")}+{V("cf_capex")}+{V("cf_lease")},"")',
      note='THEON publishes "cash conversion" = (adjusted EBITDA − capex) ÷ adjusted EBITDA (memo below), not a free-cash-flow figure.')
    S('fcf_m', '  FCF % of revenue', 'pct', 'pct', all=ratio('fcf', 'is_rev'))
    S('fcf_conv', '  FCF / profit attributable %', 'pct', 'pct', all=ratio('fcf', 'is_nip'))
    S('cc_pub', '  Cash conversion, company definition: (adjusted EBITDA + capex) ÷ adjusted EBITDA', 'pct', 'pct',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_adj")}),ISNUMBER({V("cf_capex")})),IFERROR(({V("r_adj")}+{V("cf_capex")})/{V("r_adj")},""),"")',
      note='Company figures: FY2025 84.5%, FY2024 88.5%, Q1-26 87.8%; the model uses current-definition adjusted EBITDA, so pre-2025 periods differ slightly.')
    S('capex_pct', '  Capex % of revenue', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("cf_capex")}),IFERROR(-{V("cf_capex")}/{V("is_rev")},""),"")',
      ae_in=V0['capex_pct'], note='2027E+ input: company mid-term target "c.4% of revenue" (unverified).')
    S('capex_dep', '  Capex / D&A (x)', 'line', 'x2', all=lambda: f'=IF(AND(ISNUMBER({V("cf_capex")}),ISNUMBER({V("d_dna")})),IFERROR(-{V("cf_capex")}/{V("d_dna")},""),"")')
    blank()

    # ------------------------------------------------------------------ DEBT SCHEDULE & BUYBACKS
    S('sec_dt', 'DEBT SCHEDULE, CASH SWEEP AND LEVERAGE-FLOOR BUYBACKS (interest on opening balances; no circularity)', 'section',
      note='DEBT — EUR 300m RCF (5-year from Oct-2025, 1M Euribor + 1.5%; fully drawn) and the EUR 325m HGH term loan (drawn at HGH closing); surplus cash above the minimum repays debt; buybacks only below the leverage floor')
    S('dt_beg', '  Bank debt — beginning of period', 'sched', 'm1', e26=lambda: f'={B2("bs_debt")}', ae=lambda: f'={P("bs_debt")}',
      note='2026E begins at 30-Jun-2026 (current + non-current loans and borrowings).')
    S('dt_tl', '  HGH term loan drawn (EUR m)', 'sched', 'm1', e26_in=0.0, ae=lambda: f'=IF({V("hg_ev")}>0,{PT("pt_tl")},0)',
      note='Company: HGH "entirely funded through debt"; EUR 325m syndicated senior unsecured term loan (Alpha Bank coordinator).')
    S('dt_pre', '  Cash before buybacks and the debt sweep', 'sched', 'm1',
      e26=lambda: (f'={B2("bs_cash")}+({V("cf_cfo")}-{h26("cf_cfo")})+({V("cf_cfi")}-{h26("cf_cfi")})+({V("cf_lease")}-{h26("cf_lease")})'
                   f'+({V("cf_eq")}-{h26("cf_eq")})+({V("cf_div")}-{h26("cf_div")})+({V("cf_ofin")}-{h26("cf_ofin")})+{V("dt_tl")}'),
      ae=lambda: f'={V("cf_beg")}+{V("cf_cfo")}+{V("cf_cfi")}+{V("cf_lease")}+{V("cf_eq")}+{V("cf_div")}+{V("cf_ofin")}+{V("cf_fx")}+{V("dt_tl")}')
    S('dt_ndpre', '  Net debt before buybacks (bank debt + leases − cash − term deposits)', 'sched', 'm1',
      fc=lambda: f'={V("dt_beg")}+{V("dt_tl")}+{V("bs_lease")}+{V("bs_bbl")}-{V("dt_pre")}-{V("bs_td")}')
    S('dt_floor', '  Leverage floor for buybacks: net debt / adjusted EBITDA (x, scenario)', 'driver', 'x2', e26=lambda: f'={CH(SC["lv_floor"])}', ae=lambda: f'={CH(SC["lv_floor"])}',
      note='Assumption (THEON has no open-market programme; treasury purchases serve the LTIP). Buybacks only when net debt falls below floor × adjusted EBITDA.')
    S('bb_cash', '  Share buybacks (EUR m) = MAX(0, floor × adjusted EBITDA − net debt before buybacks)', 'sched', 'm1',
      e26_in=0.0, ae=lambda: f'=MAX(0,{V("dt_floor")}*{V("r_adj")}-{V("dt_ndpre")})')
    S('dt_min', '  Minimum cash balance (EUR m)', 'driver', 'm1', e26=lambda: f'={PT("pt_mincash")}', ae=lambda: f'={PT("pt_mincash")}')
    S('dt_plug', '  Debt draw / (repayment) to minimum cash (cash sweep)', 'sched', 'm1',
      fc=lambda: f'=MAX({V("dt_min")}-({V("dt_pre")}-{V("bb_cash")}),-({V("dt_beg")}+{V("dt_tl")}))',
      note='Draws when cash would fall below the minimum (labelled financing assumption: the RCF is fully drawn, upsizable to EUR 400m); otherwise repays debt down to zero.')
    S('dt_end', '  Bank debt — end of period', 'sched', 'm1', fc=lambda: f'={V("dt_beg")}+{V("dt_tl")}+{V("dt_plug")}')
    S('dt_head', '  Memo: committed facilities (RCF EUR 300m + HGH term loan) − drawn debt (negative = draw beyond committed lines)', 'memo_calc', 'm1',
      fc=lambda: (f'=300+IF({V("hg_on")}>0,{PT("pt_tl")},0)-{V("dt_end")}' if CTX.col.kind == 'AE' else f'=300-{V("dt_end")}'))
    S('ls_rate', '  Interest rate on opening bank debt %', 'sched', 'pct', ae_in=V0['debt_rate'],
      note='RCF 1M Euribor + 1.5% (≈3.5%) plus commitment / arrangement fees and other finance costs; H1-26 finance costs EUR 10.0m on c.EUR 330m average debt ≈ 6% annualised. Base 5.0% (assumption).')
    S('ls_yield', '  Interest income yield on opening cash %', 'sched', 'pct', ae_in=V0['cash_yield'], note='H1-26 interest income ex fair-value gains ≈ EUR 1.5m.')
    blank()

    # ------------------------------------------------------------------ SHARES
    S('sec_bb', 'SHARE SCHEDULE', 'section', note='SHARES — 78,624,645 issued (30-Jun-2026) less treasury shares; buybacks from the leverage-floor rule above')
    S('bb_beg', '  Beginning shares outstanding (m)', 'line', 'm1', e26=lambda: f'={MAN["shares"]["H1-26"]}', ae=lambda: f'={P("bb_end")}',
      note='2026E begins from the H1-26 weighted average (77.59m = 78.62m issued less c.1.0m treasury shares) as the 30-Jun-2026 proxy.')
    S('bb_px', '  Average buyback price (EUR)', 'line', 'm2', e26=lambda: f'={V("v_px")}', ae=lambda: f'={P("bb_px")}*(1+{V("ds_pxg")})')
    S('bb_sh', '  Shares repurchased (m)', 'line', 'm2', e26=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)', ae=lambda: f'=IFERROR({V("bb_cash")}/{V("bb_px")},0)')
    S('bb_end', '  Ending shares outstanding (m)', 'line', 'm1', e26=lambda: f'={V("bb_beg")}-{V("bb_sh")}', ae=lambda: f'={V("bb_beg")}-{V("bb_sh")}')
    S('ds_pxg', '  Share-price appreciation % (buyback pricing)', 'sched', 'pct', ae_in=0.08)
    blank()

    # ------------------------------------------------------------------ BALANCE SHEET
    S('sec_bs', 'CONSOLIDATED STATEMENT OF FINANCIAL POSITION (condensed)', 'section',
      note='BS — "other" lines derived so totals tie to reported; 2026E rolled forward from 30-Jun-2026 + 2H flows; 2027E+ from the prior year end. Quarter ends from Q1-24 (2023 quarter-end balance sheets not published).')
    S('bs_a', 'ASSETS', 'sub', 'gen')
    S('bs_cash', '  Cash and cash equivalents', 'line', 'm1', data='bs_cash', bs=True, fc=lambda: f'={V("cf_end")}+N({V("bs_od")})',
      note='Forecast = cash-flow closing cash + the overdraft netted in the cash-flow statement (held at the last balance; the overdraft sits in loans and borrowings).')
    S('bs_td', '  Term deposits', 'line', 'm1', data='bs_td', bs=True, e26=lambda: f'={B2("bs_td")}', ae=lambda: f'={P("bs_td")}')
    S('bs_ar', '  Trade accounts receivable', 'line', 'm1', data='bs_ar', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_dso")}/365', note='Revenue × DSO / 365.')
    S('bs_inv', '  Inventories', 'line', 'm1', data='bs_inv', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dio")}/365')
    S('bs_oca', '  Other receivables, prepayments & other current assets (derived)', 'line', 'm1', data='bs_oca', bs=True, fc=lambda: f'={V("wc_rev")}*{V("wc_ocap")}')
    S('bs_ppe', '  Property, plant & equipment (incl. investment property)', 'line', 'm1', data='bs_ppe', bs=True,
      e26=lambda: f'={B2("bs_ppe")}-({V("cf_capex")}-{h26("cf_capex")})-{V("fa_dep")}',
      ae=lambda: f'={P("bs_ppe")}-{V("cf_capex")}-{V("fa_dep")}', note='Roll-forward: prior + capex − depreciation (schedule below).')
    S('bs_rou', '  Right-of-use assets', 'line', 'm1', data='bs_rou', bs=True, e26=lambda: f'={B2("bs_rou")}', ae=lambda: f'={P("bs_rou")}',
      note='Held flat (new leases = principal repayments = right-of-use depreciation; immaterial, < EUR 5m).')
    S('bs_intang', '  Intangible assets and goodwill', 'line', 'm1', data='bs_intang', bs=True,
      e26=lambda: f'={B2("bs_intang")}+{V("me_px")}-{V("fa_am2h")}',
      ae=lambda: f'={P("bs_intang")}+{V("hg_ev")}+{V("ma_sp")}-{V("fa_am")}',
      note='Acquisitions booked fully to goodwill & intangibles (acquired net working capital ignored; assumption). H1-26: Kappa goodwill EUR 37.6m and intangibles EUR 27.1m.')
    S('bs_fin', '  Equity-accounted investees and other financial assets (Exosens, Kopin, loans)', 'line', 'm1', data='bs_fin', bs=True,
      e26=lambda: f'={B2("bs_fin")}+{H2("d_assoc")}', ae=lambda: f'={P("bs_fin")}+{V("d_assoc")}',
      note='Non-operating investments: Exosens 9.8% at fair value (FVTPL), Kopin shares, associates. Forecast: + share of associates; no fair-value changes.')
    S('bs_onca', '  Deferred tax and other non-current assets (derived)', 'line', 'm1', data='bs_onca', bs=True, e26=lambda: f'={B2("bs_onca")}', ae=lambda: f'={P("bs_onca")}')
    S('bs_ta', 'TOTAL ASSETS', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_cash")}),SUM({V("bs_cash")}:{V("bs_onca")}),"")')
    S('bs_l', 'LIABILITIES AND EQUITY', 'sub', 'gen')
    S('bs_debt', '  Loans and borrowings (current + non-current)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_dc")}),{V("bs_dc")}+{V("bs_dnc")},"")', fc=lambda: f'={V("dt_end")}')
    S('bs_lease', '  Lease liabilities (current + non-current)', 'line', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_lc")}),{V("bs_lc")}+{V("bs_lnc")},"")', e26=lambda: f'={B2("bs_lease")}', ae=lambda: f'={P("bs_lease")}')
    S('bs_bbl', '  Amount owed for share buy-back (pre-IPO agreement)', 'line', 'm1', data='bs_bbl', bs=True, e26=lambda: f'={B2("bs_bbl")}', ae=lambda: f'={P("bs_bbl")}',
      note='Liability from the pre-IPO share buy-back agreement (EUR 13.6m at YE2023, settled by 2025); THEON counts it in debt.')
    S('bs_ap', '  Trade accounts payable', 'line', 'm1', data='bs_ap', bs=True, fc=lambda: f'={V("wc_cogs")}*{V("wc_dpo")}/365')
    S('bs_ocl', '  Contract liabilities, income tax payable, accrued & other current liabilities (derived)', 'line', 'm1', data='bs_ocl', bs=True,
      fc=lambda: f'={V("wc_rev")}*{V("wc_oclp")}')
    S('bs_oncl', '  Staff indemnities, grants, deferred tax & other non-current liabilities (derived)', 'line', 'm1', data='bs_oncl', bs=True,
      e26=lambda: f'={B2("bs_oncl")}', ae=lambda: f'={P("bs_oncl")}')
    S('bs_tl', 'Total liabilities', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_debt")}),SUM({V("bs_debt")}:{V("bs_oncl")}),"")')
    S('bs_eqp', '  Equity attributable to owners of the Company', 'line', 'm1', data='bs_eqp', bs=True,
      e26=lambda: f'={B2("bs_eqp")}+{H2("is_nip")}+({V("cf_div")}-{h26("cf_div")})+({V("cf_bb")}-{h26("cf_bb")})+({V("cf_eq")}-{h26("cf_eq")})',
      ae=lambda: f'={P("bs_eqp")}+{V("is_nip")}+{V("cf_div")}+{V("cf_bb")}+{V("cf_eq")}', note='Roll-forward: + profit attributable − dividends − buybacks + share issues (no OCI forecast).')
    S('bs_nci', '  Non-controlling interests', 'line', 'm1', data='bs_nci', bs=True, e26=lambda: f'={B2("bs_nci")}+{H2("is_nci")}', ae=lambda: f'={P("bs_nci")}+{V("is_nci")}',
      note='Harder Digital 40% minority. MERIO\'s 20% minority is not modelled (assumption; immaterial).')
    S('bs_teq', 'Total equity', 'line_b', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_eqp")}),{V("bs_eqp")}+{V("bs_nci")},"")')
    S('bs_tle', 'TOTAL LIABILITIES AND EQUITY', 'total', 'm1', all=lambda: f'=IF(ISNUMBER({V("bs_tl")}),{V("bs_tl")}+{V("bs_teq")},"")')
    S('bs_chk', 'BS tie-out check (TA − TL&E; should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ta")}),IF(ABS({V("bs_ta")}-{V("bs_tle")})<=0.002,0,ROUND({V("bs_ta")}-{V("bs_tle")},3)),"")')
    S('bs_chk_ta', '  Check: model total assets vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("bs_ta_pub")}),IF(ABS({V("bs_ta")}-{V("bs_ta_pub")})<=0.002,0,ROUND({V("bs_ta")}-{V("bs_ta_pub")},3)),"")')
    S('bs_ta_pub', '  Memo: total assets as reported', 'memo', 'm1', data='bs_ta', bs=True)
    S('bs_te_pub', '  Memo: total equity as reported', 'memo', 'm1', data='bs_teq', bs=True)
    S('bs_dc', '  Memo: loans and borrowings — current', 'memo', 'm1', data='bs_debt_c', bs=True)
    S('bs_dnc', '  Memo: loans and borrowings — non-current', 'memo', 'm1', data='bs_debt_nc', bs=True)
    S('bs_lc', '  Memo: lease liabilities — current', 'memo', 'm1', data='bs_lease_c', bs=True)
    S('bs_lnc', '  Memo: lease liabilities — non-current', 'memo', 'm1', data='bs_lease_nc', bs=True)
    S('bs_od', '  Memo: BS cash − cash-flow closing cash (bank overdrafts netted in the cash-flow statement; derived)', 'memo', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),{V("bs_cash")}-{V("cf_end")},"")',
      e26=lambda: f'={B2("bs_od")}', ae=lambda: f'={P("bs_od")}')
    S('bs_chk_cash', '  Check: BS cash − overdraft memo vs cash-flow ending cash (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(AND(ISNUMBER({V("bs_cash")}),ISNUMBER({V("cf_end")})),IF(ABS({V("bs_cash")}-N({V("bs_od")})-{V("cf_end")})<=0.002,0,ROUND({V("bs_cash")}-N({V("bs_od")})-{V("cf_end")},3)),"")')
    blank()

    # ------------------------------------------------------------------ WORKING CAPITAL
    S('sec_wc', 'WORKING CAPITAL', 'section', note='WORKING CAPITAL — forecast drivers (blue = input) at FY2025 year-end levels (defence deliveries are Q4-weighted, so quarter ends are not comparable)')
    S('wc_rev', '  Revenue — annualised (quarters × 4)', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}*{4 if CTX.col.q else 1},"")')
    S('wc_cogs', '  Cost of sales — annualised', 'line', 'm1', all=lambda: f'=IF(ISNUMBER({V("is_cogs")}),{V("is_cogs")}*{4 if CTX.col.q else 1},"")')
    S('wc_dso', '  DSO — trade receivables / revenue × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ar")}/{V("wc_rev")}*365,"")', e26_in=V0['wc']['dso'], ae_in=V0['wc']['dso'])
    S('wc_dio', '  Inventory days — inventories / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_inv")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dio'], ae_in=V0['wc']['dio'])
    S('wc_dpo', '  Payable days — trade payables / cost of sales × 365', 'line', 'd', hist=lambda: f'=IFERROR({V("bs_ap")}/{V("wc_cogs")}*365,"")', e26_in=V0['wc']['dpo'], ae_in=V0['wc']['dpo'])
    S('wc_ocap', '  Other current assets % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_oca")}/{V("wc_rev")},"")', e26_in=V0['wc']['oca'], ae_in=V0['wc']['oca'])
    S('wc_oclp', '  Other current liabilities % of revenue', 'pct', 'pct', hist=lambda: f'=IFERROR({V("bs_ocl")}/{V("wc_rev")},"")',
      e26_in=V0['wc']['ocl'], ae_in=V0['wc']['ocl'], note=V0['wc']['note'])
    S('wc_nwc', '  Net working capital (trade receivables + inventories − trade payables)', 'line', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("bs_ar")}),{V("bs_ar")}+{V("bs_inv")}-{V("bs_ap")},"")')
    S('wc_nwc_p', '  NWC % of revenue (annualised)', 'pct', 'pct', all=lambda: f'=IF(ISNUMBER({V("wc_nwc")}),IFERROR({V("wc_nwc")}/{V("wc_rev")},""),"")',
      note='Company "NWC absorption (% of LTM revenues)": FY2025 41.0%, FY2024 44.2%, Q1-26 41.1% (company definition differs slightly).')
    blank()

    # ------------------------------------------------------------------ SCHEDULES
    S('sec_sch', 'BALANCE SHEET FORECAST SCHEDULES', 'section', note='BS FORECAST SCHEDULES — explicit driver assumptions')
    S('fa_h', 'Depreciation and amortisation split', 'sub', 'gen')
    S('fa_am', '  Amortisation of acquired intangibles (Kappa run-rate + HGH PPA + bolt-ons)', 'sched', 'm1',
      e26=lambda: f'={V0["amort_kappa"]}', ae=lambda: f'={V0["amort_kappa"]}+N({V("hg_amort")})+N({V("ma_sp")})*0.25/10',
      note='Kappa: H1-26 amortisation of intangibles EUR 1.86m → EUR 3.7m p.a. (assumption). HGH from the deal block. Bolt-ons: 25% of spend amortised over 10 years (assumption).')
    S('fa_am2h', '  Amortisation — 2H/26E', 'sched', 'm1', e26=lambda: f'={V("fa_am")}/2')
    S('fa_rdep', '  Right-of-use depreciation (= lease payments)', 'sched', 'm1', e26=lambda: f'=-({V("cf_lease")}-{h26("cf_lease")})', ae=lambda: f'=-{V("cf_lease")}')
    S('fa_dep', '  Depreciation of PP&E (D&A − amortisation − right-of-use)', 'sched', 'm1',
      e26=lambda: f'={H2("d_dna")}-{V("fa_am2h")}-{V("fa_rdep")}', ae=lambda: f'={V("d_dna")}-{V("fa_am")}-{V("fa_rdep")}',
      note='2026E = 2H only (the balance sheet rolls forward from 30-Jun-2026).')
    blank()

    # ------------------------------------------------------------------ RATIOS
    S('sec_ra', 'RATIO ANALYSIS', 'section', note='RETURNS — annual columns (NOPAT on adjusted EBIT; invested capital excludes non-operating investments)')
    S('ra_h', 'DuPont decomposition of ROIC', 'sub', 'gen')
    S('ra_ebit', 'Adjusted EBIT', 'line', 'm1', ann=True, all=lambda: f'={V("r_ebit")}')
    S('ra_t', 'Effective tax rate (23% normalised where not meaningful)', 'line', 'pct', ann=True,
      all=lambda: f'=IF(AND(ISNUMBER({V("is_etr")}),{V("is_etr")}>0.15,{V("is_etr")}<0.35),{V("is_etr")},0.23)')
    S('ra_nopat', 'NOPAT = Adjusted EBIT × (1 − tax rate)', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}*(1-{V("ra_t")}),"n/a")')
    S('ra_ic', 'Invested capital (IC) = Equity + Net debt − non-operating investments', 'line', 'm1', ann=True, all=lambda: f'=IFERROR({V("ra_eq")}+{V("ra_nd")}-{V("ra_inv")},"n/a")')
    S('ra_eq', '  Total equity', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_teq")}),{V("bs_teq")},"n/a")')
    S('ra_nd', '  Net debt = loans + leases + buy-back liability − cash − term deposits', 'line', 'm1', ann=True,
      all=lambda: f'=IFERROR({V("bs_debt")}+{V("bs_lease")}+{V("bs_bbl")}-{V("bs_cash")}-{V("bs_td")},"n/a")')
    S('ra_inv', '  Non-operating investments (equity-accounted investees and financial assets)', 'line', 'm1', ann=True, all=lambda: f'=IF(ISNUMBER({V("bs_fin")}),{V("bs_fin")},"n/a")')
    S('ra_roic', 'ROIC = NOPAT / IC', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_nopat")}/{V("ra_ic")},"n/a")')
    S('ra_mg', '  Margin = Adjusted EBIT / Revenue', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_ebit")}/{V("is_rev")},"n/a")')
    S('ra_to', '  Capital turnover = Revenue / IC', 'line', 'x2', ann=True, all=lambda: f'=IFERROR({V("is_rev")}/{V("ra_ic")},"n/a")')
    S('ra_tb', '  Tax burden = (1 − effective tax rate)', 'line', 'pct', ann=True, all=lambda: f'=IFERROR(1-{V("ra_t")},"n/a")')
    S('ra_chk', '  Check: Margin × Turnover × Tax burden = ROIC', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("ra_mg")}*{V("ra_to")}*{V("ra_tb")},"n/a")')
    S('rn_h', 'RONTA decomposition', 'sub', 'gen')
    S('rn_nopat', 'NOPAT', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nopat")}')
    S('rn_nta', '  Net tangible operating assets = TA − cash − deposits − investments − intangibles − (payables + other current liabilities)', 'line', 'm1', ann=True,
      all=lambda: f'=IFERROR({V("bs_ta")}-{V("bs_cash")}-{V("bs_td")}-{V("bs_fin")}-{V("bs_intang")}-{V("bs_ap")}-{V("bs_ocl")},"n/a")')
    S('rn_ronta', 'RONTA = NOPAT / net tangible operating assets', 'total', 'pct', ann=True, all=lambda: f'=IFERROR({V("rn_nopat")}/{V("rn_nta")},"n/a")')
    S('roe_h', 'Return on Equity (ROE)', 'sub', 'gen')
    S('roe', 'ROE = Profit attributable / equity attributable', 'line', 'pct', ann=True, all=lambda: f'=IFERROR({V("is_nip")}/{V("bs_eqp")},"n/a")')
    S('lv_h', 'Leverage', 'sub', 'gen')
    S('lv_nd', 'Net debt (negative = net cash)', 'line', 'm1', ann=True, all=lambda: f'={V("ra_nd")}')
    S('lv_eb', 'Adjusted EBITDA (current definition)', 'line', 'm1', ann=True, all=lambda: f'={V("r_adj")}')
    S('lv_x', 'Net debt / adjusted EBITDA (x)', 'total', 'x2', ann=True, all=lambda: f'=IFERROR({V("lv_nd")}/{V("lv_eb")},"n/a")',
      note='Company: pro forma c.3.0x after HGH, lowering to c.2.5x by 2027 (Q2/H1-26 update; unverified). Company net debt includes leases and the buy-back liability.')
    S('lv_pf', 'Memo: net debt / adjusted EBITDA pro forma for HGH (2026E: + EV EUR 300m debt-funded, + HGH standalone EBITDA)', 'line', 'x2', ann=True,
      e26=lambda: f'=IFERROR(({V("lv_nd")}+{PT("pt_hg_on")}*{PT("pt_hg_ev")})/({V("lv_eb")}+{PT("pt_hg_on")}*{PT("pt_hg_rev")}*{PT("pt_hg_m")}),"n/a")',
      note='Compare: company "pro-forma level of c.3.0x before lowering to c.2.5x by 2027" (Q2/H1-26 update; unverified).')
    blank()

    # ------------------------------------------------------------------ VALUATION
    S('sec_val', 'VALUATION', 'section', note=V0['px_note'])
    S('v_px', 'Share price (EUR, Euronext Amsterdam: THEON)', 'sched', 'm2', e26_in=V0['px'], ae=lambda: f'={P("v_px")}',
      note=V0['px_cell_note'])
    S('v_sh', 'Shares outstanding at period end (m)', 'line', 'm1', e26=lambda: f'={V("bb_end")}', ae=lambda: f'={V("bb_end")}')
    S('v_mc', 'Market capitalisation (EUR m)', 'line', 'm', e26=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")', ae=lambda: f'=IFERROR({V("v_px")}*{V("v_sh")},"n/a")')
    S('v_nd', 'Net debt (EUR m)', 'line', 'm', e26=lambda: f'={V("lv_nd")}', ae=lambda: f'={V("lv_nd")}')
    S('v_ndx', 'Net debt less non-operating investments (EUR m; DCF / EV bridge)', 'line', 'm',
      e26=lambda: f'={V("lv_nd")}-{V("ra_inv")}', ae=lambda: f'={V("lv_nd")}-{V("ra_inv")}',
      note='Exosens (FVTPL), Kopin, associates and loans are carried at book / fair value outside invested capital and deducted from EV (UBER precedent).')
    S('v_nci', 'Non-controlling interests (book, EUR m)', 'line', 'm', e26=lambda: f'={V("bs_nci")}', ae=lambda: f'={V("bs_nci")}')
    S('v_ev', 'Enterprise value (EUR m) = market cap + net debt − investments + NCI', 'line_b', 'm', e26=lambda: f'=IFERROR({V("v_mc")}+{V("v_ndx")}+{V("v_nci")},"n/a")',
      ae=lambda: f'=IFERROR({V("v_mc")}+{V("v_ndx")}+{V("v_nci")},"n/a")')
    S('v_mh', 'Multiples', 'sub', 'gen')
    for k, lab, f in [('v_evs', '  EV / Revenue', lambda: f'=IFERROR({V("v_ev")}/{V("is_rev")},"n/a")'),
                      ('v_eveb', '  EV / Adjusted EBITDA', lambda: f'=IFERROR({V("v_ev")}/{V("r_adj")},"n/a")'),
                      ('v_evop', '  EV / Adjusted EBIT', lambda: f'=IFERROR({V("v_ev")}/{V("r_ebit")},"n/a")'),
                      ('v_evic', '  EV / IC', lambda: f'=IFERROR({V("v_ev")}/{V("ra_ic")},"n/a")'),
                      ('v_pe', '  P / E (IFRS EPS)', lambda: f'=IFERROR({V("v_px")}/{V("eps_dil")},"n/a")'),
                      ('v_pea', '  P / E (model adjusted EPS)', lambda: f'=IFERROR({V("v_px")}/{V("e_eps")},"n/a")'),
                      ('v_fcfy', '  FCF yield', lambda: f'=IFERROR({V("fcf")}/{V("v_mc")},"n/a")'),
                      ('v_dy', '  Dividend yield', lambda: f'=IFERROR({V("dps")}/{V("v_px")},"n/a")')]:
        S(k, lab, 'line', 'pct' if k in ('v_fcfy', 'v_dy') else 'x', e26=f, ae=f)
